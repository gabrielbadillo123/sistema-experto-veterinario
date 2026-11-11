#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 SISTEMA EXPERTO VETERINARIO -- INTERFAZ GRAFICA (Tkinter)
================================================================================

Esta interfaz grafica reutiliza TODA la logica del sistema experto (base de
conocimiento, memoria de trabajo y motor de inferencia) definida en el
archivo "sistema_experto_veterinario.py". Por eso ambos archivos deben estar
guardados en la misma carpeta.

Para ejecutarla:
    python3 sistema_experto_veterinario_gui.py

Tkinter viene incluido con Python en Windows y macOS. En Linux, si no abre,
instala el paquete del sistema (por ejemplo: sudo apt install python3-tk).
================================================================================
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Permite ejecutar el script desde cualquier carpeta de trabajo, siempre que
# el archivo sistema_experto_veterinario.py este junto a este archivo.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sistema_experto_veterinario as sev


# ---------------------------------------------------------------------------
# Paleta de colores y tipografias de la interfaz
# ---------------------------------------------------------------------------
COLOR_FONDO = "#eef2f3"          # fondo general de la ventana
COLOR_TARJETA = "#ffffff"        # fondo de las tarjetas/paneles
COLOR_BORDE = "#dde3e5"          # borde sutil de las tarjetas
COLOR_HOVER = "#f2f7f7"          # resaltado al pasar el mouse sobre una tarjeta

COLOR_PRIMARIO = "#1f6f78"       # color de marca (encabezados, acentos)
COLOR_PRIMARIO_OSCURO = "#154e54"
COLOR_PRIMARIO_CLARO = "#cdeaea"

COLOR_TEXTO = "#1f2933"          # texto principal
COLOR_TEXTO_SUAVE = "#66757f"    # texto secundario / descripciones

COLOR_SI = "#3f9142"
COLOR_NO = "#d1495b"
COLOR_NEUTRO = "#8a97a0"

# Estilo por nivel de urgencia: color de acento, fondo de insignia y texto.
URGENCIA_ESTILO = {
    "Alta":  {"acento": "#e5484d", "chip_bg": "#fde2e2", "chip_fg": "#b3261e"},
    "Media": {"acento": "#f2b705", "chip_bg": "#fff3cd", "chip_fg": "#8a6100"},
    "Baja":  {"acento": "#43aa8b", "chip_bg": "#e1f5e6", "chip_fg": "#1f7a3f"},
}

ICONOS_ESPECIE = {
    "perro": "🐶", "gato": "🐱", "vaca": "🐄", "caballo": "🐴",
    "ave": "🐔", "cerdo": "🐖", "oveja": "🐑", "conejo": "🐰",
}

FUENTE_TITULO = ("Segoe UI", 18, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 10)
FUENTE_NORMAL = ("Segoe UI", 12)
FUENTE_PEQUENA = ("Segoe UI", 10)
FUENTE_EMOJI = ("Segoe UI Emoji", 20)


# ---------------------------------------------------------------------------
# Utilidades de dibujo (rectangulos redondeados y ajuste de color)
# ---------------------------------------------------------------------------
def _puntos_rectangulo_redondeado(x1, y1, x2, y2, radio):
    radio = max(0, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + radio, y1,
        x2 - radio, y1,
        x2, y1,
        x2, y1 + radio,
        x2, y2 - radio,
        x2, y2,
        x2 - radio, y2,
        x1 + radio, y2,
        x1, y2,
        x1, y2 - radio,
        x1, y1 + radio,
        x1, y1,
    ]


def _ajustar_color(color_hex, factor):
    color_hex = color_hex.lstrip("#")
    if len(color_hex) != 6:
        return "#" + color_hex
    r, g, b = (int(color_hex[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, min(255, int(c * factor))) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


class BotonRedondeado(tk.Canvas):
    """Boton con esquinas redondeadas dibujado sobre un Canvas, con efecto
    de resaltado al pasar el mouse (algo que un tk.Button plano no ofrece)."""

    def __init__(self, parent, texto, comando=None, color=COLOR_PRIMARIO,
                 color_texto="white", ancho=220, alto=46, fuente=FUENTE_NORMAL,
                 radio=14, color_hover=None):
        super().__init__(parent, width=ancho, height=alto, bg=parent["bg"],
                          highlightthickness=0, bd=0, cursor="hand2")
        self.comando = comando
        self.color = color
        self.color_hover = color_hover or _ajustar_color(color, 0.85)
        self.color_texto = color_texto
        self.texto = texto
        self.fuente = fuente
        self.ancho = ancho
        self.alto = alto
        self.radio = radio
        self._dibujar(self.color)
        self.bind("<Enter>", lambda e: self._dibujar(self.color_hover))
        self.bind("<Leave>", lambda e: self._dibujar(self.color))
        self.bind("<Button-1>", self._al_hacer_clic)

    def _dibujar(self, color):
        self.delete("all")
        puntos = _puntos_rectangulo_redondeado(1, 1, self.ancho - 1, self.alto - 1, self.radio)
        self.create_polygon(puntos, smooth=True, fill=color, outline=color)
        self.create_text(self.ancho / 2, self.alto / 2, text=self.texto,
                          fill=self.color_texto, font=self.fuente)

    def _al_hacer_clic(self, event):
        if self.comando:
            self.comando()


class EnlaceTexto(tk.Label):
    """Etiqueta clicable con apariencia de enlace (subrayado al pasar el mouse)."""

    def __init__(self, parent, texto, comando, bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE,
                 fuente=FUENTE_PEQUENA):
        super().__init__(parent, text=texto, font=fuente, bg=bg, fg=fg, cursor="hand2")
        self._fuente_normal = fuente
        self._fuente_subrayada = fuente + ("underline",)
        self.bind("<Button-1>", lambda e: comando())
        self.bind("<Enter>", lambda e: self.configure(font=self._fuente_subrayada, fg=COLOR_PRIMARIO))
        self.bind("<Leave>", lambda e: self.configure(font=self._fuente_normal, fg=fg))


class TarjetaMenu(tk.Frame):
    """Fila de menu tipo tarjeta: icono + titulo + descripcion + flecha,
    con resaltado al pasar el mouse sobre cualquiera de sus partes."""

    def __init__(self, parent, icono, titulo, descripcion, comando, acento=COLOR_PRIMARIO):
        super().__init__(parent, bg=COLOR_TARJETA, highlightthickness=1,
                          highlightbackground=COLOR_BORDE, cursor="hand2")
        self.comando = comando

        self.icono_lbl = tk.Label(self, text=icono, font=FUENTE_EMOJI, bg=acento,
                                   fg="white", width=3)
        self.icono_lbl.pack(side="left", fill="y")

        self.texto_frame = tk.Frame(self, bg=COLOR_TARJETA)
        self.texto_frame.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        self.titulo_lbl = tk.Label(self.texto_frame, text=titulo, font=("Segoe UI", 13, "bold"),
                                    bg=COLOR_TARJETA, fg=COLOR_TEXTO, anchor="w")
        self.titulo_lbl.pack(fill="x")

        self.desc_lbl = tk.Label(self.texto_frame, text=descripcion, font=FUENTE_PEQUENA,
                                  bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE, anchor="w",
                                  wraplength=420, justify="left")
        self.desc_lbl.pack(fill="x")

        self.chevron_lbl = tk.Label(self, text="›", font=("Segoe UI", 20), bg=COLOR_TARJETA,
                                     fg=COLOR_TEXTO_SUAVE)
        self.chevron_lbl.pack(side="right", padx=16)

        for widget in (self, self.texto_frame, self.titulo_lbl, self.desc_lbl, self.chevron_lbl):
            widget.bind("<Button-1>", lambda e: self.comando())
            widget.bind("<Enter>", self._al_entrar)
            widget.bind("<Leave>", self._al_salir)

    def _al_entrar(self, event):
        self._pintar(COLOR_HOVER)

    def _al_salir(self, event):
        self._pintar(COLOR_TARJETA)

    def _pintar(self, color):
        self.configure(bg=color)
        self.texto_frame.configure(bg=color)
        self.titulo_lbl.configure(bg=color)
        self.desc_lbl.configure(bg=color)
        self.chevron_lbl.configure(bg=color)


class TarjetaEspecie(tk.Frame):
    """Tarjeta cuadrada para elegir la especie del animal."""

    def __init__(self, parent, icono, titulo, comando):
        super().__init__(parent, bg=COLOR_TARJETA, highlightthickness=1,
                          highlightbackground=COLOR_BORDE, cursor="hand2", width=190, height=110)
        self.pack_propagate(False)
        self.comando = comando

        self.icono_lbl = tk.Label(self, text=icono, font=("Segoe UI Emoji", 30), bg=COLOR_TARJETA)
        self.icono_lbl.pack(pady=(16, 4))
        self.titulo_lbl = tk.Label(self, text=titulo, font=("Segoe UI", 11, "bold"),
                                    bg=COLOR_TARJETA, fg=COLOR_TEXTO, wraplength=170, justify="center")
        self.titulo_lbl.pack()

        for widget in (self, self.icono_lbl, self.titulo_lbl):
            widget.bind("<Button-1>", lambda e: self.comando())
            widget.bind("<Enter>", self._al_entrar)
            widget.bind("<Leave>", self._al_salir)

    def _al_entrar(self, event):
        self.configure(highlightbackground=COLOR_PRIMARIO, highlightthickness=2, bg=COLOR_HOVER)
        self.icono_lbl.configure(bg=COLOR_HOVER)
        self.titulo_lbl.configure(bg=COLOR_HOVER)

    def _al_salir(self, event):
        self.configure(highlightbackground=COLOR_BORDE, highlightthickness=1, bg=COLOR_TARJETA)
        self.icono_lbl.configure(bg=COLOR_TARJETA)
        self.titulo_lbl.configure(bg=COLOR_TARJETA)


class MarcoDesplazable(tk.Frame):
    """Frame con scroll vertical (Tkinter no trae uno por defecto), usado
    para la lista de tarjetas de resultados del diagnostico."""

    def __init__(self, parent, bg=COLOR_FONDO, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                        style="Suave.Vertical.TScrollbar")
        self.interior = tk.Frame(self.canvas, bg=bg)
        self._id_interior = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.interior.bind("<Configure>", self._al_cambiar_interior)
        self.canvas.bind("<Configure>", self._al_cambiar_canvas)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._con_rueda))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _al_cambiar_interior(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _al_cambiar_canvas(self, event):
        self.canvas.itemconfig(self._id_interior, width=event.width)

    def _con_rueda(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class SistemaExpertoGUI(tk.Tk):
    """Ventana principal de la interfaz grafica del sistema experto."""

    def __init__(self):
        super().__init__()
        self.title("Sistema Experto Veterinario")
        self.geometry("900x640")
        self.minsize(760, 560)
        self.configure(bg=COLOR_FONDO)

        self._configurar_estilos_ttk()

        # --- estado del diagnostico en curso (equivalente a la memoria de
        #     trabajo mientras el usuario responde preguntas en pantalla) ---
        self.especie = None
        self.memoria = None
        self.sintomas_pendientes = []
        self.indice_pregunta = 0
        self.servicio_bayes = None      # modelo (capa logica) del motor bayesiano
        self.controlador = None         # controlador MVC del diagnostico

        # Base de conocimiento leida desde la base de datos (o, si no hay BD,
        # desde las reglas internas del modulo).
        self.reglas, self.reglas_sistema = sev.cargar_reglas()

        self.contenedor = tk.Frame(self, bg=COLOR_FONDO)
        self.contenedor.pack(fill="both", expand=True)

        self.mostrar_menu_principal()

    def _configurar_estilos_ttk(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Progreso.Horizontal.TProgressbar", troughcolor=COLOR_BORDE,
                         background=COLOR_PRIMARIO, bordercolor=COLOR_FONDO,
                         lightcolor=COLOR_PRIMARIO, darkcolor=COLOR_PRIMARIO, thickness=14)
        estilo.configure("Suave.Vertical.TScrollbar", background=COLOR_BORDE,
                         troughcolor=COLOR_FONDO, bordercolor=COLOR_FONDO,
                         arrowcolor=COLOR_TEXTO_SUAVE, gripcount=0)

    # -------------------------------------------------------------------
    # Utilidades de layout
    # -------------------------------------------------------------------
    def limpiar_contenedor(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def encabezado(self, texto, subtitulo=None, icono=None):
        header = tk.Frame(self.contenedor, bg=COLOR_PRIMARIO)
        header.pack(fill="x")
        interior = tk.Frame(header, bg=COLOR_PRIMARIO)
        interior.pack(pady=(20, 18))

        if icono:
            tk.Label(interior, text=icono, font=("Segoe UI Emoji", 28),
                     bg=COLOR_PRIMARIO, fg="white").pack()
        tk.Label(interior, text=texto, font=FUENTE_TITULO, bg=COLOR_PRIMARIO,
                 fg="white").pack(pady=(4, 0))
        if subtitulo:
            tk.Label(interior, text=subtitulo, font=FUENTE_SUBTITULO, bg=COLOR_PRIMARIO,
                     fg=COLOR_PRIMARIO_CLARO).pack(pady=(4, 0))
        return header

    def _con_manejo_errores(self, funcion):
        """
        Envuelve una funcion para que, si lanza un error, se muestre en una
        ventana emergente en vez de fallar en silencio (que es lo que pasa
        por defecto con los botones de Tkinter cuando el codigo interno
        lanza una excepcion: el boton parece "no hacer nada").
        """
        def envoltura(*args, **kwargs):
            try:
                return funcion(*args, **kwargs)
            except AttributeError as e:
                messagebox.showerror(
                    "Archivo desactualizado",
                    "Esta accion necesita una funcion que no existe en tu "
                    "archivo 'sistema_experto_veterinario.py'.\n\n"
                    "Es probable que tengas una version vieja de ese archivo. "
                    "Vuelve a descargarlo (la version mas reciente) y "
                    "reemplaza el que tienes en esta carpeta.\n\n"
                    f"Detalle tecnico: {e}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Ocurrio un error",
                    f"No se pudo completar la accion.\n\nDetalle tecnico:\n{e}"
                )
        return envoltura

    # -------------------------------------------------------------------
    # Pantalla: menu principal
    # -------------------------------------------------------------------
    def mostrar_menu_principal(self):
        self.limpiar_contenedor()
        self.encabezado("Sistema Experto Veterinario",
                         "Diagnostico asistido por reglas para animales domesticos", "🩺")

        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=48, pady=26)

        opciones = tk.Frame(cuerpo, bg=COLOR_FONDO)
        opciones.pack(fill="x")

        TarjetaMenu(opciones, "🩺", "Diagnosticar un animal",
                    "Responde una serie de preguntas sobre los sintomas del animal.",
                    self.iniciar_diagnostico).pack(fill="x", pady=5)

        # Ver sev.MOSTRAR_OPCIONES_AVANZADAS para reactivar las demas opciones.
        if not sev.MOSTRAR_OPCIONES_AVANZADAS:
            self._pie_menu(cuerpo)
            return

        chip = tk.Label(cuerpo, text=f"  Base de conocimiento: {len(self.reglas)} reglas de enfermedad + "
                              f"{len(self.reglas_sistema)} reglas de sistema  ",
                         font=FUENTE_PEQUENA, bg=COLOR_PRIMARIO_CLARO, fg=COLOR_PRIMARIO_OSCURO)
        chip.pack(before=opciones, pady=(0, 22))
        TarjetaMenu(opciones, "📖", "Ver base de conocimiento",
                    "Consulta todas las reglas de produccion del sistema experto.",
                    self.mostrar_base_conocimiento, acento=COLOR_PRIMARIO_OSCURO).pack(fill="x", pady=5)
        TarjetaMenu(opciones, "🌳", "Ver arbol de decision",
                    "Explora la estructura del arbol usado para inferir diagnosticos.",
                    self.mostrar_arbol_decision, acento="#4a7c59").pack(fill="x", pady=5)
        TarjetaMenu(opciones, "🖼️", "Generar diagrama del arbol (PNG)",
                    "Crea una imagen del arbol de decision en esta misma carpeta.",
                    self.generar_diagrama, acento="#4a6fa5").pack(fill="x", pady=5)
        TarjetaMenu(opciones, "🧩", "Granulos de conocimiento por hipotesis",
                    "Consulta en la base de datos las reglas que concluyen cada hipotesis.",
                    lambda: self.iniciar_diagnostico(self.mostrar_granulos),
                    acento="#7a5195").pack(fill="x", pady=5)
        TarjetaMenu(opciones, "🗂️", "Historial de consultas",
                    "Revisa las consultas y diagnosticos registrados en la base de datos.",
                    self.mostrar_historial, acento="#8a6100").pack(fill="x", pady=5)
        self._pie_menu(cuerpo)

    def _pie_menu(self, cuerpo):
        pie = tk.Frame(cuerpo, bg=COLOR_FONDO)
        pie.pack(side="bottom", fill="x", pady=(20, 0))
        tk.Label(pie, text="Herramienta de apoyo academico. No reemplaza a un veterinario.",
                 font=("Segoe UI", 9, "italic"), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE).pack()
        EnlaceTexto(pie, "Salir del programa", self.destroy).pack(pady=(8, 0))

    # -------------------------------------------------------------------
    # Pantalla: elegir especie
    # -------------------------------------------------------------------
    def iniciar_diagnostico(self, accion=None):
        """Pantalla de especies. `accion(especie)` se ejecuta al elegir una;
        por defecto inicia las preguntas del diagnostico."""
        accion = accion or self.comenzar_preguntas
        self.limpiar_contenedor()
        self.encabezado("Selecciona el tipo de animal",
                         "Elige la especie", "🐾")

        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=40, pady=25)

        rejilla = tk.Frame(cuerpo, bg=COLOR_FONDO)
        rejilla.pack()

        especies = sorted(set(r.especie for r in sev.REGLAS))
        columnas = 4
        for indice, especie in enumerate(especies):
            nombre = sev.NOMBRES_ESPECIE.get(especie, especie)
            icono = ICONOS_ESPECIE.get(especie, "🐾")
            fila, columna = divmod(indice, columnas)
            tarjeta = TarjetaEspecie(rejilla, icono, nombre,
                                     lambda e=especie: accion(e))
            tarjeta.grid(row=fila, column=columna, padx=8, pady=8)

        EnlaceTexto(cuerpo, "← Volver al menu", self.mostrar_menu_principal).pack(pady=(26, 0))

    def comenzar_preguntas(self, especie):
        if sev.USAR_MOTOR_BAYESIANO:
            # Motor bayesiano (paquete inferencia/, tres capas + MVC): esta
            # ventana es la Vista; el controlador decide la siguiente pregunta.
            self.especie = especie
            if self.servicio_bayes is None:
                from inferencia.capa_logica.servicio_diagnostico import crear_servicio
                self.servicio_bayes = crear_servicio()
            from inferencia.capa_presentacion.controlador import ControladorDiagnostico
            self.controlador = ControladorDiagnostico(self.servicio_bayes, self)
            self.controlador.seleccionar_especie(especie)
            return
        self.especie = especie
        self.memoria = sev.MemoriaDeTrabajo(especie)
        self.sintomas_pendientes = sev.sintomas_por_especie(especie)
        self.indice_pregunta = 0
        self.mostrar_siguiente_pregunta()

    # -------------------------------------------------------------------
    # Pantalla: preguntas de sintomas (una por una, con barra de progreso)
    # -------------------------------------------------------------------
    def mostrar_siguiente_pregunta(self):
        if self.indice_pregunta >= len(self.sintomas_pendientes):
            self.mostrar_resultado()
            return

        self.limpiar_contenedor()
        nombre_especie = sev.NOMBRES_ESPECIE.get(self.especie, self.especie)
        icono_especie = ICONOS_ESPECIE.get(self.especie, "🐾")
        self.encabezado(f"Diagnostico -- {nombre_especie}",
                         "Responde con sinceridad cada pregunta", icono_especie)

        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=40, pady=28)

        tarjeta = tk.Frame(cuerpo, bg=COLOR_TARJETA, highlightthickness=1,
                            highlightbackground=COLOR_BORDE)
        tarjeta.pack(fill="both", expand=True)

        interior = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        interior.pack(expand=True)

        total = len(self.sintomas_pendientes)
        actual = self.indice_pregunta + 1
        tk.Label(interior, text=f"PREGUNTA {actual} DE {total}", font=("Segoe UI", 9, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE).pack(pady=(34, 10))

        barra = ttk.Progressbar(interior, style="Progreso.Horizontal.TProgressbar",
                                 length=440, maximum=total, value=actual)
        barra.pack(pady=(0, 28))

        sintoma = self.sintomas_pendientes[self.indice_pregunta]
        pregunta = sev.PREGUNTAS.get(sintoma, f"¿Presenta '{sintoma}'?")
        tk.Label(interior, text=pregunta, font=("Segoe UI", 16, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO, wraplength=560, justify="center").pack(pady=(0, 30), padx=30)

        frame_botones = tk.Frame(interior, bg=COLOR_TARJETA)
        frame_botones.pack(pady=(0, 34))

        BotonRedondeado(frame_botones, "✓  Si", lambda: self.responder(sintoma, True),
                         color=COLOR_SI, ancho=160, alto=52,
                         fuente=("Segoe UI", 13, "bold")).pack(side="left", padx=12)
        BotonRedondeado(frame_botones, "✗  No", lambda: self.responder(sintoma, False),
                         color=COLOR_NO, ancho=160, alto=52,
                         fuente=("Segoe UI", 13, "bold")).pack(side="left", padx=12)

        EnlaceTexto(cuerpo, "Cancelar y volver al menu", self.mostrar_menu_principal).pack(pady=(18, 0))

    # -------------------------------------------------------------------
    # Vista del motor bayesiano (la invoca ControladorDiagnostico)
    # -------------------------------------------------------------------
    def mostrar_pregunta(self, sintoma, numero, maximo, lider):
        self.limpiar_contenedor()
        nombre_especie = sev.NOMBRES_ESPECIE.get(self.especie, self.especie)
        icono_especie = ICONOS_ESPECIE.get(self.especie, "🐾")
        self.encabezado(f"Diagnostico -- {nombre_especie}",
                         "El sistema elige la pregunta que mas informacion aporta", icono_especie)

        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=40, pady=28)
        tarjeta = tk.Frame(cuerpo, bg=COLOR_TARJETA, highlightthickness=1,
                            highlightbackground=COLOR_BORDE)
        tarjeta.pack(fill="both", expand=True)
        interior = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        interior.pack(expand=True)

        tk.Label(interior, text=f"PREGUNTA {numero} (MAXIMO {maximo})", font=("Segoe UI", 9, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE).pack(pady=(34, 10))
        barra = ttk.Progressbar(interior, style="Progreso.Horizontal.TProgressbar",
                                 length=440, maximum=1.0, value=lider.probabilidad)
        barra.pack(pady=(0, 4))
        tk.Label(interior, text=f"Hipotesis lider: {lider.hipotesis.nombre} ({lider.probabilidad * 100:.1f}%)",
                 font=FUENTE_PEQUENA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE).pack(pady=(0, 24))

        tk.Label(interior, text=sintoma.pregunta, font=("Segoe UI", 16, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_TEXTO, wraplength=560, justify="center").pack(pady=(0, 30), padx=30)

        frame_botones = tk.Frame(interior, bg=COLOR_TARJETA)
        frame_botones.pack(pady=(0, 34))
        for texto, valor, color in (("✓  Si", "si", COLOR_SI), ("✗  No", "no", COLOR_NO),
                                    ("?  No se", "nose", COLOR_NEUTRO)):
            BotonRedondeado(frame_botones, texto, lambda v=valor: self.controlador.responder(v),
                             color=color, ancho=150, alto=52,
                             fuente=("Segoe UI", 13, "bold")).pack(side="left", padx=10)

        EnlaceTexto(cuerpo, "Cancelar y volver al menu", self.mostrar_menu_principal).pack(pady=(18, 0))

    def _mostrar_resultado_bayesiano(self, resultado, hay_sintomas):
        self.limpiar_contenedor()
        self.encabezado("Resultado del diagnostico",
                         "Hipotesis mas probables segun el teorema de Bayes", "📋")
        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=28, pady=20)

        frame_botones = tk.Frame(cuerpo, bg=COLOR_FONDO)
        frame_botones.pack(side="bottom", pady=(14, 0))
        BotonRedondeado(frame_botones, "🔄  Nuevo diagnostico", self.iniciar_diagnostico,
                         color=COLOR_PRIMARIO, ancho=220, alto=44).pack(side="left", padx=8)
        BotonRedondeado(frame_botones, "🏠  Menu principal", self.mostrar_menu_principal,
                         color=COLOR_NEUTRO, ancho=190, alto=44).pack(side="left", padx=8)

        if not hay_sintomas:
            tarjeta = tk.Frame(cuerpo, bg=COLOR_TARJETA, highlightthickness=1,
                                highlightbackground=COLOR_BORDE)
            tarjeta.pack(fill="both", expand=True, pady=10)
            centro = tk.Frame(tarjeta, bg=COLOR_TARJETA)
            centro.pack(expand=True)
            tk.Label(centro, text="🔍", font=("Segoe UI Emoji", 40), bg=COLOR_TARJETA).pack(pady=(0, 12))
            tk.Label(centro, text="No se registro ningun sintoma.\nNo es posible generar un diagnostico.",
                     font=FUENTE_NORMAL, bg=COLOR_TARJETA, fg=COLOR_TEXTO, justify="center").pack()
            return

        scroll = MarcoDesplazable(cuerpo, bg=COLOR_FONDO)
        scroll.pack(fill="both", expand=True, pady=(0, 12))
        lista = scroll.interior

        sistemas_txt = ", ".join(f"{n} ({p * 100:.0f}%)" for n, p in list(resultado.sistemas.items())[:2])
        folio_txt = f"   |   Consulta registrada con folio #{resultado.id_consulta}" if resultado.id_consulta else ""
        tk.Label(lista, text=f"Sistemas afectados (hipotesis intermedias): {sistemas_txt}{folio_txt}",
                 font=FUENTE_PEQUENA, bg=COLOR_FONDO, fg=COLOR_PRIMARIO_OSCURO, anchor="w",
                 wraplength=760, justify="left").pack(fill="x", pady=(0, 4), padx=2)
        tk.Label(lista, text=f"{len(resultado.pasos)} preguntas  |  {resultado.motivo_parada}  |  "
                              f"Conocimiento: {self.servicio_bayes.fuente}",
                 font=FUENTE_PEQUENA, bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE, anchor="w",
                 wraplength=760, justify="left").pack(fill="x", pady=(0, 8), padx=2)
        tk.Label(lista, text="Las 5 hipotesis mas probables y su peso probabilistico",
                 font=("Segoe UI", 11, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE,
                 anchor="w").pack(fill="x", pady=(0, 10), padx=2)
        for r in resultado.hipotesis:
            self._crear_tarjeta_hipotesis(lista, r)

        tk.Label(cuerpo,
                 text="⚠ Herramienta de apoyo academico. No reemplaza el diagnostico "
                      "de un veterinario profesional.",
                 font=("Segoe UI", 9, "italic"), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE,
                 wraplength=740, justify="center").pack(side="bottom", pady=(4, 0))

    def _crear_tarjeta_hipotesis(self, parent, r):
        h = r.hipotesis
        estilo = URGENCIA_ESTILO.get(h.urgencia, URGENCIA_ESTILO["Baja"])
        tarjeta = tk.Frame(parent, bg=COLOR_TARJETA, highlightthickness=1,
                            highlightbackground=COLOR_BORDE)
        tarjeta.pack(fill="x", pady=6, padx=2)
        tk.Frame(tarjeta, bg=estilo["acento"], width=6).pack(side="left", fill="y")
        contenido = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        contenido.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        fila_top = tk.Frame(contenido, bg=COLOR_TARJETA)
        fila_top.pack(fill="x")
        tk.Label(fila_top, text=f"{r.posicion}. {h.nombre}", font=("Segoe UI", 13, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO, anchor="w", wraplength=420,
                 justify="left").pack(side="left")
        tk.Label(fila_top, text=f"{r.probabilidad * 100:.1f}%", font=("Segoe UI", 13, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(side="right")
        ttk.Progressbar(contenido, style="Progreso.Horizontal.TProgressbar", length=600,
                        maximum=1.0, value=r.probabilidad).pack(anchor="w", pady=(6, 6))
        tk.Label(contenido, text=f" Urgencia: {h.urgencia} ", font=("Segoe UI", 9, "bold"),
                 bg=estilo["chip_bg"], fg=estilo["chip_fg"]).pack(anchor="w", pady=(0, 6))
        if r.sintomas_a_favor:
            tk.Label(contenido, text=f"Sintomas a favor: {', '.join(r.sintomas_a_favor)}",
                     font=FUENTE_PEQUENA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE,
                     wraplength=600, justify="left", anchor="w").pack(fill="x")
        if r.sintomas_en_contra:
            tk.Label(contenido, text=f"Sintomas en contra: {', '.join(r.sintomas_en_contra)}",
                     font=FUENTE_PEQUENA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE,
                     wraplength=600, justify="left", anchor="w").pack(fill="x")
        if r.posicion == 1:
            tk.Label(contenido, text=f"Recomendacion: {h.recomendacion}",
                     font=("Segoe UI", 10), bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                     wraplength=600, justify="left", anchor="w").pack(fill="x", pady=(8, 0))

    def responder(self, sintoma, es_si):
        if es_si:
            self.memoria.asertar(sintoma)
        self.indice_pregunta += 1
        self.mostrar_siguiente_pregunta()

    # -------------------------------------------------------------------
    # Pantalla: resultado del diagnostico
    # -------------------------------------------------------------------
    def mostrar_resultado(self, resultado=None, hay_sintomas=True):
        if resultado is not None:       # resultado del motor bayesiano
            self._mostrar_resultado_bayesiano(resultado, hay_sintomas)
            return
        self.limpiar_contenedor()
        self.encabezado("Resultado del diagnostico",
                         "Estos son los hallazgos segun los sintomas indicados", "📋")

        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=28, pady=20)

        # Los botones de abajo se empaquetan primero, anclados a "bottom",
        # para que siempre queden visibles sin importar cuanto texto tenga
        # el area de resultados (que se empaqueta despues, ocupando lo que
        # sobre del espacio disponible).
        frame_botones = tk.Frame(cuerpo, bg=COLOR_FONDO)
        frame_botones.pack(side="bottom", pady=(14, 0))
        BotonRedondeado(frame_botones, "🔄  Nuevo diagnostico", self.iniciar_diagnostico,
                         color=COLOR_PRIMARIO, ancho=220, alto=44).pack(side="left", padx=8)
        BotonRedondeado(frame_botones, "🏠  Menu principal", self.mostrar_menu_principal,
                         color=COLOR_NEUTRO, ancho=190, alto=44).pack(side="left", padx=8)

        if not self.memoria.hechos:
            tarjeta = tk.Frame(cuerpo, bg=COLOR_TARJETA, highlightthickness=1,
                                highlightbackground=COLOR_BORDE)
            tarjeta.pack(fill="both", expand=True, pady=10)
            centro = tk.Frame(tarjeta, bg=COLOR_TARJETA)
            centro.pack(expand=True)
            tk.Label(centro, text="🔍", font=("Segoe UI Emoji", 40), bg=COLOR_TARJETA).pack(pady=(0, 12))
            tk.Label(centro, text="No se registro ningun sintoma.\nNo es posible generar un diagnostico.",
                     font=FUENTE_NORMAL, bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                     justify="center").pack()
            return

        motor = sev.MotorInferencia(self.reglas, self.reglas_sistema)
        resultados = motor.evaluar(self.memoria)
        folio = sev.registrar_consulta(self.memoria, self.sintomas_pendientes, resultados)
        umbral = 0.4
        candidatos = [r for r in resultados if r[1] >= umbral]

        scroll = MarcoDesplazable(cuerpo, bg=COLOR_FONDO)
        scroll.pack(fill="both", expand=True, pady=(0, 12))
        lista = scroll.interior

        sistemas_txt = ", ".join(sev.SISTEMAS[s][0] for s in self.memoria.sistemas) or "ninguno"
        folio_txt = f"   |   Consulta registrada con folio #{folio}" if folio else ""
        tk.Label(lista, text=f"Sistemas afectados (hipotesis intermedias): {sistemas_txt}{folio_txt}",
                 font=FUENTE_PEQUENA, bg=COLOR_FONDO, fg=COLOR_PRIMARIO_OSCURO, anchor="w",
                 wraplength=760, justify="left").pack(fill="x", pady=(0, 8), padx=2)

        if not candidatos:
            tarjeta = tk.Frame(lista, bg=COLOR_TARJETA, highlightthickness=1,
                                highlightbackground=COLOR_BORDE)
            tarjeta.pack(fill="x", pady=6, padx=2)
            tk.Label(tarjeta,
                     text="No se encontro una enfermedad que coincida claramente con "
                          "los sintomas indicados.\n\nSe recomienda una consulta "
                          "veterinaria presencial.",
                     font=FUENTE_NORMAL, bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                     wraplength=660, justify="left", padx=18, pady=18).pack(fill="x")
        else:
            tk.Label(lista, text=f"Se muestran los {min(5, len(candidatos))} diagnosticos mas probables",
                     font=("Segoe UI", 11, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE,
                     anchor="w").pack(fill="x", pady=(0, 10), padx=2)
            for regla, porcentaje, coincidentes in candidatos[:5]:
                self._crear_tarjeta_diagnostico(lista, regla, porcentaje, coincidentes)

        tk.Label(cuerpo,
                 text="⚠ Herramienta de apoyo academico. No reemplaza el diagnostico "
                      "de un veterinario profesional.",
                 font=("Segoe UI", 9, "italic"), bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE,
                 wraplength=740, justify="center").pack(side="bottom", pady=(4, 0))

    def _crear_tarjeta_diagnostico(self, parent, regla, porcentaje, coincidentes):
        estilo = URGENCIA_ESTILO.get(regla.urgencia, URGENCIA_ESTILO["Baja"])

        tarjeta = tk.Frame(parent, bg=COLOR_TARJETA, highlightthickness=1,
                            highlightbackground=COLOR_BORDE)
        tarjeta.pack(fill="x", pady=6, padx=2)

        barra = tk.Frame(tarjeta, bg=estilo["acento"], width=6)
        barra.pack(side="left", fill="y")

        contenido = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        contenido.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        fila_top = tk.Frame(contenido, bg=COLOR_TARJETA)
        fila_top.pack(fill="x")
        tk.Label(fila_top, text=regla.enfermedad, font=("Segoe UI", 13, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO, anchor="w", wraplength=420,
                 justify="left").pack(side="left")
        tk.Label(fila_top, text=f"{porcentaje * 100:.0f}%", font=("Segoe UI", 13, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(side="right")

        tk.Label(contenido, text=f" Urgencia: {regla.urgencia} ", font=("Segoe UI", 9, "bold"),
                 bg=estilo["chip_bg"], fg=estilo["chip_fg"]).pack(anchor="w", pady=(6, 8))

        tk.Label(contenido, text=f"Sintomas que coinciden: {', '.join(sorted(coincidentes))}",
                 font=FUENTE_PEQUENA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE,
                 wraplength=600, justify="left", anchor="w").pack(fill="x")
        tk.Label(contenido, text=f"Recomendacion: {regla.recomendacion}",
                 font=("Segoe UI", 10), bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                 wraplength=600, justify="left", anchor="w").pack(fill="x", pady=(8, 0))

    # -------------------------------------------------------------------
    # Pantallas de consulta (base de conocimiento / arbol de decision)
    # -------------------------------------------------------------------
    def mostrar_texto_en_ventana(self, titulo, texto, icono=None):
        self.limpiar_contenedor()
        self.encabezado(titulo, icono=icono)
        cuerpo = tk.Frame(self.contenedor, bg=COLOR_FONDO)
        cuerpo.pack(fill="both", expand=True, padx=24, pady=18)

        EnlaceTexto(cuerpo, "← Volver al menu", self.mostrar_menu_principal).pack(side="bottom", pady=(10, 0))

        tarjeta = tk.Frame(cuerpo, bg=COLOR_TARJETA, highlightthickness=1,
                            highlightbackground=COLOR_BORDE)
        tarjeta.pack(side="top", fill="both", expand=True)

        area = scrolledtext.ScrolledText(tarjeta, font=("Consolas", 10), wrap="word",
                                          bg=COLOR_TARJETA, fg=COLOR_TEXTO, relief="flat",
                                          padx=14, pady=12, borderwidth=0,
                                          insertbackground=COLOR_TEXTO)
        area.pack(side="top", fill="both", expand=True, padx=2, pady=2)
        area.insert("end", texto)
        area.configure(state="disabled")

    def mostrar_base_conocimiento(self):
        self.mostrar_texto_en_ventana("Base de conocimiento (reglas)",
                                       sev.construir_texto_base_conocimiento(), icono="📖")

    def mostrar_arbol_decision(self):
        self.mostrar_texto_en_ventana("Arbol de decision",
                                       sev.construir_texto_arbol_decision(), icono="🌳")

    def mostrar_granulos(self, especie):
        self.mostrar_texto_en_ventana("Granulos de conocimiento por hipotesis",
                                       sev.texto_desde_bd("texto_granulos", especie=especie),
                                       icono="🧩")

    def mostrar_historial(self):
        self.mostrar_texto_en_ventana("Historial de consultas",
                                       sev.texto_desde_bd("texto_historial"), icono="🗂️")

    def generar_diagrama(self):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "arbol_decision.png")
        ok = sev.generar_diagrama_png(ruta)
        if ok:
            messagebox.showinfo("Diagrama generado",
                                 f"Se genero la vista general:\n{ruta}\n\n"
                                 "y un arbol por especie en la carpeta 'arbol_decision'.")
        else:
            messagebox.showerror("Error",
                                  "No se pudo generar el diagrama. Verifica que "
                                  "matplotlib este instalado (pip install matplotlib).")


def main():
    app = SistemaExpertoGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
