# AGENTS.md

Documentación de lo implementado en este sandbox y consideraciones para quien
retome el trabajo (humano o agente).

## Objetivo

Automatizar con Playwright (Python) el reporte **"Historial de Atenciones"**
del portal LUXMED: login asistido, selección de rol de acceso, navegación al
reporte, y por cada paciente de una lista, búsqueda, generación del registro
de atención y descarga + lectura del PDF resultante.

## Archivos

- `luxmed_reportes_automation.py` — script único (monolito, a pedido). Toda
  la lógica vive aquí: config, generación de datos fake, lectura de Excel,
  pasos de UI, orquestación y CLI.
- `.env.example` — plantilla de variables de entorno. Copiar a `.env` y
  completar `LOGIN_URL` real antes de correr.
- `requirements.txt` — `playwright`, `python-dotenv`, `openpyxl`, `pdfplumber`.
- `.gitignore` — excluye `.venv/`, `.env`, `data/`, `output/`.
- `data/patients.xlsx` — generado por `--generate-fake-data`, **no está en
  git** (ver abajo, nunca debe tener pacientes reales).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env            # y editar LOGIN_URL
```

## Uso

```bash
python luxmed_reportes_automation.py --generate-fake-data --count 5   # solo genera data/patients.xlsx
python luxmed_reportes_automation.py --run                            # corre el flujo completo
```

Si `PATIENTS_FILE` no existe al correr `--run`, el script genera uno fake
automáticamente (es un sandbox de prueba, así que esto es intencional).

## Flujo implementado

Todo corre en **una sola instancia de Chromium propia de Playwright**
(`pw.chromium.launch(...)` + `browser.new_context()`), nunca el navegador
personal del usuario ni un perfil persistente.

1. **Login asistido** (`assisted_login`): navega a `LOGIN_URL` y hace
   `wait_for(state="visible", timeout=LOGIN_TIMEOUT_MS)` sobre el botón
   "Acceder" del home. El usuario inicia sesión manualmente en la ventana —
   por eso `HEADLESS` debe ser `false` mientras esto ocurre. No hay
   scraping de credenciales, el script no las toca.
2. **Una sola vez por sesión** (no por paciente):
   - `open_reportes_card`: scroll, click en "Acceder" dentro de la tarjeta
     "Reportes", auto-wait de modal.
   - `select_role_and_save`: click en columna "Nombre", click en el radio
     de la fila "ESPECIALISTA DISTRITAL CALIDAD DE LOS SERVICIOS DE SALUD",
     scroll, click "Guardar".
   - `open_historial_atenciones`: click en "Reportes Administrativos" de la
     barra, click en "Historial de Atenciones" (única opción por ahora),
     modal → scroll → click "Aceptar".
3. **Por cada paciente** del Excel (`process_patient`):
   - `search_patient`: llena `Numero de Identificacion` (placeholder),
     `paciente_fecha_desde`/`paciente_fecha_hasta` (primer/último día del
     mes actual, formato `DATE_FORMAT`), selecciona `select-entidad` por el
     texto de la columna M del Excel, click en
     `#searchpacientedatatble-button`, scroll.
   - `select_result_row`: click en el `<td tabindex="0">` del resultado,
     luego en el ícono `i.fa.fa-file-pdf-o.bigger-125.fa-fw.red` que aparece.
   - `fill_motivo_and_save`: modal → `select#impresatencionmedica_ctmotivo`
     = value `3088` ("Otros"), `textarea#impresatencionmedica_observacion`
     = siempre `"RCPROVINCIAL"`, click "Guardar".
   - `print_atencion_and_extract_pdf`: click en
     `button[onclick="printatencionAction()"]`, auto-wait del modal final,
     y extracción del PDF (ver siguiente sección).
   - Antes de cada paciente (excepto el primero) se cierra cualquier modal
     abierto (`close_modal_if_open`) para dejar la página en el estado del
     formulario de búsqueda.

## Extracción del PDF (sin CLI externo)

El modal final muestra el PDF en un `iframe`/`embed`/`object`. El script:

1. Lee el atributo `src`/`data` de ese elemento.
2. Si es un `data:application/pdf;base64,...`, decodifica directo.
3. Si es una URL, la descarga con `page.context.request.get(url)` —
   reutiliza las cookies/sesión de Playwright, no hace falta re-autenticar.
4. Guarda el PDF en `output/atencion_<ci>_<timestamp>.pdf`.
5. Extrae texto con `pdfplumber` (librería Python pura, no shell a
   `pdftotext` ni similares) y lo guarda en el `.txt` homónimo.

Esto cumple el requisito de "leer el PDF con Playwright/Python, no CLI".

## Datos de prueba (fake)

`generate_fake_patients_file` crea un `.xlsx` con columnas **A a M**:

- **A** = Número de Identificación → cédula ecuatoriana de **10 dígitos
  con dígito verificador válido** (algoritmo módulo 10 estándar, coeficientes
  `[2,1,2,1,2,1,2,1,2]`), para que pase validaciones de formulario del lado
  cliente si las hay.
- **B–L** = nombre, apellido, fecha nacimiento, teléfono, email, dirección,
  ciudad, provincia, género, estado civil, observación — todo mockeado,
  sin relación con personas reales.
- **M** = Entidad (por defecto `"27 DE OCTUBRE"`, configurable vía
  `DEFAULT_ENTIDAD` en `.env`).

**Nunca** se debe reemplazar `data/patients.xlsx` con datos reales de
pacientes en este sandbox — el archivo está en `.gitignore` justamente para
evitar ese riesgo, pero la responsabilidad de no pegar datos sensibles ahí
es de quien lo use.

## Selectores: exactos vs. heurísticos

El sitio es una ruta protegida — no se pudo inspeccionar en vivo. En el
código, cada paso está comentado con `[EXACTO]` o `[HEURISTICO]`:

- **`[EXACTO]`**: selectores dados literalmente por el usuario (`name`,
  `id`, `placeholder`, clases CSS, `value` de option, `onclick`). Deberían
  funcionar tal cual contra el sitio real.
- **`[HEURISTICO]`**: no había selector dado, así que se ubican por texto
  visible (`get_by_role`, `get_by_text`). Son los puntos más frágiles:
  - Botón "Acceder" de la tarjeta "Reportes" (`open_reportes_card`) — usado
    también como señal de que el login terminó.
  - Botón "Reportes Administrativos" de la barra de navegación
    (`open_historial_atenciones`).
  - Ítem "Historial de Atenciones" dentro del desplegable.

**Antes de usarlo en serio**: correr `--run` una vez con `HEADLESS=false`
contra el sitio real y confirmar que estos tres puntos heurísticos
encuentran el elemento correcto. Si el sitio usa textos ligeramente
distintos (mayúsculas, espacios, íconos sin texto), ajustar esos locators.

## Otras decisiones y consideraciones

- **`HEADLESS`**: es variable de entorno como se pidió, pero durante el
  login debe ser `false` porque el login es asistido (el usuario necesita
  ver la ventana). El resto del flujo funciona igual en headless o no.
- **`DATE_FORMAT`**: se asumió `%d/%m/%Y` (formato común en Ecuador) para
  los campos de fecha. Es un env var precisamente porque no se pudo
  confirmar el formato real que espera el input — ajustar si el sitio
  rechaza las fechas.
- **Selección de entidad**: `select_option_by_text` normaliza (quita
  tildes, mayúsculas) y compara primero por igualdad exacta y luego por
  coincidencia parcial, para tolerar pequeñas diferencias de formato entre
  el Excel y el texto de las `<option>` del sitio.
- **Instancia de navegador aislada**: se usa `pw.chromium.launch()` +
  `browser.new_context()` (contexto nuevo, sin perfil persistente) para no
  tocar el Chrome personal del usuario ni reusar sesiones/cookies previas.
- **`requirements.txt`**: se pineó `playwright==1.62.0` (no `1.47.0` como
  primer intento) porque con Python 3.13 la versión vieja arrastra una
  versión de `greenlet` sin wheel precompilado y falla el build en Windows
  (requiere MSVC con headers internos de CPython). Verificado instalando en
  este entorno (Python 3.13.2).
- **Verificado en este sandbox** (sin acceso al sitio real): creación del
  venv, instalación de dependencias, generación de `data/patients.xlsx`,
  validación del dígito verificador de las 5 cédulas generadas, y lectura
  del Excel con `load_patients`. **No verificado**: todo el flujo de
  browser contra el sitio real de LUXMED (requiere credenciales y acceso
  que no están disponibles aquí).

## Pendiente / próximos pasos sugeridos

- Correr un dry-run real con `HEADLESS=false` y confirmar los tres
  selectores heurísticos.
- Confirmar el formato de fecha real de `paciente_fecha_desde`/`_hasta`.
- Si el flujo debe reintentar ante fallos por paciente (en vez de abortar
  todo el batch), agregar manejo de errores por paciente en el `for` de
  `run()` — hoy una excepción en un paciente detiene el resto del batch.
