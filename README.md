# 🏥 LuxMed

**Validación automatizada de cobertura de seguros médicos** — para un médico, contra 3 portales web, con PDFs de respaldo por paciente a partir de un listado en Excel.

![Estado](https://img.shields.io/badge/estado-fase%20de%20dise%C3%B1o-orange)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Plataforma](https://img.shields.io/badge/plataforma-Windows-lightgrey)
![Licencia](https://img.shields.io/badge/licencia-por%20definir-lightgrey)

---

## 📋 Qué hace

El médico carga un Excel con su listado de pacientes. El sistema, de forma **asistida** (el médico autentica y supervisa, nunca desatendida), consulta 3 portales web de seguros por paciente, descarga y verifica los PDFs de respaldo, y entrega:

- Un **PDF combinado** por paciente (cobertura + titular del seguro + atención médica, según corresponda).
- Un **Excel de resultados** — el original más una columna `ESTADO` (Correcto, Desactualizado, CI no válida, Error Portal 1/2/3).
- Un **resumen numérico del lote** al terminar (conteos por estado, por rama, duración).

Todo corre **on-premise**, en la máquina del médico, sin servidor central y sin retención de datos fuera del equipo.

## 🚦 Estado del proyecto

> **Fase de diseño — sin código todavía.** Este repositorio contiene únicamente especificación de comportamiento y decisiones de arquitectura. Ver [`CLAUDE.md`](./CLAUDE.md) y [`AGENTS.md`](./AGENTS.md) para el detalle completo antes de escribir la primera línea de código.

## 🧩 Flujo de negocio

```
Excel de pacientes
      │
      ▼
Normalización (cédula válida, se descarta CEDULA_INVALIDA)
      │
      ▼
Portal 1 (siempre) ──── NO_ENCONTRADO ──→ corta el flujo para ese paciente
      │
      ▼
¿Menor de edad o seguro IESS/Campesino?
      │                              │
     Sí (Rama A)                    No (Rama B)
      │                              │
      ▼                              │
Portal 2 (titular del seguro)        │
      │                              │
      ▼                              ▼
          Portal 3 (atención médica, sesión asistida)
                      │
                      ▼
        PDF combinado + Excel de resultados + resumen
```

- **Rama A**: 3 PDFs, éxito = los 3 verificados.
- **Rama B**: 2 PDFs (omite Portal 2), éxito = los 2 verificados.
- Timeouts → reintentos acotados; fallo persistente → estado de error específico, el lote continúa con el siguiente paciente.
- Pausable/reanudable con checkpoint por paciente; idempotente al reanudar (no re-descarga trabajo ya válido).
- Throttling con jitter entre consultas — sin ráfagas contra un mismo portal.

## 🏗️ Arquitectura

**Monolito de despliegue** (un solo ejecutable) + **arquitectura interna hexagonal** (puertos y adaptadores). No porque el flujo de negocio vaya a cambiar (es estable), sino porque los **adapters de scraping sí van a cambiar** — son páginas de terceros que pueden alterar su HTML/JS/captcha sin aviso. Aislar "cómo hablo con el Portal 2" detrás de una interfaz estable evita re-testear reglas de negocio cada vez que un portal se actualiza.

Detalle completo, justificación y decisiones ya tomadas: [`docs/arquitectura.md`](./docs/arquitectura.md).

## 📁 Estructura del repositorio

```
domain/            Reglas de negocio puras. Sin Playwright, sin pandas, sin GUI.
application/          Casos de uso / orquestación. Depende de domain + ports.
  ports/                  Interfaces — el contrato que infra debe cumplir.
infrastructure/       Adapters concretos (Playwright por portal, PDF, Excel, SQLite, throttling).
interface/
  gui/                  Consumidor de application/, sin lógica de negocio propia.
  cli/                    Opcional, delgado, de soporte/debug.

docs/
  BDD/                    Especificación de comportamiento vigente (Gherkin, .feature) — fuente de verdad del qué.
  arquitectura.md           Decisiones de arquitectura interna — el cómo a nivel de capas.
  gui.md                     Diseño superficial de la GUI.
  legal.md                    Contexto legal (no comportamiento de software).

CLAUDE.md             Guía de contexto para Claude Code.
AGENTS.md               Guía agnóstica de herramienta — qué instalar antes de trabajar aquí.
```

La regla de dependencia: las flechas de import solo apuntan hacia adentro. `domain` no conoce `infrastructure` ni `interface`.

## 🔒 Invariantes de diseño

No se rediscuten sin una razón nueva y explícita:

1. On-premise, sin servidor central.
2. Retención cero de datos de paciente fuera de la máquina del médico.
3. Automatización **asistida**, nunca desatendida — el sistema no vence controles de acceso.
4. Sin LLM — procesamiento 100% determinista.
5. Sin manejo de credenciales — las del Portal 3 se escriben directo en el navegador.
6. Excel como fuente de verdad, procesado localmente.
7. Encadenamiento fijo: Portal 1 siempre → Portal 2 condicional → Portal 3 siempre (salvo corte).

Detalle completo en [`CLAUDE.md`](./CLAUDE.md).

## 🛠️ Stack tecnológico

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.12+ |
| Automatización de navegador | Playwright (visible, contexto no persistente) |
| HTTP directo | httpx |
| Excel | pandas + openpyxl |
| Verificación/lectura de PDF | pikepdf / pdfplumber |
| Estado y checkpoints | SQLite |
| Reintentos | tenacity |
| CLI de soporte | typer |
| GUI (candidato, no confirmado) | PySide6 (Qt) |
| Empaquetado | PyInstaller `--onedir` (no confirmado) |

## 🧪 Estrategia de pruebas (prevista)

- Unit tests de `domain` y `application` con *fakes* de los `ports` — sin browser real.
- Tests de contrato/integración de adapters contra los portales reales — separados, más lentos, corridos manualmente respetando el throttling.

## ⚖️ Contexto legal

El software implementa medidas técnicas que *contribuyen* al cumplimiento; el cumplimiento real (persona jurídica, convenios de acceso, LOPDP, habilitación SERCOP) vive en contratos fuera del código. Ver [`docs/legal.md`](./docs/legal.md) — no es asesoría legal.

## 🤝 Desarrollo

Antes de tocar código, lee [`AGENTS.md`](./AGENTS.md) — incluye qué skill de Playwright instalar y las reglas no negociables de la arquitectura. No hay comandos de build/lint/test todavía; se agregan cuando exista el primer código.

## 📄 Licencia

Por definir.
