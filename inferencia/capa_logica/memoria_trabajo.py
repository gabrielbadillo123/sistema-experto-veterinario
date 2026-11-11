"""Memoria de trabajo: hechos de la sesión y distribución de probabilidad."""
from typing import Dict, List

from inferencia.modelo.entidades import Hipotesis, PasoInferencia


class MemoriaTrabajo:
    def __init__(self, especie: str, hipotesis: List[Hipotesis]):
        self.especie = especie
        self.hipotesis: Dict[str, Hipotesis] = {h.id_hipotesis: h for h in hipotesis}
        # P(H) a priori normalizada dentro de la especie (sin dato -> uniforme)
        pesos = {h.id_hipotesis: (h.prob_apriori or 1.0) for h in hipotesis}
        total = sum(pesos.values())
        self.posterior: Dict[str, float] = {h: p / total for h, p in pesos.items()}
        self.hechos: Dict[str, str] = {}          # id_sintoma -> 'si' | 'no' | 'nose'
        self.pasos: List[PasoInferencia] = []

    def registrar(self, id_sintoma: str, respuesta: str):
        self.hechos[id_sintoma] = respuesta

    def preguntados(self):
        return self.hechos.keys()

    def confirmados(self):
        return [s for s, r in self.hechos.items() if r == "si"]

    def negados(self):
        return [s for s, r in self.hechos.items() if r == "no"]
