# Architecture.md · LuxMed System 🏥

> **Versión de Arquitectura:** 1.3.0 (Septiembre 2026)  
> **Modelo de Despliegue:** On-Premise Blindado (Ecuador)

---

## 1. Resumen Ejecutivo (High-Level Overview)

### Objetivo del Sistema
LuxMed es un software de escritorio para auditoría médica, extracción pasiva y validación de cobertura de salud On-Premise. El sistema automatiza de extremo a extremo la verificación de aseguramiento de carteras de pacientes en tres portales regulatorios de salud en Ecuador.

El problema central que resuelve es la saturación y lentitud del flujo de atención clínica manual: los doctores pierden valioso tiempo de consulta navegando por portales web desvinculados, descargando actas dispersas y conciliando hojas de cálculo desactualizadas y con datos corruptos. LuxMed centraliza esta ingesta, higieniza la información de filiación, unifica los soportes clínicos en un único documento consolidado por paciente y emite un reporte visual de auditoría.

### Usuarios Principales
- **Médicos de Consulta / Auditores Médicos:** Personal que requiere verificar la cobertura activa, consultar el tipo de seguro y consolidar la historia médica antes o durante la consulta física.
- **Personal de Admisión / Recepción Clínica:** Operadores encargados de arrastrar el listado masivo diario de pacientes, validar cédulas de identidad desactualizadas y descargar los entregables limpios y corregidos.

---

## 2. Principios de Diseño y Objetivos (Goals & Constraints)

### Metas de la Arquitectura
- **Aislamiento Tecnológico Absoluto (Hexagonal Directa):** Separar las reglas de negocio médicas de los motores técnicos de automatización y de la interfaz gráfica. Los cambios en los formularios o selectores de los portales gubernamentales externos no deben impactar la lógica central del paciente.
- **Idempotencia y Determinismo Visual:** Garantizar que ante clics repetidos o interrupciones en los bucles de los portales web externos, la cola de datos local en memoria y en base de datos permanezca consistente y sin duplicaciones de procesos.
- **Seguridad Estricta y Cumplimiento de Datos de Salud:** Cumplir con los estándares de confidencialidad de la Ley Orgánica de Protección de Datos Personales (LOPDP) de Ecuador, garantizando que el historial de los pacientes no sea expuesto a servidores ajenos a la clínica.

### Limitaciones & Restricciones
- **Despliegue On-Premise Estricto:** La aplicación corre de forma aislada en máquinas físicas de las sucursales médicas. No existe una infraestructura en la nube centralizada ni APIs intermedias propias debido a restricciones de conectividad interna.
- **Datos de Origen Altamente Corruptos:** El Excel de entrada provee información con fechas inconsistentes o cédulas mal formateadas (longitudes mayores a 10 dígitos, errores sintácticos). El sistema debe operar bajo la premisa de *"Ingesta Selectiva e Higienización Forzada"*.
- **Navegación Web Compleja en los Portales:** Los portales gubernamentales exigen el mantenimiento de cookies de sesión, tokens de formulario dinámicos y la prevención de fallos de red tradicionales al descargar streams de PDFs.

---

## 3. Vistas de la Arquitectura (C4 Model)

### Diagrama de Contexto (Nivel 1)

```text
  ┌─────────────────┐             ┌─────────────────────────┐
  │                 │   Arrastra  │                         │
  │  Médico / Admin ├────────────►│       Sistema LuxMed    │
  │                 │   Excel     │  (Aplicación de Escritorio)
  └────────┬────────┘             └────────────┬────────────┘
           ▲                                   │
           │ Abre PDF Unificado                │ Llena Cédula / Consulta / Captura PDF
           │ y Excel Espejo                    ▼
  ┌────────┴────────┐             ┌─────────────────────────┐
  │                 │             │ Portales Web Externos   │
  │  Sistema de     │             │ • P1: Portal Coberturas │
  │  Archivos Local │             │ • P2: Portal Validación │
  │  (Windows OS)   │             │ • P3: Portal Destino    │
  └─────────────────┘             └─────────────────────────┘
```

### Diagrama de Contenedores (Nivel 2)

```text
                      [ INTERFAZ DE USUARIO (PyQt6) ]
        (Login View ➔ Dropzone Stitch ➔ Dashboard Processing View)
                                      │
                Invoca casos de uso   │ Emite estados / Logs en vivo via QThread
                vía Puertos           ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                           CORE APLICACIÓN                           │
  │                                                                     │
  │   [ Orchestrator Service ] ◄───────► [ Validator Service ]          │
  │   (Árbol de Decisión P1, P2, P3)     (Longitud Cédula / Edad Inm.) │
  └──────────────────────────────────┬──────────────────────────────────┘
                                      │
          Inyección de Dependencias   │ Implementa contratos (Puertos)
          en el arranque (main.py)    ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                         ADAPTADORES INFRAES                         │
  │                                                                     │
  │   [ Excel Handler ]     [ SQLite Adapter ]     [ Playwright Scraper ]
  │  (Pandas + openpyxl)      (luxmed.db)         (Intercepción de Red) 
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Stack Tecnológico (Tech Stack & Rationale)

- **Lenguaje:** `Python 3.11+`. Ofrece soporte nativo para manipulación masiva de datos y robustez en la integración de hilos concurrentes de escritorio.
- **Interfaz Gráfica (UI):** `PyQt6`. Elegido por su rendimiento nativo en sistemas operativos Windows, capacidad de manejo asíncrono con hilos secundarios nativos (`QThread`), acoplamiento exacto de los layouts de Stitch y estabilidad visual On-Premise.
- **Motor de Automatización y Extracción:** `Playwright`. Se descartó Selenium debido a que Playwright cuenta con capacidades avanzadas de intercepción y escucha directa de las respuestas de la red de Chromium, lo que permite capturar el flujo binario de los archivos PDF en memoria sin depender de descargas físicas del sistema operativo Windows.
- **Motor de Ingesta Selectiva:** `Pandas`. Permite abrir archivos masivos en milisegundos y aislar únicamente vectores específicos de datos (Columnas B, C, E, G, H, M).
- **Estilizado y Reportes de Auditoría de Excel:** `openpyxl`. Se seleccionó para interactuar de forma directa con los archivos estructurados `.xlsx` de origen, inyectando propiedades de celdas y formateo de color (`PatternFill`) sin destruir las propiedades nativas del libro original.
- **Base de Datos Local:** `SQLite`. Almacenamiento On-Premise relacional de configuración cero, empotrado en un solo archivo binario local (`luxmed.db`), garantizando transaccionalidad e invariantes.

---

## 5. Flujo de Datos y Comunicación (Data Flow)

### Flujo Secuencial del Paciente & Árbol de Decisiones Clínicas

1. **Carga e Ingesta Parcial:**  
   El usuario deposita el Excel en la Dropzone. El adaptador de Pandas lee únicamente: **B** (Nombres), **C** (Cédula), **E** (Fecha Nacimiento), **G** (Tipo Seguro), **H** (Código Clínica) y **M** (Nombre Establecimiento).

2. **Higienización en el Dominio:**  
   El Validator evalúa la cédula (Columna C): si no tiene exactamente 10 dígitos numéricos, el paciente es marcado inmediatamente como **INVÁLIDO** (`CEDULA_INVALIDA`), sin ningún algoritmo adicional de dígito verificador. La columna E transforma el string de fecha y calcula dinámicamente la edad actual; si el paciente es menor de edad y el sistema detecta que carece de cobertura previa, es clasificado automáticamente como **INVÁLIDO**. Los registros sanos ingresan en la base de datos SQLite en estado **PENDIENTE**.

3. **Auditoría de Red en P_1 (Portal de Coberturas):**  
   El orquestador arranca el `QThread` de Playwright. Rellena los inputs de Cédula y Fecha de consulta en el Portal de Coberturas. Al presionar el botón de consulta, Playwright no descarga el archivo; intercepta de forma asíncrona la respuesta del servidor web y captura los bytes del PDF de previsualización directamente en memoria.

4. **Evaluación de Cobertura Activa y Rutas de Desvío (Rama A / Rama B):**
   - **Si el Portal de Coberturas no reporta cobertura vigente en ninguna entidad:**  
     El paciente pasa a estado **INVÁLIDO** (`NO_ENCONTRADO`), se guarda el fallo en SQLite y se marca su fila para pintarse en rojo en el reporte de auditoría. El flujo para este registro concluye inmediatamente.
   - **Si el Portal de Coberturas reporta cobertura vigente en la familia IESS (cualquiera de sus variantes):**  
     El paciente se clasifica en **Rama A**. El bot consulta el Portal_2, el cual no genera ningún documento — solo devuelve si existe un titular distinto que le derive la cobertura al paciente (`seguro_derivado`). Si `seguro_derivado = True`, el bot vuelve a consultar el Portal_1, ahora con la cédula del titular, para capturar su documento de cobertura, y luego continúa al Portal_3 con la cédula del titular. Si `seguro_derivado = False`, no hay documento adicional y el bot navega directo al Portal_3 con la cédula del propio paciente.
   - **Si el Portal de Coberturas reporta cobertura vigente en la Entidad Previsional Especial:**  
     El paciente se clasifica en **Rama B**, se omite el Portal_2 y el bot navega directamente a extraer la información técnica del Portal_3 con la cédula del propio paciente.

   Las dos familias de cobertura son mutuamente excluyentes: ningún paciente tiene cobertura vigente de ambas al mismo tiempo, por lo que no existe un caso de doble afiliación simultánea a resolver.

5. **Consolidación y Cierre de Entregables:**  
   Al finalizar el árbol de decisiones del paciente, un adaptador basado en memoria unifica los flujos de bytes capturados de los portales en un único archivo PDF consolidado: Portal 1 (paciente) → Portal 1 (titular, re-consulta) → Portal 3 cuando `seguro_derivado = True`; o Portal 1 (paciente) → Portal 3 cuando `seguro_derivado = False` o en Rama B. El archivo se indexa bajo la nomenclatura plana `NOMBRE_CEDULA.pdf` dentro de la carpeta del mes correspondiente a la fecha de atención, evitando la saturación del sistema de archivos y la colisión entre corridas de meses distintos.

---

## 6. Infraestructura y Despliegue (Deployment & Infra)

### Entorno de Ejecución
La aplicación opera en un entorno local On-Premise dentro de los equipos de escritorio con sistemas operativos Windows de cada sucursal. Los binarios de Chromium requeridos por Playwright se descargan e instalan de forma aislada dentro de la subcarpeta local de la aplicación (`data/binarios_wsp`), eliminando la necesidad de instalaciones previas en los sistemas globales de los clientes.

### Estrategia de Git & Gestión de Ramas
El desarrollo de LuxMed se gestiona de forma estricta mediante el aislamiento de características por ramas bajo la metodología de desarrollo por contratos:
- **`domain`:** Contiene únicamente las entidades puras y las interfaces abstractas (Puertos). Es el núcleo inmutable del proyecto.
- **`application`:** Almacena los coordinadores lógicos, el validador estructural de cédulas y el árbol relacional de toma de decisiones de los seguros.
- **`infrastructure/playwright`:** Aloja de forma exclusiva los selectores, intercepciones de red y el comportamiento del bot de Playwright.
- **`interface`:** Rama asignada al diseño de las pantallas mutables de PyQt6 extraídas de los patrones de Stitch.

---

## 7. Seguridad y Cumplimiento (Security)

- **Autenticación Local (RBAC Básico):** Acceso protegido a la aplicación a través de la interfaz de Login nativa que valida credenciales locales almacenadas de forma cifrada en la base de datos local SQLite. Esta capa protege el acceso a la aplicación misma — es independiente de cualquier autenticación contra los portales externos, y existe como blindaje LOPDP para que solo un médico autorizado pueda operar el sistema.
- **Privacidad de Datos Médicos (LOPDP):** Ningún dato personal identificable (PII) o registro de salud de los pacientes viaja a servidores web externos de desarrollo. Toda la información de auditoría se procesa localmente en la memoria RAM de la máquina y se escribe en caliente en el almacenamiento local del consultorio.
- **Autenticación al Portal 3 (único portal que requiere sesión):** Es un flujo **manual asistido**, no automatizado: al arrancar un lote, el sistema abre el navegador en modo visible en la página de login del Portal 3 y pausa hasta que el médico introduce sus propias credenciales. El sistema no captura, almacena ni transmite esas credenciales. La sesión/cookie resultante se mantiene **únicamente en memoria (RAM)** durante toda la corrida del lote — nunca se persiste a disco. Si la aplicación se cierra o falla a mitad de la corrida, la sesión se pierde junto con el resto del estado en memoria y el médico debe re-autenticarse al reanudar (ver `08_pausa_reanudacion_lote.feature`); es el mismo comportamiento ya definido para una expiración de sesión a mitad de lote.
- **Portal 2 no requiere autenticación:** es un formulario público, protegido únicamente por el widget anti-bot ALTCHA (ver business-rules.md §5) — no exige login ni credenciales institucionales.

---

## 8. Registro de Decisiones de Arquitectura (ADR)

### ADR 001: Migración de Arquitectura por Capas (DDD) a Hexagonal Directa

- **Contexto:** En el desarrollo de Trinity, la organización basada en un enfoque DDD estricto generaba una excesiva dispersión de archivos y subcarpetas (`domain/services`, `infrastructure/repositories/sqlite`, etc.), dificultando el control de versiones en equipos de dos desarrolladores bajo cronogramas ajustados.
- **Decisión:** Para LuxMed se adopta una Arquitectura Hexagonal Directa pura. El sistema se divide en un núcleo de negocio (`domain` y `application`) expuesto exclusivamente por Puertos (Interfaces abstractas), y una carpeta plana de Adaptadores (`infrastructure/`) donde cada tecnología (SQLite, Pandas, Playwright, PyQt6) implementa su contrato de forma directa y paralela.
- **Consecuencias:** Reducción del 40% en la duplicación de archivos de mapeo, eliminación total de colisiones y conflictos de fusión (*merge conflicts*) en el control de versiones de GitHub y facilidad absoluta para reescribir selectores web o vistas gráficas sin afectar el core del negocio.

### ADR 002: Intercepción de Respuestas de Red sobre Descargas Físicas de Archivos

- **Contexto:** El bot requiere capturar las actas PDF emitidas por los tres portales de salud de forma masiva. Confiar en la descarga tradicional del navegador de Windows genera bloqueos intermitentes en las interfaces de usuario de escritorio y requiere lidiar de forma compleja con rutas variables de descargas locales de los operadores.
- **Decisión:** Forzar a Playwright a utilizar la intercepción de eventos de red y capturar los flujos binarios de los PDFs directamente en la memoria RAM en formato de variables de bytes.
- **Consecuencias:** Eliminación absoluta de errores causados por ventanas emergentes de descarga de Windows, reducción drástica del espacio en disco duro durante la fase de procesamiento activo y facilidad total para fusionar los reportes de los portales en caliente antes de escribir el archivo único indexado definitivo.

### ADR 003: Abstracción de Entidades Previsionales y Portales en la Documentación

- **Contexto:** LuxMed no es un proyecto formalmente aprobado por las instituciones gubernamentales cuyos portales consulta. Nombrar esas entidades específicas (o sus URLs) en la documentación de arquitectura y de negocio expone innecesariamente esa relación no oficial.
- **Decisión:** La documentación (`ARCHITECTURE.md`, `business-rules.md`, `docs/BDD/*.feature`) se refiere a las entidades previsionales únicamente como **IESS** (nombre genérico del régimen general, no considerado sensible) y **Entidad Previsional Especial** (agrupa el resto de regímenes especiales), y a los portales solo por su rol funcional (Portal de Coberturas / Portal de Validación Secundaria / Portal de Destino Técnico), sin URLs ni nombres de ministerios u organismos. El nombre real de cada entidad y portal puede seguir existiendo en el código (selectores, configuración), donde no constituye documentación pública del proyecto.
- **Consecuencias:** La documentación queda desacoplada de los nombres reales de terceros no vinculados formalmente al proyecto. Como contrapartida, cualquier persona que solo lea la documentación (sin el código) no puede saber a qué organismo específico corresponde cada portal — es una decisión consciente de este ADR, no un vacío de información.