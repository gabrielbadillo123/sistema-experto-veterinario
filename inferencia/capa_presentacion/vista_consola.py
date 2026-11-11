"""Capa de presentación (MVC) — Vista de consola del motor bayesiano."""

AVISO = ("AVISO: Este sistema es una herramienta de apoyo academico y NO\n"
         "reemplaza el diagnostico de un medico veterinario profesional.")


def formatear_resultado(resultado, hay_sintomas=True) -> str:
    lineas = ["", "=" * 70, "RESULTADO DEL DIAGNOSTICO (inferencia bayesiana)", "=" * 70]
    if not hay_sintomas:
        lineas += ["No se registro ningun sintoma. No es posible generar un diagnostico.", "=" * 70]
        return "\n".join(lineas)
    sistemas = list(resultado.sistemas.items())[:3]
    lineas.append("Sistemas afectados (hipotesis intermedias): " +
                  ", ".join(f"{n} ({p * 100:.1f}%)" for n, p in sistemas))
    if resultado.id_consulta:
        lineas.append(f"Consulta registrada en la base de datos con el folio #{resultado.id_consulta}.")
    lineas += ["", "Las 5 hipotesis mas probables y su peso probabilistico P(H | sintomas):", ""]
    for r in resultado.hipotesis:
        h = r.hipotesis
        lineas.append(f"{r.posicion}. {h.nombre}  --  probabilidad: {r.probabilidad * 100:.2f}%  "
                      f"(urgencia: {h.urgencia})")
        if r.sintomas_a_favor:
            lineas.append(f"   Sintomas a favor:   {', '.join(r.sintomas_a_favor)}")
        if r.sintomas_en_contra:
            lineas.append(f"   Sintomas en contra: {', '.join(r.sintomas_en_contra)}")
        lineas.append(f"   Recomendacion: {h.recomendacion}")
        lineas.append("")
    lineas += [f"Preguntas realizadas: {len(resultado.pasos)}. {resultado.motivo_parada}.", "", AVISO, "=" * 70]
    return "\n".join(lineas)


class VistaConsola:
    MAPA = {"s": "si", "si": "si", "sí": "si", "y": "si", "n": "no", "no": "no",
            "?": "nose", "ns": "nose", "nose": "nose", "no se": "nose", "no sé": "nose"}

    def __init__(self, entrada=input, salida=print):
        self.entrada, self.salida = entrada, salida
        self.controlador = None
        self.resultado = None

    def mostrar_pregunta(self, sintoma, numero, maximo, lider):
        while True:
            r = self.entrada(f"[{numero}/{maximo}] {sintoma.pregunta} (s/n/?=no se): ").strip().lower()
            if r in self.MAPA:
                break
            self.salida("  Por favor responde 's' (si), 'n' (no) o '?' (no se).")
        self.controlador.responder(self.MAPA[r])

    def mostrar_resultado(self, resultado, hay_sintomas=True):
        self.resultado = resultado
        self.salida(formatear_resultado(resultado, hay_sintomas))
