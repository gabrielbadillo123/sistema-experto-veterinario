"""Capa lógica: motor de inferencia probabilístico (Bayes ingenuo).

El motor NO conoce enfermedades ni síntomas. En cada ciclo:
  1. consulta a la BC los síntomas candidatos              (Q2)
  2. por cada candidato consulta sus gránulos P(s|H)        (Q3)
     y estima la ganancia de información esperada
  3. pregunta el síntoma más informativo
  4. con la respuesta vuelve a consultar los gránulos (Q3) y aplica Bayes:
         P(H | e) = P(e | H) · P(H) / Σ_k P(e | H_k) · P(H_k)
  5. evalúa la condición de parada
Al terminar entrega las 5 hipótesis con mayor probabilidad a posteriori.
"""
import math
from typing import Dict, List, Optional, Tuple

from inferencia.modelo.entidades import (PasoInferencia, ResultadoDiagnostico,
                              ResultadoHipotesis, Sintoma)
from inferencia.capa_logica.memoria_trabajo import MemoriaTrabajo


def entropia(distribucion: Dict[str, float]) -> float:
    return -sum(p * math.log2(p) for p in distribucion.values() if p > 0)


class MotorInferenciaBayesiano:
    RESPUESTAS = ("si", "no", "nose")

    def __init__(self, repo_conocimiento):
        self.repo = repo_conocimiento
        self.memoria: Optional[MemoriaTrabajo] = None
        self.motivo_parada = ""
        self._cargar_parametros()

    def _cargar_parametros(self):
        p = self.repo.parametro
        self.p_fuga = p("p_fuga", 0.03)
        self.umbral = p("umbral_confianza", 0.90)
        self.min_preguntas = int(p("min_preguntas", 4))
        self.max_preguntas = int(p("max_preguntas", 15))
        self.ganancia_minima = p("ganancia_minima", 0.005)
        self.num_hipotesis = int(p("num_hipotesis", 5))

    # ------------------------------------------------------------------
    def iniciar(self, especie: str):
        hipotesis = self.repo.hipotesis_de_especie(especie)              # Q1
        if not hipotesis:
            raise ValueError(f"No hay conocimiento para la especie '{especie}'")
        self.memoria = MemoriaTrabajo(especie, hipotesis)
        self.motivo_parada = ""

    # ---- Teorema de Bayes sobre la distribución completa --------------
    def _actualizar(self, dist: Dict[str, float], verosim: Dict[str, float],
                    presente: bool) -> Tuple[Dict[str, float], float]:
        """Devuelve (posterior, P(evidencia))."""
        no_norm = {}
        for h, p_h in dist.items():
            p_s_h = verosim.get(h, self.p_fuga)
            no_norm[h] = p_h * (p_s_h if presente else 1.0 - p_s_h)
        p_evidencia = sum(no_norm.values())
        return {h: v / p_evidencia for h, v in no_norm.items()}, p_evidencia

    def _ganancia_informacion(self, verosim: Dict[str, float]) -> float:
        dist = self.memoria.posterior
        post_si, p_si = self._actualizar(dist, verosim, True)
        post_no, p_no = self._actualizar(dist, verosim, False)
        return entropia(dist) - (p_si * entropia(post_si) + p_no * entropia(post_no))

    # ---- Selección de la siguiente consulta ---------------------------
    def siguiente_pregunta(self) -> Optional[Sintoma]:
        mem = self.memoria
        if self._debe_detenerse():
            return None
        candidatos = self.repo.sintomas_candidatos(mem.especie, mem.preguntados())   # Q2
        mejor, mejor_ganancia = None, -1.0
        for sintoma in candidatos:
            verosim = self.repo.verosimilitudes_de_sintoma(mem.especie, sintoma.id_sintoma)  # Q3
            g = self._ganancia_informacion(verosim)
            if g > mejor_ganancia:
                mejor, mejor_ganancia = sintoma, g
        if mejor is None:
            self.motivo_parada = "No quedan síntomas por preguntar"
            return None
        if mejor_ganancia < self.ganancia_minima and len(mem.hechos) >= self.min_preguntas:
            self.motivo_parada = "Ninguna pregunta restante aporta información"
            return None
        self._ganancia_pendiente = mejor_ganancia
        return mejor

    def registrar_respuesta(self, sintoma: Sintoma, respuesta: str):
        if respuesta not in self.RESPUESTAS:
            raise ValueError("Respuesta inválida: use si / no / nose")
        mem = self.memoria
        mem.registrar(sintoma.id_sintoma, respuesta)
        if respuesta != "nose":                     # 'no sé' no aporta evidencia
            verosim = self.repo.verosimilitudes_de_sintoma(mem.especie, sintoma.id_sintoma)  # Q3
            mem.posterior, _ = self._actualizar(mem.posterior, verosim, respuesta == "si")
        mem.pasos.append(PasoInferencia(len(mem.hechos), sintoma, respuesta,
                                        getattr(self, "_ganancia_pendiente", 0.0),
                                        self.top_hipotesis(explicar=False)))

    def _debe_detenerse(self) -> bool:
        mem = self.memoria
        n = len(mem.hechos)
        if n >= self.max_preguntas:
            self.motivo_parada = f"Se alcanzó el máximo de {self.max_preguntas} preguntas"
            return True
        if n >= self.min_preguntas and max(mem.posterior.values()) >= self.umbral:
            self.motivo_parada = f"La hipótesis líder superó el umbral de {self.umbral:.0%}"
            return True
        return False

    # ---- Resultados ----------------------------------------------------
    def top_hipotesis(self, explicar=True) -> List[ResultadoHipotesis]:
        mem = self.memoria
        orden = sorted(mem.posterior.items(), key=lambda kv: kv[1], reverse=True)
        resultado = []
        for i, (id_h, p) in enumerate(orden[: self.num_hipotesis], start=1):
            r = ResultadoHipotesis(i, mem.hipotesis[id_h], p)
            if explicar:
                granulos = self.repo.granulos_de_hipotesis(id_h)                    # Q4
                r.sintomas_a_favor = [s for s in mem.confirmados() if s in granulos]
                r.sintomas_en_contra = [s for s in mem.negados() if s in granulos]
            resultado.append(r)
        return resultado

    def sistemas_afectados(self) -> Dict[str, float]:
        """Hipótesis intermedias: P(sistema) = Σ P(H) de sus enfermedades."""
        mem = self.memoria
        acumulado: Dict[str, float] = {}
        for id_h, p in mem.posterior.items():
            sis = mem.hipotesis[id_h].id_sistema
            acumulado[sis] = acumulado.get(sis, 0.0) + p
        return {self.repo.nombre_sistema(s): p                                       # Q5
                for s, p in sorted(acumulado.items(), key=lambda kv: kv[1], reverse=True)}

    def resultado(self) -> ResultadoDiagnostico:
        return ResultadoDiagnostico(self.memoria.especie, self.top_hipotesis(),
                                    self.sistemas_afectados(), self.memoria.pasos,
                                    self.motivo_parada or "Interrogatorio finalizado")
