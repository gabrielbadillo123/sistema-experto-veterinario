-- =============================================================================
--  SISTEMA EXPERTO VETERINARIO -- ESQUEMA DE BASE DE DATOS (SQL Server 2022)
--  Servidor: GABO\SQLEXPRESS   Base de datos: SistemaExpertoVet
--  Parte A: Base de conocimiento (BC)
--  Parte B: Sistema transaccional (usuarios, roles, consultas, diagnosticos)
--
--  Ejecutar en orden (SSMS o "python base_datos.py"):
--    01_esquema.sql -> 02_carga_conocimiento.sql -> 03_consultas_granulos.sql
--    -> 04_roles.sql
-- =============================================================================

IF DB_ID(N'SistemaExpertoVet') IS NULL
    CREATE DATABASE SistemaExpertoVet;
GO
USE SistemaExpertoVet;
GO

-- Borrado en orden inverso de dependencias (permite reinstalar)
DROP VIEW  IF EXISTS v_granulos;
DROP TABLE IF EXISTS parametro_inferencia, bitacora, diagnostico, consulta_sintoma, consulta, animal, propietario,
                     premisa, regla, hipotesis, sintoma, sistema, especie,
                     usuario, rol_permiso, permiso, rol;
GO

-- -----------------------------------------------------------------------------
-- PARTE B (primero, porque la BC referencia al experto que registra cada regla)
-- -----------------------------------------------------------------------------

CREATE TABLE rol (
    id_rol        INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_rol PRIMARY KEY,
    nombre        NVARCHAR(40)  NOT NULL CONSTRAINT uq_rol_nombre UNIQUE,
    descripcion   NVARCHAR(255) NOT NULL
);

CREATE TABLE permiso (
    id_permiso    INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_permiso PRIMARY KEY,
    clave         NVARCHAR(40)  NOT NULL CONSTRAINT uq_permiso_clave UNIQUE,
    descripcion   NVARCHAR(255) NOT NULL
);

CREATE TABLE rol_permiso (
    id_rol        INT NOT NULL CONSTRAINT fk_rp_rol     REFERENCES rol (id_rol),
    id_permiso    INT NOT NULL CONSTRAINT fk_rp_permiso REFERENCES permiso (id_permiso),
    CONSTRAINT pk_rol_permiso PRIMARY KEY (id_rol, id_permiso)
);

CREATE TABLE usuario (
    id_usuario         INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_usuario PRIMARY KEY,
    id_rol             INT           NOT NULL CONSTRAINT fk_usuario_rol REFERENCES rol (id_rol),
    nombre             NVARCHAR(100) NOT NULL,
    correo             NVARCHAR(120) NOT NULL CONSTRAINT uq_usuario_correo UNIQUE,
    contrasena_hash    CHAR(64)      NOT NULL,      -- SHA-256 en hexadecimal
    cedula_profesional NVARCHAR(20)  NULL,          -- solo para el rol Experto
    activo             BIT           NOT NULL CONSTRAINT df_usuario_activo DEFAULT 1,
    fecha_alta         DATETIME2(0)  NOT NULL CONSTRAINT df_usuario_fecha DEFAULT SYSDATETIME()
);

-- -----------------------------------------------------------------------------
-- PARTE A: BASE DE CONOCIMIENTO
-- -----------------------------------------------------------------------------

CREATE TABLE especie (
    id_especie    VARCHAR(20)  NOT NULL CONSTRAINT pk_especie PRIMARY KEY,
    nombre        NVARCHAR(60) NOT NULL
);

-- Sistema afectado = dominio de las hipotesis intermedias
CREATE TABLE sistema (
    id_sistema    VARCHAR(5)   NOT NULL CONSTRAINT pk_sistema PRIMARY KEY,
    nombre        NVARCHAR(80) NOT NULL
);

-- Sintoma = hecho observable (pregunta al usuario); signo guia de un solo sistema
CREATE TABLE sintoma (
    id_sintoma    VARCHAR(40)   NOT NULL CONSTRAINT pk_sintoma PRIMARY KEY,
    pregunta      NVARCHAR(200) NOT NULL,
    id_sistema    VARCHAR(5)    NOT NULL CONSTRAINT fk_sintoma_sistema REFERENCES sistema (id_sistema)
);

-- Hipotesis = conclusion de una regla
--   intermedia: "sistema S afectado en la especie E"
--   final:      una enfermedad concreta de la especie E
CREATE TABLE hipotesis (
    id_hipotesis  INT           NOT NULL CONSTRAINT pk_hipotesis PRIMARY KEY,
    tipo          VARCHAR(10)   NOT NULL CONSTRAINT ck_hip_tipo CHECK (tipo IN ('intermedia', 'final')),
    nombre        NVARCHAR(120) NOT NULL,
    id_especie    VARCHAR(20)   NOT NULL CONSTRAINT fk_hip_especie REFERENCES especie (id_especie),
    id_sistema    VARCHAR(5)    NOT NULL CONSTRAINT fk_hip_sistema REFERENCES sistema (id_sistema),
    urgencia      VARCHAR(5)    NULL     CONSTRAINT ck_hip_urgencia CHECK (urgencia IN ('Baja', 'Media', 'Alta')),
    recomendacion NVARCHAR(500) NULL,
    CONSTRAINT uq_hipotesis UNIQUE (id_especie, tipo, nombre),
    CONSTRAINT ck_hip_final CHECK (tipo = 'intermedia' OR (urgencia IS NOT NULL AND recomendacion IS NOT NULL))
);

-- Regla de produccion. nivel 1: concluye hipotesis intermedia (RS###);
-- nivel 2: concluye hipotesis final (R###).
CREATE TABLE regla (
    id_regla       VARCHAR(10)  NOT NULL CONSTRAINT pk_regla PRIMARY KEY,
    nivel          TINYINT      NOT NULL CONSTRAINT ck_regla_nivel CHECK (nivel IN (1, 2)),
    id_hipotesis   INT          NOT NULL CONSTRAINT fk_regla_hipotesis REFERENCES hipotesis (id_hipotesis),
    id_experto     INT          NULL     CONSTRAINT fk_regla_experto REFERENCES usuario (id_usuario),
    fecha_registro DATETIME2(0) NOT NULL CONSTRAINT df_regla_fecha DEFAULT SYSDATETIME(),
    activa         BIT          NOT NULL CONSTRAINT df_regla_activa DEFAULT 1
);

-- Premisa (condicion SI) de una regla. Junto con la conclusion forma el
-- granulo de conocimiento. Tipos: especie / sintoma / hipotesis intermedia.
CREATE TABLE premisa (
    id_premisa     INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_premisa PRIMARY KEY,
    id_regla       VARCHAR(10) NOT NULL CONSTRAINT fk_premisa_regla REFERENCES regla (id_regla) ON DELETE CASCADE,
    orden          TINYINT     NOT NULL,
    tipo           VARCHAR(10) NOT NULL CONSTRAINT ck_premisa_tipo_valor CHECK (tipo IN ('especie', 'sintoma', 'hipotesis')),
    id_especie     VARCHAR(20) NULL CONSTRAINT fk_premisa_especie   REFERENCES especie (id_especie),
    id_sintoma     VARCHAR(40) NULL CONSTRAINT fk_premisa_sintoma   REFERENCES sintoma (id_sintoma),
    id_hipotesis   INT         NULL CONSTRAINT fk_premisa_hipotesis REFERENCES hipotesis (id_hipotesis),
    CONSTRAINT uq_premisa_orden UNIQUE (id_regla, orden),
    CONSTRAINT ck_premisa_tipo CHECK (
        (tipo = 'especie'   AND id_especie IS NOT NULL AND id_sintoma IS NULL AND id_hipotesis IS NULL) OR
        (tipo = 'sintoma'   AND id_sintoma IS NOT NULL AND id_especie IS NULL AND id_hipotesis IS NULL) OR
        (tipo = 'hipotesis' AND id_hipotesis IS NOT NULL AND id_especie IS NULL AND id_sintoma IS NULL))
);

-- -----------------------------------------------------------------------------
-- PARTE B: SISTEMA TRANSACCIONAL
-- -----------------------------------------------------------------------------

CREATE TABLE propietario (
    id_propietario INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_propietario PRIMARY KEY,
    id_usuario     INT           NULL CONSTRAINT fk_prop_usuario REFERENCES usuario (id_usuario),
    nombre         NVARCHAR(100) NOT NULL,
    telefono       VARCHAR(20)   NULL,
    correo         NVARCHAR(120) NULL,
    direccion      NVARCHAR(200) NULL
);

CREATE TABLE animal (
    id_animal      INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_animal PRIMARY KEY,
    id_propietario INT          NOT NULL CONSTRAINT fk_animal_prop    REFERENCES propietario (id_propietario),
    id_especie     VARCHAR(20)  NOT NULL CONSTRAINT fk_animal_especie REFERENCES especie (id_especie),
    nombre         NVARCHAR(60) NOT NULL,              -- nombre, arete o identificador
    sexo           CHAR(1)      NULL CONSTRAINT ck_animal_sexo CHECK (sexo IN ('M', 'H')),
    edad_meses     INT          NULL,
    peso_kg        DECIMAL(7,2) NULL
);

CREATE TABLE consulta (
    id_consulta    INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_consulta PRIMARY KEY,
    id_animal      INT           NOT NULL CONSTRAINT fk_consulta_animal  REFERENCES animal (id_animal),
    id_usuario     INT           NOT NULL CONSTRAINT fk_consulta_usuario REFERENCES usuario (id_usuario),
    fecha          DATETIME2(0)  NOT NULL CONSTRAINT df_consulta_fecha DEFAULT SYSDATETIME(),
    estado         VARCHAR(13)   NOT NULL CONSTRAINT df_consulta_estado DEFAULT 'abierta'
                                 CONSTRAINT ck_consulta_estado CHECK (estado IN ('abierta', 'diagnosticada', 'validada')),
    observaciones  NVARCHAR(MAX) NULL
);

-- Memoria de trabajo persistida: respuesta a cada pregunta de la consulta
CREATE TABLE consulta_sintoma (
    id_consulta    INT         NOT NULL CONSTRAINT fk_cs_consulta REFERENCES consulta (id_consulta) ON DELETE CASCADE,
    id_sintoma     VARCHAR(40) NOT NULL CONSTRAINT fk_cs_sintoma  REFERENCES sintoma (id_sintoma),
    presente       BIT         NOT NULL,
    CONSTRAINT pk_consulta_sintoma PRIMARY KEY (id_consulta, id_sintoma)
);

-- Hipotesis inferidas por el motor (intermedias y finales) en una consulta
CREATE TABLE diagnostico (
    id_diagnostico INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_diagnostico PRIMARY KEY,
    id_consulta    INT          NOT NULL CONSTRAINT fk_diag_consulta  REFERENCES consulta (id_consulta) ON DELETE CASCADE,
    id_hipotesis   INT          NOT NULL CONSTRAINT fk_diag_hipotesis REFERENCES hipotesis (id_hipotesis),
    id_regla       VARCHAR(10)  NOT NULL CONSTRAINT fk_diag_regla     REFERENCES regla (id_regla),
    coincidencia   DECIMAL(5,2) NULL,                  -- porcentaje (solo hipotesis finales)
    posicion       TINYINT      NULL,                  -- ranking 1..5 (solo hipotesis finales)
    validado_por   INT          NULL CONSTRAINT fk_diag_experto REFERENCES usuario (id_usuario),
    validacion     VARCHAR(11)  NULL CONSTRAINT ck_diag_validacion CHECK (validacion IN ('confirmado', 'descartado'))
);

CREATE TABLE bitacora (
    id_bitacora    INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_bitacora PRIMARY KEY,
    id_usuario     INT           NULL CONSTRAINT fk_bitacora_usuario REFERENCES usuario (id_usuario),
    fecha          DATETIME2(0)  NOT NULL CONSTRAINT df_bitacora_fecha DEFAULT SYSDATETIME(),
    accion         VARCHAR(40)   NOT NULL,
    detalle        NVARCHAR(255) NULL
);
GO
