#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 SISTEMA EXPERTO VETERINARIO
 Diagnostico de enfermedades en animales domesticos mediante un
 SISTEMA DE PRODUCCION (reglas SI-ENTONCES)
================================================================================

Arquitectura (basada en Newell y Simon, 1972 - "Sistemas de produccion"):

        Base de Conocimiento (BC)          Memoria de Trabajo
             [ Reglas ]      <---------->      [ Hechos ]
                    \\                          /
                     \\                        /
                      \\                      /
                     Motor de Inferencias
                    (encadenamiento hacia adelante)
                              |
                              v
                     Mundo Exterior (usuario)

  - Base de Conocimiento (BC): lista REGLAS. Cada regla tiene la forma
        SI (conjunto de sintomas presentes) ENTONCES (enfermedad, recomendacion)
  - Memoria de trabajo: el conjunto `hechos`, que se va llenando con las
    respuestas (sintomas confirmados) que da el usuario sobre el animal.
  - Motor de inferencia: la clase MotorInferencia, que compara los hechos
    contra cada regla (encadenamiento hacia adelante / forward chaining) y
    calcula que tanto coincide cada regla con los hechos conocidos.

Autor: Sistema generado para proyecto academico de Sistemas Expertos.
================================================================================
"""

from dataclasses import dataclass, field, replace
from typing import Set, List, Dict, Tuple
import os
import sys

# Opciones de consulta tecnica en los menus (base de conocimiento, arbol de
# decision, diagrama, granulos e historial). Ocultas por indicacion del
# profesor: el usuario solo diagnostica. Cambiar a True para volver a
# mostrarlas en la consola y en la interfaz grafica.
MOSTRAR_OPCIONES_AVANZADAS = False

# Motor de inferencia del diagnostico. True: motor bayesiano del paquete
# inferencia/ (tres capas + MVC), que identifica las 5 hipotesis mas probables
# con su peso probabilistico mediante consultas sucesivas y granulares a la
# base de conocimiento. False: motor anterior de dos ciclos con indice de Jaccard.
USAR_MOTOR_BAYESIANO = True


# =============================================================================
# 1. BASE DE CONOCIMIENTO (BC) -- REGLAS DE PRODUCCION
# =============================================================================

@dataclass(frozen=True)
class Regla:
    """Una regla de produccion: SI <sintomas> ENTONCES <enfermedad>."""
    id: str
    especie: str
    enfermedad: str
    sintomas: frozenset
    recomendacion: str
    urgencia: str  # "Baja", "Media", "Alta"
    sistema: str = ""  # hipotesis intermedia (ver SISTEMAS), se asigna mas abajo


def R(id_, especie, enfermedad, sintomas, recomendacion, urgencia):
    return Regla(id_, especie, enfermedad, frozenset(sintomas), recomendacion, urgencia)


REGLAS: List[Regla] = [

    # ---------- PERRO (25) ----------
    R("R001", "perro", "Parvovirosis canina",
     {"diarrea_sangre", "fiebre", "letargia", "perdida_apetito", "vomito"},
     "Aislar al animal, evitar contacto con otros perros y trasladarlo de inmediato al veterinario. Requiere hidratacion IV urgente; es una enfermedad viral muy contagiosa y potencialmente mortal en cachorros.",
     "Alta"),
    R("R002", "perro", "Moquillo canino (Distemper)",
     {"convulsiones", "fiebre", "secrecion_nasal", "secrecion_ocular", "tos"},
     "Consulta veterinaria urgente. Es una enfermedad viral grave que puede dejar secuelas neurologicas; se recomienda ademas vacunacion preventiva en el resto de la camada.",
     "Alta"),
    R("R003", "perro", "Sarna sarcoptica",
     {"costras_piel", "perdida_pelo", "picazon_intensa"},
     "Llevar al veterinario para tratamiento antiparasitario topico u oral. Es contagiosa para otros animales y, en menor medida, para personas.",
     "Media"),
    R("R004", "perro", "Otitis externa",
     {"dolor_al_tocar_oido", "mal_olor_oidos", "sacude_cabeza"},
     "Limpieza otica y evaluacion veterinaria para descartar acaros, hongos o bacterias antes de aplicar tratamiento.",
     "Baja"),
    R("R005", "perro", "Leptospirosis canina",
     {"aumento_sed", "dolor_abdominal", "fiebre", "ictericia", "vomito"},
     "Atencion veterinaria urgente; es zoonotica (se transmite a humanos). Extremar higiene al manipular al animal.",
     "Alta"),
    R("R006", "perro", "Parasitosis intestinal (lombrices)",
     {"abdomen_hinchado", "diarrea", "perdida_peso", "vomito"},
     "Administrar desparasitante segun indicacion veterinaria y repetir el esquema de desparasitacion periodica.",
     "Media"),
    R("R007", "perro", "Insuficiencia renal cronica",
     {"aumento_orina", "aumento_sed", "letargia", "perdida_peso", "vomito"},
     "Evaluacion veterinaria con examenes de sangre y orina; puede requerir dieta especial y manejo cronico.",
     "Alta"),
    R("R008", "perro", "Diabetes mellitus canina",
     {"aumento_apetito", "aumento_orina", "aumento_sed", "perdida_peso"},
     "Consulta veterinaria para confirmar con glucemia; requiere manejo con insulina y dieta controlada de por vida.",
     "Media"),
    R("R009", "perro", "Enfermedad de Lyme (borreliosis)",
     {"cojera", "fiebre", "ganglios_inflamados", "letargia"},
     "Consulta veterinaria para tratamiento antibiotico; revisar y retirar garrapatas del cuerpo del animal.",
     "Media"),
    R("R010", "perro", "Ehrlichiosis canina",
     {"fiebre", "ganglios_inflamados", "perdida_peso", "sangrado_nariz"},
     "Consulta veterinaria urgente; enfermedad transmitida por garrapatas que afecta la coagulacion de la sangre.",
     "Alta"),
    R("R011", "perro", "Hepatitis infecciosa canina",
     {"dolor_abdominal", "fiebre", "ictericia", "opacidad_ojos", "vomito"},
     "Atencion veterinaria urgente; enfermedad viral que afecta el higado, prevenible con vacunacion.",
     "Alta"),
    R("R012", "perro", "Tos de las perreras (traqueobronquitis)",
     {"estornudos", "secrecion_nasal", "tos"},
     "Reposo y consulta veterinaria; evitar collares que compriman la traquea y aislar de otros perros mientras dura el contagio.",
     "Baja"),
    R("R013", "perro", "Dirofilariasis (gusano del corazon)",
     {"dificultad_respirar", "letargia", "perdida_peso", "tos"},
     "Consulta veterinaria para prueba de deteccion; se transmite por mosquitos y requiere tratamiento especializado y prevencion mensual.",
     "Alta"),
    R("R014", "perro", "Pancreatitis canina",
     {"dolor_abdominal", "letargia", "perdida_apetito", "vomito"},
     "Atencion veterinaria urgente; suspender alimento graso y mantener hidratacion.",
     "Alta"),
    R("R015", "perro", "Pioderma (infeccion bacteriana de piel)",
     {"costras_piel", "mal_olor_piel", "picazon_intensa"},
     "Consulta veterinaria para tratamiento antibiotico topico o sistemico segun gravedad.",
     "Media"),
    R("R016", "perro", "Dermatitis atopica (alergia)",
     {"enrojecimiento_piel", "perdida_pelo", "picazon_intensa"},
     "Consulta veterinaria para identificar el alergeno y manejo con antihistaminicos o dieta hipoalergenica.",
     "Media"),
    R("R017", "perro", "Hipotiroidismo canino",
     {"aumento_peso", "letargia", "perdida_pelo", "piel_seca"},
     "Consulta veterinaria con perfil tiroideo; se trata con hormona tiroidea de por vida.",
     "Media"),
    R("R018", "perro", "Sindrome de Cushing (hiperadrenocorticismo)",
     {"abdomen_hinchado", "aumento_orina", "aumento_sed", "perdida_pelo"},
     "Consulta veterinaria con examenes hormonales; frecuente en perros mayores.",
     "Media"),
    R("R019", "perro", "Enfermedad de Addison (hipoadrenocorticismo)",
     {"debilidad", "letargia", "perdida_apetito", "vomito"},
     "Emergencia veterinaria; puede causar colapso si no se trata con reemplazo hormonal.",
     "Alta"),
    R("R020", "perro", "Epilepsia idiopatica",
     {"convulsiones", "perdida_conciencia"},
     "Consulta veterinaria para descartar otras causas y evaluar tratamiento anticonvulsivo.",
     "Media"),
    R("R021", "perro", "Torsion gastrica (dilatacion-volvulo)",
     {"abdomen_hinchado", "arcadas_sin_vomito", "dificultad_respirar", "salivacion_excesiva"},
     "EMERGENCIA veterinaria inmediata; puede ser mortal en pocas horas sin cirugia.",
     "Alta"),
    R("R022", "perro", "Displasia de cadera",
     {"cojera", "dificultad_levantarse", "dolor_al_caminar"},
     "Consulta veterinaria con radiografias; manejo con control de peso, ejercicio moderado y posible cirugia.",
     "Media"),
    R("R023", "perro", "Rotura de ligamento cruzado",
     {"cojera", "no_apoya_pata"},
     "Consulta veterinaria; frecuentemente requiere cirugia de reconstruccion articular.",
     "Media"),
    R("R024", "perro", "Otohematoma",
     {"hinchazon_oreja", "sacude_cabeza"},
     "Consulta veterinaria para drenaje; suele originarse por rascado intenso debido a otitis.",
     "Baja"),
    R("R025", "perro", "Conjuntivitis canina",
     {"enrojecimiento_ojos", "picazon_ojos", "secrecion_ocular"},
     "Limpieza ocular con suero fisiologico y consulta veterinaria si no mejora en pocos dias.",
     "Baja"),

    # ---------- GATO (25) ----------
    R("R026", "gato", "Panleucopenia felina (moquillo felino)",
     {"diarrea", "fiebre", "letargia", "perdida_apetito", "vomito"},
     "Aislamiento y atencion veterinaria urgente; enfermedad viral muy contagiosa y grave, sobre todo en gatitos.",
     "Alta"),
    R("R027", "gato", "Rinotraqueitis viral felina (Herpesvirus)",
     {"estornudos", "fiebre", "secrecion_nasal", "secrecion_ocular", "ulceras_boca"},
     "Consulta veterinaria; mantener al gato hidratado y en ambiente calido. Puede requerir antivirales o antibioticos de apoyo.",
     "Media"),
    R("R028", "gato", "Calicivirus felino",
     {"cojera", "estornudos", "fiebre", "secrecion_ocular", "ulceras_boca"},
     "Consulta veterinaria; ofrecer comida blanda por las ulceras bucales y vigilar la hidratacion.",
     "Media"),
    R("R029", "gato", "Toxoplasmosis felina",
     {"dificultad_respirar", "fiebre", "ictericia", "letargia", "perdida_apetito"},
     "Consulta veterinaria; precaucion especial si hay mujeres embarazadas en el hogar (zoonosis).",
     "Media"),
    R("R030", "gato", "Enfermedad renal cronica felina",
     {"aumento_orina", "aumento_sed", "letargia", "perdida_peso", "vomito"},
     "Examenes de sangre y orina en el veterinario; manejo con dieta renal y controles periodicos.",
     "Alta"),
    R("R031", "gato", "Hipertiroidismo felino",
     {"aumento_apetito", "aumento_sed", "hiperactividad", "perdida_peso"},
     "Consulta veterinaria para medir hormona tiroidea; frecuente en gatos mayores de 8 anios.",
     "Media"),
    R("R032", "gato", "Inmunodeficiencia felina (FIV)",
     {"fiebre", "infecciones_recurrentes", "letargia", "perdida_peso"},
     "Prueba veterinaria especifica (test FIV); mantener al gato en interior y sin contacto con otros gatos por contagio.",
     "Media"),
    R("R033", "gato", "Otitis por acaros (Otodectes)",
     {"mal_olor_oidos", "picazon_intensa", "sacude_cabeza"},
     "Revision veterinaria de oidos y tratamiento antiparasitario especifico; muy comun y contagiosa entre gatos.",
     "Baja"),
    R("R034", "gato", "Leucemia felina (FeLV)",
     {"infecciones_recurrentes", "letargia", "palidez_encias", "perdida_peso"},
     "Prueba veterinaria especifica (test FeLV); manejo de soporte y separacion de otros gatos sanos.",
     "Alta"),
    R("R035", "gato", "Peritonitis infecciosa felina (PIF)",
     {"abdomen_hinchado", "fiebre", "letargia", "perdida_peso"},
     "Consulta veterinaria especializada; enfermedad viral grave y de dificil tratamiento.",
     "Alta"),
    R("R036", "gato", "Diabetes mellitus felina",
     {"aumento_apetito", "aumento_orina", "aumento_sed", "perdida_peso"},
     "Consulta veterinaria para confirmar con glucemia; manejo con insulina y dieta controlada.",
     "Media"),
    R("R037", "gato", "Enfermedad del tracto urinario inferior felino (FLUTD)",
     {"dificultad_orinar", "maullidos_al_orinar", "sangre_orina"},
     "Consulta veterinaria urgente, sobre todo en gatos machos por riesgo de obstruccion urinaria.",
     "Alta"),
    R("R038", "gato", "Obstruccion por bolas de pelo (tricobezoares)",
     {"estrenimiento", "perdida_apetito", "vomito"},
     "Cepillado regular y pastas o alimentos para bolas de pelo; consulta veterinaria si persiste.",
     "Baja"),
    R("R039", "gato", "Asma felino",
     {"dificultad_respirar", "sibilancias", "tos"},
     "Consulta veterinaria; puede requerir broncodilatadores o corticoides inhalados.",
     "Media"),
    R("R040", "gato", "Gingivitis / enfermedad dental",
     {"dificultad_comer", "mal_aliento", "ulceras_boca"},
     "Revision veterinaria dental y limpieza profesional; puede requerir extracciones.",
     "Baja"),
    R("R041", "gato", "Lipidosis hepatica felina (higado graso)",
     {"ictericia", "letargia", "perdida_apetito", "perdida_peso"},
     "Emergencia veterinaria; puede requerir alimentacion asistida por sonda.",
     "Alta"),
    R("R042", "gato", "Pancreatitis felina",
     {"dolor_abdominal", "letargia", "perdida_apetito", "vomito"},
     "Consulta veterinaria urgente y manejo con fluidos y analgesia.",
     "Alta"),
    R("R043", "gato", "Anemia felina (hemoplasmosis)",
     {"letargia", "palidez_encias", "perdida_apetito"},
     "Consulta veterinaria con analisis de sangre; tratamiento con antibioticos especificos.",
     "Media"),
    R("R044", "gato", "Dermatitis alergica felina",
     {"costras_piel", "perdida_pelo", "picazon_intensa"},
     "Consulta veterinaria para identificar la causa (pulgas, alimento, ambiental) y tratamiento.",
     "Media"),
    R("R045", "gato", "Dermatofitosis (tina/hongos)",
     {"costras_piel", "perdida_pelo", "zonas_circulares_sin_pelo"},
     "Consulta veterinaria; es contagiosa para otras mascotas y personas, extremar higiene.",
     "Baja"),
    R("R046", "gato", "Cardiomiopatia hipertrofica felina",
     {"debilidad_patas_traseras", "dificultad_respirar", "letargia"},
     "Emergencia veterinaria; enfermedad cardiaca comun en gatos que puede causar coagulos.",
     "Alta"),
    R("R047", "gato", "Rabia felina",
     {"agresividad", "cambios_comportamiento", "paralisis", "salivacion_excesiva"},
     "EMERGENCIA de salud publica; aislar al animal y notificar a la autoridad sanitaria de inmediato, no manipular sin proteccion.",
     "Alta"),
    R("R048", "gato", "Conjuntivitis felina",
     {"enrojecimiento_ojos", "picazon_ojos", "secrecion_ocular"},
     "Limpieza ocular con suero fisiologico y consulta veterinaria si no mejora.",
     "Baja"),
    R("R049", "gato", "Otitis externa felina",
     {"dolor_al_tocar_oido", "mal_olor_oidos", "sacude_cabeza"},
     "Limpieza otica y evaluacion veterinaria antes de aplicar tratamiento.",
     "Baja"),
    R("R050", "gato", "Estreñimiento / megacolon felino",
     {"abdomen_hinchado", "estrenimiento", "perdida_apetito"},
     "Consulta veterinaria; puede requerir cambio de dieta, laxantes o manejo mas especializado.",
     "Media"),

    # ---------- VACA (25) ----------
    R("R051", "vaca", "Mastitis bovina",
     {"disminucion_produccion_leche", "fiebre", "leche_anormal", "ubre_inflamada"},
     "Ordenio con manejo higienico separado, revision veterinaria y posible tratamiento antibiotico intramamario.",
     "Media"),
    R("R052", "vaca", "Fiebre aftosa",
     {"ampollas_boca", "ampollas_pezunas", "cojera", "fiebre", "salivacion_excesiva"},
     "Notificar de inmediato a la autoridad sanitaria: enfermedad de declaracion obligatoria y alto impacto economico.",
     "Alta"),
    R("R053", "vaca", "Timpanismo (meteorismo)",
     {"dificultad_respirar", "disminucion_produccion_leche", "hinchazon_abdominal"},
     "Emergencia veterinaria: puede requerir sonda o trocar de urgencia para liberar el gas acumulado en el rumen.",
     "Alta"),
    R("R054", "vaca", "Fasciolasis hepatica",
     {"diarrea", "disminucion_produccion_leche", "ictericia", "perdida_peso"},
     "Tratamiento antiparasitario (fasciolicida) indicado por el veterinario y control de caracoles en potreros humedos.",
     "Media"),
    R("R055", "vaca", "Brucelosis bovina",
     {"aborto", "fiebre", "retencion_placenta"},
     "Aislar al animal y notificar al veterinario: es zoonotica y de control sanitario obligatorio.",
     "Alta"),
    R("R056", "vaca", "Diarrea viral bovina (BVD)",
     {"diarrea", "fiebre", "perdida_peso", "ulceras_boca"},
     "Consulta veterinaria; aislar animales afectados y revisar el plan de vacunacion del hato.",
     "Media"),
    R("R057", "vaca", "Rinotraqueitis infecciosa bovina (IBR)",
     {"dificultad_respirar", "enrojecimiento_hocico", "fiebre", "secrecion_nasal", "tos"},
     "Consulta veterinaria; enfermedad viral respiratoria contagiosa, vacunacion preventiva recomendada.",
     "Media"),
    R("R058", "vaca", "Carbunco sintomatico (pierna negra)",
     {"cojera", "fiebre", "hinchazon_muscular"},
     "Notificacion a la autoridad sanitaria; enfermedad bacteriana grave y de rapida evolucion.",
     "Alta"),
    R("R059", "vaca", "Carbunco bacteridiano (antrax)",
     {"dificultad_respirar", "fiebre", "hinchazon_cuello", "sangrado_orificios"},
     "EMERGENCIA y notificacion obligatoria a la autoridad sanitaria; es zoonotica y de alto riesgo.",
     "Alta"),
    R("R060", "vaca", "Leptospirosis bovina",
     {"aborto", "fiebre", "ictericia", "sangre_orina"},
     "Consulta veterinaria urgente; es zoonotica, extremar higiene al manipular al animal.",
     "Alta"),
    R("R061", "vaca", "Coccidiosis bovina",
     {"diarrea_sangre", "letargia", "perdida_peso"},
     "Tratamiento antiparasitario coccidiostato y mejora en la higiene de los corrales.",
     "Media"),
    R("R062", "vaca", "Pododermatitis (footrot)",
     {"cojera", "hinchazon_pezuna", "mal_olor_pezuna"},
     "Limpieza y tratamiento local de la pezuña, y consulta veterinaria si no mejora.",
     "Media"),
    R("R063", "vaca", "Fiebre de leche (hipocalcemia)",
     {"debilidad", "incapacidad_levantarse", "temblores"},
     "Emergencia veterinaria; requiere aplicacion de calcio intravenoso, comun tras el parto.",
     "Alta"),
    R("R064", "vaca", "Cetosis bovina",
     {"disminucion_produccion_leche", "perdida_apetito", "perdida_peso"},
     "Consulta veterinaria y ajuste de la dieta energetica, comun en el inicio de la lactancia.",
     "Media"),
    R("R065", "vaca", "Desplazamiento de abomaso",
     {"abdomen_hinchado", "disminucion_produccion_leche", "perdida_apetito"},
     "Emergencia veterinaria; frecuentemente requiere correccion quirurgica.",
     "Alta"),
    R("R066", "vaca", "Metritis",
     {"fiebre", "perdida_apetito", "secrecion_vaginal_anormal"},
     "Consulta veterinaria para tratamiento antibiotico; comun tras partos dificiles.",
     "Alta"),
    R("R067", "vaca", "Papilomatosis (verrugas)",
     {"nodulos_piel", "perdida_pelo"},
     "Generalmente se resuelve sola; consulta veterinaria si las verrugas interfieren con la alimentacion o el ordeño.",
     "Baja"),
    R("R068", "vaca", "Queratoconjuntivitis infecciosa (pinkeye)",
     {"enrojecimiento_ojos", "opacidad_ojos", "secrecion_ocular"},
     "Consulta veterinaria; es contagiosa entre el ganado, aislar animales afectados.",
     "Media"),
    R("R069", "vaca", "Rabia bovina",
     {"agresividad", "paralisis", "salivacion_excesiva"},
     "EMERGENCIA de salud publica; notificar a la autoridad sanitaria y no manipular sin proteccion.",
     "Alta"),
    R("R070", "vaca", "Tetanos bovino",
     {"dificultad_masticar", "espasmos", "rigidez_muscular"},
     "Emergencia veterinaria; revisar heridas recientes y estado de vacunacion.",
     "Alta"),
    R("R071", "vaca", "Babesiosis (fiebre de garrapata)",
     {"fiebre", "letargia", "palidez_encias", "sangre_orina"},
     "Consulta veterinaria urgente; transmitida por garrapatas, requiere tratamiento especifico.",
     "Alta"),
    R("R072", "vaca", "Anaplasmosis bovina",
     {"fiebre", "ictericia", "letargia", "palidez_encias"},
     "Consulta veterinaria urgente; enfermedad transmitida por garrapatas que afecta los globulos rojos.",
     "Alta"),
    R("R073", "vaca", "Diarrea neonatal (colibacilosis en terneros)",
     {"deshidratacion", "diarrea", "letargia"},
     "Rehidratacion urgente del ternero y consulta veterinaria; principal causa de muerte en terneros jovenes.",
     "Alta"),
    R("R074", "vaca", "Complejo respiratorio bovino (neumonia)",
     {"dificultad_respirar", "estertores", "fiebre", "secrecion_nasal", "tos"},
     "Consulta veterinaria; comun en el destete y por hacinamiento o mal manejo del clima.",
     "Alta"),
    R("R075", "vaca", "Sarna bovina",
     {"costras_piel", "perdida_pelo", "picazon_intensa"},
     "Tratamiento antiparasitario indicado por el veterinario y mejora en las condiciones de higiene.",
     "Media"),

    # ---------- CABALLO (25) ----------
    R("R076", "caballo", "Colico equino",
     {"ausencia_heces", "dolor_abdominal", "revolcarse", "sudoracion_excesiva"},
     "Emergencia veterinaria inmediata; no dar alimento y mantener al caballo en movimiento suave mientras llega el veterinario.",
     "Alta"),
    R("R077", "caballo", "Laminitis",
     {"calor_en_pezunas", "cojera", "renuencia_moverse"},
     "Reposo absoluto sobre superficie blanda y atencion veterinaria urgente; revisar dieta rica en granos como posible causa.",
     "Alta"),
    R("R078", "caballo", "Influenza equina",
     {"fiebre", "letargia", "secrecion_nasal", "tos"},
     "Reposo, aislamiento del resto de la caballeriza y control veterinario; muy contagiosa entre equinos.",
     "Media"),
    R("R079", "caballo", "Tetanos equino",
     {"dificultad_masticar", "espasmos", "fiebre", "rigidez_muscular"},
     "Emergencia veterinaria; revisar heridas recientes y estado de vacunacion antitetanica.",
     "Alta"),
    R("R080", "caballo", "Papera equina (adenitis equina)",
     {"dificultad_tragar", "fiebre", "hinchazon_ganglios", "secrecion_nasal"},
     "Aislamiento y consulta veterinaria; muy contagiosa entre caballos jovenes.",
     "Media"),
    R("R081", "caballo", "Rinoneumonitis equina (Herpesvirus)",
     {"aborto", "fiebre", "secrecion_nasal", "tos"},
     "Consulta veterinaria; puede causar abortos en yeguas gestantes, vacunacion preventiva recomendada.",
     "Media"),
    R("R082", "caballo", "Encefalomielitis equina",
     {"cambios_comportamiento", "debilidad", "fiebre", "incoordinacion"},
     "Emergencia veterinaria; enfermedad viral transmitida por mosquitos que afecta el sistema nervioso.",
     "Alta"),
    R("R083", "caballo", "Anemia infecciosa equina",
     {"fiebre", "letargia", "palidez_encias", "perdida_peso"},
     "Consulta veterinaria con prueba especifica (test de Coggins); no tiene cura y requiere control sanitario.",
     "Alta"),
    R("R084", "caballo", "Fiebre del Potomac",
     {"cojera", "diarrea", "fiebre", "letargia"},
     "Consulta veterinaria urgente; puede complicarse con laminitis secundaria.",
     "Alta"),
    R("R085", "caballo", "Salmonelosis equina",
     {"diarrea", "dolor_abdominal", "fiebre"},
     "Consulta veterinaria urgente; aislar al animal por ser contagiosa.",
     "Alta"),
    R("R086", "caballo", "Ulceras gastricas equinas",
     {"bruxismo", "dolor_abdominal", "perdida_apetito", "perdida_peso"},
     "Consulta veterinaria; revisar manejo de alimentacion y niveles de estres del caballo.",
     "Media"),
    R("R087", "caballo", "Enfermedad respiratoria obstructiva recurrente (heaves)",
     {"dificultad_respirar", "secrecion_nasal", "tos"},
     "Consulta veterinaria; mejorar ventilacion y reducir polvo/heno de mala calidad en el establo.",
     "Media"),
    R("R088", "caballo", "Sindrome metabolico equino",
     {"aumento_peso", "cojera", "deposito_grasa_anormal"},
     "Consulta veterinaria; manejo con dieta baja en azucares y ejercicio controlado.",
     "Media"),
    R("R089", "caballo", "Enfermedad de Cushing equina (PPID)",
     {"aumento_sed", "cojera", "pelaje_largo_anormal", "perdida_peso"},
     "Consulta veterinaria con perfil hormonal; comun en caballos mayores.",
     "Media"),
    R("R090", "caballo", "Enfermedad navicular",
     {"cojera", "dolor_talones", "renuencia_moverse"},
     "Consulta veterinaria con radiografias; manejo con herrajes especiales y control del ejercicio.",
     "Media"),
    R("R091", "caballo", "Artritis / enfermedad articular degenerativa",
     {"cojera", "dificultad_levantarse", "rigidez_muscular"},
     "Consulta veterinaria; manejo con antiinflamatorios y ejercicio controlado.",
     "Media"),
    R("R092", "caballo", "Grietas y problemas de casco",
     {"cojera", "grietas_casco"},
     "Consulta con veterinario o herrador; revisar el herraje y la humedad del casco.",
     "Baja"),
    R("R093", "caballo", "Ranilla podrida (thrush)",
     {"cojera", "mal_olor_pezuna"},
     "Limpieza y secado del casco; consulta veterinaria o de herrador si no mejora.",
     "Baja"),
    R("R094", "caballo", "Dermatofilosis (rain rot)",
     {"costras_piel", "mechones_pelo_pegados", "perdida_pelo"},
     "Mantener al caballo seco y limpio; consulta veterinaria para tratamiento topico.",
     "Baja"),
    R("R095", "caballo", "Dermatofitosis equina (tina)",
     {"costras_piel", "perdida_pelo", "zonas_circulares_sin_pelo"},
     "Consulta veterinaria; es contagiosa, desinfectar cepillos y equipo de montar.",
     "Baja"),
    R("R096", "caballo", "Estrongilidosis (parasitos internos)",
     {"diarrea", "pelaje_opaco", "perdida_peso"},
     "Desparasitacion segun programa veterinario y rotacion de potreros.",
     "Media"),
    R("R097", "caballo", "Botulismo equino",
     {"debilidad", "dificultad_tragar", "paralisis"},
     "EMERGENCIA veterinaria; puede ser mortal por afectar los musculos respiratorios.",
     "Alta"),
    R("R098", "caballo", "Miopatia por esfuerzo (tying-up)",
     {"renuencia_moverse", "rigidez_muscular", "sudoracion_excesiva"},
     "Detener el ejercicio de inmediato y llamar al veterinario; comun tras esfuerzo intenso.",
     "Alta"),
    R("R099", "caballo", "Ahogo esofagico (choke)",
     {"dificultad_tragar", "salivacion_excesiva", "secrecion_nasal_alimento"},
     "Emergencia veterinaria; no dar agua ni comida hasta que el veterinario lo revise.",
     "Alta"),
    R("R100", "caballo", "Rabia equina",
     {"agresividad", "cambios_comportamiento", "paralisis", "salivacion_excesiva"},
     "EMERGENCIA de salud publica; notificar a la autoridad sanitaria y no manipular sin proteccion.",
     "Alta"),

    # ---------- AVE (25) ----------
    R("R101", "ave", "Enfermedad de Newcastle",
     {"diarrea_verde", "dificultad_respirar", "disminucion_postura", "paralisis_alas_patas", "torticolis"},
     "Aislar el lote y notificar a un medico veterinario avicola; enfermedad viral de alta mortalidad y declaracion obligatoria.",
     "Alta"),
    R("R102", "ave", "Coriza infecciosa",
     {"disminucion_postura", "estornudos", "hinchazon_cara", "secrecion_nasal"},
     "Tratamiento antibiotico segun indicacion veterinaria y mejora de ventilacion del galpon.",
     "Media"),
    R("R103", "ave", "Coccidiosis aviar",
     {"disminucion_postura", "letargia", "plumas_erizadas", "sangre_heces"},
     "Tratamiento coccidiostato en agua o alimento y mejora en la limpieza de la cama del galpon.",
     "Media"),
    R("R104", "ave", "Bronquitis infecciosa aviar",
     {"disminucion_postura", "estornudos", "secrecion_nasal", "tos"},
     "Consulta con veterinario avicola; reforzar bioseguridad del galpon para evitar contagio masivo.",
     "Media"),
    R("R105", "ave", "Influenza aviar",
     {"dificultad_respirar", "disminucion_postura", "hinchazon_cara", "letargia"},
     "Notificacion obligatoria a la autoridad sanitaria; enfermedad de alto riesgo, algunas cepas son zoonoticas.",
     "Alta"),
    R("R106", "ave", "Enfermedad de Marek",
     {"paralisis_alas_patas", "perdida_peso", "tumores_visibles"},
     "Consulta veterinaria avicola; enfermedad viral prevenible con vacunacion en pollitos.",
     "Alta"),
    R("R107", "ave", "Enfermedad de Gumboro (bursitis infecciosa)",
     {"diarrea", "letargia", "plumas_erizadas", "temblores"},
     "Consulta veterinaria avicola; afecta el sistema inmune de aves jovenes.",
     "Alta"),
    R("R108", "ave", "Viruela aviar",
     {"costras_cresta", "dificultad_respirar", "nodulos_piel"},
     "Consulta veterinaria; vacunacion preventiva disponible, mejorar control de mosquitos (vectores).",
     "Media"),
    R("R109", "ave", "Colera aviar",
     {"diarrea_verde", "fiebre", "hinchazon_cara", "letargia"},
     "Tratamiento antibiotico segun indicacion veterinaria; enfermedad bacteriana de alta mortalidad.",
     "Alta"),
    R("R110", "ave", "Colibacilosis aviar",
     {"diarrea", "dificultad_respirar", "letargia", "perdida_apetito"},
     "Consulta veterinaria; mejorar higiene del agua y el alimento del galpon.",
     "Media"),
    R("R111", "ave", "Salmonelosis aviar (pulorosis)",
     {"diarrea_blanca", "letargia", "plumas_erizadas"},
     "Consulta veterinaria urgente; puede transmitirse a humanos por consumo de huevos contaminados.",
     "Alta"),
    R("R112", "ave", "Micoplasmosis (enfermedad respiratoria cronica)",
     {"dificultad_respirar", "estornudos", "hinchazon_cara", "secrecion_nasal"},
     "Consulta veterinaria; frecuente en galpones con mala ventilacion.",
     "Media"),
    R("R113", "ave", "Aspergilosis aviar",
     {"dificultad_respirar", "letargia", "perdida_peso"},
     "Consulta veterinaria; causada por hongos en cama o alimento humedo, mejorar almacenamiento.",
     "Media"),
    R("R114", "ave", "Sindrome ascitico",
     {"abdomen_hinchado", "dificultad_respirar", "letargia"},
     "Consulta veterinaria; comun en pollos de engorde de crecimiento rapido.",
     "Media"),
    R("R115", "ave", "Higado graso (sindrome hepatico graso)",
     {"aumento_peso", "disminucion_postura", "letargia"},
     "Ajuste de la dieta con apoyo veterinario; comun en aves de postura sobrealimentadas.",
     "Media"),
    R("R116", "ave", "Sindrome de la caida de postura (EDS)",
     {"disminucion_postura", "huevos_deformes"},
     "Consulta veterinaria avicola; enfermedad viral que afecta la calidad del cascaron.",
     "Baja"),
    R("R117", "ave", "Laringotraqueitis infecciosa",
     {"dificultad_respirar", "sangre_pico", "tos"},
     "Consulta veterinaria urgente; enfermedad viral respiratoria de alta contagiosidad.",
     "Alta"),
    R("R118", "ave", "Botulismo aviar",
     {"debilidad", "paralisis_alas_patas", "plumas_erizadas"},
     "Retirar alimento en descomposicion del galpon y consultar al veterinario urgentemente.",
     "Alta"),
    R("R119", "ave", "Ascaridiasis (lombrices intestinales)",
     {"diarrea", "perdida_peso", "plumas_erizadas"},
     "Desparasitacion segun indicacion veterinaria y mejora en la limpieza del galpon.",
     "Media"),
    R("R120", "ave", "Piojos y acaros externos",
     {"perdida_plumas", "picazon_intensa", "plumas_erizadas"},
     "Tratamiento antiparasitario topico y limpieza de nidos y perchas.",
     "Baja"),
    R("R121", "ave", "Onfalitis (infeccion del ombligo en pollitos)",
     {"hinchazon_ombligo", "letargia", "plumas_erizadas"},
     "Consulta veterinaria; mejorar la higiene de la incubadora y nacedora.",
     "Media"),
    R("R122", "ave", "Encefalomielitis aviar",
     {"disminucion_postura", "paralisis_alas_patas", "temblores"},
     "Consulta veterinaria avicola; enfermedad viral que afecta el sistema nervioso de aves jovenes.",
     "Media"),
    R("R123", "ave", "Raquitismo (deficiencia nutricional)",
     {"deformidad_huesos", "disminucion_postura", "patas_debiles"},
     "Ajustar la dieta con apoyo veterinario, revisando niveles de calcio, fosforo y vitamina D.",
     "Baja"),
    R("R124", "ave", "Picaje / canibalismo (por estres o hacinamiento)",
     {"heridas_piel", "perdida_plumas", "plumas_erizadas"},
     "Reducir la densidad del galpon, mejorar ventilacion e iluminacion; consulta veterinaria si hay heridas infectadas.",
     "Baja"),
    R("R125", "ave", "Prolapso de cloaca",
     {"disminucion_postura", "hinchazon_cloaca", "sangre_heces"},
     "Consulta veterinaria urgente; frecuente en aves de postura por huevos grandes o esfuerzo excesivo.",
     "Media"),

    # ---------- CERDO (25) ----------
    R("R126", "cerdo", "Peste porcina clasica",
     {"diarrea", "fiebre", "manchas_rojas_piel", "temblores"},
     "Notificacion obligatoria a la autoridad sanitaria y aislamiento inmediato del lote; alta mortalidad.",
     "Alta"),
    R("R127", "cerdo", "Diarrea porcina epidemica",
     {"deshidratacion", "diarrea", "perdida_apetito", "vomito"},
     "Rehidratacion oral urgente (sobre todo en lechones) y consulta veterinaria; muy contagiosa en la piara.",
     "Alta"),
    R("R128", "cerdo", "Erisipela porcina",
     {"cojera", "fiebre", "manchas_rojas_piel"},
     "Tratamiento antibiotico veterinario; las lesiones en forma de rombo en la piel son un signo caracteristico.",
     "Media"),
    R("R129", "cerdo", "Peste porcina africana",
     {"dificultad_respirar", "fiebre", "letargia", "manchas_rojas_piel"},
     "Notificacion obligatoria a la autoridad sanitaria; enfermedad viral de muy alta mortalidad, sin vacuna disponible.",
     "Alta"),
    R("R130", "cerdo", "Sindrome respiratorio y reproductivo porcino (PRRS)",
     {"aborto", "dificultad_respirar", "fiebre", "letargia"},
     "Consulta veterinaria; afecta tanto la reproduccion como el sistema respiratorio del hato.",
     "Alta"),
    R("R131", "cerdo", "Gastroenteritis transmisible (TGE)",
     {"deshidratacion", "diarrea", "perdida_peso", "vomito"},
     "Rehidratacion urgente y consulta veterinaria; muy grave en lechones jovenes.",
     "Alta"),
    R("R132", "cerdo", "Enfermedad de Aujeszky (pseudorrabia)",
     {"convulsiones", "dificultad_respirar", "temblores"},
     "Notificacion a la autoridad sanitaria; enfermedad viral neurologica de control obligatorio.",
     "Alta"),
    R("R133", "cerdo", "Rinitis atrofica",
     {"deformidad_hocico", "estornudos", "secrecion_nasal"},
     "Consulta veterinaria; mejorar ventilacion y manejo del galpon para prevenir contagio.",
     "Media"),
    R("R134", "cerdo", "Enfermedad de Glasser",
     {"cojera", "dificultad_respirar", "fiebre", "hinchazon_articulaciones"},
     "Tratamiento antibiotico veterinario; comun en el destete por estres.",
     "Alta"),
    R("R135", "cerdo", "Neumonia enzootica (mycoplasma)",
     {"dificultad_respirar", "perdida_peso", "tos"},
     "Consulta veterinaria; mejorar ventilacion y densidad de animales en el galpon.",
     "Media"),
    R("R136", "cerdo", "Colibacilosis porcina",
     {"deshidratacion", "diarrea", "letargia"},
     "Rehidratacion y tratamiento antibiotico segun indicacion veterinaria; comun en lechones lactantes.",
     "Alta"),
    R("R137", "cerdo", "Salmonelosis porcina",
     {"diarrea", "fiebre", "perdida_apetito"},
     "Consulta veterinaria; mejorar higiene del agua y alimento.",
     "Media"),
    R("R138", "cerdo", "Leptospirosis porcina",
     {"aborto", "fiebre", "ictericia"},
     "Consulta veterinaria urgente; es zoonotica, extremar higiene al manipular a los animales.",
     "Alta"),
    R("R139", "cerdo", "Parvovirosis porcina",
     {"aborto", "retencion_placenta"},
     "Consulta veterinaria; principal causa infecciosa de fallas reproductivas en cerdas, prevenible con vacuna.",
     "Media"),
    R("R140", "cerdo", "Circovirosis porcina (PCV2)",
     {"dificultad_respirar", "palidez_piel", "perdida_peso"},
     "Consulta veterinaria; frecuente en lechones en la etapa de destete.",
     "Media"),
    R("R141", "cerdo", "Ileitis porcina (enteropatia proliferativa)",
     {"diarrea", "palidez_piel", "perdida_peso"},
     "Consulta veterinaria para tratamiento antibiotico especifico.",
     "Media"),
    R("R142", "cerdo", "Disenteria porcina",
     {"diarrea_sangre", "letargia", "perdida_peso"},
     "Consulta veterinaria urgente; mejorar higiene y desinfeccion de instalaciones.",
     "Alta"),
    R("R143", "cerdo", "Coccidiosis porcina",
     {"diarrea", "letargia", "perdida_peso"},
     "Tratamiento antiparasitario coccidiostato y mejora en la higiene de las jaulas de maternidad.",
     "Media"),
    R("R144", "cerdo", "Sarna sarcoptica porcina",
     {"costras_piel", "perdida_pelo", "picazon_intensa"},
     "Tratamiento antiparasitario indicado por el veterinario.",
     "Media"),
    R("R145", "cerdo", "Piojos porcinos",
     {"parasitos_visibles", "perdida_pelo", "picazon_intensa"},
     "Tratamiento antiparasitario topico y limpieza de instalaciones.",
     "Baja"),
    R("R146", "cerdo", "Tetanos porcino",
     {"dificultad_masticar", "espasmos", "rigidez_muscular"},
     "Emergencia veterinaria; revisar heridas recientes (por ejemplo, tras castracion).",
     "Alta"),
    R("R147", "cerdo", "Rabia porcina",
     {"agresividad", "paralisis", "salivacion_excesiva"},
     "EMERGENCIA de salud publica; notificar a la autoridad sanitaria y no manipular sin proteccion.",
     "Alta"),
    R("R148", "cerdo", "Hernia umbilical o inguinal",
     {"bulto_abdominal", "letargia"},
     "Consulta veterinaria para evaluar si requiere correccion quirurgica.",
     "Baja"),
    R("R149", "cerdo", "Artritis porcina",
     {"cojera", "dificultad_levantarse", "fiebre", "hinchazon_articulaciones"},
     "Consulta veterinaria para tratamiento antiinflamatorio o antibiotico segun la causa.",
     "Media"),
    R("R150", "cerdo", "Sindrome de estres porcino",
     {"dificultad_respirar", "rigidez_muscular", "temblores"},
     "Manejo cuidadoso para evitar estres (transporte, calor, manejo brusco) y consulta veterinaria; puede ser mortal.",
     "Alta"),

    # ---------- OVEJA (25) ----------
    R("R151", "oveja", "Ectima contagioso (Orf)",
     {"cojera", "costras_boca", "salivacion_excesiva"},
     "Usar guantes al manipular (zoonotica); consulta veterinaria, suele resolverse sola en unas semanas.",
     "Media"),
    R("R152", "oveja", "Enterotoxemia",
     {"convulsiones", "diarrea", "dolor_abdominal"},
     "Emergencia veterinaria; revisar cambios bruscos de dieta como posible desencadenante.",
     "Alta"),
    R("R153", "oveja", "Fasciolasis ovina",
     {"diarrea", "ictericia", "perdida_peso"},
     "Tratamiento antiparasitario (fasciolicida) y manejo de zonas de pastoreo humedas.",
     "Media"),
    R("R154", "oveja", "Footrot (pododermatitis)",
     {"cojera", "hinchazon_pezuna", "mal_olor_pezuna"},
     "Limpieza y tratamiento local de la pezuña; consulta veterinaria si se extiende al hato.",
     "Media"),
    R("R155", "oveja", "Coccidiosis ovina",
     {"diarrea_sangre", "letargia", "perdida_peso"},
     "Tratamiento antiparasitario coccidiostato y mejora en la higiene de los corrales.",
     "Media"),
    R("R156", "oveja", "Haemonchosis (parasito gastrointestinal)",
     {"abdomen_hinchado", "letargia", "palidez_encias", "perdida_peso"},
     "Desparasitacion urgente segun indicacion veterinaria; puede causar anemia severa.",
     "Alta"),
    R("R157", "oveja", "Linfadenitis caseosa",
     {"hinchazon_ganglios", "nodulos_piel"},
     "Consulta veterinaria; aislar animales con abscesos abiertos por ser contagiosa.",
     "Media"),
    R("R158", "oveja", "Fiebre aftosa ovina",
     {"ampollas_boca", "cojera", "fiebre", "salivacion_excesiva"},
     "Notificar de inmediato a la autoridad sanitaria: enfermedad de declaracion obligatoria.",
     "Alta"),
    R("R159", "oveja", "Lengua azul (bluetongue)",
     {"cojera", "fiebre", "hinchazon_cara", "ulceras_boca"},
     "Consulta veterinaria; transmitida por insectos, notificar a la autoridad sanitaria.",
     "Alta"),
    R("R160", "oveja", "Paratuberculosis (enfermedad de Johne)",
     {"diarrea", "letargia", "perdida_peso"},
     "Consulta veterinaria; enfermedad cronica de dificil tratamiento, aislar animales afectados.",
     "Media"),
    R("R161", "oveja", "Neumonia (pasteurelosis)",
     {"dificultad_respirar", "fiebre", "tos"},
     "Tratamiento antibiotico veterinario urgente; comun en cambios bruscos de clima.",
     "Alta"),
    R("R162", "oveja", "Mastitis ovina",
     {"fiebre", "leche_anormal", "ubre_inflamada"},
     "Consulta veterinaria para tratamiento antibiotico intramamario.",
     "Media"),
    R("R163", "oveja", "Toxemia de la gestacion",
     {"convulsiones", "debilidad", "incapacidad_levantarse", "perdida_apetito"},
     "Emergencia veterinaria; comun en hembras gestando multiples crias con dieta insuficiente.",
     "Alta"),
    R("R164", "oveja", "Cetosis (en cabras lecheras)",
     {"disminucion_produccion_leche", "letargia", "perdida_apetito"},
     "Consulta veterinaria y ajuste de la dieta energetica.",
     "Media"),
    R("R165", "oveja", "Fiebre de leche (hipocalcemia)",
     {"debilidad", "incapacidad_levantarse", "temblores"},
     "Emergencia veterinaria; requiere aplicacion de calcio, comun tras el parto.",
     "Alta"),
    R("R166", "oveja", "Calculos urinarios (urolitiasis)",
     {"dificultad_orinar", "dolor_abdominal", "sangre_orina"},
     "Emergencia veterinaria, mas frecuente en machos castrados jovenes.",
     "Alta"),
    R("R167", "oveja", "Sarna",
     {"costras_piel", "perdida_pelo", "picazon_intensa"},
     "Tratamiento antiparasitario indicado por el veterinario.",
     "Media"),
    R("R168", "oveja", "Piojos y garrapatas",
     {"parasitos_visibles", "perdida_pelo", "picazon_intensa"},
     "Tratamiento antiparasitario topico y control de garrapatas en el potrero.",
     "Baja"),
    R("R169", "oveja", "Aborto enzootico (clamidiosis)",
     {"aborto", "secrecion_vaginal_anormal"},
     "Consulta veterinaria urgente; es zoonotica, extremar higiene con hembras que abortaron.",
     "Alta"),
    R("R170", "oveja", "Toxoplasmosis ovina",
     {"aborto", "fiebre"},
     "Consulta veterinaria; principal causa infecciosa de aborto en ovejas, extremar higiene.",
     "Media"),
    R("R171", "oveja", "Listeriosis",
     {"fiebre", "incoordinacion", "paralisis_facial"},
     "Emergencia veterinaria; asociada a consumo de ensilaje en mal estado.",
     "Alta"),
    R("R172", "oveja", "Polioencefalomalacia",
     {"ceguera", "convulsiones", "incoordinacion"},
     "Emergencia veterinaria; relacionada con deficiencia de vitamina B1 (tiamina).",
     "Alta"),
    R("R173", "oveja", "Tetanos (ovino/caprino)",
     {"dificultad_masticar", "espasmos", "rigidez_muscular"},
     "Emergencia veterinaria; revisar heridas recientes (castracion, descole) y vacunacion.",
     "Alta"),
    R("R174", "oveja", "Rabia (ovina/caprina)",
     {"agresividad", "paralisis", "salivacion_excesiva"},
     "EMERGENCIA de salud publica; notificar a la autoridad sanitaria y no manipular sin proteccion.",
     "Alta"),
    R("R175", "oveja", "Timpanismo caprino/ovino",
     {"dificultad_respirar", "hinchazon_abdominal"},
     "Emergencia veterinaria; puede requerir liberacion urgente del gas acumulado.",
     "Alta"),

    # ---------- CONEJO (25) ----------
    R("R176", "conejo", "Mixomatosis",
     {"hinchazon_parpados", "letargia", "nodulos_piel", "secrecion_ocular"},
     "Consulta veterinaria urgente; enfermedad viral transmitida por insectos, con alta mortalidad y sin cura especifica.",
     "Alta"),
    R("R177", "conejo", "Enfermedad hemorragica viral (RHDV)",
     {"dificultad_respirar", "fiebre", "letargia", "sangrado_nariz"},
     "Emergencia veterinaria; enfermedad viral de curso muy rapido y alta mortalidad, vacunacion preventiva recomendada.",
     "Alta"),
    R("R178", "conejo", "Coccidiosis en conejos",
     {"diarrea", "letargia", "perdida_apetito", "perdida_peso"},
     "Tratamiento coccidiostato indicado por el veterinario y limpieza estricta de jaulas y bebederos.",
     "Media"),
    R("R179", "conejo", "Pasteurelosis (rinitis / snuffles)",
     {"estornudos", "secrecion_nasal", "secrecion_ocular"},
     "Consulta veterinaria; puede volverse cronica, mejorar ventilacion e higiene de la jaula.",
     "Media"),
    R("R180", "conejo", "Estasis gastrointestinal",
     {"abdomen_hinchado", "ausencia_heces", "bruxismo", "perdida_apetito"},
     "Emergencia veterinaria; comun por dieta baja en fibra o estres, requiere atencion rapida.",
     "Alta"),
    R("R181", "conejo", "Maloclusion dental",
     {"dificultad_comer", "perdida_peso", "salivacion_excesiva"},
     "Consulta veterinaria para limado de dientes; revisar la dieta con suficiente fibra.",
     "Media"),
    R("R182", "conejo", "Sarna (acariasis) en conejos",
     {"costras_piel", "perdida_pelo", "picazon_intensa"},
     "Tratamiento antiparasitario indicado por el veterinario.",
     "Media"),
    R("R183", "conejo", "Dermatofitosis (tina)",
     {"costras_piel", "perdida_pelo", "zonas_circulares_sin_pelo"},
     "Consulta veterinaria; es contagiosa para otras mascotas y personas.",
     "Baja"),
    R("R184", "conejo", "Otitis (acaros del oido)",
     {"costras_oido", "mal_olor_oidos", "sacude_cabeza"},
     "Consulta veterinaria para tratamiento antiparasitario especifico de oidos.",
     "Media"),
    R("R185", "conejo", "Pododermatitis (mal de patas)",
     {"cojera", "dificultad_moverse", "heridas_patas"},
     "Mejorar la superficie de la jaula (evitar rejillas) y consulta veterinaria si hay infeccion.",
     "Media"),
    R("R186", "conejo", "Abscesos subcutaneos",
     {"bulto_piel", "fiebre"},
     "Consulta veterinaria para drenaje y tratamiento antibiotico; en conejos suelen ser dificiles de curar.",
     "Baja"),
    R("R187", "conejo", "Encefalitozoonosis",
     {"incoordinacion", "paralisis", "torticolis"},
     "Consulta veterinaria; enfermedad parasitaria que afecta el sistema nervioso y los riñones.",
     "Alta"),
    R("R188", "conejo", "Enteritis mucoide",
     {"diarrea_mucosa", "letargia", "perdida_apetito"},
     "Emergencia veterinaria; mas frecuente en conejos jovenes recien destetados.",
     "Alta"),
    R("R189", "conejo", "Timpanismo / gases en conejos",
     {"abdomen_hinchado", "dolor_abdominal", "perdida_apetito"},
     "Emergencia veterinaria; requiere atencion rapida para aliviar el dolor y el gas acumulado.",
     "Alta"),
    R("R190", "conejo", "Golpe de calor",
     {"dificultad_respirar", "letargia", "salivacion_excesiva"},
     "Emergencia: trasladar a un lugar fresco y llevar al veterinario de inmediato; los conejos son muy sensibles al calor.",
     "Alta"),
    R("R191", "conejo", "Conjuntivitis (ojo llorón)",
     {"enrojecimiento_ojos", "secrecion_ocular"},
     "Limpieza ocular con suero fisiologico y consulta veterinaria si no mejora.",
     "Baja"),
    R("R192", "conejo", "Mastitis en conejas",
     {"fiebre", "letargia", "ubre_inflamada"},
     "Consulta veterinaria urgente para tratamiento antibiotico.",
     "Alta"),
    R("R193", "conejo", "Hepatococcidiosis (coccidiosis hepatica)",
     {"abdomen_hinchado", "ictericia", "perdida_peso"},
     "Tratamiento antiparasitario veterinario; puede ser grave en conejos jovenes.",
     "Alta"),
    R("R194", "conejo", "Neumonia en conejos",
     {"dificultad_respirar", "letargia", "secrecion_nasal"},
     "Consulta veterinaria urgente y tratamiento antibiotico.",
     "Alta"),
    R("R195", "conejo", "Uñas o garras rotas",
     {"cojera", "heridas_patas", "una_rota"},
     "Curacion local de la herida y consulta veterinaria si hay signos de infeccion.",
     "Baja"),
    R("R196", "conejo", "Bola de pelo (tricobezoar)",
     {"abdomen_hinchado", "heces_unidas_pelo", "perdida_apetito"},
     "Consulta veterinaria; cepillado regular y dieta alta en fibra para prevenirlo.",
     "Media"),
    R("R197", "conejo", "Fracturas oseas (por caida o mal manejo)",
     {"cojera", "dificultad_moverse", "dolor_al_tocar"},
     "Emergencia veterinaria; los conejos tienen huesos fragiles y requieren manejo muy cuidadoso.",
     "Alta"),
    R("R198", "conejo", "Papilomatosis oral",
     {"dificultad_comer", "ulceras_boca"},
     "Consulta veterinaria; suele resolverse sola pero conviene confirmar el diagnostico.",
     "Baja"),
    R("R199", "conejo", "Torticolis vestibular (infeccion de oido interno)",
     {"incoordinacion", "mal_olor_oidos", "torticolis"},
     "Consulta veterinaria urgente; puede deberse a infeccion bacteriana o parasitaria del oido interno.",
     "Alta"),
    R("R200", "conejo", "Miasis (gusanera)",
     {"heridas_piel", "letargia", "mal_olor_piel"},
     "Emergencia veterinaria; comun en climas calidos si el conejo tiene heridas o suciedad en el pelaje.",
     "Alta"),
]

assert len(REGLAS) >= 25, "La base de conocimiento debe tener al menos 25 reglas."


# =============================================================================
# 2. TEXTO DE LAS PREGUNTAS PARA CADA SINTOMA (para la Memoria de Trabajo)
# =============================================================================

PREGUNTAS: Dict[str, str] = {
    "vomito": "¿El animal ha presentado vomito?",
    "diarrea": "¿El animal tiene diarrea?",
    "diarrea_sangre": "¿La diarrea tiene sangre?",
    "fiebre": "¿El animal tiene fiebre (temperatura elevada)?",
    "letargia": "¿El animal esta decaido / con poca energia (letargia)?",
    "perdida_apetito": "¿El animal ha perdido el apetito?",
    "aumento_apetito": "¿El animal come mas de lo normal?",
    "tos": "¿El animal tose?",
    "secrecion_nasal": "¿Tiene secrecion (moco) nasal?",
    "secrecion_ocular": "¿Tiene secrecion en los ojos?",
    "picazon_intensa": "¿Se rasca o lame de forma intensa y frecuente?",
    "perdida_pelo": "¿Ha perdido pelo en zonas del cuerpo?",
    "costras_piel": "¿Tiene costras o escamas en la piel?",
    "mal_olor_oidos": "¿Los oidos tienen mal olor?",
    "sacude_cabeza": "¿Sacude la cabeza con frecuencia?",
    "dolor_al_tocar_oido": "¿Muestra dolor o molestia al tocarle los oidos?",
    "ictericia": "¿Las encias, piel o parte blanca de los ojos se ven amarillas (ictericia)?",
    "aumento_sed": "¿Bebe agua mas de lo normal?",
    "dolor_abdominal": "¿Muestra signos de dolor abdominal (se queja, adopta posturas raras)?",
    "abdomen_hinchado": "¿Tiene el abdomen hinchado o distendido?",
    "perdida_peso": "¿Ha perdido peso de forma notoria?",
    "aumento_orina": "¿Orina mas de lo normal?",
    "estornudos": "¿Estornuda con frecuencia?",
    "ulceras_boca": "¿Tiene ulceras o llagas en la boca?",
    "dificultad_respirar": "¿Respira con dificultad o de forma agitada?",
    "hiperactividad": "¿Esta mas activo/inquieto de lo habitual?",
    "infecciones_recurrentes": "¿Ha tenido infecciones repetidas (piel, boca, respiratorias)?",
    "convulsiones": "¿Ha tenido convulsiones o temblores fuertes?",
    "ubre_inflamada": "¿Tiene la ubre inflamada o caliente?",
    "leche_anormal": "¿La leche se ve anormal (grumos, sangre, color raro)?",
    "disminucion_produccion_leche": "¿Ha disminuido notoriamente la produccion de leche?",
    "ampollas_boca": "¿Tiene ampollas o llagas en la boca/lengua?",
    "ampollas_pezunas": "¿Tiene ampollas o lesiones en las pezunas?",
    "salivacion_excesiva": "¿Saliva mas de lo normal?",
    "cojera": "¿El animal cojea o le cuesta caminar?",
    "hinchazon_abdominal": "¿Tiene el abdomen (panza/rumen) muy hinchado?",
    "aborto": "¿Ha tenido un aborto reciente?",
    "retencion_placenta": "¿Retuvo la placenta tras el parto por mas tiempo de lo normal?",
    "revolcarse": "¿Se revuelca o patea su propio abdomen con frecuencia?",
    "sudoracion_excesiva": "¿Suda de forma excesiva?",
    "ausencia_heces": "¿Ha dejado de defecar?",
    "calor_en_pezunas": "¿Las pezunas estan calientes al tacto?",
    "renuencia_moverse": "¿Se resiste a moverse o caminar?",
    "rigidez_muscular": "¿Presenta rigidez muscular general?",
    "espasmos": "¿Tiene espasmos musculares?",
    "dificultad_masticar": "¿Le cuesta masticar o abrir la boca?",
    "diarrea_verde": "¿La diarrea es de color verdoso?",
    "torticolis": "¿Tuerce el cuello hacia atras o de lado (torticolis)?",
    "paralisis_alas_patas": "¿Tiene paralisis en alas o patas?",
    "disminucion_postura": "¿Ha bajado la produccion de huevos (postura)?",
    "hinchazon_cara": "¿Tiene la cara hinchada?",
    "sangre_heces": "¿Hay sangre visible en las heces?",
    "plumas_erizadas": "¿Tiene las plumas erizadas y sucias?",
    "manchas_rojas_piel": "¿Tiene manchas rojas o moradas en la piel?",
    "temblores": "¿Presenta temblores?",
    "deshidratacion": "¿Muestra signos de deshidratacion (piel poco elastica, ojos hundidos)?",
    "costras_boca": "¿Tiene costras alrededor de la boca o el hocico?",
    "hinchazon_parpados": "¿Tiene los parpados hinchados?",
    "nodulos_piel": "¿Tiene nodulos o bultos en la piel?",
    "sangrado_nariz": "¿Ha sangrado por la nariz?",

    # --- sintomas adicionales (base de conocimiento ampliada a 25 x especie) ---
    "agresividad": "¿Ha mostrado agresividad inusual o cambios bruscos de conducta?",
    "arcadas_sin_vomito": "¿Hace arcadas o intenta vomitar sin lograrlo?",
    "aumento_peso": "¿Ha subido de peso de forma notoria?",
    "bruxismo": "¿Rechina los dientes con frecuencia?",
    "bulto_abdominal": "¿Se le nota un bulto o protuberancia en el abdomen?",
    "bulto_piel": "¿Tiene algun bulto debajo de la piel?",
    "cambios_comportamiento": "¿Ha tenido cambios extranios de comportamiento?",
    "ceguera": "¿Parece haber perdido la vision (ceguera)?",
    "costras_cresta": "¿Tiene costras o granos en la cresta o zonas sin plumas?",
    "costras_oido": "¿Tiene costras dentro o alrededor del oido?",
    "debilidad": "¿Se le nota debilidad general?",
    "debilidad_patas_traseras": "¿Tiene debilidad o le cuesta mover las patas traseras?",
    "deformidad_hocico": "¿Tiene el hocico deformado o hundido?",
    "deformidad_huesos": "¿Tiene los huesos o patas con alguna deformidad?",
    "deposito_grasa_anormal": "¿Tiene acumulaciones de grasa anormales (por ejemplo en el cuello)?",
    "diarrea_blanca": "¿Tiene diarrea de color blanquecino?",
    "diarrea_mucosa": "¿La diarrea tiene mucosidad o gelatina visible?",
    "dificultad_comer": "¿Le cuesta comer o mastica con dificultad?",
    "dificultad_levantarse": "¿Le cuesta levantarse?",
    "dificultad_moverse": "¿Tiene dificultad para moverse o desplazarse?",
    "dificultad_orinar": "¿Tiene dificultad o esfuerzo notorio para orinar?",
    "dificultad_tragar": "¿Tiene dificultad para tragar?",
    "dolor_al_caminar": "¿Muestra dolor evidente al caminar?",
    "dolor_al_tocar": "¿Se queja o reacciona con dolor cuando se le toca la zona afectada?",
    "enrojecimiento_ojos": "¿Tiene los ojos enrojecidos?",
    "enrojecimiento_piel": "¿Tiene zonas de la piel enrojecidas o irritadas?",
    "estrenimiento": "¿Ha dejado de defecar con normalidad (estreñimiento)?",
    "ganglios_inflamados": "¿Se le notan los ganglios (bolitas bajo la piel) inflamados?",
    "grietas_casco": "¿Tiene grietas visibles en el casco?",
    "heridas_patas": "¿Tiene heridas o llagas en las patas?",
    "heridas_piel": "¿Tiene heridas abiertas en la piel?",
    "hinchazon_articulaciones": "¿Tiene alguna articulacion hinchada?",
    "hinchazon_cloaca": "¿Tiene la cloaca hinchada o sobresalida (prolapso)?",
    "hinchazon_cuello": "¿Tiene el cuello hinchado?",
    "hinchazon_ganglios": "¿Tiene los ganglios del cuello o mandibula inflamados?",
    "hinchazon_muscular": "¿Tiene alguna zona muscular hinchada?",
    "hinchazon_ombligo": "¿Tiene el ombligo hinchado o con mal aspecto?",
    "hinchazon_oreja": "¿Tiene la oreja hinchada?",
    "hinchazon_pezuna": "¿Tiene la pezuña hinchada?",
    "huevos_deformes": "¿Ha puesto huevos con cascaron deforme o muy delgado?",
    "incapacidad_levantarse": "¿Es incapaz de levantarse por si mismo/a?",
    "incoordinacion": "¿Se le nota descoordinado al caminar o moverse (como mareado)?",
    "mal_aliento": "¿Tiene mal aliento notorio?",
    "mal_olor_pezuna": "¿La pezuña tiene mal olor?",
    "mal_olor_piel": "¿La piel tiene mal olor?",
    "maullidos_al_orinar": "¿Maulla o se queja al intentar orinar?",
    "no_apoya_pata": "¿Evita apoyar por completo una de las patas?",
    "opacidad_ojos": "¿Tiene los ojos opacos o nublados?",
    "palidez_encias": "¿Tiene las encias palidas (en vez de rosadas)?",
    "palidez_piel": "¿Tiene la piel palida?",
    "paralisis": "¿Tiene paralisis en alguna parte del cuerpo?",
    "paralisis_facial": "¿Tiene parte de la cara caida o paralizada?",
    "patas_debiles": "¿Tiene las patas debiles o le cuesta sostenerse en ellas?",
    "pelaje_largo_anormal": "¿Tiene el pelaje anormalmente largo o rizado para la epoca?",
    "pelaje_opaco": "¿Tiene el pelaje opaco o deslucido?",
    "perdida_conciencia": "¿Ha perdido el conocimiento en algun momento?",
    "perdida_plumas": "¿Ha perdido plumas en varias zonas?",
    "picazon_ojos": "¿Se rasca o frota los ojos con frecuencia?",
    "piel_seca": "¿Tiene la piel notablemente seca?",
    "sangrado_orificios": "¿Ha sangrado por la nariz, boca u otros orificios?",
    "sangre_orina": "¿Hay sangre visible en la orina?",
    "sangre_pico": "¿Ha sangrado por el pico?",
    "secrecion_nasal_alimento": "¿Sale comida o liquido por la nariz?",
    "secrecion_vaginal_anormal": "¿Tiene una secrecion vaginal anormal?",
    "sibilancias": "¿Se le escuchan silbidos al respirar?",
    "tumores_visibles": "¿Se le notan bultos o tumores visibles en el cuerpo?",
    "zonas_circulares_sin_pelo": "¿Tiene zonas circulares sin pelo bien delimitadas?",

    # --- sintomas discriminantes agregados en la correccion de reglas (v2) ---
    "enrojecimiento_hocico": "¿Tiene el hocico (morro) muy enrojecido o inflamado?",
    "estertores": "¿Se escuchan ruidos humedos o crepitantes en el pecho al respirar?",
    "dolor_talones": "¿Muestra dolor al presionar la zona de los talones del casco?",
    "mechones_pelo_pegados": "¿Tiene mechones de pelo pegados por costras (aspecto de pincel)?",
    "parasitos_visibles": "¿Se ven piojos, liendres o garrapatas a simple vista en el pelaje?",
    "una_rota": "¿Tiene alguna uña rota, arrancada o sangrante?",
    "heces_unidas_pelo": "¿Las heces salen pequenas y unidas por pelo (en forma de collar)?",
}


# Verificacion de consistencia: toda regla debe tener pregunta para cada uno
# de sus sintomas. Si esto falla, el programa avisa de inmediato al iniciar
# (en vez de fallar en silencio mas adelante al hacer clic en un boton).
_sintomas_sin_pregunta = {s for _r in REGLAS for s in _r.sintomas if s not in PREGUNTAS}
assert not _sintomas_sin_pregunta, (
    f"Faltan preguntas en PREGUNTAS para estos sintomas: {_sintomas_sin_pregunta}"
)


NOMBRES_ESPECIE = {
    "perro": "Perro",
    "gato": "Gato",
    "vaca": "Vaca / Ganado bovino",
    "caballo": "Caballo / Equino",
    "ave": "Ave de corral (gallina, pollo)",
    "cerdo": "Cerdo",
    "oveja": "Oveja / Cabra",
    "conejo": "Conejo",
}


# =============================================================================
# 3. HIPOTESIS INTERMEDIAS: SISTEMA AFECTADO  (correccion v2 del arbol)
# =============================================================================
#
# En la version anterior el arbol iba directo de la especie a sus 25
# enfermedades (un solo nivel, sin preguntas). Se agrega un nivel de
# hipotesis intermedias: el SISTEMA AFECTADO. El razonamiento queda en dos
# pasos de encadenamiento hacia adelante:
#
#   Nivel 1 (reglas RS###):  SI especie = E Y <signo guia>  ENTONCES sistema = S
#   Nivel 2 (reglas R###):   SI especie = E Y sistema = S Y <sintomas>
#                            ENTONCES enfermedad = H
#
# Cada sistema tiene un vocabulario de "signos guia"; un signo pertenece a un
# solo sistema.

SISTEMAS: Dict[str, Tuple[str, frozenset]] = {
    "DIG": ("Digestivo y hepatico", frozenset({
        "vomito", "diarrea", "diarrea_sangre", "diarrea_verde", "diarrea_blanca",
        "diarrea_mucosa", "dolor_abdominal", "abdomen_hinchado", "hinchazon_abdominal",
        "ausencia_heces", "estrenimiento", "arcadas_sin_vomito", "sangre_heces",
        "ictericia", "dificultad_tragar", "dificultad_comer", "mal_aliento",
        "ulceras_boca", "bruxismo", "secrecion_nasal_alimento", "deshidratacion",
        "bulto_abdominal", "heces_unidas_pelo"})),
    "RES": ("Respiratorio y cardiaco", frozenset({
        "tos", "estornudos", "secrecion_nasal", "dificultad_respirar", "sibilancias",
        "sangre_pico", "deformidad_hocico", "sangrado_nariz", "hinchazon_cara",
        "estertores", "enrojecimiento_hocico", "debilidad_patas_traseras"})),
    "PIEL": ("Piel, pelo y plumas", frozenset({
        "picazon_intensa", "perdida_pelo", "costras_piel", "enrojecimiento_piel",
        "mal_olor_piel", "piel_seca", "zonas_circulares_sin_pelo", "nodulos_piel",
        "perdida_plumas", "plumas_erizadas", "heridas_piel", "costras_cresta", "bulto_piel",
        "mechones_pelo_pegados", "parasitos_visibles", "manchas_rojas_piel",
        "costras_boca"})),
    "NERV": ("Nervioso", frozenset({
        "convulsiones", "perdida_conciencia", "paralisis", "paralisis_alas_patas",
        "paralisis_facial", "torticolis", "incoordinacion", "temblores", "espasmos",
        "rigidez_muscular", "agresividad", "cambios_comportamiento", "ceguera",
        "dificultad_masticar"})),
    "LOC": ("Locomotor (patas, pezunas, articulaciones)", frozenset({
        "cojera", "no_apoya_pata", "dificultad_levantarse", "dolor_al_caminar",
        "renuencia_moverse", "calor_en_pezunas", "grietas_casco", "mal_olor_pezuna",
        "hinchazon_pezuna", "hinchazon_articulaciones", "heridas_patas",
        "dificultad_moverse", "hinchazon_muscular", "deformidad_huesos",
        "patas_debiles", "dolor_talones", "una_rota", "incapacidad_levantarse",
        "dolor_al_tocar"})),
    "REP": ("Reproductivo y productivo (leche / huevos)", frozenset({
        "aborto", "retencion_placenta", "secrecion_vaginal_anormal", "ubre_inflamada",
        "leche_anormal", "disminucion_produccion_leche", "disminucion_postura",
        "huevos_deformes", "hinchazon_cloaca"})),
    "URI": ("Urinario, endocrino y metabolico", frozenset({
        "aumento_sed", "aumento_orina", "aumento_apetito", "aumento_peso",
        "dificultad_orinar", "sangre_orina", "maullidos_al_orinar", "hiperactividad",
        "deposito_grasa_anormal", "pelaje_largo_anormal"})),
    "OJO": ("Ojos y oidos", frozenset({
        "secrecion_ocular", "enrojecimiento_ojos", "picazon_ojos", "opacidad_ojos",
        "hinchazon_parpados", "mal_olor_oidos", "sacude_cabeza", "dolor_al_tocar_oido",
        "hinchazon_oreja", "costras_oido"})),
    "SIS": ("Sistemico / infeccioso general", frozenset({
        "fiebre", "letargia", "palidez_encias", "palidez_piel", "ganglios_inflamados",
        "hinchazon_ganglios", "infecciones_recurrentes", "perdida_peso", "debilidad",
        "sangrado_orificios", "hinchazon_cuello", "tumores_visibles",
        "hinchazon_ombligo", "pelaje_opaco", "perdida_apetito", "sudoracion_excesiva",
        "salivacion_excesiva", "revolcarse", "ampollas_boca", "ampollas_pezunas"})),
}

_signos_repetidos = [s for s in PREGUNTAS
                     if sum(s in v[1] for v in SISTEMAS.values()) != 1]
assert not _signos_repetidos, f"Cada sintoma debe pertenecer a un solo sistema: {_signos_repetidos}"

# Sistema (hipotesis intermedia) al que pertenece cada regla de nivel 2.
_ASIGNACION_SISTEMAS = {
    "DIG": "R001 R006 R011 R014 R021 R026 R038 R040 R041 R042 R050 R053 R054 R056 "
           "R061 R065 R073 R076 R084 R085 R086 R096 R099 R103 R107 R110 R111 R119 "
           "R127 R131 R136 R137 R141 R142 R143 R148 R152 R153 R155 R160 R175 R178 "
           "R180 R181 R188 R189 R193 R196 R198",
    "RES": "R012 R013 R027 R028 R039 R046 R057 R074 R078 R080 R081 R087 R102 R104 "
           "R105 R112 R113 R114 R117 R133 R135 R161 R179 R190 R194",
    "PIEL": "R003 R015 R016 R044 R045 R067 R075 R094 R095 R108 R120 R124 R128 R144 "
            "R145 R151 R157 R167 R168 R182 R183 R186 R200",
    "NERV": "R020 R047 R069 R070 R079 R082 R097 R100 R101 R106 R118 R122 R132 R146 "
            "R147 R150 R163 R171 R172 R173 R174 R187 R199",
    "LOC": "R009 R022 R023 R058 R062 R063 R077 R090 R091 R092 R093 R098 R123 R134 "
           "R149 R154 R165 R185 R195 R197",
    "REP": "R051 R055 R060 R064 R066 R116 R125 R130 R138 R139 R162 R164 R169 R170 R192",
    "URI": "R007 R008 R017 R018 R030 R031 R036 R037 R088 R089 R115 R166",
    "OJO": "R004 R024 R025 R033 R048 R049 R068 R176 R184 R191",
    "SIS": "R002 R005 R010 R019 R029 R032 R034 R035 R043 R052 R059 R071 R072 R083 "
           "R109 R121 R126 R129 R140 R156 R158 R159 R177",
}
SISTEMA_POR_REGLA: Dict[str, str] = {
    id_: sistema for sistema, ids in _ASIGNACION_SISTEMAS.items() for id_ in ids.split()
}
assert len(SISTEMA_POR_REGLA) == len(REGLAS) and all(r.id in SISTEMA_POR_REGLA for r in REGLAS), \
    "Cada regla debe tener exactamente un sistema asignado."

REGLAS = [replace(r, sistema=SISTEMA_POR_REGLA[r.id]) for r in REGLAS]

_sin_signo_guia = [r.id for r in REGLAS if not (r.sintomas & SISTEMAS[r.sistema][1])]
assert not _sin_signo_guia, f"Reglas sin ningun signo guia de su sistema: {_sin_signo_guia}"


@dataclass(frozen=True)
class ReglaSistema:
    """Regla de nivel 1: SI especie Y <signo guia> ENTONCES sistema afectado."""
    id: str
    especie: str
    signo: str
    sistema: str


def _generar_reglas_sistema() -> List[ReglaSistema]:
    """Deriva las reglas de nivel 1 a partir de las reglas de nivel 2: un signo
    activa el sistema S en la especie E si es signo guia de S y aparece en
    alguna enfermedad de E clasificada en S."""
    reglas, n = [], 0
    for especie in NOMBRES_ESPECIE:
        for sistema, (_, vocabulario) in SISTEMAS.items():
            signos = set()
            for r in REGLAS:
                if r.especie == especie and r.sistema == sistema:
                    signos |= r.sintomas & vocabulario
            for signo in sorted(signos):
                n += 1
                reglas.append(ReglaSistema(f"RS{n:03d}", especie, signo, sistema))
    return reglas


REGLAS_SISTEMA: List[ReglaSistema] = _generar_reglas_sistema()


# =============================================================================
# 4. MEMORIA DE TRABAJO
# =============================================================================

class MemoriaDeTrabajo:
    """
    Representa la 'memoria de trabajo' (hechos) del sistema de produccion:
    los sintomas que se han confirmado como presentes en el animal evaluado
    y las hipotesis intermedias (sistemas afectados) que el motor deduce.
    """

    def __init__(self, especie: str):
        self.especie = especie
        self.hechos: Set[str] = set()
        self.sistemas: Dict[str, Set[str]] = {}  # sistema -> signos que lo activaron

    def asertar(self, sintoma: str) -> None:
        """Agrega un hecho (sintoma confirmado) a la memoria de trabajo."""
        self.hechos.add(sintoma)

    def asertar_sistema(self, sistema: str, signo: str) -> None:
        """Agrega una hipotesis intermedia deducida por una regla de nivel 1."""
        self.sistemas.setdefault(sistema, set()).add(signo)

    def contiene(self, sintoma: str) -> bool:
        return sintoma in self.hechos


# =============================================================================
# 5. MOTOR DE INFERENCIAS (encadenamiento hacia adelante / forward chaining)
# =============================================================================

class MotorInferencia:
    """
    Compara la memoria de trabajo (hechos) contra la base de conocimiento
    en dos ciclos de encadenamiento hacia adelante:
      1. Reglas de nivel 1: deducen los sistemas afectados.
      2. Reglas de nivel 2: solo se evaluan las enfermedades cuyo sistema
         quedo activado, y se calcula su grado de coincidencia.
    """

    def __init__(self, base_conocimiento: List[Regla],
                 reglas_sistema: List[ReglaSistema] = None):
        self.base_conocimiento = base_conocimiento
        self.reglas_sistema = REGLAS_SISTEMA if reglas_sistema is None else reglas_sistema

    def inferir_sistemas(self, memoria: MemoriaDeTrabajo) -> Dict[str, Set[str]]:
        """Ciclo 1: dispara las reglas RS### cuyas premisas estan en los hechos."""
        for regla in self.reglas_sistema:
            if regla.especie == memoria.especie and memoria.contiene(regla.signo):
                memoria.asertar_sistema(regla.sistema, regla.signo)
        return memoria.sistemas

    def evaluar(self, memoria: MemoriaDeTrabajo) -> List[Tuple[Regla, float, Set[str]]]:
        """
        Devuelve una lista de tuplas (regla, porcentaje_coincidencia,
        sintomas_coincidentes) para las reglas de la especie indicada cuyo
        sistema fue activado, ordenada de mayor a menor coincidencia.
        """
        sistemas = self.inferir_sistemas(memoria)
        resultados = []
        for regla in self.base_conocimiento:
            if regla.especie != memoria.especie or regla.sistema not in sistemas:
                continue
            coincidentes = regla.sintomas & memoria.hechos
            if not coincidentes:
                continue
            # Indice de Jaccard: coincidencias sobre la union de los
            # sintomas que pide la regla y los que reporto el usuario.
            # Asi una regla no llega a 100% si al animal le falta algun
            # sintoma que la regla pide, NI si el animal tiene otros
            # sintomas positivos que la regla no contempla.
            union = regla.sintomas | memoria.hechos
            porcentaje = len(coincidentes) / len(union)
            resultados.append((regla, porcentaje, coincidentes))

        resultados.sort(key=lambda t: (t[1], len(t[2])), reverse=True)
        return resultados


# =============================================================================
# 6. ARBOL DE DECISION (corregido)
# =============================================================================
#
# Estructura:  Especie -> Sistema afectado (hipotesis intermedia)
#              -> preguntas SI/NO sobre sintomas discriminantes -> Enfermedad
#
# Dentro de cada sistema, el arbol se construye eligiendo en cada nodo el
# sintoma que divide a las enfermedades candidatas en dos grupos lo mas
# parecidos posible (asi el arbol queda balanceado y con pocas preguntas).
# Cada hoja corresponde exactamente a una regla de nivel 2; en la hoja se
# listan los sintomas restantes que la regla pide para confirmarse.

@dataclass
class NodoArbol:
    tipo: str                    # "raiz", "especie", "sistema", "pregunta", "hoja"
    texto: str
    sintoma: str = ""            # solo en nodos "pregunta"
    regla: Regla = None          # solo en nodos "hoja"
    confirmar: Tuple[str, ...] = ()
    hijos: List[Tuple[str, "NodoArbol"]] = field(default_factory=list)  # (etiqueta, hijo)


def _discriminar(reglas: List[Regla], ya_preguntados: Set[str]) -> NodoArbol:
    if len(reglas) == 1:
        regla = reglas[0]
        return NodoArbol("hoja", regla.enfermedad, regla=regla,
                         confirmar=tuple(sorted(regla.sintomas - ya_preguntados)))
    candidatos = sorted({s for r in reglas for s in r.sintomas})
    mejor, mejor_puntaje = None, -1
    for s in candidatos:
        con = sum(1 for r in reglas if s in r.sintomas)
        puntaje = min(con, len(reglas) - con)
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = s, puntaje
    assert mejor_puntaje > 0, f"Reglas indistinguibles: {[r.id for r in reglas]}"
    con = [r for r in reglas if mejor in r.sintomas]
    sin = [r for r in reglas if mejor not in r.sintomas]
    nodo = NodoArbol("pregunta", PREGUNTAS.get(mejor, mejor), sintoma=mejor)
    nodo.hijos.append(("SI", _discriminar(con, ya_preguntados | {mejor})))
    nodo.hijos.append(("NO", _discriminar(sin, ya_preguntados)))
    return nodo


def construir_arbol(especie: str = None) -> NodoArbol:
    """Arbol de una especie, o el arbol completo si especie es None."""
    if especie is None:
        raiz = NodoArbol("raiz", "¿Que especie es el animal?")
        for e in NOMBRES_ESPECIE:
            raiz.hijos.append((e, construir_arbol(e)))
        return raiz
    nodo_especie = NodoArbol("especie", NOMBRES_ESPECIE.get(especie, especie))
    for sistema, (nombre, _) in SISTEMAS.items():
        reglas = [r for r in REGLAS if r.especie == especie and r.sistema == sistema]
        if not reglas:
            continue
        signos = sorted(rs.signo for rs in REGLAS_SISTEMA
                        if rs.especie == especie and rs.sistema == sistema)
        nodo_sistema = NodoArbol("sistema", f"Sistema {nombre}")
        nodo_sistema.hijos.append((" o ".join(signos), _discriminar(reglas, set())))
        nodo_especie.hijos.append((sistema, nodo_sistema))
    return nodo_especie


def sintomas_por_especie(especie: str) -> List[str]:
    """Sintomas relevantes para una especie, agrupados por sistema afectado
    (primero los signos guia de cada sistema, luego el resto)."""
    vistos = []
    for sistema in SISTEMAS:
        for regla in REGLAS:
            if regla.especie == especie and regla.sistema == sistema:
                guias = sorted(regla.sintomas & SISTEMAS[sistema][1])
                otros = sorted(regla.sintomas - SISTEMAS[sistema][1])
                for s in guias + otros:
                    if s not in vistos:
                        vistos.append(s)
    return vistos


def construir_texto_arbol_decision(especie: str = None) -> str:
    """
    Construye (sin imprimir) el texto del arbol de decision corregido:
    Especie -> Sistema afectado -> preguntas SI/NO -> Enfermedad.
    Se usa tanto en la version de consola como en la interfaz grafica.
    """
    lineas = ["ARBOL DE DECISION DEL SISTEMA EXPERTO (v2)",
              "(Especie -> Sistema afectado -> preguntas SI/NO -> Enfermedad [regla])",
              "=" * 78]

    def recorrer(nodo: NodoArbol, prefijo: str, etiqueta: str, es_ultimo: bool):
        rama = "└── " if es_ultimo else "├── "
        if nodo.tipo == "especie":
            texto = nodo.texto.upper()
        elif nodo.tipo == "sistema":
            texto = f"[{nodo.texto}]"
        elif nodo.tipo == "pregunta":
            texto = f"{etiqueta}{nodo.texto}"
        else:
            r = nodo.regla
            conf = f"  | confirmar: {', '.join(nodo.confirmar)}" if nodo.confirmar else ""
            texto = f"{etiqueta}=> [{r.id}] {r.enfermedad} (urgencia {r.urgencia}){conf}"
        lineas.append(prefijo + rama + texto)
        hijo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
        for i, (etq, hijo) in enumerate(nodo.hijos):
            ultimo = i == len(nodo.hijos) - 1
            if nodo.tipo == "sistema":
                lineas.append(hijo_prefijo + f"(se activa si presenta: {etq})")
                recorrer(hijo, hijo_prefijo, "", True)
            elif nodo.tipo == "pregunta":
                recorrer(hijo, hijo_prefijo, f"{etq}: ", ultimo)
            else:
                recorrer(hijo, hijo_prefijo, "", ultimo)

    especies = [especie] if especie else list(NOMBRES_ESPECIE)
    for i, e in enumerate(especies):
        recorrer(construir_arbol(e), "", "", i == len(especies) - 1)
    lineas.append("=" * 78)
    return "\n".join(lineas)


def imprimir_arbol_decision() -> None:
    """Imprime en consola el arbol de decision (ver construir_texto_arbol_decision)."""
    print("\n" + construir_texto_arbol_decision() + "\n")


COLOR_URGENCIA = {"Alta": "#f28482", "Media": "#f6bd60", "Baja": "#cdeac0"}


def _dibujar_arbol(raiz: NodoArbol, ruta: str, titulo: str, plt, textwrap) -> None:
    """Dibuja un arbol de izquierda a derecha (hojas apiladas verticalmente)."""
    posiciones = {}
    siguiente_y = [0]

    def ubicar(nodo, nivel):
        if not nodo.hijos:
            y = siguiente_y[0]
            siguiente_y[0] += 1
        else:
            ys = [ubicar(h, nivel + 1) for _, h in nodo.hijos]
            y = sum(ys) / len(ys)
        posiciones[id(nodo)] = (nivel, y)
        return y

    ubicar(raiz, 0)
    n_hojas = siguiente_y[0]
    profundidad = max(x for x, _ in posiciones.values()) + 1
    ancho_col = 3.2
    fig, ax = plt.subplots(figsize=(max(10, profundidad * ancho_col), max(6, n_hojas * 0.62)))
    ax.axis("off")
    ax.set_xlim(-0.2, profundidad * ancho_col)
    ax.set_ylim(n_hojas, -1.2)
    ax.set_title(titulo, fontsize=13, loc="left")

    estilo = {"raiz": "#a8dadc", "especie": "#a8dadc", "sistema": "#bde0fe",
              "pregunta": "#ffffff"}

    def xy(nodo):
        nivel, y = posiciones[id(nodo)]
        return nivel * ancho_col + 0.1, y

    def dibujar(nodo):
        x, y = xy(nodo)
        for etq, hijo in nodo.hijos:
            hx, hy = xy(hijo)
            ax.plot([x + 2.6, hx], [y, hy], color="#9aa5ab", linewidth=0.8, zorder=1)
            if nodo.tipo == "pregunta":
                ax.text((x + 2.6 + hx) / 2, (y + hy) / 2, etq, fontsize=7, ha="center",
                        va="center", color="#3f9142" if etq == "SI" else "#d1495b",
                        fontweight="bold", zorder=4,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
            dibujar(hijo)
        if nodo.tipo == "hoja":
            texto = f"[{nodo.regla.id}] {nodo.regla.enfermedad}"
            color = COLOR_URGENCIA.get(nodo.regla.urgencia, "#eeeeee")
        elif nodo.tipo == "pregunta":
            texto = f"¿{nodo.sintoma}?"
            color = estilo["pregunta"]
        else:
            texto = nodo.texto
            color = estilo[nodo.tipo]
        ax.text(x, y, "\n".join(textwrap.wrap(texto, 34)), fontsize=7, ha="left",
                va="center", zorder=3,
                bbox=dict(boxstyle="round,pad=0.3", fc=color, ec="#333333", lw=0.7))

    dibujar(raiz)
    from matplotlib.patches import Patch
    leyenda = [Patch(facecolor=c, edgecolor="#333333", label=f"Urgencia {u}")
               for u, c in COLOR_URGENCIA.items()]
    leyenda.append(Patch(facecolor=estilo["sistema"], edgecolor="#333333",
                         label="Hipotesis intermedia (sistema)"))
    ax.legend(handles=leyenda, loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig(ruta, dpi=130)
    plt.close(fig)


def generar_diagrama_png(ruta: str = os.path.join("docs", "arbol_decision.png")) -> bool:
    """
    Genera las imagenes del arbol de decision corregido usando matplotlib:
      - `ruta`: vista general Especie -> Sistemas afectados.
      - carpeta `arbol_decision/` junto a `ruta`: un arbol completo por
        especie (sistema -> preguntas SI/NO -> enfermedad).
    Devuelve True si se genero correctamente.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import textwrap
        import os
    except ImportError:
        print("No se pudo generar el PNG: matplotlib no esta instalado.")
        return False

    # Vista general: solo dos niveles bajo la raiz.
    general = NodoArbol("raiz", "¿Que especie es el animal?")
    for e in NOMBRES_ESPECIE:
        nodo_e = NodoArbol("especie", NOMBRES_ESPECIE[e])
        for sistema, (nombre, _) in SISTEMAS.items():
            n = sum(1 for r in REGLAS if r.especie == e and r.sistema == sistema)
            if n:
                nodo_e.hijos.append((sistema, NodoArbol("sistema", f"{nombre} ({n} enf.)")))
        general.hijos.append((e, nodo_e))
    _dibujar_arbol(general, ruta,
                   "Arbol de decision (vista general): Especie -> Sistema afectado\n"
                   f"{len(REGLAS)} reglas de enfermedad + {len(REGLAS_SISTEMA)} reglas de sistema",
                   plt, textwrap)

    carpeta = os.path.join(os.path.dirname(os.path.abspath(ruta)), "arbol_decision")
    os.makedirs(carpeta, exist_ok=True)
    for e in NOMBRES_ESPECIE:
        _dibujar_arbol(construir_arbol(e), os.path.join(carpeta, f"arbol_{e}.png"),
                       f"Arbol de decision - {NOMBRES_ESPECIE[e]}", plt, textwrap)
    print(f"Diagrama general guardado en: {ruta}")
    print(f"Arboles por especie guardados en: {carpeta}")
    return True


# =============================================================================
# 7. IMPRESION DE LA BASE DE CONOCIMIENTO (REGLAS)
# =============================================================================

def construir_texto_base_conocimiento() -> str:
    """Construye (sin imprimir) el listado completo de reglas de produccion."""
    lineas = []
    lineas.append(f"BASE DE CONOCIMIENTO -- {len(REGLAS_SISTEMA)} reglas de nivel 1 (sistema) "
                  f"+ {len(REGLAS)} reglas de nivel 2 (enfermedad)")
    lineas.append("=" * 78)
    for especie in NOMBRES_ESPECIE:
        lineas.append(f"\n--- {NOMBRES_ESPECIE[especie].upper()} ---")
        lineas.append("  Nivel 1 -- hipotesis intermedias (sistema afectado):")
        for sistema, (nombre, _) in SISTEMAS.items():
            reglas_s = [rs for rs in REGLAS_SISTEMA
                        if rs.especie == especie and rs.sistema == sistema]
            if reglas_s:
                ids = f"{reglas_s[0].id}-{reglas_s[-1].id}"
                signos = " O ".join(rs.signo for rs in reglas_s)
                lineas.append(f"  [{ids}] SI especie = {especie} Y ({signos})")
                lineas.append(f"      ENTONCES sistema = {sistema} ({nombre})")
        lineas.append("  Nivel 2 -- hipotesis finales (enfermedad):")
        for regla in REGLAS:
            if regla.especie != especie:
                continue
            sintomas_txt = " Y ".join(sorted(regla.sintomas))
            lineas.append(f"  [{regla.id}] SI especie = {especie} Y sistema = {regla.sistema} "
                          f"Y {sintomas_txt}")
            lineas.append(f"      ENTONCES enfermedad = '{regla.enfermedad}' "
                          f"(urgencia: {regla.urgencia})")
    lineas.append("\n" + "=" * 78)
    return "\n".join(lineas)


def imprimir_base_conocimiento() -> None:
    print("\n" + construir_texto_base_conocimiento() + "\n")


# =============================================================================
# 8. INTERFAZ DE USUARIO (CONSOLA)
# =============================================================================

def preguntar_si_no(pregunta: str) -> bool:
    while True:
        resp = input(f"{pregunta} (s/n): ").strip().lower()
        if resp in ("s", "si", "sí", "y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
        print("  Por favor responde 's' (si) o 'n' (no).")


def elegir_especie() -> str:
    especies = sorted(set(r.especie for r in REGLAS))
    print("\n¿Qué tipo de animal vas a evaluar?")
    for i, e in enumerate(especies, start=1):
        print(f"  {i}. {NOMBRES_ESPECIE.get(e, e)}")
    while True:
        resp = input("Elige un numero: ").strip()
        if resp.isdigit() and 1 <= int(resp) <= len(especies):
            return especies[int(resp) - 1]
        print("  Opcion invalida, intenta de nuevo.")


def ejecutar_diagnostico() -> None:
    if USAR_MOTOR_BAYESIANO:
        ejecutar_diagnostico_bayesiano()
    else:
        ejecutar_diagnostico_jaccard()


def ejecutar_diagnostico_bayesiano() -> None:
    """Consola como Vista del MVC; el modelo es el paquete inferencia/."""
    from inferencia.capa_logica.servicio_diagnostico import crear_servicio
    from inferencia.capa_presentacion.controlador import ControladorDiagnostico
    from inferencia.capa_presentacion.vista_consola import VistaConsola
    especie = elegir_especie()
    servicio = crear_servicio()
    vista = VistaConsola()
    vista.controlador = ControladorDiagnostico(servicio, vista)
    print(f"\nResponde sobre los sintomas del animal ({NOMBRES_ESPECIE.get(especie, especie)}).")
    print(f"(s = si, n = no, ? = no se)  |  Conocimiento: {servicio.fuente}\n")
    vista.controlador.seleccionar_especie(especie)


def ejecutar_diagnostico_jaccard() -> None:
    especie = elegir_especie()
    memoria = MemoriaDeTrabajo(especie)

    sintomas = sintomas_por_especie(especie)
    print(f"\nResponde sobre los sintomas del animal ({NOMBRES_ESPECIE.get(especie, especie)}).")
    print("(Puedes escribir 's' para si, 'n' para no)\n")

    for sintoma in sintomas:
        texto = PREGUNTAS.get(sintoma, f"¿Presenta '{sintoma}'?")
        if preguntar_si_no(texto):
            memoria.asertar(sintoma)

    reglas, reglas_sistema = cargar_reglas()
    motor = MotorInferencia(reglas, reglas_sistema)
    resultados = motor.evaluar(memoria)

    print("\n" + "=" * 70)
    print("RESULTADO DEL DIAGNOSTICO")
    print("=" * 70)

    if not memoria.hechos:
        print("No se registro ningun sintoma. No es posible generar un diagnostico.")
        return

    print("Sistemas afectados (hipotesis intermedias): " +
          ", ".join(f"{SISTEMAS[s][0]} (por {', '.join(sorted(signos))})"
                    for s, signos in memoria.sistemas.items()))
    id_consulta = registrar_consulta(memoria, sintomas, resultados)
    if id_consulta:
        print(f"Consulta registrada en la base de datos con el folio #{id_consulta}.")
    print()

    UMBRAL = 0.4  # coincidencia minima (40%) para considerarse un diagnostico probable
    candidatos = [r for r in resultados if r[1] >= UMBRAL]

    if not candidatos:
        print("No se encontro una enfermedad que coincida claramente con los")
        print("sintomas indicados. Se recomienda una consulta veterinaria")
        print("presencial para una evaluacion completa.")
        return

    print(f"Se muestran los {min(5, len(candidatos))} diagnosticos mas probables:\n")
    for idx, (regla, porcentaje, coincidentes) in enumerate(candidatos[:5], start=1):
        print(f"{idx}. {regla.enfermedad}  --  coincidencia: {porcentaje * 100:.0f}%  "
              f"(urgencia: {regla.urgencia})")
        print(f"   Sintomas que coinciden: {', '.join(sorted(coincidentes))}")
        print(f"   Recomendacion: {regla.recomendacion}")
        print()

    print("AVISO: Este sistema es una herramienta de apoyo academico y NO")
    print("reemplaza el diagnostico de un medico veterinario profesional.")
    print("=" * 70 + "\n")


def cargar_reglas() -> Tuple[List[Regla], List[ReglaSistema]]:
    """Lee la base de conocimiento desde la base de datos; si no esta
    disponible, usa las reglas definidas en este archivo."""
    try:
        import base_datos
        bd = base_datos.conectar()
        try:
            reglas, reglas_sistema = base_datos.cargar_base_conocimiento(bd)
        finally:
            bd.cerrar()
        if reglas:
            return reglas, reglas_sistema
    except Exception as e:
        print(f"(No se pudo leer la BD: {e}. Se usan las reglas internas.)")
    return REGLAS, REGLAS_SISTEMA


def registrar_consulta(memoria: MemoriaDeTrabajo, sintomas: List[str], resultados) -> int:
    """Guarda la consulta en el sistema transaccional. Devuelve el folio o 0."""
    try:
        import base_datos
        bd = base_datos.conectar()
        try:
            return base_datos.guardar_consulta(bd, memoria, sintomas, resultados)
        finally:
            bd.cerrar()
    except Exception as e:
        print(f"(No se pudo registrar la consulta: {e})")
        return 0


def texto_desde_bd(funcion: str, **kwargs) -> str:
    """Ejecuta una consulta de texto de base_datos.py (granulos, historial)."""
    import base_datos
    bd = base_datos.conectar()
    try:
        return getattr(base_datos, funcion)(bd, **kwargs)
    finally:
        bd.cerrar()


def menu_principal() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 70)
    print(" SISTEMA EXPERTO VETERINARIO ".center(70, "="))
    print("=" * 70)
    print("Diagnostico de enfermedades en animales domesticos mediante reglas")
    print("de produccion.")

    while True:
        print("\nMENU PRINCIPAL")
        print("  1. Diagnosticar un animal")
        if MOSTRAR_OPCIONES_AVANZADAS:
            print("  2. Ver base de conocimiento (reglas)")
            print("  3. Ver arbol de decision")
            print("  4. Generar diagrama del arbol de decision (PNG)")
            print("  5. Granulos de conocimiento por hipotesis (BD)")
            print("  6. Historial de consultas (BD)")
        print("  0. Salir")
        opcion = input("Elige una opcion: ").strip()

        if opcion == "1":
            ejecutar_diagnostico()
        elif opcion == "0":
            print("Hasta luego.")
            sys.exit(0)
        elif not MOSTRAR_OPCIONES_AVANZADAS:
            print("Opcion invalida, intenta de nuevo.")
        elif opcion == "2":
            imprimir_base_conocimiento()
        elif opcion == "3":
            imprimir_arbol_decision()
        elif opcion == "4":
            generar_diagrama_png()
        elif opcion == "5":
            especie = elegir_especie()
            print("\n" + texto_desde_bd("texto_granulos", especie=especie) + "\n")
        elif opcion == "6":
            print("\n" + texto_desde_bd("texto_historial") + "\n")
        else:
            print("Opcion invalida, intenta de nuevo.")


if __name__ == "__main__":
    menu_principal()
