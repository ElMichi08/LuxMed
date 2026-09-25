from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from app.application.lote_service import (
    Entregables,
    ErrorPrecondicion,
    RevisionLote,
    ServicioLote,
)
from app.application.progreso import ResumenLote
from app.domain.entities import CredencialesPortal3
from app.domain.ports import IConfiguracionRepository
from app.infrastructure.ui.guards import AccionUnica
from app.infrastructure.ui.log_bridge import ArchivoLogLote, EmisorLog, LineaLog
from app.infrastructure.ui.shell.main_window import MainWindow, PaginaLote, Seccion
from app.infrastructure.ui.threads import BatchRunnerThread, TaskThread

logger = logging.getLogger(__name__)

Respuesta = QMessageBox.StandardButton


class LoteController(QObject):
    cierre_listo = pyqtSignal()

    def __init__(
        self,
        servicio: ServicioLote,
        configuracion: IConfiguracionRepository,
        ventana: MainWindow,
        emisor_log: EmisorLog,
        carpeta_logs: Path,
    ) -> None:
        super().__init__(ventana)
        self._servicio = servicio
        self._configuracion = configuracion
        self._v = ventana
        self._archivo_log = ArchivoLogLote(carpeta_logs)
        self._tareas: set[TaskThread] = set()
        self._runner: BatchRunnerThread | None = None
        self._revision: RevisionLote | None = None
        self._cerrando = False

        dropzone = ventana.upload.dropzone
        self._accion_cargar = AccionUnica([dropzone.boton], "Leyendo…", [dropzone], self)
        self._accion_iniciar = AccionUnica(
            [ventana.review.boton_iniciar], "Iniciando…", [ventana.review.boton_descartar], self
        )
        self._accion_entregables = AccionUnica(
            [ventana.processing.boton_entregables, ventana.summary.boton_entregables], "Generando…", parent=self
        )
        self._accion_credenciales = AccionUnica([ventana.settings.boton_guardar], "Guardando…", parent=self)

        dropzone.archivo_elegido.connect(self._cargar_listado)
        ventana.review.boton_iniciar.clicked.connect(self._iniciar_campana)
        ventana.review.boton_descartar.clicked.connect(self._descartar_lote)
        ventana.processing.boton_entregables.clicked.connect(self._generar_entregables)
        ventana.processing.primer_avance.connect(ventana.overlay.ocultar)
        ventana.summary.boton_entregables.clicked.connect(self._generar_entregables)
        ventana.summary.boton_nuevo.clicked.connect(self._nuevo_lote)
        ventana.summary.boton_detalle.clicked.connect(lambda: ventana.ir_a_lote(PaginaLote.PROCESO))
        ventana.settings.carpeta_cambiada.connect(self._cambiar_carpeta)
        ventana.settings.credenciales_guardadas.connect(self._guardar_credenciales)
        emisor_log.linea.connect(self._recibir_log)
        ventana.establecer_confirmacion_cierre(self.solicitar_cierre)
        self.cierre_listo.connect(ventana.close)

        ventana.settings.mostrar_carpeta(configuracion.obtener_carpeta_salida())
        ventana.settings.mostrar_credenciales(configuracion.obtener_credenciales_portal3())

    @property
    def lote_en_curso(self) -> bool:
        return self._runner is not None

    def _cargar_listado(self, ruta: str) -> None:
        if self.lote_en_curso or not self._accion_cargar.intentar():
            return
        self._v.overlay.mostrar("Leyendo el listado", Path(ruta).name)
        self._en_segundo_plano(
            lambda: self._servicio.cargar_listado(ruta), self._listado_cargado, self._listado_fallido
        )

    def _listado_cargado(self, revision: object) -> None:
        assert isinstance(revision, RevisionLote)
        self._terminar_espera(self._accion_cargar)
        self._revision = revision
        self._v.review.mostrar(revision)
        self._v.top_bar.mostrar_lote(revision.nombre_archivo, revision.lote_id, len(revision.filas))
        self._v.top_bar.mostrar_estado("Sin iniciar", "neutro")
        self._v.logs.mostrar_sesion(revision.lote_id)
        self._accion_iniciar.establecer_habilitada(bool(revision.listos))
        self._v.ir_a_lote(PaginaLote.REVISION)

    def _listado_fallido(self, mensaje: str) -> None:
        self._terminar_espera(self._accion_cargar)
        self._v.upload.dropzone.mostrar_error(mensaje)

    def _iniciar_campana(self) -> None:
        revision = self._revision
        if revision is None or self.lote_en_curso or not self._accion_iniciar.intentar():
            return
        try:
            self._servicio.verificar_precondiciones()
        except ErrorPrecondicion as error:
            self._accion_iniciar.liberar()
            self._avisar_precondicion(str(error))
            return
        self._v.logs.mostrar_archivo(str(self._archivo_log.abrir(revision.lote_id)))
        self._v.processing.iniciar(revision)
        self._v.settings.boton_carpeta.setEnabled(False)
        self._accion_entregables.establecer_habilitada(False)
        self._v.top_bar.mostrar_estado("En curso", "proceso")
        self._v.ir_a_lote(PaginaLote.PROCESO)
        self._v.overlay.mostrar("Iniciando campaña", "Preparando el navegador para el primer paciente…")
        runner = BatchRunnerThread(lambda observador: self._servicio.ejecutar(revision, observador), self)
        runner.patient_updated.connect(self._v.processing.aplicar_avance)
        runner.batch_ended.connect(self._lote_terminado)
        runner.batch_failed.connect(self._lote_fallido)
        runner.finished.connect(self._runner_finalizado)
        self._runner = runner
        runner.start()

    def _lote_terminado(self, resumen: object) -> None:
        assert isinstance(resumen, ResumenLote) and self._revision is not None
        self._v.processing.finalizar()
        self._v.summary.mostrar(self._revision, resumen)
        detenido = resumen.detenido
        self._v.top_bar.mostrar_estado("Detenido" if detenido else "Finalizado", "alerta" if detenido else "exito")
        self._accion_entregables.establecer_habilitada(True)
        if not self._cerrando:
            self._v.ir_a_lote(PaginaLote.RESUMEN)

    def _lote_fallido(self, mensaje: str) -> None:
        self._v.processing.finalizar()
        self._v.top_bar.mostrar_estado("Con error", "alerta")
        if not self._cerrando:
            QMessageBox.critical(self._v, "No se pudo completar el lote", mensaje)
            self._v.ir_a_lote(PaginaLote.REVISION)

    def _runner_finalizado(self) -> None:
        self._runner = None
        self._archivo_log.cerrar()
        self._v.overlay.ocultar()
        self._v.settings.boton_carpeta.setEnabled(True)
        self._accion_iniciar.liberar()
        if self._cerrando:
            self.cierre_listo.emit()

    def _generar_entregables(self) -> None:
        revision = self._revision
        if revision is None or self.lote_en_curso or not self._accion_entregables.intentar():
            return
        self._v.overlay.mostrar("Generando entregables", "Escribiendo el Excel limpio y el Excel auditado…")
        self._en_segundo_plano(
            lambda: self._servicio.generar_entregables(revision),
            self._entregables_generados,
            self._entregables_fallidos,
        )

    def _entregables_generados(self, entregables: object) -> None:
        assert isinstance(entregables, Entregables)
        self._terminar_espera(self._accion_entregables)
        self._v.summary.mostrar_entregables(entregables)
        self._v.ir_a_lote(PaginaLote.RESUMEN)

    def _entregables_fallidos(self, mensaje: str) -> None:
        self._terminar_espera(self._accion_entregables)
        QMessageBox.critical(self._v, "No se pudieron generar los entregables", mensaje)

    def _descartar_lote(self) -> None:
        if self.lote_en_curso or self._revision is None:
            return
        respuesta = QMessageBox.question(
            self._v,
            "Descartar lote",
            "¿Descartar este listado? Podrás cargar otro archivo.",
            Respuesta.Yes | Respuesta.No,
            Respuesta.No,
        )
        if respuesta == Respuesta.Yes:
            self._nuevo_lote()

    def _nuevo_lote(self) -> None:
        if self.lote_en_curso:
            return
        self._revision = None
        self._v.top_bar.limpiar()
        self._v.logs.mostrar_sesion("—")
        self._v.upload.dropzone.mostrar_error("")
        self._v.ir_a_lote(PaginaLote.CARGA)

    def _cambiar_carpeta(self, ruta: str) -> None:
        if self.lote_en_curso:
            return
        self._configuracion.guardar_carpeta_salida(ruta)
        self._v.settings.mostrar_carpeta(ruta)
        logger.info("Carpeta de salida actualizada")

    def _guardar_credenciales(self, credenciales: object) -> None:
        assert isinstance(credenciales, CredencialesPortal3)
        if not self._accion_credenciales.intentar():
            return
        try:
            self._configuracion.guardar_credenciales_portal3(credenciales)
        except OSError:
            logger.exception("No se pudieron guardar las credenciales del Portal 3")
            self._v.settings.confirmar_guardado("No se pudo escribir el archivo .env.", exito=False)
        else:
            self._v.settings.confirmar_guardado(
                "Credenciales guardadas. Se usarán al iniciar la próxima campaña.", exito=True
            )
        finally:
            self._accion_credenciales.liberar()

    def _recibir_log(self, linea: object) -> None:
        assert isinstance(linea, LineaLog)
        self._v.logs.agregar(linea)
        self._v.processing.agregar_log(linea)

    def solicitar_cierre(self) -> bool:
        runner = self._runner
        if runner is None:
            return not self._tareas
        if self._cerrando:
            return False
        respuesta = QMessageBox.question(
            self._v,
            "Hay un lote en curso",
            "¿Detener el lote y cerrar LuxMed? Se terminará el paciente actual antes de cerrar.",
            Respuesta.Yes | Respuesta.No,
            Respuesta.No,
        )
        if respuesta != Respuesta.Yes:
            return False
        self._cerrando = True
        runner.requestInterruption()
        self._v.overlay.mostrar("Deteniendo el lote", "Esperando a que termine el paciente actual…")
        return False

    def _avisar_precondicion(self, mensaje: str) -> None:
        caja = QMessageBox(QMessageBox.Icon.Warning, "Falta configuración", mensaje, parent=self._v)
        ir_ajustes = caja.addButton("Ir a Ajustes", QMessageBox.ButtonRole.AcceptRole)
        caja.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        caja.exec()
        if caja.clickedButton() is ir_ajustes:
            self._v.mostrar_seccion(Seccion.AJUSTES)

    def _terminar_espera(self, accion: AccionUnica) -> None:
        self._v.overlay.ocultar()
        accion.liberar()

    def _en_segundo_plano(
        self,
        tarea: Callable[[], object],
        exito: Callable[[object], None],
        fallo: Callable[[str], None],
    ) -> None:
        hilo = TaskThread(tarea, self)
        hilo.succeeded.connect(exito)
        hilo.failed.connect(fallo)
        hilo.finished.connect(lambda: self._tareas.discard(hilo))
        self._tareas.add(hilo)
        hilo.start()
