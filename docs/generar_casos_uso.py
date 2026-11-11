#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dibuja el diagrama de casos de uso de alto nivel (docs/casos_de_uso.png)."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch

CASOS = [
    ("CU-01", "Iniciar sesion"),
    ("CU-02", "Administrar usuarios y roles"),
    ("CU-03", "Respaldar / restaurar la BD"),
    ("CU-04", "Adquirir y capturar conocimiento"),
    ("CU-05", "Validar base de conocimiento"),
    ("CU-06", "Generar / visualizar arbol de decision"),
    ("CU-07", "Consultar granulos por hipotesis"),
    ("CU-08", "Registrar propietario y animal"),
    ("CU-09", "Realizar consulta diagnostica"),
    ("CU-10", "Inferir diagnostico (motor)"),
    ("CU-11", "Consultar historial de consultas"),
    ("CU-12", "Validar diagnostico"),
    ("CU-13", "Generar reportes"),
]

# actor -> (x, y, casos con los que se asocia)
ACTORES = {
    "Administrador": (0.6, 10.5, ["CU-01", "CU-02", "CU-03", "CU-13"]),
    "Ingeniero del\nconocimiento": (0.6, 5.5, ["CU-01", "CU-04", "CU-06", "CU-07", "CU-11", "CU-13"]),
    "Experto\n(Medico veterinario)": (11.4, 9.5, ["CU-01", "CU-04", "CU-05", "CU-07", "CU-08",
                                                 "CU-09", "CU-11", "CU-12", "CU-13"]),
    "Usuario final\n(propietario / productor)": (11.4, 3.0, ["CU-01", "CU-08", "CU-09", "CU-11"]),
}

INCLUDES = [("CU-09", "CU-10"), ("CU-09", "CU-08")]  # (caso base, incluido)
EXTENDS = [("CU-11", "CU-12")]  # (caso base, extension)


def actor(ax, x, y, nombre):
    ax.add_patch(plt.Circle((x, y + 0.55), 0.16, fill=False, lw=1.4))
    ax.plot([x, x], [y + 0.39, y - 0.1], color="black", lw=1.4)
    ax.plot([x - 0.3, x + 0.3], [y + 0.22, y + 0.22], color="black", lw=1.4)
    ax.plot([x, x - 0.25], [y - 0.1, y - 0.5], color="black", lw=1.4)
    ax.plot([x, x + 0.25], [y - 0.1, y - 0.5], color="black", lw=1.4)
    ax.text(x, y - 0.75, nombre, ha="center", va="top", fontsize=9, fontweight="bold")


def main(ruta=os.path.join(os.path.dirname(os.path.abspath(__file__)), "casos_de_uso.png")):
    fig, ax = plt.subplots(figsize=(13, 11.5))
    ax.set_xlim(-0.5, 12.5)
    ax.set_ylim(-0.6, 13.4)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((2.3, -0.2), 7.4, 13.2, boxstyle="round,pad=0.05",
                                fc="#f7fafa", ec="#1f6f78", lw=1.5))
    ax.text(6.0, 12.75, "Sistema Experto Veterinario", ha="center", fontsize=13,
            fontweight="bold", color="#1f6f78")

    pos = {}
    for i, (cu, nombre) in enumerate(CASOS):
        x, y = 6.0, 12.0 - i * 0.93
        pos[cu] = (x, y)
        ax.add_patch(Ellipse((x, y), 4.6, 0.72, fc="white", ec="#333333", lw=1.1, zorder=3))
        ax.text(x, y, f"{cu}  {nombre}", ha="center", va="center", fontsize=9, zorder=4)

    for nombre, (ax_x, ax_y, casos) in ACTORES.items():
        actor(ax, ax_x, ax_y, nombre)
        for cu in casos:
            cx, cy = pos[cu]
            borde = cx - 2.3 if ax_x < cx else cx + 2.3
            ax.plot([ax_x + (0.35 if ax_x < cx else -0.35), borde], [ax_y + 0.2, cy],
                    color="#7a8a92", lw=0.8, zorder=1)

    for relaciones, etiqueta in ((INCLUDES, "<<include>>"), (EXTENDS, "<<extend>>")):
        for base, otro in relaciones:
            # include: base -> incluido ; extend: extension -> base
            origen, destino = (base, otro) if etiqueta == "<<include>>" else (otro, base)
            (xo, yo), (xd, yd) = pos[origen], pos[destino]
            rad = 0.9 if yd < yo else -0.9
            ax.annotate("", xy=(xd - 2.2, yd), xytext=(xo - 2.2, yo),
                        arrowprops=dict(arrowstyle="-|>", ls="--", color="#b3261e", lw=1.1,
                                        connectionstyle=f"arc3,rad={rad}"), zorder=5)
            ax.text(xo - 2.95, (yo + yd) / 2, etiqueta, fontsize=7.5, color="#b3261e",
                    ha="right", va="center", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.1", fc="#f7fafa", ec="none"))

    ax.set_title("Diagrama de casos de uso de alto nivel", fontsize=14, loc="left")
    plt.tight_layout()
    plt.savefig(ruta, dpi=130)
    plt.close(fig)
    print(f"Diagrama guardado en: {ruta}")


if __name__ == "__main__":
    main()
