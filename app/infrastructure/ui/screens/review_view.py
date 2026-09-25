from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from app.application.lote_service import FilaRevision, RevisionLote
from app.infrastructure.ui.models.columnas import DERECHA, Columna, ModeloColumnas
from app.infrastructure.ui.models.filtro_proxy import FiltroProxy
from app.infrastructure.ui.presentacion import SIN_DATO, texto_edad, texto_fecha
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA
from app.infrastructure.ui.widgets.base import boton, columna, etiqueta, fila, marco
from app.infrastructure.ui.widgets.controles import SearchField, Tabs
from app.infrastructure.ui.widgets.kpi import DefinicionKpi, panel_kpi
from app.infrastructure.ui.widgets.paneles import NoticeBanner, ScreenHeader
from app.infrastructure.ui.widgets.tabla import crear_tabla

COLUMNA_MOTIVO = 7


def _fila(valor: object) -> FilaRevision:
    assert isinstance(valor, FilaRevision)
    return valor


def _rojo_si_descartada(valor: object) -> str | None:
    return None if _fila(valor).es_valida else COLORES.rojo


def _secundario(_valor: object) -> str | None:
    return COLORES.tinta_sec


COLUMNAS = (
    Columna("Fila del Excel", lambda f: f"{_fila(f).fila_excel:04d}", 96, mono=True, color=_secundario),
    Columna("Paciente", lambda f: _fila(f).nombre, None, negrita=lambda _f: True),
    Columna("Cédula", lambda f: _fila(f).cedula, 125, mono=True, color=_rojo_si_descartada),
    Columna("Fecha de nacimiento", lambda f: texto_fecha(_fila(f).fecha_nacimiento), 140, mono=True, color=_secundario),
    Columna("Edad", lambda f: texto_edad(_fila(f).edad, " a"), 64, DERECHA, mono=True, color=_secundario),
    Columna("Seguro", lambda f: _fila(f).seguro, 200, color=_secundario),
    Columna("Establecimiento", lambda f: _fila(f).establecimiento, 185, color=_secundario),
    Columna("Motivo", lambda f: _fila(f).motivo_descarte or SIN_DATO, 220, color=_rojo_si_descartada),
)

PESTANAS = (("listos", "Listos"), ("descartados", "Descartados"))


def _busqueda(valor: object) -> str:
    fila_revision = _fila(valor)
    return f"{fila_revision.cedula} {fila_revision.nombre}"


class ReviewView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("lienzo")
        self._encabezado = ScreenHeader("Revisión previa del lote")
        self._kpis = panel_kpi(
            (
                DefinicionKpi("total", "Total de filas"),
                DefinicionKpi("listos", "Listos para consultar", COLORES.verde, "Cédula de 10 dígitos válida"),
                DefinicionKpi("descartados", "Descartados", COLORES.rojo, "Cédula con longitud distinta a 10 dígitos"),
            )
        )
        self._aviso = NoticeBanner()
        self._pestanas = Tabs(PESTANAS)
        self._pestanas.cambiado.connect(self._cambiar_pestana)
        self._busqueda = SearchField(260)
        barra_layout = fila((0, 0, 0, 6))
        barra_layout.addWidget(self._pestanas)
        barra_layout.addStretch(1)
        barra_layout.addWidget(self._busqueda)
        barra = marco("barra_filtros", barra_layout)

        self._modelo = ModeloColumnas(COLUMNAS, parent=self)
        self._proxy = FiltroProxy(_busqueda, self)
        self._proxy.setSourceModel(self._modelo)
        self._busqueda.textChanged.connect(self._proxy.establecer_texto)
        self._tabla = crear_tabla(self._proxy, COLUMNAS, con_borde=True)

        self.boton_descartar = boton("Descartar lote")
        self.boton_iniciar = boton("Iniciar campaña", "primario")
        self._texto_pie = etiqueta("", "ayuda")
        pie_layout = fila((16, 0, 16, 0), 12)
        pie_layout.addWidget(self._texto_pie, 1)
        pie_layout.addWidget(self.boton_descartar)
        pie_layout.addWidget(self.boton_iniciar)
        pie = marco("pie_acciones", pie_layout)
        pie.setFixedHeight(GEOMETRIA.pie_acciones)

        contenido = columna((16, 16, 16, 12), 10)
        contenido.addWidget(self._encabezado)
        contenido.addWidget(self._kpis)
        contenido.addWidget(self._aviso)
        contenido.addWidget(barra)
        contenido.addWidget(self._tabla, 1)
        layout = columna()
        layout.addLayout(contenido, 1)
        layout.addWidget(pie)
        self.setLayout(layout)
        self._cambiar_pestana("listos")

    def mostrar(self, revision: RevisionLote) -> None:
        listos, descartados = len(revision.listos), len(revision.descartados)
        self._encabezado.establecer_subtitulo(
            f"Se leyeron {len(revision.filas)} filas. Revisa los descartados antes de iniciar."
        )
        self._kpis.establecer_valores({"total": len(revision.filas), "listos": listos, "descartados": descartados})
        menores = revision.menores_listos
        self._aviso.mostrar(
            f"{menores} menores de edad entre los listos. Se consultan igual; "
            "si no tienen cobertura quedan como No encontrado."
            if menores
            else ""
        )
        self._pestanas.establecer_contador("listos", listos)
        self._pestanas.establecer_contador("descartados", descartados)
        self._texto_pie.setText(
            f"Se consultarán {listos} pacientes. "
            f"Los {descartados} descartados quedarán en rojo en el Excel auditado."
        )
        self._busqueda.clear()
        self._modelo.establecer_filas(revision.filas)
        self._pestanas.seleccionar("descartados" if descartados and not listos else "listos")

    def _cambiar_pestana(self, clave: str) -> None:
        quiere_validas = clave == "listos"
        self._proxy.establecer_predicado(lambda valor: _fila(valor).es_valida is quiere_validas)
        self._tabla.setColumnHidden(COLUMNA_MOTIVO, quiere_validas)
