# AGENTS.md · Protocolo de Orquestación del Agente 🤖

> **Ecosistema de Desarrollo:** Antigravity CLI + Stitch MCP  
> **Metodología de Codificación:** Spec-Driven Development (SDD) + Principios SOLID  
> **Versión del Protocolo:** 1.0.0 (Septiembre 2026)

---

<<<<<<< HEAD
Fase de diseño con una primera capa de código: `domain/` ya tiene implementación (`models`, `branch_rules`, `success_criteria`, `estados`, `state_machine`, `reporte`) con tests en `tests/domain/`. Las demás capas (`application/`, `infrastructure/*`, `interface/`) siguen vacías. Antes de proponer o escribir código, lee en este orden:

1. `docs/BDD/*.feature` — especificación de comportamiento vigente (fuente de verdad del *qué*).
2. `docs/arquitectura.md` — decisiones de arquitectura interna (el *cómo* a nivel de capas).
3. `docs/gui.md` — diseño superficial de la GUI.
4. `docs/legal.md` — contexto legal (no comportamiento de software).
5. `CLAUDE.md` — invariantes de diseño, convención de ramas/commits y resumen de todo lo anterior.

No hay `package.json` ni `pyproject.toml` todavía. Sí hay tests: `python -m pytest` desde la raíz corre `tests/domain/` (requiere `pytest` instalado en el entorno; no hay `requirements.txt` todavía, instálalo manualmente si tu entorno no lo trae). La estructura de carpetas (`domain/`, `application/`, `infrastructure/`, `interface/`) ya está decidida — respétala en vez de improvisar una nueva.

## Ramas y commits

Una rama de git por capa, mismo nombre que la carpeta (`domain`, `application`, `infrastructure/excel`, `infrastructure/pdf`, `infrastructure/persistence`, `infrastructure/playwright`, `infrastructure/throttling`, `interface`). `main` es el tronco: ahí van `docs/BDD/*.feature`, el resto de `docs/`, `CLAUDE.md`, `AGENTS.md` y config transversal (`.gitignore`, futuro `pyproject.toml`, CI) — **nunca** directo en una rama de capa. El código de cada capa va solo en su propia rama. Si necesitás un cambio compartido mientras trabajás en una rama de capa, comitealo en `main` y traelo con `git merge main` (no rebase). Detalle completo y ejemplo real en `CLAUDE.md` → "Convención de ramas y commits". No pushees a `origin` sin que se te pida explícitamente.
=======
## 1. Reglas Inmutables de Comportamiento del Agente

### ❌ Prohibición Absoluta de Autonomía Incondicional
El agente **JAMÁS** creará archivos, modificará lógica o tomará decisiones estructurales por cuenta propia. Toda alteración en el sistema de archivos debe estar precedida por una especificación técnica o plano de contexto provisto por el usuario. El agente opera estrictamente como un ejecutor determinista guiado por contratos.

### ❌ Cero Comentarios Generados por IA
El código de producción generado debe ser limpio, autodocumentado y libre de cualquier comentario decorativo redundante o texto autogenerado típico de modelos de lenguaje (ej. `# Este método guarda los datos`). Si el código requiere claridad, se utilizará tipado estático estricto y nombres de variables descriptivos y explícitos.
>>>>>>> project-scaffolding

### 🔒 Conservación Estricta de la Arquitectura Hexagonal Directa
Cualquier archivo de código generado debe encajar quirúrgicamente dentro de la topología modular de carpetas. Los adaptadores técnicos (infraestructura) nunca se comunicarán entre sí. La comunicación cruzada se realizará obligatoriamente a través de la inyección de abstracciones definidas en el dominio.

---

## 2. Metodología de Desarrollo: Spec-Driven Development (SDD)

El desarrollo en LuxMed se rige por especificaciones estructuradas que actúan como límites (*guardrails*) matemáticos para el agente, eliminando la ambigüedad y previniendo alucinaciones lógicas.

```text
       ┌────────────────────────────────────────────────────────┐
       │             1. ESPECIFICACIÓN TÉCNICA (SDD)            │
       │ El desarrollador dicta el esquema, inputs y outputs.  │
       └───────────────────────────┬────────────────────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             2. VERIFICACIÓN DEL AGENTE MCP             │
       │ El agente lee el contexto en Stitch y valida reglas.   │
       └───────────────────────────┬────────────────────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            3. GENERACIÓN DE CÓDIGO (SOLID)             │
       │ El agente genera código determinista e inmune.         │
       └────────────────────────────────────────────────────────┘
```

### Protocolo de Interacción de Tres Pasos:

1. **Declaración del Plano:**  
   El desarrollador suministra la especificación exacta de la firma del método, la entidad de datos o la interfaz del puerto.

2. **Validación de Restricciones:**  
   El agente verifica que la especificación no viole ninguna regla previa del dominio médico o del árbol de decisión de seguros.

<<<<<<< HEAD
- Mantiene el formato narrativo usado en este proyecto para `docs/BDD/`: Preámbulo de invariantes, Terminología, Features/Scenarios en español, Apéndices que separan stack técnico y contexto legal del comportamiento verificable — el mismo formato que tenía `Requisitos.MD` y que heredaron los `.feature` actuales.
- **Úsala siempre que modifiques o agregues un escenario** en `docs/BDD/` — `06_consulta_portal3.feature` sigue con escenarios `@pendiente` (ver `docs/arquitectura.md`, sección de pendientes) hasta explorar el Portal 3 real; el resto de features ya fue confirmado por el propietario (2026-08-15). Escribir un escenario a mano sin la skill es la forma más fácil de romper la consistencia narrativa entre los 13 archivos.
- No sustituye la validación del propietario (el médico) — la skill asegura que el *formato* quede correcto, no que el *contenido* esté confirmado como comportamiento real.
=======
3. **Escritura Quirúrgica:**  
   El agente genera el código en la subcarpeta exacta de la rama de trabajo, sin modificar líneas adyacentes ni agregar dependencias no autorizadas.
>>>>>>> project-scaffolding

---

## 3. Guía de Aplicación de Principios SOLID para el Agente

Cada línea de código generada por el agente debe cumplir estrictamente con la taxonomía de diseño de software orientado a objetos:

### 1. Single Responsibility Principle (SRP)
- **Regla:** Una clase o componente debe encargarse de una sola tarea en el sistema.
- **Aplicación en LuxMed:** La clase encargada de leer las celdas B, C, E, G, H, M del Excel (`ExcelHandler`) no tiene permitido aplicar reglas de validación de cédulas ni calcular la edad. Su única responsabilidad es extraer los datos planos en bruto y entregárselos al core de la aplicación.

### 2. Open/Closed Principle (OCP)
- **Regla:** El código debe estar abierto para su extensión, pero cerrado para su modificación.
- **Aplicación en LuxMed:** Si en el futuro se añade un nuevo portal de validación médica (`Portal_4`), no se alterará la clase del orquestador central. El orquestador interactuará con una lista secuencial de servicios que implementen el contrato abstracto del scraper.

### 3. Liskov Substitution Principle (LSP)
- **Regla:** Las clases hijas deben poder sustituir a sus clases padres sin alterar el comportamiento esperado del sistema.
- **Aplicación en LuxMed:** Cualquier adaptador de persistencia alternativo que reemplace a SQLite en el futuro debe poder ser inyectado en el sistema utilizando la interfaz del puerto, sin requerir cambios en los métodos del core y sin lanzar excepciones inesperadas de tipo de datos.

### 4. Interface Segregation Principle (ISP)
- **Regla:** Es preferible diseñar muchas interfaces específicas y delgadas a una sola interfaz gigante de propósito general.
- **Aplicación en LuxMed:** No se creará un contrato unificado para la manipulación de archivos. El adaptador de combinación de PDFs implementará una interfaz dedicada exclusivamente a la consolidación binaria, aislada de las interfaces encargadas de la lectura de libros de Excel de Pandas.

### 5. Dependency Inversion Principle (DIP)
- **Regla:** El core lógico debe depender de abstracciones (Puertos), nunca de implementaciones concretas (Adaptadores).
- **Aplicación en LuxMed:** El servicio encargado de coordinar el flujo médico de los pacientes (`medical_flow.py`) no importará de forma directa a la clase de Playwright ni a la conexión de SQLite. Recibirá estas dependencias inyectadas a través de sus clases abstractas durante el arranque del sistema en el archivo `main.py`.

---

## 4. Flujo de Datos y Concurrencia Asíncrona (UI ◄─► Scraper)

El agente debe estructurar la comunicación entre el adaptador visual de PyQt6 y el adaptador de automatización de Playwright bajo un estricto patrón de desacoplamiento de hilos de ejecución para evitar congelamientos en las interfaces de las sucursales:

```text
 ┌────────────────────────────────┐       Dispara proceso       ┌────────────────────────────────┐
 │     ADAPTADOR INTERFAZ (UI)    ├────────────────────────────►│      ADAPTADOR SCRAPER (CORE)  │
 │   Corre en Hilo Principal (0)  │                             │   Corre en Hilo Secundario (1) │
 └────────────────────────────────┘                             └───────────────┬────────────────┘
                 ▲                                                              │
                 │ Reporta progreso / Actualiza tabla en vivo                  │ Emite señal
                 └──────────────────────────────────────────────────────────────┘
```

- **Aislamiento del Hilo Gráfico:**  
  La interfaz de PyQt6 opera de forma exclusiva en el hilo principal (Thread 0). Ninguna tarea de lectura de archivos con Pandas, escritura en SQLite o intercepción de red de Playwright puede ejecutarse en este espacio.

- **Encapsulación de Tareas Pesadas:**  
  El bucle de toma de decisiones de los seguros de los pacientes se envolverá obligatoriamente dentro de una clase de infraestructura que herede de `QThread`.

- **Comunicación Unidireccional por Señales:**  
  El hilo de procesamiento pasivo interactuará con la ventana gráfica enviando exclusivamente datos tipados e inmutables de actualización mediante señales nativas (`pyqtSignal(str)`). Esto garantiza el determinismo de la UI de Stitch mientras Playwright extrae los PDFs en memoria de forma transparente de fondo.