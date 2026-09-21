# business-rules.md · Reglas de Negocio de LuxMed 📋

> **Ecosistema de Operación:** Auditoría y Verificación Médica On-Premise  
> **Ámbito de Aplicación:** Flujo de Admisión y Validación de Coberturas (Ecuador)  
> **Versión de las Reglas:** 1.3.0 (Vigente a partir del 10/09/2026)

---

## 1. Propósito y Glosario (Context & Ubiquitous Language)

### Objetivo
Este documento constituye la fuente única de la verdad operativa para el sistema LuxMed. Traduce los requerimientos legales, administrativos y de auditoría de los establecimientos de salud en directrices lógicas estrictas. Su propósito es regular la ingesta de listados de pacientes, dictar el comportamiento de las consultas vehiculizadas en portales públicos ecuatorianos y normar la consolidación de expedientes para la optimización del tiempo de consulta del médico.

### Glosario de Términos (Lenguaje Ubicuo)
- **Paciente Ingestado:** Registro de un ciudadano extraído de una fila de un libro de Excel que se encuentra en proceso de carga inicial, antes de ser verificado.
- **Paciente Válido:** Ciudadano cuya identidad estructural es correcta (cédula legítima) y que posee cobertura activa demostrable en al menos una entidad previsional de salud en el Portal de Coberturas.
- **Paciente Inválido:** Registro que ha sido rechazado administrativamente debido a errores en sus datos de identidad, minoría de edad sin amparo de seguro, o por reportar ausencia total de cobertura en las entidades auditadas.
- **Portal de Coberturas (P_1):** Plataforma oficial utilizada para auditar el aseguramiento ciudadano en tiempo real.
- **Portal de Validación Secundaria (P_2):** Plataforma técnica transaccional intermedia cuyo uso es mandatorio únicamente para pacientes de **Rama A** (ver más abajo). **No genera ningún documento descargable** — solo devuelve si existe o no un titular distinto que derive la cobertura al paciente. Protegida por un widget anti-bot ALTCHA (prueba de trabajo) antes de aceptar el envío del formulario.
- **Portal de Destino Técnico (P_3):** Plataforma final de consolidación clínica e historial médico de la institución. Es el único de los tres portales que requiere una sesión autenticada.
- **Entidad Previsional:** Institución pública encargada de la seguridad social del ciudadano. El sistema distingue dos familias de cobertura **mutuamente excluyentes** — ningún paciente tiene cobertura vigente de ambas al mismo tiempo:
  - **IESS:** agrupa todas sus variantes tal como las devuelve el Portal de Coberturas (Afiliado Seguro General, Afiliado Seguro Campesino, Dependiente hijo menor de 18 años de afiliado al Seguro General, entre otras).
  - **Entidad Previsional Especial:** agrupa los regímenes de seguridad social ajenos al IESS (p. ej. fuerzas del orden y sus dependientes).
- **Seguro Derivado (`seguro_derivado`):** Propiedad booleana del paciente, derivada de la respuesta del Portal 2 (nunca leída de forma estática). `True` si el Portal 2 identifica a un titular distinto que le otorga la cobertura al paciente (dependiente); `False` si el Portal 2 no identifica ningún titular (el paciente es su propio titular). Ninguno de los dos valores constituye un rechazo — ambos son desenlaces válidos dentro de Rama A.
- **Rama A:** Ruta operativa de todo paciente cuya cobertura vigente pertenece a la familia **IESS** (cualquier variante). Pasa obligatoriamente por el Portal 2 para determinar `seguro_derivado`:
  - Si `seguro_derivado = True`: el sistema vuelve a consultar el **Portal 1** con la cédula del titular identificado, para obtener el documento de cobertura de esa persona (el "PDF del Titular"), y luego continúa al Portal 3 con la cédula del titular.
  - Si `seguro_derivado = False`: no hay documento adicional; el paciente continúa directo al Portal 3 con su propia cédula.
- **Rama B:** Ruta operativa de todo paciente cuya cobertura vigente pertenece a la familia **Entidad Previsional Especial**. Omite el Portal 2 y consulta directamente el Portal 3 con la cédula del propio paciente.
- **Reporte de Auditoría (Excel Espejo):** Documento de salida idéntico al original, modificado visualmente para resaltar en rojo la fila de todo paciente cuyo estado final sea distinto de `COMPLETADO` (ver §7).
- **Expediente Consolidado:** Archivo digital único en formato PDF que unifica de forma secuencial los soportes binarios emitidos por los portales para un paciente válido.

---

## 2. Clasificación de Reglas (Core Rules)

### Reglas de Restricción (Invariantes del Sistema)
- **Ecuación de Identidad Obligatoria:** Si la cédula de un paciente posee una longitud distinta a 10 dígitos numéricos, entonces el paciente debe ser clasificado inmediatamente como **Inválido** (`CEDULA_INVALIDA`), sin realizar ninguna consulta a los portales. No se exige ningún algoritmo adicional de dígito verificador.
- **Protección de Minoridad No Asegurada:** Si un paciente es menor de edad (menor a 18 años calculado en base a su fecha de nacimiento) y el Portal de Coberturas dictamina que no posee afiliación activa en ninguna entidad previsional, entonces el sistema debe prohibir su avance y marcarlo como **Inválido** (`NO_ENCONTRADO`). Nota: la minoría de edad **no** es, por sí sola, un factor que determine la ruta de portales (ver Rama A / Rama B) — un menor con cobertura vigente sigue la ruta normal según la familia de cobertura detectada; este invariante solo endurece el rechazo cuando no hay cobertura alguna.
- **Aislamiento de Almacenamiento On-Premise:** Los registros de salud e identificadores personales procesados nunca deben ser transmitidos a servidores web externos a la máquina local de la clínica.

### Reglas de Derivación (Cálculos y Transformaciones)
- **Determinación de Seguro Derivado:** El sistema no lee `seguro_derivado` de ninguna fuente estática: lo deriva exclusivamente de la respuesta del Portal 2 (exclusivo de Rama A). Si el Portal 2 identifica un titular que otorga la cobertura al paciente, `seguro_derivado = True` y se registran los datos de ese titular para volver a consultar el Portal 1. Si el Portal 2 no identifica ningún titular, `seguro_derivado = False`. Ninguno de los dos casos es un rechazo del paciente.
- **Cálculo Inmutable de Edad:** La edad biológica del paciente no se lee de forma estática del Excel. El sistema debe tomar la fecha de nacimiento (Columna E) y restarla de la fecha natural del sistema operativo de la máquina local en el microsegundo de la ingesta para derivar un número entero inmutable.
- **Indexación Unívoca de Expedientes:** El nombre del archivo PDF consolidado de salida debe construirse obligatoriamente concatenando el Nombre del Paciente (Columna B) y la Cédula (Columna C) bajo la estructura plana: `NOMBRE_CEDULA.pdf` (ver detalle y justificación en §7). Se permite una única subcarpeta por mes de fecha de atención; está prohibida la creación de subcarpetas adicionales por nombre de paciente para evitar la saturación del sistema de archivos de Windows.

### Reglas de Reacción (Disparadores de Eventos)
- **Disparador de Alerta de Auditoría:** Si un paciente termina su procesamiento en cualquier estado final distinto de `COMPLETADO` (independientemente del motivo — CI inválida, sin cobertura, error técnico de portal, etc.), entonces el sistema debe marcar internamente el registro con la propiedad `es_auditoria_rojo = True` para su posterior tintura visual en rojo en el Excel Auditado de salida (ver §7). El color no distingue el motivo específico.
- **Captura Binaria Directa:** En el instante en que el Portal de Coberturas previsualice el acta médica en pantalla, entonces el sistema debe interceptar la respuesta de la red y capturar los bytes del archivo PDF directamente en la memoria RAM, abortando el uso de la ventana física de descargas del sistema operativo.

---

## 3. Regla de Bifurcación de Ruta (Rama A / Rama B)

El comportamiento de la navegación automatizada depende exclusivamente de la familia de cobertura que el Portal de Coberturas (P₁) confirma para el paciente. Las familias **IESS** y **Entidad Previsional Especial** son mutuamente excluyentes, por lo que no existe (ni debe manejarse) un caso de doble afiliación simultánea:

| Validación Estructural (C) | Cobertura confirmada en P₁ | Resultado del Portal 2 (solo Rama A) | Estado Final | Ruta de Flujo Operativo | Alerta Visual en Excel Auditado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Incorrecta (longitud ≠ 10) | No aplica | No aplica | **INVÁLIDO** (`CEDULA_INVALIDA`) | Fin de flujo inmediato, ninguna consulta a portales | Pintar fila en rojo |
| Correcta | Ninguna entidad reporta cobertura | No aplica | **INVÁLIDO** (`NO_ENCONTRADO`) | Fin de flujo inmediato | Pintar fila en rojo |
| Correcta | Familia **IESS** (cualquier variante) | Identifica titular (`seguro_derivado = True`) | **VÁLIDO → Rama A** | Vuelve a consultar Portal 1 con la cédula del titular (obtiene su PDF), luego Portal 3 con la cédula del titular | Pintar fila en rojo solo si el paciente no termina en `COMPLETADO` |
| Correcta | Familia **IESS** (cualquier variante) | No identifica titular (`seguro_derivado = False`) | **VÁLIDO → Rama A** | Sin documento adicional; directo a Portal 3 con la cédula del propio paciente | Pintar fila en rojo solo si el paciente no termina en `COMPLETADO` |
| Correcta | Familia **Entidad Previsional Especial** | No aplica (se omite el Portal 2) | **VÁLIDO → Rama B** | Directo a Portal 3 con la cédula del propio paciente | Pintar fila en rojo solo si el paciente no termina en `COMPLETADO` |

La minoría de edad no participa en esta bifurcación (ver invariante "Protección de Minoridad No Asegurada" arriba): un menor de edad cae en Rama A o Rama B según la familia de cobertura que le corresponda, igual que un adulto. Ningún resultado del Portal 2 (`seguro_derivado = True` o `False`) constituye por sí solo un rechazo del paciente.

---

## 4. Flujos de Trabajo y Estados (State Machines)

El ciclo de vida de un Paciente dentro del sistema LuxMed está rígidamente secuenciado. Está estrictamente prohibido omitir estados o realizar saltos de transición no autorizados por las reglas de negocio. Los estados de error son **granulares por portal** — no existe un estado genérico único de error.

```text
 [ INGESTADO ] ──────► [ HIGIENIZADO ] ──────► [ EN_PROCESO ] ──────► [ COMPLETADO ] ──► [ EXPORTADO_DUAL ]
       │                      │                       │
       ▼                      ▼                       ▼
 [ CEDULA_INVALIDA ]   [ CEDULA_INVALIDA ]      [ NO_ENCONTRADO ]
                                                 [ ERROR_PORTAL_1 ]   (incluye fallos al re-consultar Portal 1 por el titular)
                                                 [ ERROR_PORTAL_2 ]   (solo Rama A — exclusivo de fallo de ALTCHA)
                                                 [ ERROR_PORTAL_3 ]
```

`seguro_derivado = True` / `False` (ver §1/§2) **no son estados de rechazo** — son un dato derivado dentro de `EN_PROCESO` para pacientes de Rama A, ambos con camino directo a `COMPLETADO`.

### Transiciones Válidas y Eventos Disparadores
- **`INGESTADO` ➔ `HIGIENIZADO`:** Ocurre de forma automática cuando Pandas aísla las columnas B, C, E, G, H, M y el componente Validator ratifica la longitud de la cédula y deriva la edad.
- **`INGESTADO` / `HIGIENIZADO` ➔ `CEDULA_INVALIDA`:** Ocurre si la cédula no tiene exactamente 10 dígitos numéricos. El registro se congela sin consultar ningún portal y se prepara para el reporte en rojo.
- **`HIGIENIZADO` ➔ `EN_PROCESO`:** Ocurre cuando el operador presiona el botón de inicio de campaña y el registro entra a la cola activa del hilo secundario de Playwright.
- **`EN_PROCESO` ➔ `NO_ENCONTRADO`:** Se dispara si el Portal de Coberturas (P₁) no reporta cobertura vigente en ninguna entidad, incluyendo el caso de un menor de edad sin amparo previsional (ver invariante de minoridad).
- **`EN_PROCESO` ➔ `ERROR_PORTAL_1`:** Timeout o fallo persistente tras agotar los reintentos, ya sea en la consulta original del paciente al Portal 1, o en la re-consulta al Portal 1 por el titular cuando `seguro_derivado = True` (ver §5).
- **`EN_PROCESO` ➔ `ERROR_PORTAL_2`:** Exclusivo de Rama A — fallo persistente del ALTCHA del Portal 2 ni con intervención humana (ver §5). No existe ningún otro motivo de error en el Portal 2, ya que no genera documentos.
- **`EN_PROCESO` ➔ `ERROR_PORTAL_3`:** Timeout o fallo persistente del Portal 3 tras agotar los reintentos (ver §5).
- **`EN_PROCESO` ➔ `COMPLETADO`:** Se activa cuando el paciente completa con éxito su ruta asignada: Rama A con `seguro_derivado = True` requiere el PDF del paciente (Portal 1) + el PDF del titular (Portal 1) + el PDF de Portal 3, verificados; Rama A con `seguro_derivado = False` y Rama B requieren solo el PDF del paciente (Portal 1) + el PDF de Portal 3, verificados.
- **`COMPLETADO` ➔ `EXPORTADO_DUAL`:** Estado de cierre del ciclo de vida del lote. Se dispara cuando el usuario hace uso de los botones finales del Dashboard, generando los PDFs consolidados por paciente y los dos libros de Excel (Limpio y Auditado con Celdas Rojas) — ver §7.

### Transiciones Prohibidas (Blindaje de Datos)
- Está prohibido pasar de `INGESTADO` a `EN_PROCESO` sin pasar por la validación estructural de `HIGIENIZADO`.
- Está prohibido pasar de `EN_PROCESO` a `COMPLETADO` si falta el flujo binario de soporte de al menos un portal obligatorio de su ruta.

---

## 5. Excepciones y Manejo de Errores Operativos (Edge Cases)

- **Fallo de Integridad en la Primera Descarga:**  
  Si un documento (PDF del paciente en Portal 1, PDF del titular en la re-consulta a Portal 1, o PDF de Portal 3) falla su verificación de integridad en su **primera** descarga — no al reanudar, ver §6 — el sistema lo trata igual que un timeout: reintenta hasta 3 veces adicionales y, si el fallo persiste, marca al paciente con el `ERROR_PORTAL_N` correspondiente al portal de ese documento. Este criterio es uniforme para los tres portales/documentos.

- **Caída de Servicio o Intermitencia en el Portal 1 o el Portal 3:**  
  Si el Portal 1 o el Portal 3 dejan de responder o generan un error de red a mitad del procesamiento de un paciente válido, entonces el sistema debe reintentar la carga un máximo de 3 veces adicionales con esperas exponenciales pasivas. Si el fallo persiste, el paciente se marca en el estado de error correspondiente (`ERROR_PORTAL_1` o `ERROR_PORTAL_3`), liberando el hilo para no detener la cola de la clínica, y permitiendo al médico re-procesar únicamente a los caídos al final del día. Esta misma regla aplica cuando el fallo ocurre en la re-consulta al Portal 1 para obtener el PDF del titular (`seguro_derivado = True`) — se trata como cualquier otro fallo de Portal 1, marcando `ERROR_PORTAL_1`.

- **Verificación Anti-Bot (ALTCHA) en el Portal 2 (exclusivo de Rama A):**  
  El formulario del Portal 2 exige superar un widget ALTCHA (prueba de trabajo) antes de aceptar el envío; el sistema espera pasivamente a que la verificación legítima del widget se complete. Si Playwright no logra completarla tras 3 intentos automáticos, el sistema pausa el navegador (visible) y solicita al médico resolverla manualmente; al resolverse, retoma el envío del formulario automáticamente. Si la intervención humana tampoco logra completarla, el sistema consulta al médico cómo proceder: reintentar el ciclo completo, o marcar al paciente como `ERROR_PORTAL_2` y continuar con el siguiente. Este es el **único** motivo de error posible en el Portal 2, ya que este portal no genera ningún documento — solo devuelve el dato de `seguro_derivado`.

**Nota:** las familias de cobertura IESS y Entidad Previsional Especial son mutuamente excluyentes (ver §3) — no existe, y no debe implementarse, un caso de doble afiliación simultánea entre ambas.

---

## 6. Operación del Lote: Pausa, Reanudación, Throttling e Idempotencia

- **Pausa Manual o Forzada:** El médico puede pausar el lote en cualquier momento. También se pausa de forma forzada si la sesión del Portal 3 expira a mitad del procesamiento. En ambos casos el sistema guarda un checkpoint por paciente (qué fases/portales ya se completaron) y el lote queda en estado **reanudable**, informando si será necesario re-autenticarse en el Portal 3.
- **Reanudación con Confirmación:** Al relanzar un lote pausado (y re-autenticarse en el Portal 3 si corresponde), el sistema muestra un resumen de pacientes procesados y pendientes, espera la confirmación del médico, y retoma desde el primer paciente pendiente.
- **Throttling entre Consultas:** El sistema procesa pacientes en serie y espera un intervalo prudente (con variación) entre consultas a cualquier portal, sin ráfagas concurrentes contra un mismo portal, para no ser percibido como un ataque ni provocar el bloqueo de la cuenta.
- **Idempotencia de PDFs al Reanudar:** Al reanudar, el sistema verifica la integridad de cualquier PDF ya descargado en una corrida anterior. Si está íntegro, omite su descarga y continúa con las fases pendientes; si está corrupto o incompleto, lo vuelve a descargar. La fuente de verdad de qué le falta a un paciente es el registro de fases del checkpoint — no la presencia física de los PDFs individuales, que pueden ya no existir si el paciente llegó a la fase de combinación (ver §7).

---

## 7. Consolidación y Entregables del Lote

- **Consolidación del PDF por Paciente:** Al completar las fases requeridas por su rama, el sistema combina los PDFs individuales en un único documento:
  - **Rama A, `seguro_derivado = True`:** PDF del paciente (Portal 1) → PDF del titular (Portal 1, re-consulta) → PDF de Portal 3 (con la cédula del titular).
  - **Rama A, `seguro_derivado = False`, y Rama B:** PDF del paciente (Portal 1) → PDF de Portal 3 (con la cédula del paciente).
  El archivo resultante se nombra `NOMBRE_CEDULA.pdf`, usando el nombre completo del paciente tal como se extrajo del Excel de origen, y se guarda en la carpeta del mes correspondiente a la fecha de atención de ese Excel. Como cada Excel de origen agrupa únicamente atenciones ya cerradas de un mes específico, un mismo paciente atendido en meses distintos vive en carpetas de mes distintas sin riesgo de colisión de nombre. Los PDFs individuales se descartan tras la combinación, conservando solo el PDF combinado.
- **Entregable Dual de Excel:** Al cerrar el lote (`EXPORTADO_DUAL`) el sistema produce dos libros: un **Excel Limpio** idéntico al original, y un **Excel Auditado (Espejo)** idéntico al original con las filas pintadas en rojo (`PatternFill` vía openpyxl) para todo paciente cuyo estado final sea distinto de `COMPLETADO` — el color solo señala "requiere revisión", sin distinguir visualmente el motivo específico.
- **Resumen Numérico del Lote (GUI):** Al terminar el lote, el Dashboard presenta el total de pacientes procesados; el conteo por estado final (`COMPLETADO`, `CEDULA_INVALIDA`, `NO_ENCONTRADO`, `ERROR_PORTAL_1`, `ERROR_PORTAL_2`, `ERROR_PORTAL_3`) tanto unificado como desglosado por Rama A / Rama B; y la hora de inicio, hora de fin y duración total de tiempo **activo** de procesamiento, excluyendo el tiempo que el lote estuvo en pausa.

---

## 8. Control de Versiones e Historial de Cambios (Audit & Versioning)

- **01/09/2026 (Versión 1.0.0):**  
  Cierre y congelación de las reglas operativas iniciales del sistema LuxMed para su despliegue On-Premise. Se implementa el árbol de decisiones de tres portales, la captura de PDFs indexados por formato de cédula plano en memoria RAM y el Entregable Dual (Excel Espejo con openpyxl + Excel Limpio).

- **10/09/2026 (Versión 1.1.0) — Reconciliación con docs/BDD/:**  
  Sesión SDD para alinear estas reglas con el comportamiento real del sistema documentado en `docs/BDD/`. Cambios: (1) la validación de cédula exige solo 10 dígitos, sin dígito verificador; (2) la bifurcación de ruta se redefine como Rama A (familia IESS, siempre pasa por Portal 2 como validador) / Rama B (Entidad Previsional Especial, omite Portal 2) — se elimina la matriz cruzada de 3 entidades y el edge case de doble afiliación simultánea, ya que ambas familias son mutuamente excluyentes; (3) la máquina de estados pasa a usar estados de error granulares por portal en vez de un `PENDIENTE_ERROR` genérico; (4) se documentan formalmente la pausa/reanudación, el throttling, la idempotencia de PDFs, la consolidación de PDFs (`NOMBRE_CEDULA.pdf`) y el resumen numérico del lote, antes solo especificados en `docs/BDD/`; (5) se elimina toda mención directa a entidades previsionales o portales específicos por su nombre real en este documento, por tratarse de un sistema no aprobado formalmente por dichas instituciones — el detalle técnico puede vivir en el código, no en la documentación.

- **10/09/2026 (Versión 1.2.0) — Corrección del modelo del Portal 2 (`seguro_derivado`):**  
  A partir de una revisión de código del equipo se detectó que el modelo anterior de Rama A era incorrecto: el Portal 2 **no genera ningún PDF** — solo devuelve si existe o no un titular que derive la cobertura al paciente (nueva propiedad `seguro_derivado`, booleana). Cambios: (1) cuando `seguro_derivado = True`, el "segundo documento" de Rama A ya no sale del Portal 2, sino de una **re-consulta al Portal 1** con la cédula del titular identificado — sus fallos se tratan como `ERROR_PORTAL_1`, no como un estado propio; (2) cuando `seguro_derivado = False`, el paciente no obtiene ningún documento adicional y continúa directo a Portal 3 con solo 2 documentos (igual que Rama B) — este desenlace **no es un rechazo**; (3) se eliminan los estados `SIN_COBERTURA_PORTAL_2` y `PDF_CORRUPTO_PORTAL_2`, que en el modelo anterior trataban erróneamente como fallo/rechazo lo que en realidad es el camino normal de un paciente que es su propio titular; (4) `ERROR_PORTAL_2` queda acotado exclusivamente al fallo persistente del ALTCHA, único motivo de error posible en ese portal.

- **10/09/2026 (Versión 1.3.0) — Cierre de puntos diferidos (sesión SDD, tercera ronda):**  
  Cambios: (1) la sesión/cookie del Portal 3 se mantiene únicamente en memoria (RAM) durante la corrida del lote, nunca se persiste a disco — si la app se cierra o falla, se pierde junto con el resto del estado en memoria y aplica el mismo flujo de re-autenticación que una expiración de sesión a mitad de lote (ver §6 y ARCHITECTURE.md §7); (2) se confirma que el Portal 2 no requiere ninguna autenticación, es un formulario público protegido solo por ALTCHA; (3) se agrega la regla "Fallo de Integridad en la Primera Descarga" (§5) como criterio uniforme para los tres portales/documentos (Portal 1 del paciente, Portal 1 del titular, Portal 3); (4) se confirma que ya no existe un caso separado de "Rama A sin cédula del titular" — el Portal 3 solo se omite cuando el paciente ya quedó en un estado terminal de error (`ERROR_PORTAL_1` o `ERROR_PORTAL_2`), consecuencia directa de la máquina de estados de §4.