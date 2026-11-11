"""Modelo de dominio (objetos que viajan entre las tres capas)."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Sintoma:
    id_sintoma: str
    pregunta: str
    id_sistema: str


@dataclass(frozen=True)
class Hipotesis:
    id_hipotesis: str
    id_regla: str
    nombre: str
    id_sistema: str
    urgencia: str
    recomendacion: str
    prob_apriori: float


@dataclass(frozen=True)
class Granulo:
    """Unidad mínima de conocimiento: P(sintoma | hipotesis)."""
    id_hipotesis: str
    id_sintoma: str
    verosimilitud: float


@dataclass
class PasoInferencia:
    """Registro de un ciclo (para la explicación / traza)."""
    numero: int
    sintoma: Sintoma
    respuesta: str
    ganancia_bits: float
    top: List["ResultadoHipotesis"]


@dataclass
class ResultadoHipotesis:
    posicion: int
    hipotesis: Hipotesis
    probabilidad: float
    sintomas_a_favor: List[str] = field(default_factory=list)
    sintomas_en_contra: List[str] = field(default_factory=list)


@dataclass
class ResultadoDiagnostico:
    especie: str
    hipotesis: List[ResultadoHipotesis]
    sistemas: Dict[str, float]
    pasos: List[PasoInferencia]
    motivo_parada: str
    id_consulta: Optional[int] = None
