"""Pruebas del motor bayesiano integrado.

    python -m unittest discover -s pruebas -t .
"""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sistema_experto_veterinario as sev
from inferencia.capa_datos import conocimiento_probabilistico as cp
from inferencia.capa_datos.repositorio_memoria import RepositorioConocimientoMemoria
from inferencia.capa_datos.repositorio_sqlserver import RepositorioConocimientoSQL
from inferencia.capa_logica.servicio_diagnostico import ServicioDiagnostico


def simular(servicio, especie, presentes):
    """Paciente virtual: responde 'si' solo a los sintomas que tiene."""
    pregunta = servicio.iniciar(especie)
    while pregunta is not None:
        pregunta = servicio.responder("si" if pregunta.id_sintoma in presentes else "no")
    return servicio.finalizar(guardar=False)


class ConexionSQLite:
    """Imita base_datos.Conexion para probar las consultas SQL sin SQL Server."""
    def __init__(self):
        self.con = sqlite3.connect(":memory:")
        c = self.con
        c.executescript("""
            CREATE TABLE especie (id_especie TEXT PRIMARY KEY, nombre TEXT);
            CREATE TABLE sistema (id_sistema TEXT PRIMARY KEY, nombre TEXT);
            CREATE TABLE sintoma (id_sintoma TEXT PRIMARY KEY, pregunta TEXT, id_sistema TEXT);
            CREATE TABLE hipotesis (id_hipotesis INT PRIMARY KEY, tipo TEXT, nombre TEXT, id_especie TEXT,
                                    id_sistema TEXT, urgencia TEXT, recomendacion TEXT, prob_apriori REAL);
            CREATE TABLE regla (id_regla TEXT PRIMARY KEY, nivel INT, id_hipotesis INT, activa INT DEFAULT 1);
            CREATE TABLE premisa (id_regla TEXT, orden INT, tipo TEXT, id_especie TEXT, id_sintoma TEXT,
                                  id_hipotesis INT, verosimilitud REAL);
            CREATE TABLE parametro_inferencia (clave TEXT PRIMARY KEY, valor REAL, descripcion TEXT);""")
        import base_datos
        inter, finales = base_datos.ids_hipotesis()
        sistema_de = {s: sis for sis, (_, v) in sev.SISTEMAS.items() for s in v}
        c.executemany("INSERT INTO especie VALUES (?,?)", sev.NOMBRES_ESPECIE.items())
        c.executemany("INSERT INTO sistema VALUES (?,?)", [(k, v[0]) for k, v in sev.SISTEMAS.items()])
        c.executemany("INSERT INTO sintoma VALUES (?,?,?)", [(s, p, sistema_de[s]) for s, p in sev.PREGUNTAS.items()])
        c.executemany("INSERT INTO parametro_inferencia VALUES (?,?,?)", cp.PARAMETROS)
        for (e, s), i in inter.items():
            c.execute("INSERT INTO hipotesis VALUES (?,?,?,?,?,NULL,NULL,NULL)", (i, "intermedia", s, e, s))
        for r in sev.REGLAS:
            c.execute("INSERT INTO hipotesis VALUES (?,?,?,?,?,?,?,?)", (finales[r.id], "final", r.enfermedad,
                      r.especie, r.sistema, r.urgencia, r.recomendacion, cp.prob_apriori(r)))
            c.execute("INSERT INTO regla VALUES (?,2,?,1)", (r.id, finales[r.id]))
            c.execute("INSERT INTO premisa VALUES (?,1,'especie',?,NULL,NULL,NULL)", (r.id, r.especie))
            c.execute("INSERT INTO premisa VALUES (?,2,'hipotesis',NULL,NULL,?,NULL)", (r.id, inter[(r.especie, r.sistema)]))
            for k, s in enumerate(sorted(r.sintomas), 3):
                c.execute("INSERT INTO premisa VALUES (?,?,'sintoma',NULL,?,NULL,?)", (r.id, k, s, cp.verosimilitud(r, s)))

    def filas(self, sql, params=()):
        return [tuple(f) for f in self.con.execute(sql, params).fetchall()]


class PruebasInferencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mem = ServicioDiagnostico(RepositorioConocimientoMemoria())
        cls.sql_bd = ConexionSQLite()
        cls.sql = ServicioDiagnostico(RepositorioConocimientoSQL(cls.sql_bd))

    def test_200_reglas_quedan_primeras(self):
        """Con los sintomas exactos de cada regla, su enfermedad queda en 1er lugar."""
        for r in sev.REGLAS:
            with self.subTest(regla=r.id, enfermedad=r.enfermedad):
                res = simular(self.mem, r.especie, r.sintomas)
                self.assertEqual(res.hipotesis[0].hipotesis.id_regla, r.id)

    def test_sql_y_memoria_dan_el_mismo_resultado(self):
        """Las consultas SQL granulares equivalen a la BC interna."""
        for r in sev.REGLAS[::7]:
            with self.subTest(regla=r.id):
                a = simular(self.mem, r.especie, r.sintomas)
                b = simular(self.sql, r.especie, r.sintomas)
                self.assertEqual([x.hipotesis.id_regla for x in a.hipotesis], [x.hipotesis.id_regla for x in b.hipotesis])
                self.assertAlmostEqual(a.hipotesis[0].probabilidad, b.hipotesis[0].probabilidad, places=9)

    def test_cinco_hipotesis_ordenadas(self):
        res = simular(self.mem, "perro", {"vomito", "diarrea_sangre"})
        probs = [h.probabilidad for h in res.hipotesis]
        self.assertEqual(len(probs), 5)
        self.assertEqual(probs, sorted(probs, reverse=True))
        self.assertLessEqual(sum(probs), 1 + 1e-9)

    def test_regla_desactivada_no_participa(self):
        self.sql_bd.con.execute("UPDATE regla SET activa = 0 WHERE id_regla = 'R001'")
        try:
            res = simular(self.sql, "perro", sev.REGLAS[0].sintomas)
            self.assertNotIn("R001", [h.hipotesis.id_regla for h in res.hipotesis])
        finally:
            self.sql_bd.con.execute("UPDATE regla SET activa = 1 WHERE id_regla = 'R001'")

    def test_no_se_no_cambia_la_distribucion(self):
        self.mem.iniciar("gato")
        antes = dict(self.mem.motor.memoria.posterior)
        self.mem.responder("nose")
        self.assertEqual(antes, self.mem.motor.memoria.posterior)


if __name__ == "__main__":
    unittest.main()
