#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 SISTEMA EXPERTO VETERINARIO -- CAPA DE BASE DE DATOS
================================================================================

SGBD: Microsoft SQL Server 2022 Express (servidor GABO\\SQLEXPRESS, base de
datos SistemaExpertoVet), con autenticacion de Windows mediante pyodbc.
El servidor/base se pueden cambiar en bd/config.ini (seccion [sqlserver]).

Ejecutar este archivo directamente:
    python base_datos.py
  1. Genera bd/02_carga_conocimiento.sql a partir del conocimiento del experto
     (reglas de sistema_experto_veterinario.py).
  2. Instala la BD en SQL Server ejecutando bd/01..04 (esquema, carga,
     consultas de granulos y roles).
  3. Verifica que las reglas leidas desde la BD sean las del experto.
  4. Dibuja el modelo relacional en bd/modelo_relacional.png.
  5. Muestra los granulos de conocimiento por hipotesis.
================================================================================
"""

import configparser
import hashlib
import os
import re
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sistema_experto_veterinario as sev

CARPETA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bd")
RUTA_CONFIG = os.path.join(CARPETA_BD, "config.ini")
SERVIDOR_POR_DEFECTO = r"GABO\SQLEXPRESS"


# =============================================================================
# 1. ROLES, PERMISOS Y USUARIOS INICIALES
# =============================================================================

ROLES = [
    ("Administrador", "Administra usuarios, roles, respaldos y la configuracion del sistema."),
    ("Ingeniero del conocimiento", "Adquiere el conocimiento del experto, lo codifica en reglas, "
                                   "mantiene la base de conocimiento y el arbol de decision."),
    ("Experto", "Medico veterinario: aporta y valida el conocimiento (reglas) y valida "
                "los diagnosticos emitidos por el sistema."),
    ("Usuario final", "Propietario, productor o asistente: registra animales, responde "
                      "las preguntas y consulta el diagnostico y las recomendaciones."),
]

PERMISOS = [
    ("ADMIN_USUARIOS", "Alta, baja y cambio de usuarios y asignacion de roles"),
    ("ADMIN_RESPALDOS", "Respaldar y restaurar la base de datos"),
    ("BC_EDITAR", "Crear, modificar y desactivar reglas, premisas, sintomas e hipotesis"),
    ("BC_CONSULTAR", "Consultar reglas, granulos de conocimiento y arbol de decision"),
    ("BC_VALIDAR", "Aprobar el conocimiento capturado en la base de conocimiento"),
    ("CONSULTA_CREAR", "Registrar propietario/animal y realizar una consulta diagnostica"),
    ("CONSULTA_VER_PROPIAS", "Ver el historial de sus propias consultas"),
    ("CONSULTA_VER_TODAS", "Ver el historial de todas las consultas"),
    ("DIAGNOSTICO_VALIDAR", "Confirmar o descartar el diagnostico emitido por el sistema"),
    ("REPORTES", "Generar reportes y estadisticas"),
]

ROL_PERMISOS = {
    "Administrador": [p for p, _ in PERMISOS],
    "Ingeniero del conocimiento": ["BC_EDITAR", "BC_CONSULTAR", "CONSULTA_VER_TODAS", "REPORTES"],
    "Experto": ["BC_CONSULTAR", "BC_VALIDAR", "CONSULTA_CREAR", "CONSULTA_VER_TODAS",
                "DIAGNOSTICO_VALIDAR", "REPORTES"],
    "Usuario final": ["CONSULTA_CREAR", "CONSULTA_VER_PROPIAS"],
}

# (rol, nombre, correo, contrasena de demostracion, cedula)
USUARIOS_INICIALES = [
    ("Administrador", "Administrador del sistema", "admin@vet.local", "admin123", None),
    ("Ingeniero del conocimiento", "Ingeniero del conocimiento", "ic@vet.local", "ic123", None),
    ("Experto", "MVZ Experto humano", "experto@vet.local", "experto123", "MVZ-000001"),
    ("Usuario final", "Usuario invitado", "invitado@vet.local", "invitado123", None),
]
ID_EXPERTO = 3      # usuario que aporto las reglas cargadas
ID_INVITADO = 4     # usuario con el que la GUI registra las consultas
ID_PROPIETARIO_GENERICO = 1


def hash_contrasena(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# =============================================================================
# 2. CARGA DEL CONOCIMIENTO DEL EXPERTO (generacion de INSERTs portables)
# =============================================================================

def _q(valor) -> str:
    """Literal T-SQL (cadenas Unicode con prefijo N)."""
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float)):
        return str(valor)
    return "N'" + str(valor).replace("'", "''") + "'"


def _insert(tabla: str, columnas: List[str], filas: List[tuple], identidad: bool = False) -> List[str]:
    """INSERT multi-renglon; `identidad` permite fijar el valor de una
    columna IDENTITY (SET IDENTITY_INSERT)."""
    if not filas:
        return []
    cab = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES"
    valores = [f"  ({', '.join(_q(v) for v in fila)})" for fila in filas]
    lineas = [cab, ",\n".join(valores) + ";"]
    if identidad:
        lineas = [f"SET IDENTITY_INSERT {tabla} ON;"] + lineas + [f"SET IDENTITY_INSERT {tabla} OFF;"]
    return lineas + [""]


def ids_hipotesis() -> Tuple[Dict[Tuple[str, str], int], Dict[str, int]]:
    """Ids de hipotesis: intermedias (especie, sistema) -> 1..N;
    finales: regla R### -> 100 + ###."""
    intermedias, n = {}, 0
    for especie in sev.NOMBRES_ESPECIE:
        for sistema in sev.SISTEMAS:
            if any(r.especie == especie and r.sistema == sistema for r in sev.REGLAS):
                n += 1
                intermedias[(especie, sistema)] = n
    finales = {r.id: 100 + int(r.id[1:]) for r in sev.REGLAS}
    return intermedias, finales


def generar_script_carga() -> str:
    lineas = [
        "-- =============================================================================",
        "--  CARGA DEL CONOCIMIENTO DEL EXPERTO HUMANO Y DATOS INICIALES",
        "--  Archivo GENERADO por base_datos.py a partir de sistema_experto_veterinario.py",
        "--  (no editar a mano). SQL Server 2022.",
        f"--  {len(sev.REGLAS_SISTEMA)} reglas de nivel 1 + {len(sev.REGLAS)} reglas de nivel 2",
        "-- =============================================================================",
        "USE SistemaExpertoVet;",
        "GO",
        "",
        "-- ---------- Roles, permisos y usuarios ----------",
    ]
    lineas += _insert("rol", ["id_rol", "nombre", "descripcion"],
                      [(i, n, d) for i, (n, d) in enumerate(ROLES, 1)], identidad=True)
    lineas += _insert("permiso", ["id_permiso", "clave", "descripcion"],
                      [(i, c, d) for i, (c, d) in enumerate(PERMISOS, 1)], identidad=True)
    id_rol = {n: i for i, (n, _) in enumerate(ROLES, 1)}
    id_perm = {c: i for i, (c, _) in enumerate(PERMISOS, 1)}
    lineas += _insert("rol_permiso", ["id_rol", "id_permiso"],
                      [(id_rol[r], id_perm[p]) for r, ps in ROL_PERMISOS.items() for p in ps])
    lineas += _insert("usuario", ["id_usuario", "id_rol", "nombre", "correo", "contrasena_hash",
                                  "cedula_profesional"],
                      [(i, id_rol[r], n, c, hash_contrasena(p), ced)
                       for i, (r, n, c, p, ced) in enumerate(USUARIOS_INICIALES, 1)], identidad=True)
    lineas += _insert("propietario", ["id_propietario", "id_usuario", "nombre"],
                      [(ID_PROPIETARIO_GENERICO, ID_INVITADO, "Publico general (consultas anonimas)")],
                      identidad=True)

    lineas.append("-- ---------- Base de conocimiento: catalogos ----------")
    lineas += _insert("especie", ["id_especie", "nombre"], list(sev.NOMBRES_ESPECIE.items()))
    lineas += _insert("sistema", ["id_sistema", "nombre"],
                      [(s, nombre) for s, (nombre, _) in sev.SISTEMAS.items()])
    sistema_de = {s: sis for sis, (_, voc) in sev.SISTEMAS.items() for s in voc}
    lineas += _insert("sintoma", ["id_sintoma", "pregunta", "id_sistema"],
                      [(s, p, sistema_de[s]) for s, p in sorted(sev.PREGUNTAS.items())])

    lineas.append("-- ---------- Hipotesis (intermedias y finales) ----------")
    intermedias, finales = ids_hipotesis()
    filas = [(i, "intermedia", f"Afeccion del sistema {sev.SISTEMAS[s][0]}", e, s, None, None)
             for (e, s), i in intermedias.items()]
    filas += [(finales[r.id], "final", r.enfermedad, r.especie, r.sistema, r.urgencia,
               r.recomendacion) for r in sev.REGLAS]
    lineas += _insert("hipotesis", ["id_hipotesis", "tipo", "nombre", "id_especie", "id_sistema",
                                    "urgencia", "recomendacion"], filas)

    lineas.append("-- ---------- Reglas de produccion ----------")
    reglas = [(rs.id, 1, intermedias[(rs.especie, rs.sistema)], ID_EXPERTO)
              for rs in sev.REGLAS_SISTEMA]
    reglas += [(r.id, 2, finales[r.id], ID_EXPERTO) for r in sev.REGLAS]
    lineas += _insert("regla", ["id_regla", "nivel", "id_hipotesis", "id_experto"], reglas)

    lineas.append("-- ---------- Premisas (condiciones SI de cada granulo) ----------")
    premisas = []
    for rs in sev.REGLAS_SISTEMA:
        premisas.append((rs.id, 1, "especie", rs.especie, None, None))
        premisas.append((rs.id, 2, "sintoma", None, rs.signo, None))
    for r in sev.REGLAS:
        premisas.append((r.id, 1, "especie", r.especie, None, None))
        premisas.append((r.id, 2, "hipotesis", None, None, intermedias[(r.especie, r.sistema)]))
        for k, s in enumerate(sorted(r.sintomas), 3):
            premisas.append((r.id, k, "sintoma", None, s, None))
    cols = ["id_regla", "orden", "tipo", "id_especie", "id_sintoma", "id_hipotesis"]
    for i in range(0, len(premisas), 200):          # bloques para no hacer un INSERT gigante
        lineas += _insert("premisa", cols, premisas[i:i + 200])
    lineas.append("GO")
    return "\n".join(lineas)


# =============================================================================
# 3. CONEXION A SQL SERVER
# =============================================================================

def _cadena_conexion(base: str = None) -> str:
    """Cadena ODBC. Por defecto: GABO\\SQLEXPRESS, autenticacion de Windows."""
    config = configparser.ConfigParser()
    config.read(RUTA_CONFIG, encoding="utf-8")
    c = config["sqlserver"] if config.has_section("sqlserver") else {}
    partes = [f"DRIVER={{{c.get('driver', 'ODBC Driver 17 for SQL Server')}}}",
              f"SERVER={c.get('server', SERVIDOR_POR_DEFECTO)}",
              f"DATABASE={base or c.get('database', 'SistemaExpertoVet')}",
              "TrustServerCertificate=yes"]
    if c.get("user"):
        partes += [f"UID={c.get('user')}", f"PWD={c.get('password', '')}"]
    else:
        partes.append("Trusted_Connection=yes")
    return ";".join(partes) + ";"


class Conexion:
    """Envoltura minima sobre pyodbc."""

    motor = "SQL Server"

    def __init__(self, con):
        self.con = con

    def ejecutar(self, sql: str, params: tuple = ()):
        cur = self.con.cursor()
        cur.execute(sql, params)
        return cur

    def filas(self, sql: str, params: tuple = ()) -> list:
        return [tuple(f) for f in self.ejecutar(sql, params).fetchall()]

    def insertar(self, sql: str, params: tuple = ()) -> int:
        """Ejecuta un INSERT ... OUTPUT INSERTED.<id> y devuelve el id generado."""
        return int(self.ejecutar(sql, params).fetchone()[0])

    def confirmar(self):
        self.con.commit()

    def cerrar(self):
        self.con.close()


def conectar() -> Conexion:
    import pyodbc
    return Conexion(pyodbc.connect(_cadena_conexion(), timeout=5))


def ejecutar_script(con, ruta: str) -> None:
    """Ejecuta un archivo .sql separado en lotes por lineas 'GO' (como SSMS)."""
    with open(ruta, encoding="utf-8") as f:
        lotes = re.split(r"^\s*GO\s*$", f.read(), flags=re.MULTILINE | re.IGNORECASE)
    cur = con.cursor()
    for lote in lotes:
        if lote.strip():
            cur.execute(lote)
            while cur.nextset():      # descarta los resultados de los SELECT
                pass


def instalar_bd() -> None:
    """Crea/reinstala SistemaExpertoVet en el servidor con los scripts 01..04."""
    import pyodbc
    con = pyodbc.connect(_cadena_conexion("master"), autocommit=True, timeout=5)
    try:
        for nombre in ("01_esquema.sql", "02_carga_conocimiento.sql",
                       "03_consultas_granulos.sql", "04_roles.sql"):
            ejecutar_script(con, os.path.join(CARPETA_BD, nombre))
            print(f"  ejecutado {nombre}")
    finally:
        con.close()


# =============================================================================
# 4. LECTURA DE LA BASE DE CONOCIMIENTO DESDE LA BD
# =============================================================================

def cargar_base_conocimiento(bd: Conexion) -> Tuple[List[sev.Regla], List[sev.ReglaSistema]]:
    """Reconstruye las reglas (nivel 1 y 2) a partir de las tablas regla/premisa."""
    premisas: Dict[str, list] = {}
    for id_regla, tipo, id_especie, id_sintoma in bd.filas(
            "SELECT p.id_regla, p.tipo, p.id_especie, p.id_sintoma FROM premisa p "
            "JOIN regla r ON r.id_regla = p.id_regla WHERE r.activa = 1 ORDER BY p.id_regla, p.orden"):
        premisas.setdefault(id_regla, []).append((tipo, id_especie, id_sintoma))

    reglas, reglas_sistema = [], []
    for id_regla, nivel, nombre, especie, sistema, urgencia, recomendacion in bd.filas(
            "SELECT r.id_regla, r.nivel, h.nombre, h.id_especie, h.id_sistema, h.urgencia, "
            "h.recomendacion FROM regla r JOIN hipotesis h ON h.id_hipotesis = r.id_hipotesis "
            "WHERE r.activa = 1 ORDER BY r.id_regla"):
        sintomas = [s for t, _, s in premisas.get(id_regla, []) if t == "sintoma"]
        if nivel == 1:
            reglas_sistema.append(sev.ReglaSistema(id_regla, especie, sintomas[0], sistema))
        else:
            reglas.append(sev.Regla(id_regla, especie, nombre, frozenset(sintomas),
                                    recomendacion, urgencia, sistema))
    reglas_sistema.sort(key=lambda r: r.id)
    return reglas, reglas_sistema


# =============================================================================
# 5. CONSULTAS DE GRANULOS DE CONOCIMIENTO POR HIPOTESIS
# =============================================================================
#
# Granulo de conocimiento = una regla completa: sus premisas (SI ...) y la
# hipotesis que concluye (ENTONCES ...). Se agrupan por hipotesis.

SQL_GRANULOS = """
SELECT h.id_hipotesis, h.tipo, h.nombre, h.id_especie, h.id_sistema, h.urgencia,
       r.id_regla, r.nivel, p.orden, p.tipo,
       COALESCE(p.id_especie, p.id_sintoma, hp.nombre) AS valor
FROM hipotesis h
JOIN regla r        ON r.id_hipotesis = h.id_hipotesis AND r.activa = 1
JOIN premisa p      ON p.id_regla = r.id_regla
LEFT JOIN hipotesis hp ON hp.id_hipotesis = p.id_hipotesis
WHERE (? IS NULL OR h.id_especie = ?)
  AND (? IS NULL OR h.id_hipotesis = ?)
  AND (? IS NULL OR h.tipo = ?)
ORDER BY h.id_hipotesis, r.id_regla, p.orden
"""


def granulos_por_hipotesis(bd: Conexion, especie: str = None, id_hipotesis: int = None,
                           tipo: str = None) -> List[dict]:
    """Devuelve una lista de hipotesis, cada una con sus granulos (reglas)."""
    resultado: Dict[int, dict] = {}
    for (idh, tipo_h, nombre, esp, sis, urg, id_regla, nivel, _orden, tipo_p, valor) in bd.filas(
            SQL_GRANULOS, (especie, especie, id_hipotesis, id_hipotesis, tipo, tipo)):
        h = resultado.setdefault(idh, {"id": idh, "tipo": tipo_h, "nombre": nombre,
                                       "especie": esp, "sistema": sis, "urgencia": urg,
                                       "granulos": {}})
        g = h["granulos"].setdefault(id_regla, {"nivel": nivel, "premisas": []})
        g["premisas"].append((tipo_p, valor))
    return list(resultado.values())


def texto_granulos(bd: Conexion, especie: str = None, tipo: str = None) -> str:
    def premisa_txt(tipo_p, valor):
        return {"especie": f"especie = {valor}", "sintoma": f"presenta {valor}",
                "hipotesis": f"[{valor}]"}[tipo_p]

    hipotesis = granulos_por_hipotesis(bd, especie=especie, tipo=tipo)
    lineas = [f"GRANULOS DE CONOCIMIENTO POR HIPOTESIS  ({len(hipotesis)} hipotesis, "
              f"{sum(len(h['granulos']) for h in hipotesis)} granulos)",
              f"Motor de BD: {bd.motor}", "=" * 78]
    for h in hipotesis:
        extra = f" | urgencia {h['urgencia']}" if h["urgencia"] else ""
        lineas.append(f"\nH{h['id']:03d} ({h['tipo']}) {h['nombre']}  "
                      f"[{h['especie']} / {h['sistema']}{extra}]")
        for id_regla, g in h["granulos"].items():
            premisas = " Y ".join(premisa_txt(t, v) for t, v in g["premisas"])
            lineas.append(f"   {id_regla}: SI {premisas}")
            lineas.append(f"   {' ' * len(id_regla)}  ENTONCES {h['nombre']}")
    return "\n".join(lineas)


# =============================================================================
# 6. SISTEMA TRANSACCIONAL: REGISTRO DE CONSULTAS
# =============================================================================

def guardar_consulta(bd: Conexion, memoria: "sev.MemoriaDeTrabajo", sintomas_preguntados: List[str],
                     resultados: list, id_usuario: int = ID_INVITADO,
                     nombre_animal: str = "Sin nombre", id_propietario: int = ID_PROPIETARIO_GENERICO,
                     top: int = 5) -> int:
    """Persiste una consulta completa: animal, respuestas, hipotesis inferidas."""
    intermedias, finales = ids_hipotesis()
    id_animal = bd.insertar("INSERT INTO animal (id_propietario, id_especie, nombre) "
                            "OUTPUT INSERTED.id_animal VALUES (?, ?, ?)",
                            (id_propietario, memoria.especie, nombre_animal))
    id_consulta = bd.insertar("INSERT INTO consulta (id_animal, id_usuario, estado) "
                              "OUTPUT INSERTED.id_consulta VALUES (?, ?, ?)",
                              (id_animal, id_usuario, "diagnosticada" if resultados else "abierta"))
    for s in sintomas_preguntados:
        bd.ejecutar("INSERT INTO consulta_sintoma (id_consulta, id_sintoma, presente) VALUES (?, ?, ?)",
                    (id_consulta, s, 1 if memoria.contiene(s) else 0))
    for rs in sev.REGLAS_SISTEMA:   # hipotesis intermedias deducidas (regla de nivel 1 disparada)
        if rs.especie == memoria.especie and rs.signo in memoria.sistemas.get(rs.sistema, ()):
            bd.ejecutar("INSERT INTO diagnostico (id_consulta, id_hipotesis, id_regla) VALUES (?, ?, ?)",
                        (id_consulta, intermedias[(rs.especie, rs.sistema)], rs.id))
    for pos, (regla, porcentaje, _) in enumerate(resultados[:top], 1):
        bd.ejecutar("INSERT INTO diagnostico (id_consulta, id_hipotesis, id_regla, coincidencia, posicion) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (id_consulta, finales[regla.id], regla.id, round(porcentaje * 100, 2), pos))
    bd.ejecutar("INSERT INTO bitacora (id_usuario, accion, detalle) VALUES (?, ?, ?)",
                (id_usuario, "CONSULTA", f"Consulta {id_consulta} ({memoria.especie})"))
    bd.confirmar()
    return id_consulta


def texto_historial(bd: Conexion, limite: int = 30) -> str:
    filas = bd.filas(
        f"SELECT TOP ({int(limite)}) c.id_consulta, c.fecha, a.id_especie, u.nombre, c.estado, h.nombre, d.coincidencia "
        "FROM consulta c JOIN animal a ON a.id_animal = c.id_animal "
        "JOIN usuario u ON u.id_usuario = c.id_usuario "
        "LEFT JOIN diagnostico d ON d.id_consulta = c.id_consulta AND d.posicion = 1 "
        "LEFT JOIN hipotesis h ON h.id_hipotesis = d.id_hipotesis "
        "ORDER BY c.id_consulta DESC")
    lineas = [f"HISTORIAL DE CONSULTAS (ultimas {limite}) -- motor de BD: {bd.motor}", "=" * 78]
    if not filas:
        lineas.append("Aun no hay consultas registradas.")
    for idc, fecha, esp, usuario, estado, hip, coinc in filas:
        dx = f"{hip} ({coinc:.0f}%)" if hip else "sin diagnostico"
        lineas.append(f"#{idc:<4} {fecha:%Y-%m-%d %H:%M}  {esp:<8} {estado:<13} {usuario:<20} -> {dx}")
    return "\n".join(lineas)


# =============================================================================
# 7. DIAGRAMA DEL MODELO RELACIONAL (M-R)
# =============================================================================

# Posicion (columna, fila) de cada tabla en el diagrama
_LAYOUT_MR = {
    "especie": (0, 0), "sistema": (0, 1), "sintoma": (0, 2),
    "hipotesis": (1, 0), "regla": (1, 1), "premisa": (1, 2),
    "diagnostico": (2, 0), "consulta": (2, 1), "consulta_sintoma": (2, 2),
    "animal": (3, 0), "propietario": (3, 1), "bitacora": (3, 2),
    "usuario": (4, 0), "rol": (4, 1), "rol_permiso": (4, 2), "permiso": (4, 3),
}


def generar_diagrama_mr(bd: Conexion,
                        ruta_png: str = os.path.join(CARPETA_BD, "modelo_relacional.png")) -> str:
    """Dibuja el M-R leyendo el catalogo de SQL Server (sys.columns / sys.foreign_keys)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    columnas, fks = {}, []
    for tabla, columna, tipo, es_pk, es_fk in bd.filas("""
            SELECT t.name, c.name, ty.name,
                   CASE WHEN EXISTS (SELECT 1 FROM sys.index_columns ic
                                     JOIN sys.indexes i ON i.object_id = ic.object_id
                                                       AND i.index_id = ic.index_id
                                     WHERE i.is_primary_key = 1 AND ic.object_id = t.object_id
                                       AND ic.column_id = c.column_id) THEN 1 ELSE 0 END,
                   CASE WHEN EXISTS (SELECT 1 FROM sys.foreign_key_columns fc
                                     WHERE fc.parent_object_id = t.object_id
                                       AND fc.parent_column_id = c.column_id) THEN 1 ELSE 0 END
            FROM sys.tables t
            JOIN sys.columns c ON c.object_id = t.object_id
            JOIN sys.types ty  ON ty.user_type_id = c.user_type_id
            ORDER BY t.name, c.column_id"""):
        columnas.setdefault(tabla, []).append((columna, tipo, bool(es_pk), bool(es_fk)))
    fks = bd.filas("""
            SELECT OBJECT_NAME(fk.parent_object_id), COL_NAME(fc.parent_object_id, fc.parent_column_id),
                   OBJECT_NAME(fk.referenced_object_id)
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fc ON fc.constraint_object_id = fk.object_id""")

    ancho_caja, alto_fila, sep_x, sep_y = 4.2, 0.32, 5.4, 1.0
    alto_fila_tabla = {}
    for t, (cx, cy) in _LAYOUT_MR.items():
        alto_fila_tabla[cy] = max(alto_fila_tabla.get(cy, 0), (len(columnas[t]) + 1) * alto_fila)
    y_fila, acumulado = {}, 0
    for fila in sorted(alto_fila_tabla):
        y_fila[fila] = -acumulado
        acumulado += alto_fila_tabla[fila] + sep_y

    fig, ax = plt.subplots(figsize=(27, acumulado * 0.62 + 1.5))
    ax.axis("off")
    cajas = {}
    color_cab = {"bc": "#1f6f78", "tx": "#4a6fa5"}
    tablas_bc = {"especie", "sistema", "sintoma", "hipotesis", "regla", "premisa"}
    for t, (cx, cy) in _LAYOUT_MR.items():
        x, y = cx * sep_x, y_fila[cy]
        alto = (len(columnas[t]) + 1) * alto_fila
        cajas[t] = (x, y, ancho_caja, alto)
        ax.add_patch(FancyBboxPatch((x, y - alto), ancho_caja, alto, boxstyle="round,pad=0.02",
                                    fc="white", ec="#333333", lw=1, zorder=3))
        ax.add_patch(FancyBboxPatch((x, y - alto_fila), ancho_caja, alto_fila,
                                    boxstyle="round,pad=0.02", lw=1, ec="#333333", zorder=4,
                                    fc=color_cab["bc" if t in tablas_bc else "tx"]))
        ax.text(x + ancho_caja / 2, y - alto_fila / 2, t, ha="center", va="center",
                color="white", fontsize=9, fontweight="bold", zorder=5)
        for i, (nombre, tipo, pk, fk) in enumerate(columnas[t], 1):
            marca = ("PK " if pk else "") + ("FK" if fk else "")
            ax.text(x + 0.1, y - alto_fila * (i + 0.5), f"{marca:<6}", fontsize=7,
                    va="center", family="monospace", color="#b3261e", zorder=5)
            ax.text(x + 0.75, y - alto_fila * (i + 0.5), f"{nombre}  {tipo.lower()}",
                    fontsize=7.5, va="center", zorder=5)
    def anclas(caja_o, caja_d):
        xo, yo, wo, ho = caja_o
        xd, yd, wd, hd = caja_d
        if abs(xo - xd) < 1e-6:                      # misma columna: arriba/abajo
            if yo > yd:
                return (xo + wo * 0.7, yo - ho), (xd + wd * 0.7, yd)
            return (xo + wo * 0.7, yo), (xd + wd * 0.7, yd - hd)
        if xo < xd:                                  # destino a la derecha
            return (xo + wo, yo - ho / 2), (xd, yd - min(hd / 2, 0.6))
        return (xo, yo - ho / 2), (xd + wd, yd - min(hd / 2, 0.6))

    for origen, col, destino in fks:
        (x1, y1), (x2, y2) = anclas(cajas[origen], cajas[destino])
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), zorder=6,
                    arrowprops=dict(arrowstyle="-|>", color="#777777", lw=0.9,
                                    connectionstyle="arc3,rad=0.08", shrinkA=0, shrinkB=0))
    ax.set_xlim(-0.3, 4 * sep_x + ancho_caja + 0.3)
    ax.set_ylim(-acumulado, 0.8)
    ax.set_title("Modelo relacional -- Sistema Experto Veterinario  "
                 "(verde azulado: base de conocimiento | azul: sistema transaccional; "
                 "flecha = FK hacia la tabla referenciada)", fontsize=12, loc="left")
    plt.tight_layout()
    plt.savefig(ruta_png, dpi=120)
    plt.close(fig)
    return ruta_png


# =============================================================================
# 8. PROGRAMA PRINCIPAL
# =============================================================================

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(CARPETA_BD, exist_ok=True)
    ruta_carga = os.path.join(CARPETA_BD, "02_carga_conocimiento.sql")
    with open(ruta_carga, "w", encoding="utf-8") as f:
        f.write(generar_script_carga() + "\n")
    print(f"Script de carga generado: {ruta_carga}")

    print(f"Instalando la base de datos en {SERVIDOR_POR_DEFECTO} ...")
    instalar_bd()

    bd = conectar()
    reglas, reglas_sistema = cargar_base_conocimiento(bd)
    assert {(r.id, r.sintomas, r.sistema) for r in reglas} == \
           {(r.id, r.sintomas, r.sistema) for r in sev.REGLAS}, "La BC en BD difiere de la del experto"
    assert reglas_sistema == sev.REGLAS_SISTEMA
    print(f"Verificacion OK: {len(reglas)} reglas de enfermedad y {len(reglas_sistema)} "
          f"reglas de sistema leidas desde la BD ({bd.motor}).")

    print(f"Modelo relacional: {generar_diagrama_mr(bd)}")
    print()
    print(texto_granulos(bd, especie="perro"))
    bd.cerrar()


if __name__ == "__main__":
    main()
