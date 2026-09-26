# LuxMed

**On-premise desktop application for medical insurance verification and audit in Ecuador.**

LuxMed automates the end-to-end verification of patient insurance coverage across three Ecuadorian health regulatory portals. It transforms a manual, error-prone process—where doctors lose consultation time navigating disconnected portals, downloading scattered PDFs, and reconciling corrupted spreadsheets—into a single, auditable workflow that runs entirely on local clinic machines.

---

## The Problem We Solved

Ecuadorian clinics operate with three disconnected government health portals:

| Portal | Role | Challenge |
|--------|------|-----------|
| **Portal 1** (Coverage) | Real-time insurance audit | Returns preview PDFs; no API; session/cookie management |
| **Portal 2** (Validation) | Validates dependency relationships (IESS only) | Protected by ALTCHA proof-of-work; no documents generated |
| **Portal 3** (Clinical) | Final clinical history consolidation | Requires authenticated manual login; session must stay in RAM |

**Before LuxMed:** Medical staff manually opened each portal, typed patient IDs, waited for loads, downloaded PDFs to random folders, renamed files, merged them by hand, and cross-referenced against Excel lists with malformed IDs and inconsistent dates. A single batch of 50 patients could take hours.

**After LuxMed:** Drag an Excel file → the system validates IDs, calculates ages, routes each patient through the correct portal branch (Rama A for IESS, Rama B for Special Regime), intercepts PDFs directly from network responses in memory, consolidates them into `NAME_ID.pdf` files organized by month, and outputs a clean Excel plus an audit Excel with red-flagged rows. Same batch: minutes.

---

## Architecture: Direct Hexagonal (Ports & Adapters)

LuxMed was **not** born hexagonal. It started as a strict DDD layered architecture (`domain/services`, `infrastructure/repositories/sqlite`, etc.). That approach created:

- 40% more mapping files than business logic
- Constant merge conflicts in two-developer teams
- Ripple effects when portal selectors or UI layouts changed

**ADR 001** documents the pivot to **Direct Hexagonal**: a flat `infrastructure/` folder where each technology (SQLite, Pandas, Playwright, PyQt6) implements its port contract directly and in parallel. The domain and application layers depend **only** on abstract ports (`domain/ports.py`). Adapters never talk to each other—cross-cutting communication flows through injected abstractions.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE APPLICATION                           │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │  OrchestratorService │◄───│  ValidatorService              │   │
│  │  (Decision tree P1/2/3)    │ (Cédula length, age, minor)  │   │
│  └──────────┬───────────┘    └──────────────────────────────┘   │
│             │  Dependency Injection at startup (main.py)        │
│             ▼                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      PORTS (Abstract)                       │  │
│  │  IPacienteRepository  IExcelHandler  IPdfConsolidator      │  │
│  │  IScraperService      IConfiguracionRepository              │  │
│  └────────────────────────────┬────────────────────────────────┘  │
└───────────────────────────────│───────────────────────────────────┘
                                │ Implements
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ADAPTADORES INFRAES                          │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐   │
│  │ ExcelHandler │ │ SQLiteAdapter│ │ PlaywrightScraper      │   │
│  │ (Pandas +    │ │ (luxmed.db)  │ │ (Network interception, │   │
│  │  openpyxl)   │ │              │ │  ALTCHA, session RAM)  │   │
│  └──────────────┘ └──────────────┘ └────────────────────────┘   │
│  ┌──────────────┐ ┌──────────────────────────────────────────┐  │
│  │PdfConsolidator│ │ PyQt6 UI (QThread, signals, Stitch)      │  │
│  │ (pypdf)       │ │                                            │  │
│  └──────────────┘ └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key architectural decisions** (documented in `docs/ARCHITECTURE.md`):

- **ADR 002**: Network response interception over physical downloads. Playwright captures PDF bytes directly from Chromium's network layer—no Windows download dialogs, no filesystem races, no disk I/O during active processing.
- **ADR 003**: Documentation abstracts real institution names. Portals are referred to by functional role (Coverage / Validation / Destination); entity families are "IESS" and "Entidad Previsional Especial". Real names exist only in code (selectors, config).

---

## Business Logic: The Branch Decision Tree

The heart of LuxMed is the **Rama A / Rama B** bifurcation, driven exclusively by what Portal 1 returns:

```
Patient Excel Row
       │
       ▼
┌──────────────────┐
│ Structural Valid │── No (len ≠ 10) ──► INVALID (CEDULA_INVALIDA)
│ Cédula = 10 dig? │
└────────┬─────────┘
         │ Yes
         ▼
┌──────────────────┐
│ Portal 1 Coverage?│── None ──► INVALID (NO_ENCONTRADO)
└────────┬─────────┘
         │ Yes
         ▼
    ┌────┴────┐
    ▼         ▼
  IESS?    Special Regime?
    │         │
    ▼         ▼
 Rama A    Rama B
    │         │
    ▼         ▼
 Portal 2  (omit)
 (validator)  │
    │         ▼
    ├─► Derived? ──► Portal 1 re-query with
    │   (seguro_    holder's cédula
    │    derivado)      │
    │         │         ▼
    │         ▼    Portal 3
    │        ...        │
    │         │         ▼
    │         ▼    Consolidate PDFs
    │        ...        │
    ▼         ▼         ▼
 COMPLETADO  COMPLETADO COMPLETADO
```

**Critical invariants** (from `docs/business-rules.md`):

- **Cédula length = 10 digits exactly**. No check-digit algorithm. Fail fast, no portal calls.
- **Minority + no coverage = INVALID**. But minority *with* coverage follows normal branch logic.
- **IESS and Special Regime are mutually exclusive**. No dual-affiliation case exists.
- **`seguro_derivado = True/False` are both valid outcomes** in Rama A—neither is a rejection.
- **Portal 3 session lives only in RAM**. App close or crash = re-authenticate on resume.

---

## Tech Stack & Rationale

| Layer | Technology | Why |
|-------|------------|-----|
| Language | Python 3.11+ | Data manipulation, native threading, ecosystem |
| UI | PyQt6 | Native Windows performance, `QThread` for true async, Stitch-compatible layouts |
| Automation | Playwright | **Network interception** (capture PDF bytes in RAM), ALTCHA handling, reliable selectors |
| Data Ingestion | Pandas | Millisecond reads of massive Excel; column isolation (B, C, E, G, H, M) |
| Excel Styling | openpyxl | Direct `.xlsx` manipulation, `PatternFill` for audit red-flagging |
| Database | SQLite | Zero-config, single file, ACID, embedded in `data/luxmed.db` |
| PDF Merging | pypdf | In-memory byte concatenation, no temp files |
| Specs/Tests | BDD (Gherkin) + pytest | 13 `.feature` files, strict TDD mode |

---

## Project Structure

```
LuxMed/
├── app/
│   ├── domain/                 # Pure business logic (zero dependencies)
│   │   ├── entities.py         # Paciente, EstadoPaciente, Rama, Portal, CredencialesPortal3
│   │   └── ports.py            # Abstract contracts (IPacienteRepository, IScraperService, ...)
│   ├── application/            # Use cases & orchestration
│   │   ├── orchestrator.py     # Decision tree: P1 → branch → P2/P3 → consolidate
│   │   ├── validator.py        # Cédula length, age calc, minor protection
│   │   ├── lote_service.py     # Batch lifecycle: pause/resume/checkpoint/throttle
│   │   └── progreso.py         # Typed progress signals for UI thread
│   └── infrastructure/         # Adapters (implement ports)
│       ├── database/sqlite_adapter.py
│       ├── excel/excel_handler.py
│       ├── pdf/pdf_merger.py
│       ├── scraper/            # Playwright adapters per portal
│       │   ├── playwright_scraper.py      # Portal 1 (coverage)
│       │   ├── portal_1_scrapper.py       # Low-level scrape + parse
│       │   ├── portal2_iess_adapter.py    # Portal 2 + ALTCHA
│       │   ├── portal3_adapter.py         # Portal 3 (authenticated)
│       │   ├── altcha_handler.py          # Proof-of-work automation + human fallback
│       │   └── retry_utils.py             # Exponential backoff
│       └── ui/                 # PyQt6 presentation (Stitch-derived)
│           ├── screens/        # Upload, Processing, Review, Summary, Settings, Logs
│           ├── widgets/        # Dropzone, Table, KPI, NavRail, Chip, Spinner...
│           ├── theme/          # Design tokens, QSS template, palette, fonts
│           └── threads.py      # QThread wrapper for scraper isolation
├── docs/
│   ├── ARCHITECTURE.md         # C4 diagrams, ADRs, tech stack rationale
│   ├── business-rules.md       # Ubiquitous language, invariants, state machine
│   └── BDD/                    # 13 Gherkin specs (source of truth for behavior)
├── tests/
│   ├── architecture/test_hexagonal_boundaries.py  # Enforces layer isolation
│   ├── ui/                   # PyQt6 widget & flow tests
│   └── test_*.py             # Unit/integration for orchestrator, PDF, portals, etc.
├── openspec/                   # SDD artifacts (specs, designs, tasks, archives)
├── main.py                     # Composition root: wires ports → adapters → UI
└── AGENTS.md                   # Agent orchestration protocol (SDD, SOLID, concurrency)
```

---

## Development Methodology: Spec-Driven Development (SDD)

LuxMed uses **SDD** as a guardrail against ambiguity and hallucination. Every change follows:

```
1. SPECIFICATION (SDD)     → Developer defines exact signatures, inputs, outputs
2. MCP VERIFICATION        → Agent reads Stitch context, validates rules
3. CODE GENERATION (SOLID) → Deterministic, reviewable implementation
```

**Artifacts live in `openspec/changes/<change-name>/`:**
- `spec.md` — Delta requirements with Given/When/Then scenarios (RFC 2119 keywords)
- `design.md` — Sequence diagrams for async flows, port/adapter boundaries
- `tasks.md` — Hierarchical, phase-grouped, single-session tasks
- `apply-progress.md` — Running implementation log
- `verify-report.md` — Test evidence against spec
- `archive-report.md` — Final sync at close

**Run the SDD cycle:**
```bash
# Initialize (once per project)
/sdd-init

# Explore an idea (no files created)
/sdd-explore "optimize Portal 2 wait times"

# Full pipeline: proposal → spec → design → tasks
/sdd-ff portal2-optimization

# Implement tasks in batches
/sdd-apply portal2-optimization

# Verify against specs
/sdd-verify portal2-optimization

# Archive when done
/sdd-archive portal2-optimization
```

---

## Running Locally

```bash
# 1. Clone & enter
git clone <repo-url>
cd LuxMed

# 2. Create venv & install
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 3. Configure environment
cp .env.example .env   # Set PORTAL_3 credentials, output folder, etc.

# 4. Run
python main.py
```

**UI Demo (mocked data, no portals):**
```bash
python scripts/demo_ui.py
```

**Tests:**
```bash
pytest tests/ -v
# Architecture boundary enforcement
pytest tests/architecture/test_hexagonal_boundaries.py -v
```

---

## Key Flows at a Glance

### Batch Processing (UI → Scraper Thread)
```
Main Thread (PyQt6)                    Worker Thread (QThread)
┌─────────────────────┐                ┌─────────────────────┐
│ User drops Excel    │                │                     │
│ ▼                   │                │                     │
│ Validator runs      │                │                     │
│ ▼                   │                │                     │
│ "Start Batch" click │───────────────►│ OrchestratorService │
│                     │   pyqtSignal   │ .procesar_pacientes │
│ Live table updates  │◄───────────────│ Emits AvancePaciente│
│ Progress bars       │   (typed)      │ per patient         │
│ Pause/Resume btns   │                │ Checkpoint per row  │
└─────────────────────┘                └─────────────────────┘
```

### PDF Consolidation (In-Memory)
```
Rama A, seguro_derivado=True:   P1(patient) → P1(holder) → P3(holder) → NAME_ID.pdf
Rama A, seguro_derivado=False:  P1(patient) → P3(patient)               → NAME_ID.pdf
Rama B:                         P1(patient) → P3(patient)               → NAME_ID.pdf
```
Files saved to `data/salidas/YYYY-MM/NAME_ID.pdf` — one subfolder per month, flat naming to avoid NTFS saturation.

---

## Compliance & Security

- **LOPDP (Ecuador Data Protection Law)**: Zero PII leaves the clinic machine. All processing in RAM + local SQLite.
- **Portal 3 Auth**: Manual, assisted login. Credentials never captured/stored. Session cookie = RAM only.
- **Portal 2**: Public form + ALTCHA only. No institutional credentials.
- **Audit Trail**: Every patient row in output Excel shows final state. Red = "needs review" (no motive leakage).

---

## Contributing

This project follows **strict SDD + SOLID** discipline. Agents (and humans) operate under `AGENTS.md`:

- No autonomous file creation or structural decisions
- Zero AI-generated comments in production code
- Direct Hexagonal topology enforced by `tests/architecture/test_hexagonal_boundaries.py`
- All changes require spec → design → tasks → apply → verify → archive

See `AGENTS.md` for the full orchestration protocol, SOLID application guide, and UI↔Scraper concurrency contract.

---

## License

Proprietary — Internal use for Ecuadorian clinical operations only.

---

*Built with Spec-Driven Development. Architecture decisions recorded in ADRs. Business rules versioned in `docs/business-rules.md`. Behavior specified in `docs/BDD/*.feature`.*