"""Conocimiento probabilístico aportado por el experto (DATOS, no lógica).

Complementa las reglas de producción de sistema_experto_veterinario.py con
los pesos que necesita el motor bayesiano:

  * P(H)      probabilidad a priori de cada enfermedad (prevalencia relativa)
  * P(s | H)  verosimilitud de cada síntoma de la regla (gránulo)

Para la especie canina el experto asignó pesos específicos (PESOS_EXPERTO).
Para las demás especies, mientras el experto no los asigne, se usan valores
por defecto: P(H) uniforme dentro de la especie, P(s|H) = 0,90 para el signo
guía del sistema y 0,80 para los demás síntomas. Estos valores se cargan en
SQL Server con bd/05_inferencia_probabilistica.sql (hipotesis.prob_apriori y
premisa.verosimilitud), y el motor los lee desde ahí.
"""
import sistema_experto_veterinario as sev

VEROSIMILITUD_SIGNO_GUIA = 0.90
VEROSIMILITUD_OTRO_SINTOMA = 0.80

# id_regla: (P(H) a priori, {sintoma: P(sintoma | H)})
PESOS_EXPERTO = {
    "R001": (0.05, {"diarrea_sangre": 0.95, "vomito": 0.90, "fiebre": 0.75, "letargia": 0.85, "perdida_apetito": 0.90}),  # Parvovirosis canina
    "R002": (0.03, {"secrecion_ocular": 0.85, "secrecion_nasal": 0.85, "tos": 0.75, "fiebre": 0.80, "convulsiones": 0.55}),  # Moquillo canino (Distemper)
    "R003": (0.05, {"picazon_intensa": 0.95, "costras_piel": 0.85, "perdida_pelo": 0.80}),  # Sarna sarcoptica
    "R004": (0.10, {"sacude_cabeza": 0.90, "mal_olor_oidos": 0.85, "dolor_al_tocar_oido": 0.80}),  # Otitis externa
    "R005": (0.02, {"fiebre": 0.80, "vomito": 0.80, "ictericia": 0.70, "dolor_abdominal": 0.70, "aumento_sed": 0.65}),  # Leptospirosis canina
    "R006": (0.10, {"diarrea": 0.85, "abdomen_hinchado": 0.70, "perdida_peso": 0.65, "vomito": 0.45}),  # Parasitosis intestinal (lombrices)
    "R007": (0.04, {"aumento_sed": 0.90, "aumento_orina": 0.90, "perdida_peso": 0.75, "vomito": 0.60, "letargia": 0.70}),  # Insuficiencia renal cronica
    "R008": (0.03, {"aumento_sed": 0.95, "aumento_orina": 0.95, "aumento_apetito": 0.80, "perdida_peso": 0.75}),  # Diabetes mellitus canina
    "R009": (0.02, {"cojera": 0.80, "fiebre": 0.75, "ganglios_inflamados": 0.65, "letargia": 0.70}),  # Enfermedad de Lyme (borreliosis)
    "R010": (0.04, {"fiebre": 0.80, "sangrado_nariz": 0.60, "ganglios_inflamados": 0.70, "perdida_peso": 0.70}),  # Ehrlichiosis canina
    "R011": (0.01, {"fiebre": 0.85, "vomito": 0.75, "ictericia": 0.70, "dolor_abdominal": 0.75, "opacidad_ojos": 0.60}),  # Hepatitis infecciosa canina
    "R012": (0.07, {"tos": 0.95, "estornudos": 0.65, "secrecion_nasal": 0.60}),  # Tos de las perreras (traqueobronquitis)
    "R013": (0.02, {"tos": 0.80, "dificultad_respirar": 0.75, "letargia": 0.70, "perdida_peso": 0.60}),  # Dirofilariasis (gusano del corazon)
    "R014": (0.03, {"vomito": 0.90, "dolor_abdominal": 0.90, "perdida_apetito": 0.85, "letargia": 0.70}),  # Pancreatitis canina
    "R015": (0.06, {"picazon_intensa": 0.75, "costras_piel": 0.85, "mal_olor_piel": 0.80}),  # Pioderma (infeccion bacteriana de piel)
    "R016": (0.08, {"picazon_intensa": 0.95, "enrojecimiento_piel": 0.85, "perdida_pelo": 0.65}),  # Dermatitis atopica (alergia)
    "R017": (0.03, {"aumento_peso": 0.80, "letargia": 0.80, "perdida_pelo": 0.75, "piel_seca": 0.70}),  # Hipotiroidismo canino
    "R018": (0.03, {"aumento_sed": 0.85, "aumento_orina": 0.85, "abdomen_hinchado": 0.80, "perdida_pelo": 0.70}),  # Sindrome de Cushing (hiperadrenocorticismo)
    "R019": (0.01, {"debilidad": 0.85, "letargia": 0.85, "vomito": 0.70, "perdida_apetito": 0.75}),  # Enfermedad de Addison (hipoadrenocorticismo)
    "R020": (0.02, {"convulsiones": 0.95, "perdida_conciencia": 0.80}),  # Epilepsia idiopatica
    "R021": (0.01, {"abdomen_hinchado": 0.95, "arcadas_sin_vomito": 0.90, "salivacion_excesiva": 0.75, "dificultad_respirar": 0.65}),  # Torsion gastrica (dilatacion-volvulo)
    "R022": (0.04, {"dificultad_levantarse": 0.85, "cojera": 0.70, "dolor_al_caminar": 0.80}),  # Displasia de cadera
    "R023": (0.03, {"cojera": 0.90, "no_apoya_pata": 0.85}),  # Rotura de ligamento cruzado
    "R024": (0.02, {"hinchazon_oreja": 0.95, "sacude_cabeza": 0.80}),  # Otohematoma
    "R025": (0.06, {"enrojecimiento_ojos": 0.90, "secrecion_ocular": 0.85, "picazon_ojos": 0.70}),  # Conjuntivitis canina
}

PARAMETROS = [
    ("p_fuga", 0.03, "P(s|H) cuando el sintoma no pertenece al granulo de H"),
    ("umbral_confianza", 0.90, "Probabilidad de la hipotesis lider para detener el interrogatorio"),
    ("min_preguntas", 4, "Numero minimo de preguntas antes de detenerse"),
    ("max_preguntas", 15, "Numero maximo de preguntas"),
    ("ganancia_minima", 0.005, "Ganancia de informacion minima (bits) para seguir preguntando"),
    ("num_hipotesis", 5, "Numero de hipotesis a reportar"),
]


def prob_apriori(regla) -> float:
    """P(H) sin normalizar (el motor normaliza dentro de la especie)."""
    if regla.id in PESOS_EXPERTO:
        return PESOS_EXPERTO[regla.id][0]
    n = sum(1 for r in sev.REGLAS if r.especie == regla.especie)
    return round(1.0 / n, 4)


def verosimilitud(regla, sintoma: str) -> float:
    """P(sintoma | H) del gránulo (regla, sintoma)."""
    pesos = PESOS_EXPERTO.get(regla.id, (None, {}))[1]
    if sintoma in pesos:
        return pesos[sintoma]
    guias = sev.SISTEMAS[regla.sistema][1]
    return VEROSIMILITUD_SIGNO_GUIA if sintoma in guias else VEROSIMILITUD_OTRO_SINTOMA


# Comprobación al importar: los pesos del experto corresponden a reglas reales
for _id, (_p, _v) in PESOS_EXPERTO.items():
    _r = next(r for r in sev.REGLAS if r.id == _id)
    assert set(_v) == set(_r.sintomas), f"Pesos de {_id} no coinciden con sus sintomas"
