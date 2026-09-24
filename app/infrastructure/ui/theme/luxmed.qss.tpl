QWidget {
  color: $tinta;
}

QMainWindow {
  background-color: $lienzo;
}

QFrame#tarjeta {
  background-color: $panel;
  border: 1px solid $filete;
  border-radius: 4px;
}

QFrame#riel {
  background-color: $panel;
  border-right: 1px solid $filete;
}

QPushButton {
  background-color: $panel;
  color: $tinta;
  border: 1px solid $filete;
  border-radius: 4px;
  padding: 8px 16px;
}

QPushButton:hover {
  background-color: $filete_suave;
}

QPushButton:disabled {
  color: $tinta_ter;
  background-color: $panel;
  border-color: $filete_suave;
}

QPushButton[variante="primario"] {
  background-color: $tinta;
  color: $blanco;
  border: 1px solid $tinta;
}

QPushButton[variante="primario"]:hover {
  background-color: $tinta;
  border-color: $indigo;
}

QPushButton[variante="primario"]:disabled {
  background-color: $filete_suave;
  color: $tinta_ter;
  border-color: $filete_suave;
}

QPushButton[variante="secundario"] {
  background-color: $panel;
  color: $tinta;
  border: 1px solid $filete;
}

QPushButton[variante="fantasma"] {
  background-color: transparent;
  color: $tinta_sec;
  border: 1px solid transparent;
}

QPushButton[variante="fantasma"]:hover {
  color: $tinta;
  border: 1px solid $filete;
}

QPushButton[variante="pestana"] {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 0px;
  padding: 8px 16px;
}

QPushButton[variante="pestana"]:hover {
  background-color: $filete_suave;
}

QPushButton[variante="pestana"]:checked {
  color: $tinta;
  border-bottom: 2px solid $indigo;
}

QFrame#segmentos {
  background-color: $lienzo;
  border: 1px solid $filete;
}

QPushButton[variante="segmento"] {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-right: 1px solid $filete;
  border-radius: 0px;
  padding: 4px 12px;
}

QPushButton[variante="segmento"]:hover {
  background-color: $panel;
  color: $tinta;
}

QPushButton[variante="segmento"]:checked {
  background-color: $blanco;
  color: $tinta;
}

QPushButton[variante="segmento_final"] {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-radius: 0px;
  padding: 4px 12px;
}

QPushButton[variante="segmento_final"]:hover {
  background-color: $panel;
  color: $tinta;
}

QPushButton[variante="segmento_final"]:checked {
  background-color: $blanco;
  color: $tinta;
}

QFrame#barra_superior {
  background-color: $panel;
  border-bottom: 1px solid $filete;
}

QLabel#monograma {
  background-color: $tinta;
  color: $panel;
}

QLabel#avatar {
  background-color: $filete_suave;
  color: $tinta;
  border: 1px solid $filete;
}

QToolButton#item_riel {
  background-color: transparent;
  color: $tinta_sec;
  border: none;
  border-left: 3px solid transparent;
}

QToolButton#item_riel:hover {
  background-color: $filete_suave;
}

QToolButton#item_riel:checked {
  background-color: $filete_suave;
  color: $indigo;
  border-left: 3px solid $indigo;
}

QToolButton#item_riel_historial {
  background-color: transparent;
  color: $tinta_ter;
  border: none;
  border-left: 3px solid transparent;
}

QLabel#riel_insignia {
  background-color: $rojo;
  color: $blanco;
  border-radius: 7px;
}

QLabel#riel_version {
  color: $tinta_ter;
  border-top: 1px solid $filete_suave;
}

QFrame#barra_estado {
  background-color: $filete_suave;
  border-top: 1px solid $filete;
}

QFrame#panel_bitacora {
  background-color: $lienzo;
  border-top: 1px solid $filete;
}

QLineEdit, QTextEdit, QPlainTextEdit {
  background-color: $blanco;
  color: $tinta;
  border: 1px solid $filete;
  border-radius: 4px;
  padding: 4px 8px;
  selection-background-color: $indigo_suave;
  selection-color: $tinta;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
  border: 1px solid $indigo;
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
  color: $tinta_ter;
  background-color: $panel;
}

QLineEdit[error="true"] {
  background-color: $rojo_fondo;
  border: 1px solid $rojo;
  color: $rojo;
}

QLabel[tono="exito"] {
  background-color: $verde_fondo;
  color: $verde;
  border: 1px solid $verde_borde;
  padding: 2px 8px;
}

QLabel[tono="proceso"] {
  background-color: $indigo_suave;
  color: $indigo;
  border: 1px solid $indigo_borde;
  padding: 2px 8px;
}

QLabel[tono="neutro"] {
  background-color: $filete_suave;
  color: $tinta_sec;
  border: 1px solid $filete;
  padding: 2px 8px;
}

QLabel[tono="alerta"] {
  background-color: $rojo_fondo;
  color: $rojo;
  border: 1px solid $rojo_borde;
  padding: 2px 8px;
}

QHeaderView::section {
  background-color: $filete_suave;
  color: $tinta;
  border: none;
  border-bottom: 1px solid $filete;
  border-right: 1px solid $filete;
  padding: 4px 8px;
}

QFrame#dropzone {
  background-color: $panel;
  border: 2px dashed $filete;
  border-radius: 4px;
}

QFrame#dropzone[arrastrando="true"] {
  background-color: $indigo_suave;
  border: 2px dashed $indigo;
}

QFrame#dropzone:disabled {
  background-color: $lienzo;
  border: 2px dashed $filete_suave;
}

QFrame#kpi_tile {
  background-color: transparent;
  border-bottom: 3px solid transparent;
}

QFrame#kpi_tile[activo="true"] {
  background-color: $indigo_suave;
  border-bottom: 3px solid $indigo;
}

QFrame#fila_contadores {
  background-color: $blanco;
  border: 1px solid $filete;
}

QFrame#banner_info {
  background-color: $lienzo;
  border: 1px solid $filete_suave;
}

QFrame#borde_inferior {
  border: none;
  border-bottom: 1px solid $filete;
}

QFrame#pie_revision {
  background-color: $lienzo;
  border-top: 1px solid $filete;
}

QFrame#cabecera_dialogo {
  background-color: $filete_suave;
  border-bottom: 1px solid $filete;
}

QFrame#pie_dialogo {
  background-color: $panel;
  border-top: 1px solid $filete;
}

QFrame#caja_estado_espera {
  background-color: $filete_suave;
  border: 1px solid $filete;
}

QFrame#caja_estado_tecnico {
  background-color: $filete_suave;
  border: 1px solid $filete;
}

QFrame#tira_kpi {
  background-color: $panel;
  border-bottom: 1px solid $filete;
}

QFrame#barra_filtros {
  background-color: $panel;
  border-bottom: 1px solid $filete;
}

QFrame#panel_detalle {
  background-color: $panel;
  border-left: 1px solid $filete;
}

QFrame#cabecera_detalle {
  background-color: $panel;
  border-bottom: 1px solid $filete;
}

QFrame#bloque_detalle {
  background-color: $panel;
  border-bottom: 1px solid $filete;
}

QFrame#pie_detalle {
  background-color: $panel;
  border-top: 1px solid $filete;
}

QFrame#tarjeta_expediente {
  background-color: $blanco;
  border: 1px solid $filete_suave;
}

QPushButton#boton_cerrar_detalle {
  background-color: transparent;
  color: $tinta_sec;
  border: 1px solid transparent;
}

QPushButton#boton_cerrar_detalle:hover {
  background-color: $filete_suave;
  color: $tinta;
  border: 1px solid $filete;
}

QPushButton#boton_copiar {
  background-color: transparent;
  color: $tinta_sec;
  border: 1px solid $filete_suave;
}

QPushButton#boton_copiar:hover {
  background-color: $filete_suave;
  color: $tinta;
}

QFrame#cabecera_tabla_resumen {
  background-color: $filete_suave;
  border-bottom: 1px solid $filete;
}

QFrame#fila_tabla_resumen {
  background-color: $panel;
  border-bottom: 1px solid $filete_suave;
}

QFrame#fila_total_resumen {
  background-color: $lienzo;
}

QFrame#bloque_carpeta {
  background-color: $lienzo;
  border: 1px solid $filete;
}
