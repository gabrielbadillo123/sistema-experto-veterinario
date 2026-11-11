-- =============================================================================
--  CONSULTAS DE GRANULOS DE CONOCIMIENTO POR HIPOTESIS (SQL Server 2022)
--
--  Granulo de conocimiento = una regla completa:
--      SI <premisa 1> Y <premisa 2> Y ... ENTONCES <hipotesis>
--  Las hipotesis pueden ser intermedias (sistema afectado) o finales
--  (enfermedad).
-- =============================================================================
USE SistemaExpertoVet;
GO

-- Vista: un renglon por granulo, con sus premisas en texto
CREATE OR ALTER VIEW v_granulos AS
SELECT h.id_hipotesis,
       h.tipo                AS tipo_hipotesis,
       h.nombre              AS hipotesis,
       h.id_especie,
       h.id_sistema,
       h.urgencia,
       r.id_regla,
       r.nivel,
       CONCAT(N'SI ', STRING_AGG(
           CASE p.tipo
               WHEN 'especie'   THEN CONCAT(N'especie = ', p.id_especie)
               WHEN 'sintoma'   THEN CONCAT(N'presenta ', p.id_sintoma)
               WHEN 'hipotesis' THEN CONCAT(N'[', hp.nombre, N']')
           END, N' Y ') WITHIN GROUP (ORDER BY p.orden),
           N' ENTONCES ', h.nombre) AS granulo,
       COUNT(*)              AS num_premisas
FROM hipotesis h
JOIN regla r           ON r.id_hipotesis = h.id_hipotesis AND r.activa = 1
JOIN premisa p         ON p.id_regla = r.id_regla
LEFT JOIN hipotesis hp ON hp.id_hipotesis = p.id_hipotesis
GROUP BY h.id_hipotesis, h.tipo, h.nombre, h.id_especie, h.id_sistema, h.urgencia,
         r.id_regla, r.nivel;
GO

-- Q1. Resumen: numero de granulos por hipotesis
SELECT id_hipotesis, tipo_hipotesis, hipotesis, id_especie, COUNT(*) AS granulos
FROM v_granulos
GROUP BY id_hipotesis, tipo_hipotesis, hipotesis, id_especie
ORDER BY id_hipotesis;

-- Q2. Granulos de UNA hipotesis final (enfermedad), por nombre
SELECT id_regla, granulo
FROM v_granulos
WHERE hipotesis = N'Parvovirosis canina';

-- Q3. Granulos de UNA hipotesis intermedia: que signos activan el sistema
--     digestivo en perros
SELECT id_regla, granulo
FROM v_granulos
WHERE tipo_hipotesis = 'intermedia' AND id_especie = 'perro' AND id_sistema = 'DIG';

-- Q4. Todas las hipotesis finales de una especie con su granulo
SELECT id_hipotesis, hipotesis, urgencia, granulo
FROM v_granulos
WHERE tipo_hipotesis = 'final' AND id_especie = 'gato'
ORDER BY id_sistema, hipotesis;

-- Q5. Cadena de razonamiento completa de una enfermedad: granulo de nivel 1
--     (sistema) + granulo de nivel 2 (enfermedad)
SELECT g1.id_regla AS regla_nivel_1, g1.granulo AS granulo_sistema,
       g2.id_regla AS regla_nivel_2, g2.granulo AS granulo_enfermedad
FROM v_granulos g2
JOIN premisa p     ON p.id_regla = g2.id_regla AND p.tipo = 'hipotesis'
JOIN v_granulos g1 ON g1.id_hipotesis = p.id_hipotesis
WHERE g2.hipotesis = N'Mastitis bovina';

-- Q6. Hipotesis en las que participa un sintoma (indice inverso)
SELECT s.id_sintoma, h.tipo, h.nombre AS hipotesis, h.id_especie, r.id_regla
FROM sintoma s
JOIN premisa p   ON p.id_sintoma = s.id_sintoma
JOIN regla r     ON r.id_regla = p.id_regla
JOIN hipotesis h ON h.id_hipotesis = r.id_hipotesis
WHERE s.id_sintoma = 'fiebre'
ORDER BY h.id_especie, h.nombre;

-- Q7. Hipotesis finales de urgencia Alta por especie
SELECT id_especie, COUNT(*) AS enfermedades_urgencia_alta
FROM hipotesis
WHERE tipo = 'final' AND urgencia = 'Alta'
GROUP BY id_especie;

-- Q8. Control de calidad: reglas de nivel 2 con menos de 2 sintomas
SELECT id_regla, hipotesis, num_premisas - 2 AS sintomas
FROM v_granulos
WHERE nivel = 2 AND num_premisas - 2 < 2;

-- Q9. (Transaccional) Diagnosticos mas frecuentes emitidos por el sistema
SELECT h.nombre, COUNT(*) AS veces_en_primer_lugar
FROM diagnostico d
JOIN hipotesis h ON h.id_hipotesis = d.id_hipotesis
WHERE d.posicion = 1
GROUP BY h.nombre
ORDER BY veces_en_primer_lugar DESC;
