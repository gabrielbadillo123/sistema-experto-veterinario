"""Capa de datos: elige la fuente de conocimiento.

1. SQL Server (SistemaExpertoVet) si responde y ya tiene los pesos
   probabilísticos (bd/05_inferencia_probabilistica.sql).
2. Si no, la base de conocimiento interna (las consultas no se guardan).
"""
from inferencia.capa_datos.repositorio_memoria import RepositorioConocimientoMemoria


def crear_repositorios():
    """Devuelve (repo_conocimiento, repo_consultas o None, descripcion_fuente)."""
    try:
        import base_datos
        from inferencia.capa_datos.repositorio_sqlserver import (
            RepositorioConocimientoSQL, RepositorioConsultasSQL)
        bd = base_datos.conectar()
        repo = RepositorioConocimientoSQL(bd)
        if repo.parametro("num_hipotesis") is None:
            raise RuntimeError("faltan los pesos probabilisticos: ejecute bd/05_inferencia_probabilistica.sql")
        if not repo.hipotesis_de_especie("perro"):
            raise RuntimeError("la base de conocimiento esta vacia")
        return repo, RepositorioConsultasSQL(bd), f"SQL Server ({base_datos.SERVIDOR_POR_DEFECTO})"
    except Exception as e:
        print(f"(No se pudo usar la BD para la inferencia: {e}. Se usa la base de conocimiento interna.)")
        return RepositorioConocimientoMemoria(), None, "base de conocimiento interna"
