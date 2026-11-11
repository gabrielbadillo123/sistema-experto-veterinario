"""Capa de presentación (MVC) — Controlador.

Recibe los eventos de la Vista (la GUI de Tkinter o la consola), invoca al
Modelo (ServicioDiagnostico) y le indica a la Vista qué mostrar. No contiene
lógica de inferencia ni acceso a datos.

Una vista debe implementar:
    mostrar_pregunta(sintoma, numero, maximo, lider)
    mostrar_resultado(resultado, hay_sintomas)
"""


class ControladorDiagnostico:
    def __init__(self, servicio, vista):
        self.servicio = servicio
        self.vista = vista

    def seleccionar_especie(self, id_especie):
        self._siguiente(self.servicio.iniciar(id_especie))

    def responder(self, respuesta):
        """respuesta: 'si' | 'no' | 'nose'"""
        self._siguiente(self.servicio.responder(respuesta))

    def _siguiente(self, pregunta):
        if pregunta is None:
            hay = self.servicio.hay_sintomas_confirmados()
            self.vista.mostrar_resultado(self.servicio.finalizar(guardar=hay), hay)
        else:
            hechas, maximo = self.servicio.progreso()
            self.vista.mostrar_pregunta(pregunta, hechas + 1, maximo, self.servicio.lider_actual())
