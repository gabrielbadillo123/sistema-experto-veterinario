"""Capa lógica: fachada del caso de uso CU-09 / CU-10 (realizar consulta e inferir)."""
from inferencia.capa_logica.motor_bayesiano import MotorInferenciaBayesiano


class ServicioDiagnostico:
    def __init__(self, repo_conocimiento, repo_consultas=None, fuente=""):
        self.repo_conocimiento = repo_conocimiento
        self.repo_consultas = repo_consultas
        self.fuente = fuente
        self.motor = MotorInferenciaBayesiano(repo_conocimiento)
        self._pregunta_actual = None

    def especies(self):
        return self.repo_conocimiento.especies()

    def iniciar(self, especie):
        self.motor.iniciar(especie)
        self._pregunta_actual = self.motor.siguiente_pregunta()
        return self._pregunta_actual

    def responder(self, respuesta):
        self.motor.registrar_respuesta(self._pregunta_actual, respuesta)
        self._pregunta_actual = self.motor.siguiente_pregunta()
        return self._pregunta_actual

    def progreso(self):
        return len(self.motor.memoria.hechos), self.motor.max_preguntas

    def lider_actual(self):
        return self.motor.top_hipotesis(explicar=False)[0]

    def hay_sintomas_confirmados(self):
        return bool(self.motor.memoria.confirmados())

    def finalizar(self, guardar=True):
        resultado = self.motor.resultado()
        if guardar and self.repo_consultas is not None:
            try:
                resultado.id_consulta = self.repo_consultas.guardar(resultado)
            except Exception as e:      # el diagnóstico no se pierde si falla el registro
                print(f"(No se pudo registrar la consulta: {e})")
        return resultado


def crear_servicio():
    """Ensambla las capas: datos -> lógica."""
    from inferencia.capa_datos.fabrica import crear_repositorios
    repo, repo_consultas, fuente = crear_repositorios()
    return ServicioDiagnostico(repo, repo_consultas, fuente)
