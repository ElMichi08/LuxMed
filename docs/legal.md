# Apéndice legal — Capas pendientes fuera del software

> **Origen:** este contenido vivía como Apéndice B de `Requisitos.MD` (v1.0), archivo eliminado del repositorio por decisión del propietario — su comportamiento ya está cubierto por `docs/BDD/*.feature`. Este apéndice se rescata aquí porque no tenía equivalente en ningún otro documento (a diferencia del Preámbulo de invariantes y el Apéndice A de stack, que ya estaban duplicados en `CLAUDE.md`).
>
> Estas **NO** son comportamiento del sistema — no se traducen a código ni a checks automatizados (ver `CLAUDE.md`, sección "Invariantes de diseño"). Son condiciones que deben existir fuera del software para poder operar con datos reales de pacientes.

1. **Persona jurídica** — interpone responsabilidad; prerrequisito para facturar y contratar.
2. **Autorización de acceso a las 3 fuentes** — convenio/acuerdo solicitado por el hospital, no por el proveedor. Camino crítico. Incluye consulta formal a la Superintendencia de Protección de Datos Personales describiendo la arquitectura.
3. **Cumplimiento LOPDP como encargado** — contrato de encargo, evaluación de impacto (EIPD) obligatoria por tratarse de categorías especiales a gran escala, delegado de protección de datos, inscripción en Registro Nacional, procedimiento de notificación de brechas.
4. **Habilitación como proveedor del Estado** — RUP (SERCOP), códigos CPC de software, Acuerdo de Integridad.
5. **Contratos y propiedad intelectual** — licencia vs. transferencia de titularidad, SLA, cláusula de auditoría, seguro de responsabilidad civil profesional.

> Todo este apéndice requiere validación de un abogado ecuatoriano especializado en LOPDP y contratación pública. Este documento es lectura de la norma y diseño, no asesoría legal.

## Nota adicional sobre Rama A (también rescatada de `Requisitos.MD`)

En la Rama A el paciente es un menor de edad o afiliado por un tercero, y el sistema maneja datos del **titular adulto** (representante) a partir de la cédula del menor. Esto encadena dos titulares de datos distintos. La base de legitimidad y el consentimiento del representante son responsabilidad del hospital (responsable del tratamiento) y deben existir ANTES de procesar datos reales.
