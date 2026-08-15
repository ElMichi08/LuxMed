# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado del repositorio

Este repositorio está en **fase de diseño, sin código todavía**. Contiene únicamente especificación de comportamiento y decisiones de arquitectura:

- `docs/BDD/*.feature` — especificación de comportamiento vigente y **única fuente de verdad del *qué***, un archivo por Feature. `Requisitos.MD` (v1.0, la fuente original) fue eliminado del repositorio: su contenido de comportamiento ya está cubierto y superado por `docs/BDD/` (sesión BDD 2026-08-12: consolidación de PDFs por paciente, exportación a Excel de resultados, resumen numérico del lote, y un modelo más preciso de los fallos del Portal 2); su Preámbulo de invariantes y Apéndice A de stack ya estaban duplicados más abajo en este archivo; su Apéndice B legal se rescató en `docs/legal.md`. Las features 05, 11, 12 y 13 de `docs/BDD/` fueron confirmadas explícitamente por el propietario el 2026-08-15 y ya no llevan `@borrador`. Solo `docs/BDD/06_consulta_portal3.feature` sigue con escenarios `@pendiente` — el comportamiento de fallo del Portal 3 es una extrapolación por analogía sin validar, marcada explícitamente como no confiable, y queda para una sesión donde se explore el portal real con la skill de Playwright.
- `docs/arquitectura.md` — decisiones de arquitectura interna (el *cómo* a nivel de capas), actualizado 2026-08-14 contra `docs/BDD/`.
- `docs/gui.md` — diseño superficial de la GUI, sin wireframes aún.
- `docs/legal.md` — Apéndice B legal rescatado de `Requisitos.MD` antes de su eliminación. Contexto, no comportamiento de software.

No hay `package.json`, `pyproject.toml`, ni código fuente. No hay comandos de build/lint/test que ejecutar todavía. Cuando se cree el código, la estructura de carpetas ya está decidida (ver más abajo) — respétala en vez de improvisar una nueva.

Los documentos de `docs/` se marcan explícitamente como no cerrados al 100%; se retoman al instalar la skill de Playwright en otra sesión. **Al leer estos documentos, prioriza siempre el contenido actual del archivo sobre lo resumido aquí** — este CLAUDE.md puede quedar desactualizado si los docs cambian.

## Qué es el sistema

Automatiza, para un médico, la validación de cobertura de seguros médicos consultando 3 portales web (scraping/RPA con Playwright) y produciendo PDFs de respaldo por paciente a partir de un listado en Excel.

## Invariantes de diseño (no se rediscuten)

Rescatados del Preámbulo del `Requisitos.MD` original (eliminado, ver arriba). Cualquier propuesta de código o diseño que los contradiga es inválida por defecto:

1. **On-premise, sin servidor central.** Todo corre en la máquina del médico. Un solo ejecutable, no microservicios.
2. **Retención cero fuera de la máquina.** Ningún dato de paciente sale del equipo salvo hacia los 3 portales y el almacenamiento local.
3. **Automatización asistida, no desatendida.** El médico autentica y supervisa; el sistema nunca vence controles de acceso automáticamente.
4. **Sin LLM.** Procesamiento 100% determinista, ninguna etapa usa IA.
5. **Sin manejo de credenciales.** Las credenciales del Portal 3 se escriben directo en el navegador; el sistema nunca las recibe ni almacena. Sesión solo en memoria, contexto de navegador no persistente.
6. **Excel como fuente de verdad**, procesado localmente con pandas, nunca subido a un servidor.
7. **Encadenamiento fijo de portales:** Portal 1 siempre → Portal 2 solo condicional (Rama A) → Portal 3 siempre (salvo corte por `NO_ENCONTRADO`).

El Apéndice B legal (personería jurídica, convenios de acceso, cumplimiento LOPDP, habilitación SERCOP) vive en `docs/legal.md` — es contexto legal, no comportamiento de software; no lo traduzcas a código ni a checks automatizados.

## Flujo de negocio (para orientarte antes de tocar cualquier capa)

- **Rama A** (menor de edad, o seguro "IESS"/"Afiliado Seguro Campesino"): pasa por los 3 portales, produce 3 PDFs, éxito = los 3 verificados.
- **Rama B** (cualquier otro caso): omite Portal 2, produce 2 PDFs (#1 y #3), éxito = los 2 verificados.
- Portal 1 responde "no encontrado" → estado `NO_ENCONTRADO`, corta el flujo para ese paciente sin tocar Portal 2/3.
- Timeouts en cualquier portal → reintentos acotados (3 adicionales); fallo persistente → estado de error específico (`ERROR_PORTAL_1`, y `ERROR_PORTAL_3` aún `@pendiente` de confirmar — ver `docs/BDD/06_consulta_portal3.feature`) y el lote continúa con el siguiente paciente.
- Portal 2 tiene 3 desenlaces distintos, no un solo fallo genérico (`docs/BDD/05_consulta_portal2.feature`, confirmado por el propietario 2026-08-15): cobertura vigente (PDF #2 normal), "SIN COBERTURA" sin PDF que generar (`SIN_COBERTURA_PORTAL_2` — resultado de negocio válido, no un error técnico), y dos ciclos de fallo técnico independientes que agotan reintentos automáticos y requieren decisión del médico: ALTCHA sin resolver (`ERROR_PORTAL_2`) y PDF del titular ilegible (`PDF_CORRUPTO_PORTAL_2`). Ninguno de los dos es autodecidible por el sistema.
- El lote es pausable/reanudable con checkpoint por paciente (nunca a mitad de una consulta), y los PDFs ya descargados e íntegros no se vuelven a descargar al reanudar (idempotencia).
- Throttling con jitter entre consultas, sin ráfagas concurrentes contra un mismo portal — es una regla de comportamiento del sistema, no solo cortesía.

## Arquitectura interna: hexagonal (puertos y adaptadores)

Decisión registrada en `docs/arquitectura.md`: **un único ejecutable** (no hay debate monolito-vs-servicios), pero con **capas internas desacopladas**. La razón no es "el flujo de negocio va a cambiar" (no va a cambiar) sino que **los adapters de scraping sí van a cambiar** porque son páginas de terceros que pueden alterar HTML/JS/captcha sin aviso. Mezclar lógica de negocio con código Playwright forzaría re-testear reglas que no cambiaron cada vez que un portal se actualiza.

```
domain/            Reglas de negocio puras. Sin Playwright, sin pandas, sin GUI.
application/         Casos de uso / orquestación. Depende de domain + ports, nunca de infra concreta.
  ports/                  Interfaces (Protocol/ABC) — contrato que infra debe cumplir.
infrastructure/       Adapters concretos (Playwright por portal, verificación PDF, Excel, SQLite, throttling).
interface/
  gui/                  Consumidor de application/, sin lógica de negocio propia.
  cli/                    Opcional, delgado, de soporte/debug.
main.py                 Composition root: inyecta adapters concretos en el orquestador.
```

**Regla de dependencia:** las flechas de import solo apuntan hacia adentro. `domain` no conoce `infrastructure` ni `interface`. `application` conoce `domain` y `ports`, nunca una clase concreta de Playwright o de la GUI. Antes de añadir un import, verifica que no rompe esta dirección.

Decisiones ya tomadas que vale la pena no revisitar sin razón nueva (detalle y justificación completos en `docs/arquitectura.md`):

- **Un gateway por portal** (`Portal1Gateway`, `Portal2Gateway`, `Portal3Gateway`), no una interfaz `PortalClient` genérica — cada portal tiene semántica distinta (interceptación de respuesta / sincronización ALTCHA / sesión persistente en memoria).
- **Máquina de estados explícita** en `domain/state_machine.py`, con `EstadoPaciente` y `EstadoLote` como enums separados (`PAUSADO` es de lote, nunca de un paciente individual) — no dispersa en el orquestador.
- **Comunicación orquestador → GUI vía eventos de dominio** (`PatientStateChanged`, `BatchPaused`, `SessionExpired`, `BatchCompleted`, `HumanInterventionRequested`, `HumanInterventionResolved`), traducidos a UI por una capa delgada de viewmodel fuera del dominio.
- **La intervención humana es un puerto genérico** (`ports/human_intervention.py`), no lógica ad-hoc de Portal 2 — el patrón "agotar reintentos → bloquear el worker → pedir algo al médico → reanudar" ya se repite dos veces solo en Portal 2 (ALTCHA, PDF corrupto) y es candidato a repetirse en Portal 3.
- **El mapeo estado interno → texto de reporte vive en `domain/reporte.py`**, no en el adapter de Excel — es una regla determinista, testeable sin I/O.
- **Playwright síncrono** dentro de un worker/thread dedicado (no asyncio) — coherente con procesamiento serial sin ráfagas concurrentes.
- **Pausa entre pacientes, nunca a mitad de una consulta** — evita estados intermedios corruptos en el checkpoint.
- **SQLite vía Repository pattern fino, sin ORM** — el checkpoint registra fases completadas por paciente (no presencia de archivos, por la consolidación de PDFs) e intervalos de pausa del lote; sigue sin justificar un ORM para este volumen y equipo.
- **Throttling centralizado en el orquestador**, no repetido por adapter — y es un mecanismo distinto del backoff de reintentos dentro de cada adapter.

## Stack de referencia (Apéndice A rescatado del `Requisitos.MD` original)

Python 3.12+ · Playwright (navegador visible, contexto no persistente) · httpx · pandas + openpyxl · pikepdf / pdfplumber · SQLite · tenacity (reintentos) · typer (CLI de soporte) · empaquetado tipo PyInstaller `--onedir` para distribución on-premise en Windows (no confirmado).

GUI: PySide6 (Qt) es el candidato conversado por su soporte de threading (worker thread + señales), pero **no está decidido en firme** — no lo trates como definitivo.

## Estrategia de pruebas prevista

- Unit tests de `domain` y `application` con *fakes* de los `ports` (sin browser real).
- Tests de contrato/integración de adapters contra los portales reales, separados y más lentos, corridos manualmente respetando el throttling — no golpear portales reales en cada commit.
