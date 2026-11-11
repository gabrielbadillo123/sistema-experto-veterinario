-- =============================================================================
--  ROLES DEL SISTEMA EXPERTO -- nivel SGBD (SQL Server 2022)
--
--  Los roles se definen en dos niveles:
--    1. Aplicacion: tablas rol / permiso / rol_permiso / usuario (ver 02_carga).
--    2. SGBD: roles de base de datos con privilegios minimos (este archivo).
--  Para asignar un rol a una cuenta:
--    ALTER ROLE rol_experto ADD MEMBER [GABO\usuario_windows];
-- =============================================================================
USE SistemaExpertoVet;
GO

DROP ROLE IF EXISTS rol_administrador;
DROP ROLE IF EXISTS rol_ingeniero_conocimiento;
DROP ROLE IF EXISTS rol_experto;
DROP ROLE IF EXISTS rol_usuario_final;
GO
CREATE ROLE rol_administrador;
CREATE ROLE rol_ingeniero_conocimiento;
CREATE ROLE rol_experto;
CREATE ROLE rol_usuario_final;
GO

-- 1. Administrador: control total de la base de datos
GRANT CONTROL ON DATABASE::SistemaExpertoVet TO rol_administrador;

-- 2. Ingeniero del conocimiento: mantiene la base de conocimiento,
--    solo lectura sobre lo transaccional (para analisis)
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.especie   TO rol_ingeniero_conocimiento;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.sistema   TO rol_ingeniero_conocimiento;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.sintoma   TO rol_ingeniero_conocimiento;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.hipotesis TO rol_ingeniero_conocimiento;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.regla     TO rol_ingeniero_conocimiento;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.premisa   TO rol_ingeniero_conocimiento;
GRANT SELECT ON dbo.consulta         TO rol_ingeniero_conocimiento;
GRANT SELECT ON dbo.consulta_sintoma TO rol_ingeniero_conocimiento;
GRANT SELECT ON dbo.diagnostico      TO rol_ingeniero_conocimiento;
GRANT SELECT ON dbo.v_granulos       TO rol_ingeniero_conocimiento;

-- 3. Experto (medico veterinario): consulta y valida el conocimiento
--    (activar/desactivar reglas), realiza consultas y valida diagnosticos
GRANT SELECT ON dbo.especie   TO rol_experto;
GRANT SELECT ON dbo.sistema   TO rol_experto;
GRANT SELECT ON dbo.sintoma   TO rol_experto;
GRANT SELECT ON dbo.hipotesis TO rol_experto;
GRANT SELECT ON dbo.premisa   TO rol_experto;
GRANT SELECT ON dbo.regla     TO rol_experto;
GRANT UPDATE (activa) ON dbo.regla TO rol_experto;
GRANT SELECT ON dbo.v_granulos TO rol_experto;
GRANT SELECT, INSERT, UPDATE ON dbo.propietario      TO rol_experto;
GRANT SELECT, INSERT, UPDATE ON dbo.animal           TO rol_experto;
GRANT SELECT, INSERT, UPDATE ON dbo.consulta         TO rol_experto;
GRANT SELECT, INSERT         ON dbo.consulta_sintoma TO rol_experto;
GRANT SELECT, INSERT, UPDATE ON dbo.diagnostico      TO rol_experto;
GRANT INSERT ON dbo.bitacora TO rol_experto;

-- 4. Usuario final: lee el conocimiento que necesita el motor y registra
--    sus consultas (no modifica reglas ni valida diagnosticos)
GRANT SELECT ON dbo.especie   TO rol_usuario_final;
GRANT SELECT ON dbo.sistema   TO rol_usuario_final;
GRANT SELECT ON dbo.sintoma   TO rol_usuario_final;
GRANT SELECT ON dbo.hipotesis TO rol_usuario_final;
GRANT SELECT ON dbo.regla     TO rol_usuario_final;
GRANT SELECT ON dbo.premisa   TO rol_usuario_final;
GRANT SELECT, INSERT ON dbo.propietario      TO rol_usuario_final;
GRANT SELECT, INSERT ON dbo.animal           TO rol_usuario_final;
GRANT SELECT, INSERT ON dbo.consulta         TO rol_usuario_final;
GRANT SELECT, INSERT ON dbo.consulta_sintoma TO rol_usuario_final;
GRANT SELECT, INSERT ON dbo.diagnostico      TO rol_usuario_final;
GRANT INSERT ON dbo.bitacora TO rol_usuario_final;
GO

-- Verificacion: permisos por rol
SELECT pr.name AS rol, pe.permission_name AS permiso, OBJECT_NAME(pe.major_id) AS objeto
FROM sys.database_permissions pe
JOIN sys.database_principals pr ON pr.principal_id = pe.grantee_principal_id
WHERE pr.name LIKE 'rol[_]%'
ORDER BY pr.name, objeto, permiso;
