QWidget {
  color: $tinta;
  font-family: "Archivo";
  font-size: 12px;
}

QMainWindow, QWidget#lienzo, QStackedWidget#paginas {
  background-color: $lienzo;
}

QWidget#fondo_blanco {
  background-color: $blanco;
}

QToolTip {
  background-color: $tinta;
  color: $blanco;
  border: none;
  padding: 4px 8px;
}

QFrame#barra_superior {
  background-color: $panel;
  border-bottom: 1px solid $filete;
}

QLabel#marca {
  font-size: 14px;
  font-weight: 600;
}

QFrame#separador_vertical {
  background-color: $filete;
}

QLabel#avatar {
  background-color: $filete_suave;
  border: 1px solid $filete;
  font-family: "IBM Plex Mono";
  font-size: 10px;
  font-weight: 700;
}

QFrame#riel {
  background-color: $lienzo;
  border-right: 1px solid $filete;
}

QToolButton#item_riel {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-left: 3px solid transparent;
  font-size: 10px;
  font-weight: 500;
  padding-top: 6px;
}

QToolButton#item_riel:hover {
  background-color: $filete_suave;
}

QToolButton#item_riel:checked {
  background-color: $cabecera;
  color: $indigo;
  border-left: 3px solid $indigo;
}

QToolButton#item_riel:disabled {
  color: $tinta_ter;
  background-color: transparent;
}

QLabel#riel_version {
  color: $tinta_ter;
  border-top: 1px solid $filete_suave;
  font-family: "IBM Plex Mono";
  font-size: 9px;
  padding: 8px 0px;
}

QPushButton {
  background-color: $boton;
  color: $tinta;
  border: 1px solid $filete;
  border-radius: 3px;
  padding: 0px 16px;
  min-height: 30px;
  font-size: 12px;
  font-weight: 500;
}

QPushButton:hover {
  background-color: $filete_suave;
}

QPushButton:pressed {
  background-color: $boton_presionado;
}

QPushButton:disabled {
  background-color: $boton;
  color: $tinta_ter;
  border-color: $filete_suave;
}

QPushButton[variante="primario"] {
  background-color: $tinta;
  color: $blanco;
  border: 1px solid $tinta;
}

QPushButton[variante="primario"]:hover {
  background-color: $tinta_hover;
}

QPushButton[variante="primario"]:disabled {
  background-color: $filete_suave;
  color: $tinta_ter;
  border-color: $filete_suave;
}

QPushButton[variante="pestana"] {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 0px;
  font-size: 13px;
  font-weight: 400;
  padding: 0px 16px;
}

QPushButton[variante="pestana"]:hover {
  color: $tinta;
}

QPushButton[variante="pestana"]:checked {
  color: $indigo;
  font-weight: 600;
  border-bottom: 2px solid $indigo;
}

QFrame#segmentos {
  background-color: $boton;
  border: 1px solid $filete;
}

QPushButton[variante="segmento"] {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-right: 1px solid $filete;
  border-radius: 0px;
  min-height: 28px;
  padding: 0px 12px;
  font-weight: 400;
}

QPushButton[variante="segmento"][ultimo="true"] {
  border-right: none;
}

QPushButton[variante="segmento"]:hover {
  color: $tinta;
}

QPushButton[variante="segmento"]:checked {
  background-color: $blanco;
  color: $tinta;
  font-weight: 600;
}

QLineEdit {
  background-color: $blanco;
  color: $tinta;
  border: 1px solid $filete;
  border-radius: 0px;
  min-height: 30px;
  padding: 0px 8px;
  selection-background-color: $indigo_suave;
  selection-color: $tinta;
}

QLineEdit:focus {
  border: 1px solid $indigo;
}

QLineEdit[solo_lectura="true"] {
  background-color: $campo_lectura;
  font-family: "IBM Plex Mono";
  font-size: 13px;
  font-weight: 500;
  min-height: 34px;
}

QLabel[tono="exito"], QLabel[tono="proceso"], QLabel[tono="neutro"], QLabel[tono="alerta"] {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
}

QLabel[tono="exito"] {
  background-color: $verde_fondo;
  color: $verde;
  border: 1px solid $verde_borde;
}

QLabel[tono="proceso"] {
  background-color: $indigo_suave;
  color: $indigo;
  border: 1px solid $indigo_borde;
}

QLabel[tono="neutro"] {
  background-color: $boton;
  color: $tinta_sec;
  border: 1px solid $filete_suave;
}

QLabel[tono="alerta"] {
  background-color: $rojo_fondo;
  color: $rojo;
  border: 1px solid $rojo_borde;
}

QLabel[rol="titulo"] {
  font-size: 20px;
  font-weight: 600;
}

QLabel[rol="titulo_seccion"] {
  font-size: 14px;
  font-weight: 600;
}

QLabel[rol="subtitulo"] {
  color: $tinta_sec;
  font-size: 13px;
}

QLabel[rol="ayuda"] {
  color: $tinta_sec;
  font-size: 12px;
}

QLabel[rol="nota"] {
  color: $tinta_ter;
  font-size: 11px;
  font-style: italic;
}

QLabel[rol="etiqueta"] {
  color: $tinta_sec;
  font-family: "Archivo Narrow";
  font-size: 11px;
  font-weight: 600;
}

QLabel[rol="mono"] {
  color: $tinta_sec;
  font-family: "IBM Plex Mono";
  font-size: 12px;
}

QLabel[rol="error"] {
  color: $rojo;
  font-size: 12px;
}

QLabel[rol="exito"] {
  color: $verde;
  font-size: 12px;
}

QFrame#panel {
  background-color: $panel;
  border: 1px solid $filete;
  border-radius: 3px;
}

QFrame#tira_kpi {
  background-color: $panel;
  border: none;
  border-bottom: 1px solid $filete;
}

QFrame#cinta_kpi {
  background-color: $panel;
  border: 1px solid $filete;
  border-radius: 3px;
}

QFrame[rol="kpi"] {
  background-color: transparent;
  border: none;
  border-right: 1px solid $filete;
  border-bottom: 3px solid transparent;
}

QFrame[rol="kpi"][ultimo="true"] {
  border-right: none;
}

QFrame[rol="kpi"][activo="true"] {
  background-color: $indigo_suave;
  border-bottom: 3px solid $indigo;
}

QLabel[rol="kpi_cifra"] {
  font-family: "IBM Plex Mono";
  font-size: 26px;
  font-weight: 700;
}

QLabel[rol="kpi_nota"] {
  font-size: 11px;
}

QFrame#dropzone {
  background-color: $panel;
  border: 2px dashed $filete;
  border-radius: 3px;
}

QFrame#dropzone[arrastrando="true"] {
  background-color: $indigo_suave;
  border: 2px dashed $indigo;
}

QFrame#banner {
  background-color: $panel;
  border: 1px solid $filete;
  border-left: 3px solid $indigo;
}

QFrame#barra_filtros {
  background-color: $panel;
  border: none;
  border-bottom: 1px solid $filete;
}

QFrame#pie_acciones {
  background-color: $panel;
  border: none;
  border-top: 1px solid $filete;
}

QFrame#cabecera_pantalla {
  background-color: $panel;
  border: none;
  border-bottom: 1px solid $filete_suave;
}

QFrame#barra_estado {
  background-color: $cabecera;
  border: none;
  border-top: 1px solid $filete;
}

QFrame#bitacora {
  background-color: $boton;
  border: none;
  border-top: 1px solid $filete;
}

QToolButton#bitacora_toggle {
  background-color: transparent;
  border: none;
  font-family: "Archivo Narrow";
  font-size: 11px;
  font-weight: 600;
}

QPlainTextEdit {
  background-color: $panel;
  color: $tinta;
  border: none;
  font-family: "IBM Plex Mono";
  font-size: 12px;
  selection-background-color: $indigo_suave;
  selection-color: $tinta;
}

QTableView {
  background-color: $blanco;
  border: none;
  gridline-color: $filete_celda;
  selection-background-color: $indigo_suave;
  selection-color: $tinta;
  outline: 0;
}

QTableView#tabla_con_borde {
  border: 1px solid $filete;
}

QTableView::item {
  border-bottom: 1px solid $filete_suave;
  padding: 0px 10px;
}

QTableView::item:hover {
  background-color: $fila_hover;
}

QHeaderView::section {
  background-color: $cabecera;
  color: $tinta;
  border: none;
  border-bottom: 1px solid $filete;
  border-right: 1px solid $filete_suave;
  padding: 0px 10px;
  font-family: "Archivo Narrow";
  font-size: 12px;
  font-weight: 600;
}

QScrollBar:vertical {
  background: $panel;
  width: 8px;
  margin: 0px;
}

QScrollBar:horizontal {
  background: $panel;
  height: 8px;
  margin: 0px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
  background: $filete;
  min-height: 24px;
  min-width: 24px;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
  background: $tinta_ter;
}

QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {
  background: none;
  width: 0px;
  height: 0px;
}

QFrame#tarjeta_carga {
  background-color: $panel;
  border: 1px solid $filete;
  border-radius: 3px;
}

QMessageBox {
  background-color: $panel;
}
