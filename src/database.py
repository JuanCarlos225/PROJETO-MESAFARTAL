import os
import sqlite3
from contextlib import contextmanager

# La base se guarda siempre en la raíz del repositorio, sin importar desde dónde se ejecute
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mesafartai.db')


def inicializar_base():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tabla de Usuarios (Donadores y ONGs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('DONADOR', 'ONG')) NOT NULL,
            codigo_postal TEXT NOT NULL,
            latitud REAL,
            longitud REAL,
            telefono TEXT
        )
    ''')

    # 2. Tabla de Donaciones de Alimentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donador_id INTEGER,
            descripcion_alimento TEXT NOT NULL,
            cantidad_kg REAL,
            fecha_validez TEXT,
            estado TEXT DEFAULT 'DISPONIBLE',
            ruta_imagen TEXT,
            FOREIGN KEY (donador_id) REFERENCES usuarios (id)
        )
    ''')

    # 3. Tabla de Asignaciones Logísticas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asignaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donacion_id INTEGER,
            ong_id INTEGER,
            distancia_km REAL,
            fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donacion_id) REFERENCES donaciones (id),
            FOREIGN KEY (ong_id) REFERENCES usuarios (id)
        )
    ''')

    cursor.execute("PRAGMA table_info(donaciones)")
    if "ruta_imagen" not in [c[1] for c in cursor.fetchall()]:
        cursor.execute("ALTER TABLE donaciones ADD COLUMN ruta_imagen TEXT")

    # Carga inicial (datos de prueba)
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        # ONGs de prueba
        cursor.execute("INSERT INTO usuarios (nombre, tipo, codigo_postal, latitud, longitud, telefono) VALUES ('ONG Plato Caliente', 'ONG', '06700-000', -23.612, -46.781, '11999990001')")
        cursor.execute("INSERT INTO usuarios (nombre, tipo, codigo_postal, latitud, longitud, telefono) VALUES ('Albergue Esperanza', 'ONG', '06705-000', -23.625, -46.795, '11999990002')")

        # Donadores de prueba
        cursor.execute("INSERT INTO usuarios (nombre, tipo, codigo_postal, latitud, longitud, telefono) VALUES ('Supermercado Silva', 'DONADOR', '06701-000', -23.615, -46.785, '11999990003')")
        cursor.execute("INSERT INTO usuarios (nombre, tipo, codigo_postal, latitud, longitud, telefono) VALUES ('Restaurante Sabor', 'DONADOR', '06703-000', -23.618, -46.789, '11999990004')")
        print(" Datos iniciales de prueba insertados con éxito!")

    conn.commit()
    conn.close()
    print(" Base de datos 'mesafartai.db' inicializada con éxito!")

# ---------------------------------------------------------------------------
# Funciones de acceso a datos (usadas por el chatbot y el dashboard)
# ---------------------------------------------------------------------------
@contextmanager
def conexion():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def listar_usuarios(tipo=None):
    with conexion() as conn:
        if tipo:
            filas = conn.execute("SELECT * FROM usuarios WHERE tipo = ? ORDER BY nombre", (tipo,)).fetchall()
        else:
            filas = conn.execute("SELECT * FROM usuarios ORDER BY tipo, nombre").fetchall()
    return [dict(f) for f in filas]


def crear_donacion(donador_id, descripcion, cantidad_kg, fecha_validez, ruta_imagen=None):
    with conexion() as conn:
        cur = conn.execute(
            "INSERT INTO donaciones (donador_id, descripcion_alimento, cantidad_kg, fecha_validez, ruta_imagen) "
            "VALUES (?, ?, ?, ?, ?)",
            (donador_id, descripcion, cantidad_kg, fecha_validez, ruta_imagen),
        )
        return cur.lastrowid


def crear_asignacion(donacion_id, ong_id, distancia_km):
    with conexion() as conn:
        conn.execute("INSERT INTO asignaciones (donacion_id, ong_id, distancia_km) VALUES (?, ?, ?)",
                     (donacion_id, ong_id, distancia_km))
        conn.execute("UPDATE donaciones SET estado = 'ASIGNADA' WHERE id = ?", (donacion_id,))


def donaciones_de_donador(donador_id, limite=5):
    with conexion() as conn:
        filas = conn.execute(
            """SELECT d.id, d.descripcion_alimento, d.cantidad_kg, d.fecha_validez, d.estado,
                      u.nombre AS ong, m.distancia_km
               FROM donaciones d
               LEFT JOIN asignaciones m ON m.donacion_id = d.id
               LEFT JOIN usuarios u ON u.id = m.ong_id
               WHERE d.donador_id = ? ORDER BY d.id DESC LIMIT ?""", (donador_id, limite)).fetchall()
    return [dict(f) for f in filas]


def donaciones_de_ong(ong_id):
    with conexion() as conn:
        filas = conn.execute(
            """SELECT d.id, d.descripcion_alimento, d.cantidad_kg, d.fecha_validez, d.estado, d.ruta_imagen,
                      u.nombre AS donador, u.telefono, m.distancia_km
               FROM asignaciones m
               JOIN donaciones d ON d.id = m.donacion_id
               JOIN usuarios u ON u.id = d.donador_id
               WHERE m.ong_id = ?
               ORDER BY (d.fecha_validez IS NULL), d.fecha_validez, d.id""", (ong_id,)).fetchall()
    return [dict(f) for f in filas]


def historial_completo():
    """Todas las donaciones con su donador y ONG (para el dashboard)."""
    with conexion() as conn:
        filas = conn.execute(
            """SELECT d.id, don.nombre AS donador, d.descripcion_alimento AS alimento, d.cantidad_kg AS kg,
                      d.fecha_validez AS validez, d.estado, d.ruta_imagen AS imagen, ong.nombre AS ong, m.distancia_km AS distancia_km,
                      m.fecha_asignacion AS fecha_match
               FROM donaciones d
               JOIN usuarios don ON don.id = d.donador_id
               LEFT JOIN asignaciones m ON m.donacion_id = d.id
               LEFT JOIN usuarios ong ON ong.id = m.ong_id
               ORDER BY d.id DESC""").fetchall()
    return [dict(f) for f in filas]


if __name__ == "__main__":
    inicializar_base()
