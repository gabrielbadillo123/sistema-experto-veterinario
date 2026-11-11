"""Capa de datos: consultas GRANULARES a la base SistemaExpertoVet (SQL Server).

Cada método es una consulta pequeña y parametrizada sobre las tablas de la
base de conocimiento (hipotesis, regla, premisa, sintoma, sistema y
parametro_inferencia). El motor las invoca sucesivamente en cada ciclo de
razonamiento; no carga reglas como condicionales en el código.

Solo se consideran las reglas activas (regla.activa = 1), de modo que las
reglas que el experto desactiva (CU-05) dejan de participar en la inferencia.
"""
from typing import Dict, Iterable, List, Optional

from inferencia.modelo.entidades import Hipotesis, Sintoma

# Fragmento común: gránulos de nivel 2 (premisas de tipo síntoma de reglas activas)
_GRANULOS = ("FROM premisa p "
             "JOIN regla r ON r.id_regla = p.id_regla "
             "JOIN hipotesis h ON h.id_hipotesis = r.id_hipotesis "
             "WHERE r.nivel = 2 AND r.activa = 1 AND p.tipo = 'sintoma' ")


class RepositorioConocimientoSQL:
    def __init__(self, bd):
        self.bd = bd                 # base_datos.Conexion (pyodbc)
        self.num_consultas = 0       # evidencia de las consultas sucesivas

    def _filas(self, sql, params=()):
        self.num_consultas += 1
        return self.bd.filas(sql, tuple(params))

    # Q1: hipótesis finales de la especie con su P(H) a priori
    def hipotesis_de_especie(self, id_especie: str) -> List[Hipotesis]:
        filas = self._filas(
            "SELECT h.id_hipotesis, r.id_regla, h.nombre, h.id_sistema, h.urgencia, "
            "h.recomendacion, h.prob_apriori "
            "FROM hipotesis h JOIN regla r ON r.id_hipotesis = h.id_hipotesis "
            "WHERE h.tipo = 'final' AND r.nivel = 2 AND r.activa = 1 AND h.id_especie = ? "
            "ORDER BY r.id_regla", (id_especie,))
        return [Hipotesis(int(i), reg, n, s, u, rec, float(p) if p is not None else 0.0)
                for i, reg, n, s, u, rec, p in filas]

    # Q2: síntomas de la especie que aún no se han preguntado
    def sintomas_candidatos(self, id_especie: str, excluidos: Iterable[str]) -> List[Sintoma]:
        excluidos = list(excluidos)
        filtro = ""
        if excluidos:
            filtro = "AND s.id_sintoma NOT IN (" + ",".join("?" * len(excluidos)) + ") "
        filas = self._filas(
            "SELECT DISTINCT s.id_sintoma, s.pregunta, s.id_sistema "
            "FROM premisa p "
            "JOIN regla r ON r.id_regla = p.id_regla "
            "JOIN hipotesis h ON h.id_hipotesis = r.id_hipotesis "
            "JOIN sintoma s ON s.id_sintoma = p.id_sintoma "
            "WHERE r.nivel = 2 AND r.activa = 1 AND p.tipo = 'sintoma' AND h.id_especie = ? "
            + filtro + "ORDER BY s.id_sintoma",
            (id_especie, *excluidos))
        return [Sintoma(*f) for f in filas]

    # Q3: gránulos de UN síntoma -> {id_hipotesis: P(s|H)}
    def verosimilitudes_de_sintoma(self, id_especie: str, id_sintoma: str) -> Dict[int, float]:
        filas = self._filas(
            "SELECT r.id_hipotesis, p.verosimilitud " + _GRANULOS +
            "AND h.id_especie = ? AND p.id_sintoma = ?", (id_especie, id_sintoma))
        return {int(h): float(v) if v is not None else 0.85 for h, v in filas}

    # Q4: gránulos de UNA hipótesis (explicación del resultado)
    def granulos_de_hipotesis(self, id_hipotesis: int) -> Dict[str, float]:
        filas = self._filas(
            "SELECT p.id_sintoma, p.verosimilitud " + _GRANULOS + "AND r.id_hipotesis = ?",
            (id_hipotesis,))
        return {s: float(v) if v is not None else 0.85 for s, v in filas}

    # Q5: nombre de la hipótesis intermedia (sistema afectado)
    def nombre_sistema(self, id_sistema: str) -> str:
        filas = self._filas("SELECT nombre FROM sistema WHERE id_sistema = ?", (id_sistema,))
        return filas[0][0] if filas else id_sistema

    # Q6: parámetro del motor
    def parametro(self, clave: str, defecto: Optional[float] = None) -> float:
        filas = self._filas("SELECT valor FROM parametro_inferencia WHERE clave = ?", (clave,))
        return float(filas[0][0]) if filas else defecto

    # Q7: especies con conocimiento cargado
    def especies(self):
        return self._filas("SELECT id_especie, nombre FROM especie ORDER BY id_especie")


class RepositorioConsultasSQL:
    """Persistencia de la consulta en el sistema transaccional existente
    (animal, consulta, consulta_sintoma, diagnostico y bitacora)."""

    def __init__(self, bd):
        self.bd = bd

    def guardar(self, resultado, nombre_animal="Sin nombre") -> int:
        import base_datos
        import sistema_experto_veterinario as sev
        intermedias, _ = base_datos.ids_hipotesis()
        bd = self.bd
        id_animal = bd.insertar("INSERT INTO animal (id_propietario, id_especie, nombre) "
                                "OUTPUT INSERTED.id_animal VALUES (?, ?, ?)",
                                (base_datos.ID_PROPIETARIO_GENERICO, resultado.especie, nombre_animal))
        id_consulta = bd.insertar("INSERT INTO consulta (id_animal, id_usuario, estado, observaciones) "
                                  "OUTPUT INSERTED.id_consulta VALUES (?, ?, ?, ?)",
                                  (id_animal, base_datos.ID_INVITADO, "diagnosticada",
                                   f"Motor bayesiano: {len(resultado.pasos)} preguntas. "
                                   f"{resultado.motivo_parada}"))
        confirmados = set()
        for paso in resultado.pasos:                 # memoria de trabajo (no sé no se guarda)
            if paso.respuesta in ("si", "no"):
                bd.ejecutar("INSERT INTO consulta_sintoma (id_consulta, id_sintoma, presente) "
                            "VALUES (?, ?, ?)",
                            (id_consulta, paso.sintoma.id_sintoma, 1 if paso.respuesta == "si" else 0))
                if paso.respuesta == "si":
                    confirmados.add(paso.sintoma.id_sintoma)
        for rs in sev.REGLAS_SISTEMA:                # hipótesis intermedias activadas (nivel 1)
            if rs.especie == resultado.especie and rs.signo in confirmados:
                bd.ejecutar("INSERT INTO diagnostico (id_consulta, id_hipotesis, id_regla) "
                            "VALUES (?, ?, ?)",
                            (id_consulta, intermedias[(rs.especie, rs.sistema)], rs.id))
        for r in resultado.hipotesis:                # las 5 hipótesis finales con su probabilidad
            bd.ejecutar("INSERT INTO diagnostico (id_consulta, id_hipotesis, id_regla, coincidencia, posicion) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (id_consulta, r.hipotesis.id_hipotesis, r.hipotesis.id_regla,
                         round(r.probabilidad * 100, 2), r.posicion))
        bd.ejecutar("INSERT INTO bitacora (id_usuario, accion, detalle) VALUES (?, ?, ?)",
                    (base_datos.ID_INVITADO, "CONSULTA",
                     f"Consulta {id_consulta} ({resultado.especie}) - inferencia bayesiana"))
        bd.confirmar()
        return id_consulta
