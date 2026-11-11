"""Capa de datos: misma interfaz de consultas granulares (Q1..Q7) pero sobre
la base de conocimiento interna de sistema_experto_veterinario.py.

Se usa cuando SQL Server no está disponible (RNF03): el diagnóstico sigue
funcionando con el mismo motor, aunque la consulta no se guarde.
"""
from typing import Dict, Iterable, List, Optional

import sistema_experto_veterinario as sev
from inferencia.capa_datos import conocimiento_probabilistico as cp
from inferencia.modelo.entidades import Hipotesis, Sintoma


class RepositorioConocimientoMemoria:
    def __init__(self, reglas=None):
        self.reglas = [r for r in (reglas or sev.REGLAS)]
        self.sistema_de = {s: sis for sis, (_, voc) in sev.SISTEMAS.items() for s in voc}
        self.parametros = {c: v for c, v, _ in cp.PARAMETROS}
        self.num_consultas = 0

    def _contar(self):
        self.num_consultas += 1

    @staticmethod
    def _id(regla) -> int:
        return 100 + int(regla.id[1:])          # mismo id que en la tabla hipotesis

    def hipotesis_de_especie(self, id_especie: str) -> List[Hipotesis]:        # Q1
        self._contar()
        return [Hipotesis(self._id(r), r.id, r.enfermedad, r.sistema, r.urgencia,
                          r.recomendacion, cp.prob_apriori(r))
                for r in self.reglas if r.especie == id_especie]

    def sintomas_candidatos(self, id_especie: str, excluidos: Iterable[str]) -> List[Sintoma]:  # Q2
        self._contar()
        excluidos = set(excluidos)
        ids = sorted({s for r in self.reglas if r.especie == id_especie for s in r.sintomas} - excluidos)
        return [Sintoma(s, sev.PREGUNTAS.get(s, f"¿Presenta '{s}'?"), self.sistema_de.get(s, ""))
                for s in ids]

    def verosimilitudes_de_sintoma(self, id_especie: str, id_sintoma: str) -> Dict[int, float]:  # Q3
        self._contar()
        return {self._id(r): cp.verosimilitud(r, id_sintoma)
                for r in self.reglas if r.especie == id_especie and id_sintoma in r.sintomas}

    def granulos_de_hipotesis(self, id_hipotesis: int) -> Dict[str, float]:   # Q4
        self._contar()
        r = next(r for r in self.reglas if self._id(r) == id_hipotesis)
        return {s: cp.verosimilitud(r, s) for s in r.sintomas}

    def nombre_sistema(self, id_sistema: str) -> str:                           # Q5
        self._contar()
        return sev.SISTEMAS[id_sistema][0] if id_sistema in sev.SISTEMAS else id_sistema

    def parametro(self, clave: str, defecto: Optional[float] = None) -> float:  # Q6
        self._contar()
        return self.parametros.get(clave, defecto)

    def especies(self):                                                          # Q7
        self._contar()
        presentes = {r.especie for r in self.reglas}
        return [(e, n) for e, n in sev.NOMBRES_ESPECIE.items() if e in presentes]
