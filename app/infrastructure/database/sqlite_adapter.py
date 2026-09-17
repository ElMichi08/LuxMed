from __future__ import annotations
import sqlite3
from datetime import date
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro
from app.domain.ports import IPacienteRepository
 
class SQLiteAdapter(IPacienteRepository):
    def __init__(self, ruta_db: str = "data/luxmed.db") -> None:
        self._ruta_db = ruta_db
        self._inicializar_tabla()

    def _inicializar_tabla(self) -> None:
        with sqlite3.connect(self._ruta_db) as conexion:
            cursor = conexion.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_y_apellidos TEXT NOT NULL,
                    cedula TEXT NOT NULL UNIQUE,
                    fecha_nacimiento TEXT NOT NULL,
                    aporta TEXT NOT NULL,
                    fecha_atencion TEXT NOT NULL,
                    nom_establecimiento TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    entidad_detectada TEXT NOT NULL,
                    seguro_derivado INTEGER NOT NULL DEFAULT 0,
                    pdf_p1_propio_bytes BLOB,
                    cedula_acreditador TEXT,
                    pdf_p1_acreditador_bytes BLOB,
                    pdf_p3_bytes BLOB,
                    pdf_consolidado BLOB,
                    es_auditoria_rojo INTEGER NOT NULL DEFAULT 0
                );
            """)
            conexion.commit()

    def guardar_lote(self, pacientes: list[Paciente]) -> None:
        with sqlite3.connect(self._ruta_db) as conexion:
            cursor = conexion.cursor()
            for p in pacientes:
                try:
                    cursor.execute("""
                        INSERT INTO pacientes (
                            nombre_y_apellidos, cedula, fecha_nacimiento, aporta, 
                            fecha_atencion, nom_establecimiento, estado, 
                            entidad_detectada, seguro_derivado, pdf_p1_propio_bytes, 
                            cedula_acreditador, pdf_p1_acreditador_bytes, pdf_p3_bytes, 
                            pdf_consolidado, es_auditoria_rojo
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p.nombre_y_apellidos,
                        p.cedula,
                        p.fecha_nacimiento.isoformat(),
                        p.aporta,
                        p.fecha_atencion.isoformat(),
                        p.nom_establecimiento,
                        p.estado.value,
                        p.entidad_detectada.value,
                        1 if p.seguro_derivado else 0,
                        sqlite3.Binary(p.pdf_p1_propio_bytes) if p.pdf_p1_propio_bytes else None,
                        p.cedula_acreditador,
                        sqlite3.Binary(p.pdf_p1_acreditador_bytes) if p.pdf_p1_acreditador_bytes else None,
                        sqlite3.Binary(p.pdf_p3_bytes) if p.pdf_p3_bytes else None,
                        sqlite3.Binary(p.pdf_consolidado) if p.pdf_consolidado else None,
                        1 if p.es_auditoria_rojo else 0
                    ))
                except sqlite3.IntegrityError:
                    continue
            conexion.commit()

    def obtener_pendientes(self) -> list[Paciente]:
        pacientes = []
        with sqlite3.connect(self._ruta_db) as conexion:
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM pacientes WHERE estado = ?", (EstadoValidacion.PENDIENTE.value,))
            
            for fila in cursor.fetchall():
                pacientes.append(Paciente(
                    nombre_y_apellidos=fila["nombre_y_apellidos"],
                    cedula=fila["cedula"],
                    fecha_nacimiento=date.fromisoformat(fila["fecha_nacimiento"]),
                    aporta=fila["aporta"],
                    fecha_atencion=date.fromisoformat(fila["fecha_atencion"]),
                    nom_establecimiento=fila["nom_establecimiento"],
                    estado=EstadoValidacion(fila["estado"]),
                    entidad_detectada=EntidadSeguro(fila["entidad_detectada"]),
                    seguro_derivado=bool(fila["seguro_derivado"]),
                    pdf_p1_propio_bytes=fila["pdf_p1_propio_bytes"],
                    cedula_acreditador=fila["cedula_acreditador"],
                    pdf_p1_acreditador_bytes=fila["pdf_p1_acreditador_bytes"],
                    pdf_p3_bytes=fila["pdf_p3_bytes"],
                    pdf_consolidado=fila["pdf_consolidado"],
                    es_auditoria_rojo=bool(fila["es_auditoria_rojo"])
                ))
        return pacientes

    def actualizar_estado(self, paciente: Paciente) -> None:
        with sqlite3.connect(self._ruta_db) as conexion:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE pacientes SET 
                    estado = ?, 
                    entidad_detectada = ?, 
                    seguro_derivado = ?, 
                    aporta = ?,
                    pdf_p1_propio_bytes = ?, 
                    cedula_acreditador = ?, 
                    pdf_p1_acreditador_bytes = ?, 
                    pdf_p3_bytes = ?, 
                    pdf_consolidado = ?,
                    es_auditoria_rojo = ? 
                WHERE cedula = ?
            """, (
                paciente.estado.value,
                paciente.entidad_detectada.value,
                1 if paciente.seguro_derivado else 0,
                paciente.aporta,
                sqlite3.Binary(paciente.pdf_p1_propio_bytes) if paciente.pdf_p1_propio_bytes else None,
                paciente.cedula_acreditador,
                sqlite3.Binary(paciente.pdf_p1_acreditador_bytes) if paciente.pdf_p1_acreditador_bytes else None,
                sqlite3.Binary(paciente.pdf_p3_bytes) if paciente.pdf_p3_bytes else None,
                sqlite3.Binary(paciente.pdf_consolidado) if paciente.pdf_consolidado else None,
                1 if paciente.es_auditoria_rojo else 0,
                paciente.cedula
            ))
            conexion.commit()
