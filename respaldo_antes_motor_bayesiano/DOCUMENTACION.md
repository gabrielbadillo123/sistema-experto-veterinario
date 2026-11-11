# Sistema Experto Veterinario — Entregable de requerimientos corregidos

| Requerimiento | Dónde está |
|---|---|
| 1. Correcciones al árbol de decisión | §1, `docs/arbol_decision.png`, `docs/arbol_decision/arbol_<especie>.png` |
| 2. Correcciones y actualización de las reglas | §2, `sistema_experto_veterinario.py` |
| 3. BD de conocimiento + sistema transaccional, M-R exportado | §3, carpeta `bd/` (SQL Server, base `SistemaExpertoVet`) |
| 4. Carga del conocimiento del experto y consultas de gránulos por hipótesis | §4, `bd/02_carga_conocimiento.sql`, `bd/03_consultas_granulos.sql` |
| 5. Definición de roles | §5, `bd/04_roles.sql` |
| 6. Casos de uso de alto nivel | §6, `docs/casos_de_uso.png` |

**Interfaz para el usuario:** por indicación del profesor, la aplicación solo muestra **Diagnosticar un animal**. Las opciones de ver reglas, árbol, diagrama, gránulos e historial siguen programadas pero están ocultas. Se reactivan cambiando a `True` la constante `MOSTRAR_OPCIONES_AVANZADAS` al inicio de `sistema_experto_veterinario.py`.

---

## 1. Correcciones al árbol de decisión

**Problema de la versión anterior.** El árbol tenía un solo nivel: *Especie → 25 enfermedades*. No había nodos de decisión (preguntas). Tampoco se veía qué síntoma separa una enfermedad de otra, ni existían hipótesis intermedias. En realidad era una lista agrupada por especie.

**Árbol corregido.** Tiene cuatro niveles y en cada nodo interno se hace una pregunta de SÍ/NO:

```
Especie
 └── Sistema afectado (hipótesis intermedia)        ← se activa con un "signo guía"
      └── ¿síntoma discriminante?  SI / NO
           └── ¿síntoma discriminante?  SI / NO
                └── Enfermedad [Rxxx]  + síntomas a confirmar
```

- **Nivel 1 – Especie:** perro, gato, vaca, caballo, ave, cerdo, oveja/cabra y conejo.
- **Nivel 2 – Sistema afectado** (9 hipótesis intermedias): Digestivo y hepático, Respiratorio y cardiaco, Piel/pelo/plumas, Nervioso, Locomotor, Reproductivo y productivo, Urinario/endocrino/metabólico, Ojos y oídos, y Sistémico/infeccioso general. Cada síntoma pertenece a un solo sistema y funciona como su *signo guía*.
- **Niveles 3 en adelante – Preguntas discriminantes:** en cada nodo se elige el síntoma que divide a las enfermedades candidatas en dos grupos lo más parecidos posible, al estilo de ID3. Así el árbol queda balanceado y se necesitan pocas preguntas para llegar a una hoja.
- **Hoja – Enfermedad:** cada hoja corresponde exactamente a una regla de nivel 2. Además indica los síntomas que faltan para confirmarla.

**Verificación automática.** El árbol tiene 200 hojas y las 200 son coherentes con su regla: los síntomas respondidos con SÍ en el camino están en la regla y los respondidos con NO no están.

**Diagramas:**
- `docs/arbol_decision.png`: vista general *Especie → Sistema afectado*, con el número de enfermedades en cada rama.
- `docs/arbol_decision/arbol_perro.png`, `arbol_gato.png`, …: árbol completo de cada especie. Las hojas tienen el color de su urgencia.
- Se regeneran con `python -c "import sistema_experto_veterinario as s; s.generar_diagrama_png()"`.

## 2. Correcciones y actualización de las reglas

### 2.1 Anomalías detectadas en la base de conocimiento

Se compararon todas las reglas de una misma especie entre sí:

| Tipo de anomalía | Reglas | Problema |
|---|---|---|
| Reglas **idénticas** (mismas premisas, conclusión distinta) | R057 / R074 (vaca), R180 / R196 (conejo) | Conflicto: ambas se disparan al 100% y no se pueden distinguir |
| Reglas **subsumidas** (las premisas de una están contenidas en las de otra) | R011⊂R005, R028⊂R027, R090⊂R077, R094⊂R095, R149⊂R134, R145⊂R144, R168⊂R167, R195⊂R185 | La regla más general se dispara siempre que se dispara la específica |

### 2.2 Correcciones aplicadas (se agregó un síntoma discriminante)

| Regla | Enfermedad | Cambio | Síntoma nuevo / pregunta |
|---|---|---|---|
| R011 | Hepatitis infecciosa canina | + `opacidad_ojos` | "ojo azul" característico |
| R028 | Calicivirus felino | + `cojera` | síndrome de cojera del calicivirus |
| R057 | IBR bovina | + `enrojecimiento_hocico` | "nariz roja" (nuevo) |
| R074 | Complejo respiratorio bovino | + `estertores` | ruidos pulmonares (nuevo) |
| R090 | Enfermedad navicular | + `dolor_talones` | dolor en talones (nuevo) |
| R094 | Dermatofilosis (rain rot) | + `mechones_pelo_pegados` | lesión en pincel (nuevo) |
| R145 | Piojos porcinos | + `parasitos_visibles` | piojos visibles (nuevo) |
| R149 | Artritis porcina | + `dificultad_levantarse` | — |
| R168 | Piojos y garrapatas (oveja) | + `parasitos_visibles` | — |
| R180 | Estasis gastrointestinal (conejo) | + `bruxismo` | rechinido de dientes por dolor |
| R195 | Uñas rotas (conejo) | + `una_rota` | uña rota (nuevo) |
| R196 | Bola de pelo (conejo) | `ausencia_heces` → `heces_unidas_pelo` | heces en collar (nuevo) |

Después de las correcciones quedan **0 conflictos**. Para cada una de las 200 reglas, si se responden exactamente sus síntomas, esa regla sale en primer lugar con 100% de coincidencia y ninguna otra empata.

### 2.3 Reglas actualizadas según el árbol (encadenamiento en dos niveles)

```
Nivel 1 (292 reglas RS###):  SI especie = E  Y  presenta <signo guía>
                             ENTONCES sistema afectado = S
Nivel 2 (200 reglas R###):   SI especie = E  Y  sistema afectado = S  Y  <síntomas>
                             ENTONCES enfermedad = H  (urgencia, recomendación)
```

- La **especie** pasó a ser una premisa explícita. Antes era un filtro implícito.
- El motor (`MotorInferencia`) hace dos ciclos de encadenamiento hacia adelante. En el primero, las reglas RS deducen los sistemas afectados y los guardan en la memoria de trabajo. En el segundo, solo se evalúan las enfermedades de los sistemas que quedaron activos, y el grado de coincidencia se calcula con el índice de Jaccard.
- Las reglas de nivel 1 se generan a partir de las de nivel 2. Así, toda enfermedad tiene al menos un signo guía de su sistema; el programa lo comprueba al arrancar.

Ejemplo:
```
RS007: SI especie = perro Y presenta vomito ENTONCES sistema = Digestivo y hepático
R001 : SI especie = perro Y [sistema Digestivo y hepático] Y diarrea_sangre Y fiebre
       Y letargia Y perdida_apetito Y vomito ENTONCES Parvovirosis canina (urgencia Alta)
```

## 3. Base de datos de conocimiento y sistema transaccional

**SGBD: Microsoft SQL Server 2022 Express.** Servidor `GABO\SQLEXPRESS`, base de datos `SistemaExpertoVet`. La aplicación se conecta con autenticación de Windows mediante `pyodbc` y el *ODBC Driver 17 for SQL Server*. Al arrancar lee las reglas desde la BD y guarda cada consulta en ella. Si el servidor no responde, el diagnóstico sigue funcionando con las reglas internas, pero la consulta no se guarda.

Para usar otro servidor, crea `bd/config.ini`:
```ini
[sqlserver]
server = GABO\SQLEXPRESS
database = SistemaExpertoVet
; user = ...      (solo si se usa autenticacion SQL en lugar de Windows)
; password = ...
```

### 3.1 Tablas

**Base de conocimiento:**

| Tabla | Contenido |
|---|---|
| `especie` | 8 especies |
| `sistema` | 9 sistemas (dominio de las hipótesis intermedias) |
| `sintoma` | 134 síntomas, con su pregunta y el sistema del que son signo guía |
| `hipotesis` | 61 intermedias (especie × sistema) y 200 finales (enfermedades, con urgencia y recomendación) |
| `regla` | 492 reglas (nivel 1 y 2): conclusión, experto que la aportó, fecha y si está activa |
| `premisa` | 1,655 condiciones SI: tipo especie, síntoma o hipótesis |

**Sistema transaccional:**

| Tabla | Contenido |
|---|---|
| `rol`, `permiso`, `rol_permiso`, `usuario` | Seguridad y roles de la aplicación |
| `propietario`, `animal` | Paciente y su dueño |
| `consulta` | Cada sesión de diagnóstico: quién la hizo, cuándo y su estado |
| `consulta_sintoma` | Memoria de trabajo guardada (respuesta SÍ/NO a cada pregunta) |
| `diagnostico` | Hipótesis inferidas (intermedias y finales), la regla que se disparó, el % de coincidencia, la posición en el ranking y la validación del experto |
| `bitacora` | Registro de las acciones |

### 3.2 Modelo relacional (M-R)

- `bd/modelo_relacional.png`: diagrama generado a partir del catálogo de la BD (PK, FK y relaciones).
- **Exportación del M-R desde SQL Server Management Studio (SSMS):**
  1. Conectarse a `GABO\SQLEXPRESS` y expandir *Bases de datos → SistemaExpertoVet*.
  2. Clic derecho en *Diagramas de base de datos → Nuevo diagrama de base de datos*. Si pide instalar el soporte de diagramas, aceptar.
  3. Seleccionar todas las tablas → *Agregar*. SSMS dibuja las tablas con sus PK y relaciones.
  4. Guardar el diagrama. Para exportarlo como imagen: clic derecho en el lienzo → *Copiar diagrama al Portapapeles* y pegarlo en Word o Paint.

## 4. Carga del conocimiento del experto y consultas de gránulos

**Carga.** `python base_datos.py` hace lo siguiente:
1. Genera `bd/02_carga_conocimiento.sql` (INSERTs en T-SQL) a partir del conocimiento capturado del experto humano. Cada regla queda ligada al usuario Experto (`id_experto`).
2. Ejecuta los scripts `01` a `04` en `GABO\SQLEXPRESS` y vuelve a leer las reglas desde las tablas, para comprobar que lo guardado es igual al conocimiento original.
3. Dibuja el M-R.

**Gránulo de conocimiento** = una regla completa: sus premisas (SI) más la hipótesis que concluye (ENTONCES). Los gránulos se agrupan por hipótesis.

**Consultas** (`bd/03_consultas_granulos.sql`): crea la vista `v_granulos` y contiene estas consultas:

| Consulta | Qué responde |
|---|---|
| Q1 | Número de gránulos por hipótesis |
| Q2 | Gránulos de una hipótesis final (p. ej. *Parvovirosis canina*) |
| Q3 | Gránulos de una hipótesis intermedia (qué signos activan el sistema digestivo del perro) |
| Q4 | Todas las hipótesis finales de una especie con su gránulo |
| Q5 | Cadena de razonamiento completa: gránulo de nivel 1 más el de nivel 2 |
| Q6 | Índice inverso: en qué hipótesis participa un síntoma |
| Q7 | Hipótesis de urgencia Alta por especie |
| Q8 | Control de calidad: reglas con menos de 2 síntomas |
| Q9 | Diagnósticos emitidos con más frecuencia (transaccional) |

Las consultas se ejecutan en SSMS. La opción **Gránulos de conocimiento por hipótesis** de la aplicación está oculta (ver el inicio del documento). Ejemplo de salida:

```
H101 (final) Parvovirosis canina  [perro / DIG | urgencia Alta]
   R001: SI especie = perro Y [Afeccion del sistema Digestivo y hepatico] Y presenta diarrea_sangre
         Y presenta fiebre Y presenta letargia Y presenta perdida_apetito Y presenta vomito
         ENTONCES Parvovirosis canina
```

## 5. Roles

| Rol | Responsabilidad | Permisos de la aplicación | Rol de base de datos (SQL Server) |
|---|---|---|---|
| **Administrador** | Administra usuarios, roles, respaldos y configuración | Todos | `rol_administrador`: CONTROL sobre la base de datos |
| **Ingeniero del conocimiento** | Obtiene el conocimiento del experto, lo convierte en reglas y mantiene la BC y el árbol | BC_EDITAR, BC_CONSULTAR, CONSULTA_VER_TODAS, REPORTES | `rol_ingeniero_conocimiento`: CRUD en tablas de la BC y SELECT en las transaccionales |
| **Experto** (médico veterinario) | Aporta y valida el conocimiento y valida los diagnósticos del sistema | BC_CONSULTAR, BC_VALIDAR, CONSULTA_CREAR, CONSULTA_VER_TODAS, DIAGNOSTICO_VALIDAR, REPORTES | `rol_experto`: lectura de la BC, UPDATE(activa) en `regla`, CRUD de consultas y diagnósticos |
| **Usuario final** (propietario/productor) | Registra al animal, contesta las preguntas y ve el diagnóstico y las recomendaciones | CONSULTA_CREAR, CONSULTA_VER_PROPIAS | `rol_usuario_final`: lectura de la BC e INSERT de consultas |

Los roles se definen en dos niveles:
- **Aplicación:** tablas `rol`/`permiso`/`rol_permiso`, con un usuario de demostración por rol.
- **SGBD:** roles de base de datos de SQL Server (`CREATE ROLE`/`GRANT`) con privilegios mínimos (`bd/04_roles.sql`). Una cuenta se asigna a un rol con `ALTER ROLE rol_experto ADD MEMBER [GABO\usuario];`.

## 6. Casos de uso de alto nivel

Diagrama: `docs/casos_de_uso.png` (se puede regenerar con `python docs/generar_casos_uso.py`).

| ID | Caso de uso | Actores | Tipo | Descripción |
|---|---|---|---|---|
| CU-01 | Iniciar sesión | Todos | Primario | El usuario se identifica con su correo y contraseña. El sistema habilita las funciones de su rol. |
| CU-02 | Administrar usuarios y roles | Administrador | Secundario | Dar de alta, de baja o modificar usuarios y asignarles un rol. Las acciones quedan en la bitácora. |
| CU-03 | Respaldar / restaurar la BD | Administrador | Secundario | Generar y restaurar respaldos de la base de conocimiento y de la transaccional. |
| CU-04 | Adquirir y capturar conocimiento | Ingeniero del conocimiento, Experto | Primario | El ingeniero entrevista al experto y captura síntomas, hipótesis, reglas y premisas. El sistema rechaza reglas idénticas o subsumidas dentro de una especie. |
| CU-05 | Validar base de conocimiento | Experto | Primario | El experto revisa los gránulos capturados y activa o desactiva reglas. |
| CU-06 | Generar / visualizar árbol de decisión | Ingeniero del conocimiento | Secundario | El árbol de decisión se construye a partir de las reglas vigentes y se muestra en texto o en PNG. |
| CU-07 | Consultar gránulos por hipótesis | Ingeniero, Experto | Primario | Se elige una especie o hipótesis y se listan las reglas (premisas y conclusión) que llevan a ella. |
| CU-08 | Registrar propietario y animal | Usuario final, Experto | Primario | Se capturan los datos del dueño y del paciente (especie, sexo, edad y peso). |
| CU-09 | Realizar consulta diagnóstica | Usuario final, Experto | Primario | El usuario elige la especie y contesta las preguntas. Incluye CU-08 y CU-10. Al final se muestran los diagnósticos más probables con su urgencia y recomendación, y la consulta se guarda. |
| CU-10 | Inferir diagnóstico | (Motor de inferencia) | Primario, incluido | Hace dos ciclos de encadenamiento hacia adelante (sistema y después enfermedad) y ordena las hipótesis por coincidencia. |
| CU-11 | Consultar historial de consultas | Usuario final (las suyas), Experto, Ingeniero | Secundario | Muestra las consultas anteriores con su diagnóstico principal. |
| CU-12 | Validar diagnóstico | Experto | Primario, extiende CU-11 | Desde el historial, el experto confirma o descarta el diagnóstico del sistema. Sirve para retroalimentar la BC. |
| CU-13 | Generar reportes | Administrador, Experto, Ingeniero | Secundario | Estadísticas: diagnósticos más frecuentes, urgencias y uso del sistema. |

## 7. Cómo ejecutar

```bash
pip install pyodbc matplotlib               # conexión a SQL Server y diagramas
python base_datos.py                        # (re)instala la BD en GABO\SQLEXPRESS y genera el M-R
python sistema_experto_veterinario_gui.py   # interfaz gráfica
python sistema_experto_veterinario.py       # versión de consola
```

`python base_datos.py` **borra y vuelve a crear** la base `SistemaExpertoVet`, incluido el historial de consultas.

**Instalar a mano desde SSMS** (*Archivo → Abrir → Archivo…* → *Ejecutar*, en este orden):
1. `bd/01_esquema.sql`
2. `bd/02_carga_conocimiento.sql`
3. `bd/03_consultas_granulos.sql`
4. `bd/04_roles.sql`
