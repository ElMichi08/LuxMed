# business-rules.md · Reglas de Negocio de LuxMed 📋

> **Ecosistema de Operación:** Auditoría y Verificación Médica On-Premise  
> **Ámbito de Aplicación:** Flujo de Admisión y Validación de Coberturas (Ecuador)  
> **Versión de las Reglas:** 1.0.0 (Vigente a partir del 01/09/2026)

---

## 1. Propósito y Glosario (Context & Ubiquitous Language)

### Objetivo
Este documento constituye la fuente única de la verdad operativa para el sistema LuxMed. Traduce los requerimientos legales, administrativos y de auditoría de los establecimientos de salud en directrices lógicas estrictas. Su propósito es regular la ingesta de listados de pacientes, dictar el comportamiento de las consultas vehiculizadas en portales públicos ecuatorianos y normar la consolidación de expedientes para la optimización del tiempo de consulta del médico.

### Glosario de Términos (Lenguaje Ubicuo)
- **Paciente Ingestado:** Registro de un ciudadano extraído de una fila de un libro de Excel que se encuentra en proceso de carga inicial, antes de ser verificado.
- **Paciente Válido:** Ciudadano cuya identidad estructural es correcta (cédula legítima) y que posee cobertura activa demostrable en al menos una entidad previsional de salud en el Portal de Coberturas.
- **Paciente Inválido:** Registro que ha sido rechazado administrativamente debido a errores en sus datos de identidad, minoría de edad sin amparo de seguro, o por reportar ausencia total de cobertura en las entidades auditadas.
- **Portal de Coberturas (P_1):** Plataforma oficial del Ministerio de Salud Pública (MSP) utilizada para auditar el aseguramiento ciudadano en tiempo real.
- **Portal de Validación Secundaria (P_2):** Plataforma técnica transaccional intermedia cuyo uso es mandatorio únicamente para los afiliados al Seguro General.
- **Portal de Destino Técnico (P_3):** Plataforma final de consolidación clínica e historial médico de la institución.
- **Entidad Previsional:** Institución pública encargada de la seguridad social del ciudadano (IESS, ISSFA o ISSPOL).
- **Reporte de Auditoría (Excel Espejo):** Documento de salida idéntico al original, modificado visualmente para resaltar con color de alerta las inconsistencias de los datos de la clínica frente a la realidad del portal.
- **Expediente Consolidado:** Archivo digital único en formato PDF que unifica de forma secuencial los soportes binarios emitidos por los portales para un paciente válido.

---

## 2. Clasificación de Reglas (Core Rules)

### Reglas de Restricción (Invariantes del Sistema)
- **Ecuación de Identidad Obligatoria:** Si la cédula de un paciente no supera la validación matemática del algoritmo del coeficiente 2-1-2 (dígito verificador de Ecuador) o posee una longitud distinta a 10 dígitos, entonces el paciente debe ser clasificado inmediatamente como **Inválido**.
- **Protección de Minoridad No Asegurada:** Si un paciente es menor de edad (menor a 18 años calculado en base a su fecha de nacimiento) y el Portal de Coberturas dictamina que no posee afiliación activa en ninguna entidad previsional, entonces el sistema debe prohibir su avance y marcarlo como **Inválido**.
- **Aislamiento de Almacenamiento On-Premise:** Los registros de salud e identificadores personales procesados nunca deben ser transmitidos a servidores web externos a la máquina local de la clínica.

### Reglas de Derivación (Cálculos y Transformaciones)
- **Cálculo Inmutable de Edad:** La edad biológica del paciente no se lee de forma estática del Excel. El sistema debe tomar la fecha de nacimiento (Columna E) y restarla de la fecha natural del sistema operativo de la máquina local en el microsegundo de la ingesta para derivar un número entero inmutable.
- **Indexación Unívoca de Expedientes:** El nombre del archivo PDF consolidado de salida debe construirse obligatoriamente concatenando la Cédula (Columna C) y el Nombre del Paciente (Columna B) bajo la estructura plana: `[CÉDULA]_[NOMBRE]_REPORT.pdf`. Está prohibida la creación de subcarpetas profundas por nombre de paciente para evitar la saturación del sistema de archivos de Windows.

### Reglas de Reacción (Disparadores de Eventos)
- **Disparador de Alerta de Auditoría:** Si los datos de filiación del Excel difieren de la información oficial devuelta por los portales de salud, entonces el sistema debe marcar internamente el registro con la propiedad `es_auditoria_rojo = True` para su posterior tintura visual en el Excel de salida.
- **Captura Binaria Directa:** En el instante en que el Portal de Coberturas previsualice el acta médica en pantalla, entonces el sistema debe interceptar la respuesta de la red y capturar los bytes del archivo PDF directamente en la memoria RAM, abortando el uso de la ventana física de descargas del sistema operativo.

---

## 3. Matriz de Decisiones (Tablas de Verdad de Coberturas)

El comportamiento de la navegación automatizada y el direccionamiento del paciente a través de los flujos de portales web depende estrictamente de las variables de aseguramiento cruzadas detectadas en el Portal de Coberturas (P₁):

| Validación Estructural (C) | Condición de Minoridad (E) | Cobertura IESS | Cobertura ISSFA | Cobertura ISSPOL | Estado Final del Paciente | Ruta de Flujo Operativo | Alerta Visual en Excel (Auditoría) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Incorrecta (Falla 2-1-2) | Cualquier Edad | No aplica | No aplica | No aplica | **INVÁLIDO** | Fin de Flujo inmediato | Pintar Fila en Rojo |
| Correcta | Menor de Edad (< 18) | NO | NO | NO | **INVÁLIDO** | Fin de Flujo inmediato | Pintar Fila en Rojo |
| Correcta | Mayor de Edad (≥ 18) | NO | NO | NO | **INVÁLIDO** | Fin de Flujo inmediato | Pintar Fila en Rojo |
| Correcta | Cualquier Edad | NO | SÍ | NO | **VÁLIDO** | Salta Directo a Portal 3 | Conservar Color Original |
| Correcta | Cualquier Edad | NO | NO | SÍ | **VÁLIDO** | Salta Directo a Portal 3 | Conservar Color Original |
| Correcta | Cualquier Edad | SÍ | NO | NO | **VÁLIDO** | Pasa por Portal 2, luego a Portal 3 | Conservar Color Original |
| Correcta | Cualquier Edad | SÍ | SÍ | SÍ o Cualquier Edo. | **VÁLIDO** | Prioriza ISSFA/ISSPOL: Salta a Portal 3 | Pintar Celda en Rojo (Diferido) |

---

## 4. Flujos de Trabajo y Estados (State Machines)

El ciclo de vida de un Paciente dentro del sistema LuxMed está rígidamente secuenciado. Está estrictamente prohibido omitir estados o realizar saltos de transición no autorizados por las reglas de negocio.

```text
 [ INGESTADO ] ──────► [ HIGIENIZADO ] ──────► [ EN_PROCESO ] ──────► [ PROCESADO_VÁLIDO ]
       │                      │                       │                      │
       │                      ▼                       ▼                      ▼
       └──────────────► [ RECHAZADO_INV ]       [ RECHAZADO_INV ]      [ EXPORTADO_DUAL ]
```

### Transiciones Válidas y Eventos Disparadores
- **`INGESTADO` ➔ `HIGIENIZADO`:** Ocurre de forma automática cuando Pandas aísla las columnas B, C, E, G, H, M y el componente Validator ratifica la estructura de la cédula y deriva la edad.
- **`INGESTADO` / `HIGIENIZADO` ➔ `RECHAZADO_INVÁLIDO`:** Ocurre si falla el dígito verificador 2-1-2 o si se detecta un menor de edad sin amparo previsional. El registro se congela y se prepara para el reporte rojo.
- **`HIGIENIZADO` ➔ `EN_PROCESO`:** Ocurre cuando el operador presiona el botón de inicio de campaña y el registro entra a la cola activa del hilo secundario de Playwright.
- **`EN_PROCESO` ➔ `RECHAZADO_INVÁLIDO`:** Se dispara si en el Portal de Coberturas (P₁) las tres entidades (IESS, ISSFA, ISSPOL) devuelven explícitamente el mensaje de texto "no registra cobertura".
- **`EN_PROCESO` ➔ `PROCESADO_VÁLIDO`:** Se activa cuando el paciente completa con éxito su ruta asignada de portales (según la Matriz de Decisiones), habiendo capturado en memoria el 100% de los bytes de los PDFs requeridos.
- **`PROCESADO_VÁLIDO` ➔ `EXPORTADO_DUAL`:** Estado de cierre del ciclo de vida del lote. Se dispara cuando el usuario hace uso de los botones finales del Dashboard, generando el PDF consolidado único y los dos libros de Excel (Limpio y Auditado con Celdas Rojas).

### Transiciones Prohibidas (Blindaje de Datos)
- Está prohibido pasar de `INGESTADO` a `EN_PROCESO` sin pasar por la validación estructural de `HIGIENIZADO`.
- Está prohibido pasar de `EN_PROCESO` a `PROCESADO_VÁLIDO` si falta el flujo binario de soporte de al menos un portal obligatorio de su ruta.

---

## 5. Excepciones y Manejo de Errores Operativos (Edge Cases)

- **Caída de Servicio o Intermitencia en un Portal Web Externo:**  
  Si un portal gubernamental deja de responder o genera un error de red a mitad del procesamiento de un paciente válido, entonces el sistema debe reintentar la carga un máximo de 3 veces con esperas exponenciales pasivas. Si el fallo persiste, el paciente se marcará en estado `PENDIENTE_ERROR`, liberando el hilo para no detener la cola de la clínica, y permitiendo al doctor re-procesar únicamente a los caídos al final del día.

- **Doble Afiliación Simultánea en el Portal (IESS + Fuerza Armada):**  
  Si un paciente reporta afiliación activa en el IESS y simultáneamente en el ISSFA o ISSPOL, entonces por orden de optimización de tiempos clínicos, la regla de negocio dictamina priorizar las Fuerzas Armadas: el bot omitirá el Portal 2, saltará directo al Portal 3, y marcará la celda del seguro previo en el Excel de Auditoría en color de advertencia para alertar al departamento de facturación de la clínica.

---

## 6. Control de Versiones e Historial de Cambios (Audit & Versioning)

- **01/09/2026 (Versión 1.0.0):**  
  Cierre y congelación de las reglas operativas iniciales del sistema LuxMed para su despliegue On-Premise. Se implementa el árbol de decisiones de tres portales, la captura de PDFs indexados por formato de cédula plano en memoria RAM y el Entregable Dual (Excel Espejo con openpyxl + Excel Limpio).