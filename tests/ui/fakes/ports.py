from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import (
    AccionOperador,
    DecisionOperador,
    DetallePaciente,
    FilaError,
    PreviewLote,
    ResultadoEntregables,
    ResumenLote,
    SeleccionEntregables,
    SesionUsuario,
    SolicitudOperador,
)
from app.application.ui_ports import (
    IBatchIntake,
    IBatchSummaryQuery,
    IDeliverablesExporter,
    IErrorListQuery,
    ILocalAuthenticator,
    IOperatorGate,
    IOutputFolderSettings,
    IPatientDetailQuery,
)
from tests.ui.fakes.dataset import (
    detalle_simulado,
    errores_simulados,
    preview_lote_simulado,
    resumen_lote_simulado,
)

CREDENCIALES_VALIDAS: dict[str, str] = {
    "admision.01": "lux2026",
}


class FakeLocalAuthenticator(ILocalAuthenticator):
    def __init__(self, credenciales: dict[str, str] | None = None) -> None:
        self._credenciales = (
            credenciales if credenciales is not None else dict(CREDENCIALES_VALIDAS)
        )

    def autenticar(self, usuario: str, contrasena: str) -> SesionUsuario | None:
        esperada = self._credenciales.get(usuario)
        if esperada is None or esperada != contrasena:
            return None
        iniciales = "".join(
            parte[0] for parte in usuario.replace(".", " ").split()[:2]
        ).upper()
        return SesionUsuario(
            usuario=usuario, iniciales=iniciales or usuario[:2].upper()
        )


class FakeBatchIntake(IBatchIntake):
    def leer_listado(self, ruta: Path) -> PreviewLote:
        return preview_lote_simulado()


class FakeOperatorGate(IOperatorGate):
    def __init__(self) -> None:
        self.solicitudes: list[SolicitudOperador] = []
        self.cierres: list[AccionOperador] = []
        self._decision: DecisionOperador | None = None

    def resolver_con(self, decision: DecisionOperador | None) -> None:
        self._decision = decision

    def solicitar(self, solicitud: SolicitudOperador) -> None:
        self.solicitudes.append(solicitud)

    def esperar(
        self,
        accion: AccionOperador,
        resuelto: Callable[[], bool],
    ) -> DecisionOperador | None:
        return self._decision

    def cerrar(self, accion: AccionOperador) -> None:
        self.cierres.append(accion)


class FakePatientDetailQuery(IPatientDetailQuery):
    def detalle(self, paciente_id: str) -> DetallePaciente:
        return detalle_simulado(paciente_id)


class FakeBatchSummaryQuery(IBatchSummaryQuery):
    def __init__(self, incompleto: bool = False) -> None:
        self._incompleto = incompleto

    def resumen_actual(self) -> ResumenLote:
        return resumen_lote_simulado(incompleto=self._incompleto)


class FakeOutputFolderSettings(IOutputFolderSettings):
    def __init__(self, carpeta_inicial: Path | None = None) -> None:
        self._carpeta = carpeta_inicial or Path("D:/LuxMed/salidas/2026-09")

    def obtener(self) -> Path:
        return self._carpeta

    def guardar(self, carpeta: Path) -> None:
        self._carpeta = carpeta


class FakeDeliverablesExporter(IDeliverablesExporter):
    def __init__(self) -> None:
        self.exportaciones: list[SeleccionEntregables] = []

    def exportar(self, seleccion: SeleccionEntregables) -> ResultadoEntregables:
        self.exportaciones.append(seleccion)
        resumen = resumen_lote_simulado()
        return ResultadoEntregables(
            carpeta=seleccion.carpeta_destino,
            filas_excel=resumen.cabecera.total_filas,
            filas_en_rojo=resumen.filas_en_rojo,
            expedientes_generados=resumen.expedientes_consolidados
            if seleccion.expedientes
            else 0,
        )


class FakeErrorListQuery(IErrorListQuery):
    def errores_pendientes(self) -> tuple[FilaError, ...]:
        return errores_simulados()
