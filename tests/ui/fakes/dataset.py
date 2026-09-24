from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from app.application.dto import (
    CabeceraLote,
    ContadoresLote,
    ConteoEstado,
    DetallePaciente,
    EstadoLote,
    EstadoPaciente,
    EstadoPaso,
    ExpedienteConsolidado,
    FilaError,
    FilaPaciente,
    FilaRevision,
    MotivoDetencion,
    PasoRuta,
    Portal,
    PreviewLote,
    ProgresoLote,
    Rama,
    ResultadoEjecucion,
    ResumenLote,
    RutaPortales,
)

NOMBRES = (
    "Carlos Luis",
    "Maria Elena",
    "Jorge Anibal",
    "Monica Patricia",
    "Wilson Fernando",
    "Daniel Esteban",
    "Rosa Beatriz",
    "Gonzalo Dario",
    "Viviana Patricia",
    "Dario Alfonso",
    "Beatriz Eugenia",
    "Maria Fernanda",
    "Kevin Santiago",
    "Ruben Dario",
    "Segundo Agustin",
    "Hipatia Valeria",
    "Ana Lucia",
    "Pedro Pablo",
    "Sofia Alejandra",
    "Luis Alberto",
)
APELLIDOS = (
    "Mendoza Zambrano",
    "Alava Chavez",
    "Paredes Guaman",
    "Villacres Correa",
    "Lopez Caicedo",
    "Rodriguez Moran",
    "Cevallos Moreno",
    "Tapia Suarez",
    "Andrade Morales",
    "Chuquimarca Vela",
    "Alcivar Moreta",
    "Quishpe Andrade",
    "Naranjo Pilataxi",
    "Espinoza Cadena",
    "Toapanta Chimbo",
    "Tayupanta Guaman",
    "Vera Intriago",
    "Zambrano Lucero",
    "Salazar Ponce",
    "Bravo Cedeno",
)
SEGUROS = ("IESS", "Entidad Previsional Especial", "ISSFA", "ISSPOL")
ESTABLECIMIENTOS = (
    "Hosp. Teodoro Maldonado",
    "Clinica Guayaquil Norte",
    "Hosp. Metropolitano",
    "Centro Quirurgico Los Ceibos",
    "Hospital Central",
    "Pediatria Santa Clara",
    "Hosp. San Francisco",
    "Unidad Medica El Bosque",
)
MOTIVOS_DESCARTE = (
    "Cédula con 8 dígitos",
    "Cédula con 11 dígitos",
    "Cédula con 7 dígitos",
    "Cédula con 12 dígitos",
    "Cédula con caracteres no numéricos",
)

TOTAL_FILAS = 428
TOTAL_DESCARTADOS = 94
TOTAL_COMPLETADOS = 311
TOTAL_NO_ENCONTRADOS = 19
TOTAL_ERROR_PORTAL_3 = 4
TOTAL_LISTOS = TOTAL_COMPLETADOS + TOTAL_NO_ENCONTRADOS + TOTAL_ERROR_PORTAL_3
MENORES_DE_EDAD_LISTOS = 12

LOTE_ID = "2026-09-08-01"
ARCHIVO = "cartera_septiembre.xlsx"
FECHA_REFERENCIA = date(2026, 9, 8)


@dataclass(frozen=True, slots=True)
class PacienteSimulado:
    paciente_id: str
    fila_excel: int
    nombre: str
    cedula: str
    cedula_valida: bool
    motivo_descarte: str | None
    fecha_nacimiento: date
    edad: int
    seguro: str
    establecimiento: str
    rama: Rama | None
    seguro_derivado: bool | None
    estado: EstadoPaciente
    ruta: RutaPortales
    hora: datetime | None


def _longitud_por_motivo(motivo: str) -> int:
    for texto, longitud in (("7", 7), ("8", 8), ("11", 11), ("12", 12)):
        if f"con {texto} dígitos" in motivo:
            return longitud
    return 9


def _cedula_invalida(aleatorio: random.Random, indice: int) -> tuple[str, str]:
    motivo = MOTIVOS_DESCARTE[indice % len(MOTIVOS_DESCARTE)]
    if "caracteres no numéricos" in motivo:
        digitos = "".join(str(aleatorio.randint(0, 9)) for _ in range(9))
        return digitos + "A", motivo
    longitud = _longitud_por_motivo(motivo)
    cedula = "".join(str(aleatorio.randint(0, 9)) for _ in range(longitud))
    return cedula, motivo


def _cedula_valida(aleatorio: random.Random) -> str:
    return "".join(str(aleatorio.randint(0, 9)) for _ in range(10))


def _fecha_nacimiento(
    aleatorio: random.Random, menor_de_edad: bool
) -> tuple[date, int]:
    hoy = FECHA_REFERENCIA
    edad = aleatorio.randint(1, 17) if menor_de_edad else aleatorio.randint(18, 90)
    fecha = date(hoy.year - edad, aleatorio.randint(1, 12), aleatorio.randint(1, 28))
    if fecha > hoy:
        fecha = fecha.replace(year=fecha.year - 1)
    return fecha, edad


def _ruta_y_hora(
    aleatorio: random.Random,
    estado: EstadoPaciente,
    rama: Rama,
    hora_base: datetime,
    indice: int,
) -> tuple[RutaPortales, datetime]:
    hora = hora_base + timedelta(seconds=indice * 7)
    paso_p2 = EstadoPaso.OMITIDO if rama is Rama.B else EstadoPaso.RESUELTO
    if estado is EstadoPaciente.COMPLETADO:
        return RutaPortales(EstadoPaso.RESUELTO, paso_p2, EstadoPaso.RESUELTO), hora
    if estado is EstadoPaciente.NO_ENCONTRADO:
        return RutaPortales(
            EstadoPaso.FALLIDO, EstadoPaso.PENDIENTE, EstadoPaso.PENDIENTE
        ), hora
    return RutaPortales(EstadoPaso.RESUELTO, paso_p2, EstadoPaso.FALLIDO), hora


def _generar_pacientes() -> tuple[PacienteSimulado, ...]:
    aleatorio = random.Random(2026)
    pacientes: list[PacienteSimulado] = []
    hora_base = datetime(2026, 9, 8, 14, 0, 0)
    fila_excel = 14

    for indice in range(TOTAL_DESCARTADOS):
        cedula, motivo = _cedula_invalida(aleatorio, indice)
        fecha_nacimiento, edad = _fecha_nacimiento(aleatorio, menor_de_edad=False)
        nombre = f"{aleatorio.choice(APELLIDOS)} {aleatorio.choice(NOMBRES)}"
        pacientes.append(
            PacienteSimulado(
                paciente_id=f"P{fila_excel:04d}",
                fila_excel=fila_excel,
                nombre=nombre,
                cedula=cedula,
                cedula_valida=False,
                motivo_descarte=motivo,
                fecha_nacimiento=fecha_nacimiento,
                edad=edad,
                seguro=aleatorio.choice(SEGUROS),
                establecimiento=aleatorio.choice(ESTABLECIMIENTOS),
                rama=None,
                seguro_derivado=None,
                estado=EstadoPaciente.CEDULA_INVALIDA,
                ruta=RutaPortales(
                    EstadoPaso.PENDIENTE, EstadoPaso.PENDIENTE, EstadoPaso.PENDIENTE
                ),
                hora=None,
            )
        )
        fila_excel += aleatorio.randint(2, 5)

    resultados_listos = (
        [EstadoPaciente.COMPLETADO] * TOTAL_COMPLETADOS
        + [EstadoPaciente.NO_ENCONTRADO] * TOTAL_NO_ENCONTRADOS
        + [EstadoPaciente.ERROR_PORTAL_3] * TOTAL_ERROR_PORTAL_3
    )
    aleatorio.shuffle(resultados_listos)

    for indice, estado in enumerate(resultados_listos):
        menor_de_edad = indice < MENORES_DE_EDAD_LISTOS
        fecha_nacimiento, edad = _fecha_nacimiento(aleatorio, menor_de_edad)
        nombre = f"{aleatorio.choice(APELLIDOS)} {aleatorio.choice(NOMBRES)}"
        rama = aleatorio.choice((Rama.A, Rama.B))
        seguro_derivado = aleatorio.random() < 0.3 if rama is Rama.A else None
        ruta, hora = _ruta_y_hora(aleatorio, estado, rama, hora_base, indice)
        pacientes.append(
            PacienteSimulado(
                paciente_id=f"P{fila_excel:04d}",
                fila_excel=fila_excel,
                nombre=nombre,
                cedula=_cedula_valida(aleatorio),
                cedula_valida=True,
                motivo_descarte=None,
                fecha_nacimiento=fecha_nacimiento,
                edad=edad,
                seguro=aleatorio.choice(SEGUROS),
                establecimiento=aleatorio.choice(ESTABLECIMIENTOS),
                rama=rama,
                seguro_derivado=seguro_derivado,
                estado=estado,
                ruta=ruta,
                hora=hora,
            )
        )
        fila_excel += aleatorio.randint(2, 5)

    return tuple(pacientes)


PACIENTES_SIMULADOS: tuple[PacienteSimulado, ...] = _generar_pacientes()


def cabecera_simulada(estado: EstadoLote = EstadoLote.SIN_INICIAR) -> CabeceraLote:
    return CabeceraLote(
        lote_id=LOTE_ID, archivo=ARCHIVO, total_filas=TOTAL_FILAS, estado=estado
    )


def _fila_revision(paciente: PacienteSimulado) -> FilaRevision:
    return FilaRevision(
        fila_excel=paciente.fila_excel,
        nombre=paciente.nombre,
        cedula=paciente.cedula,
        fecha_nacimiento=paciente.fecha_nacimiento,
        edad=paciente.edad,
        seguro=paciente.seguro,
        establecimiento=paciente.establecimiento,
        motivo_descarte=paciente.motivo_descarte,
    )


def preview_lote_simulado() -> PreviewLote:
    listos = tuple(_fila_revision(p) for p in PACIENTES_SIMULADOS if p.cedula_valida)
    descartados = tuple(
        _fila_revision(p) for p in PACIENTES_SIMULADOS if not p.cedula_valida
    )
    return PreviewLote(
        cabecera=cabecera_simulada(),
        listos=listos,
        descartados=descartados,
        menores_de_edad_listos=MENORES_DE_EDAD_LISTOS,
    )


def _fila_paciente(paciente: PacienteSimulado) -> FilaPaciente:
    return FilaPaciente(
        paciente_id=paciente.paciente_id,
        nombre=paciente.nombre,
        cedula=paciente.cedula,
        edad=paciente.edad,
        rama=paciente.rama,
        seguro_derivado=paciente.seguro_derivado,
        ruta=paciente.ruta,
        estado=paciente.estado,
        hora=paciente.hora,
    )


def filas_paciente_simuladas() -> tuple[FilaPaciente, ...]:
    return tuple(_fila_paciente(p) for p in PACIENTES_SIMULADOS)


def contadores_simulados() -> ContadoresLote:
    return ContadoresLote(
        total=TOTAL_FILAS,
        completados=TOTAL_COMPLETADOS,
        invalidos=TOTAL_DESCARTADOS + TOTAL_NO_ENCONTRADOS,
        en_proceso=0,
        pendientes=0,
        con_error=TOTAL_ERROR_PORTAL_3,
    )


def progreso_simulado() -> ProgresoLote:
    return ProgresoLote(
        procesados=TOTAL_FILAS,
        total=TOTAL_FILAS,
        portal_actual=None,
        contadores=contadores_simulados(),
    )


def _titular_derivado(cedula_propia: str) -> str:
    generador = random.Random(cedula_propia)
    return "".join(str(generador.randint(0, 9)) for _ in range(10))


def _nombre_expediente(paciente: PacienteSimulado) -> str:
    nombre_normalizado = paciente.nombre.upper().replace(",", "").replace(" ", "_")
    return f"{nombre_normalizado}_{paciente.cedula}.pdf"


def detalle_simulado(paciente_id: str) -> DetallePaciente:
    paciente = next(p for p in PACIENTES_SIMULADOS if p.paciente_id == paciente_id)
    fila = _fila_paciente(paciente)
    hora = paciente.hora or datetime(2026, 9, 8, 14, 0, 0)

    if paciente.estado is EstadoPaciente.CEDULA_INVALIDA:
        return DetallePaciente(
            fila=fila,
            cedula_titular=None,
            cobertura=None,
            pasos=(),
            expediente=None,
            reprocesable=False,
        )

    if paciente.estado is EstadoPaciente.NO_ENCONTRADO:
        pasos_no_encontrado = (
            PasoRuta(
                Portal.P1,
                "Portal 1 · Coberturas",
                hora,
                None,
                "sin cobertura registrada",
            ),
        )
        return DetallePaciente(
            fila=fila,
            cedula_titular=None,
            cobertura=None,
            pasos=pasos_no_encontrado,
            expediente=None,
            reprocesable=False,
        )

    cedula_titular = (
        _titular_derivado(paciente.cedula) if paciente.seguro_derivado else None
    )
    pasos = [PasoRuta(Portal.P1, "Portal 1 · Coberturas", hora, 214, None)]
    if paciente.rama is Rama.A:
        nota_p2 = "seguro derivado detectado" if paciente.seguro_derivado else None
        pasos.append(
            PasoRuta(
                Portal.P2,
                "Portal 2 · Validación",
                hora + timedelta(seconds=14),
                None if nota_p2 else 180,
                nota_p2,
            )
        )
        if cedula_titular is not None:
            pasos.append(
                PasoRuta(
                    Portal.P1,
                    f"Portal 1 (titular {cedula_titular})",
                    hora + timedelta(seconds=27),
                    208,
                    None,
                )
            )

    if paciente.estado is EstadoPaciente.ERROR_PORTAL_3:
        pasos.append(
            PasoRuta(
                Portal.P3,
                "Portal 3 · Destino",
                hora + timedelta(seconds=48),
                None,
                "sin respuesta del portal",
            )
        )
        return DetallePaciente(
            fila=fila,
            cedula_titular=cedula_titular,
            cobertura=paciente.seguro,
            pasos=tuple(pasos),
            expediente=None,
            reprocesable=True,
        )

    pasos.append(
        PasoRuta(
            Portal.P3, "Portal 3 · Destino", hora + timedelta(seconds=48), 96, None
        )
    )
    documentos = sum(1 for paso in pasos if paso.tamano_kb is not None)
    tamano_total = sum(paso.tamano_kb for paso in pasos if paso.tamano_kb is not None)
    expediente = ExpedienteConsolidado(
        nombre_archivo=_nombre_expediente(paciente),
        documentos=documentos,
        tamano_kb=tamano_total,
        ruta=Path("data/pdf_exports/2026-09") / _nombre_expediente(paciente),
    )
    return DetallePaciente(
        fila=fila,
        cedula_titular=cedula_titular,
        cobertura=paciente.seguro,
        pasos=tuple(pasos),
        expediente=expediente,
        reprocesable=False,
    )


_ESTADOS_RESUMEN = (
    EstadoPaciente.COMPLETADO,
    EstadoPaciente.CEDULA_INVALIDA,
    EstadoPaciente.NO_ENCONTRADO,
    EstadoPaciente.ERROR_PORTAL_1,
    EstadoPaciente.ERROR_PORTAL_2,
    EstadoPaciente.ERROR_PORTAL_3,
)
_ESTADOS_SIN_RAMA = (EstadoPaciente.CEDULA_INVALIDA, EstadoPaciente.NO_ENCONTRADO)
HORA_INICIO_LOTE = datetime(2026, 9, 8, 8, 32, 0)
HORA_FIN_LOTE = datetime(2026, 9, 8, 11, 47, 0)


def _conteos_por_estado() -> tuple[ConteoEstado, ...]:
    conteos = []
    for estado in _ESTADOS_RESUMEN:
        pacientes_estado = tuple(p for p in PACIENTES_SIMULADOS if p.estado is estado)
        if estado in _ESTADOS_SIN_RAMA:
            rama_a: int | None = None
            rama_b: int | None = None
        else:
            rama_a = sum(1 for p in pacientes_estado if p.rama is Rama.A)
            rama_b = sum(1 for p in pacientes_estado if p.rama is Rama.B)
        conteos.append(
            ConteoEstado(
                estado=estado, total=len(pacientes_estado), rama_a=rama_a, rama_b=rama_b
            )
        )
    return tuple(conteos)


def resumen_lote_simulado(incompleto: bool = False) -> ResumenLote:
    conteos = _conteos_por_estado()
    total = sum(conteo.total for conteo in conteos)
    filas_en_rojo = total - TOTAL_COMPLETADOS
    return ResumenLote(
        cabecera=cabecera_simulada(
            EstadoLote.DETENIDO if incompleto else EstadoLote.FINALIZADO
        ),
        procesados=total,
        pendientes=0,
        conteos=conteos,
        hora_inicio=HORA_INICIO_LOTE,
        hora_fin=None if incompleto else HORA_FIN_LOTE,
        duracion=None if incompleto else (HORA_FIN_LOTE - HORA_INICIO_LOTE),
        filas_en_rojo=filas_en_rojo,
        expedientes_consolidados=TOTAL_COMPLETADOS,
        incompleto=incompleto,
    )


def resultado_detenido_simulado() -> ResultadoEjecucion:
    return ResultadoEjecucion(
        estado_lote=EstadoLote.DETENIDO,
        motivo_detencion=MotivoDetencion.SESION_EXPIRADA,
        resumen=resumen_lote_simulado(incompleto=True),
    )


MOTIVOS_ERROR_PORTAL_3 = (
    "Tiempo de espera agotado",
    "Conexión interrumpida al transferir el PDF",
    "Respuesta incompleta",
    "Conexión rechazada",
)


def errores_simulados() -> tuple[FilaError, ...]:
    pacientes = tuple(
        p for p in PACIENTES_SIMULADOS if p.estado is EstadoPaciente.ERROR_PORTAL_3
    )
    errores = []
    for indice, paciente in enumerate(pacientes):
        errores.append(
            FilaError(
                paciente_id=paciente.paciente_id,
                nombre=paciente.nombre,
                cedula=paciente.cedula,
                portal_fallido=Portal.P3,
                motivo=MOTIVOS_ERROR_PORTAL_3[indice % len(MOTIVOS_ERROR_PORTAL_3)],
                intentos=3,
                intentos_maximos=3,
                ultimo_intento=paciente.hora or HORA_INICIO_LOTE,
                estado=paciente.estado,
            )
        )
    return tuple(errores)
