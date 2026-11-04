# -*- coding: utf-8 -*-
"""
Cloud Balance - Contabilidad Digital
Capa de acceso a datos (SQLite)

Centraliza la conexión a SQLite y las operaciones sobre las tablas
`usuarios`, `proyectos`, `cuentas`, `asientos` y `partidas` que usa todo el
sistema contable (login/registro + páginas de la app PySide6).

La base es un solo archivo (`cloud_balance.db`, junto a los .py): para
exportar o respaldar el sistema basta con copiar ese archivo. Si no existe,
se crea sola (con sus tablas y un usuario Administrador inicial).
"""

import os
import sqlite3
import sys
from datetime import datetime

import bcrypt

import roles

# ══════════════════════════════════════════════════════════
#  UBICACIÓN DE LA BASE DE DATOS
# ══════════════════════════════════════════════════════════
def _carpeta_datos() -> str:
    """Dónde vive cloud_balance.db.
    - Ejecutando los .py: junto a los archivos (como siempre).
    - Dentro del .exe: en la carpeta del usuario (AppData\\Roaming\\CloudBalance),
      porque la carpeta interna del .exe es temporal o de solo lectura."""
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        carpeta = os.path.join(base, "CloudBalance")
        os.makedirs(carpeta, exist_ok=True)
        return carpeta
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(_carpeta_datos(), "cloud_balance.db")

# Administrador inicial: se crea SOLO la primera vez, cuando la tabla
# `usuarios` está vacía, para poder entrar y crear los demás usuarios.
ADMIN_INICIAL_USUARIO = "admin"
ADMIN_INICIAL_PASSWORD = "Admin123"
ADMIN_INICIAL_NOMBRE = "Administrador del Sistema"


class DBError(Exception):
    """Error de base de datos con mensaje amigable para mostrar en la UI."""
    pass


_ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario   TEXT NOT NULL UNIQUE COLLATE NOCASE,
    contrasena_hash  TEXT NOT NULL,
    nombre_completo  TEXT,
    rol              TEXT NOT NULL DEFAULT 'Operador',
    activo           INTEGER NOT NULL DEFAULT 1,
    ultimo_login     TEXT,
    fecha_creacion   TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS proyectos (
    id              TEXT PRIMARY KEY,
    usuario_id      INTEGER NOT NULL
                    REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE CASCADE,
    nombre          TEXT NOT NULL COLLATE NOCASE,
    fecha_creacion  TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_proyectos_usuario ON proyectos(usuario_id);

CREATE TABLE IF NOT EXISTS cuentas (
    id             TEXT PRIMARY KEY,
    usuario_id     INTEGER NOT NULL
                   REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE CASCADE,
    proyecto_id    TEXT NOT NULL
                   REFERENCES proyectos(id) ON UPDATE CASCADE ON DELETE CASCADE,
    codigo         TEXT,
    nombre         TEXT NOT NULL COLLATE NOCASE,
    naturaleza     TEXT NOT NULL,
    saldo_inicial  REAL NOT NULL DEFAULT 0,
    descripcion    TEXT,
    fecha          TEXT,
    UNIQUE (proyecto_id, nombre)
);
CREATE INDEX IF NOT EXISTS idx_cuentas_usuario ON cuentas(usuario_id);

CREATE TABLE IF NOT EXISTS asientos (
    id           TEXT PRIMARY KEY,
    usuario_id   INTEGER NOT NULL
                 REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE CASCADE,
    proyecto_id  TEXT NOT NULL
                 REFERENCES proyectos(id) ON UPDATE CASCADE ON DELETE CASCADE,
    numero       INTEGER NOT NULL,
    fecha        TEXT NOT NULL,
    descripcion  TEXT,
    UNIQUE (proyecto_id, numero)
);
CREATE INDEX IF NOT EXISTS idx_asientos_usuario ON asientos(usuario_id);

CREATE TABLE IF NOT EXISTS partidas (
    id           TEXT PRIMARY KEY,
    asiento_id   TEXT NOT NULL
                 REFERENCES asientos(id) ON UPDATE CASCADE ON DELETE CASCADE,
    cuenta_id    TEXT NOT NULL
                 REFERENCES cuentas(id) ON UPDATE CASCADE ON DELETE CASCADE,
    tipo         TEXT NOT NULL,
    monto        REAL NOT NULL DEFAULT 0,
    descripcion  TEXT
);
CREATE INDEX IF NOT EXISTS idx_partidas_asiento ON partidas(asiento_id);
CREATE INDEX IF NOT EXISTS idx_partidas_cuenta ON partidas(cuenta_id);
"""

_esquema_verificado = False


def _dict_factory(cursor, fila):
    return {col[0]: fila[i] for i, col in enumerate(cursor.description)}


def _cursor_dict(conn):
    """Cursor cuyas filas se devuelven como diccionarios."""
    cur = conn.cursor()
    cur.row_factory = _dict_factory
    return cur


def _es_duplicado(e: Exception) -> bool:
    """True si el error de SQLite es por violar una restricción UNIQUE."""
    return isinstance(e, sqlite3.IntegrityError) and "UNIQUE" in str(e).upper()


def obtener_conexion():
    """Abre y devuelve una conexión nueva a SQLite (activando las llaves
    foráneas). La primera vez crea las tablas si no existen.
    Lanza DBError con un mensaje claro si algo falla."""
    global _esquema_verificado
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        if not _esquema_verificado:
            _crear_esquema(conn)
            _esquema_verificado = True
        return conn
    except sqlite3.Error as e:
        raise DBError(
            "No se pudo abrir la base de datos local. "
            f"Verifica que la carpeta tenga permisos de escritura ({DB_PATH})."
        ) from e


def _crear_esquema(conn) -> None:
    """Crea las tablas (si faltan) y el Administrador inicial (si no hay usuarios)."""
    conn.executescript(_ESQUEMA_SQL)
    (total,) = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()
    if total == 0:
        hash_pw = bcrypt.hashpw(ADMIN_INICIAL_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn.execute(
            "INSERT INTO usuarios (nombre_usuario, contrasena_hash, nombre_completo, rol) "
            "VALUES (?, ?, ?, ?)",
            (ADMIN_INICIAL_USUARIO, hash_pw, ADMIN_INICIAL_NOMBRE, roles.ROL_ADMIN),
        )
    conn.commit()


def asegurar_esquema() -> None:
    """Compatibilidad: garantiza que la base y sus tablas existan."""
    obtener_conexion().close()


# ══════════════════════════════════════════════════════════
#  SESIÓN ACTUAL (usuario que inició sesión)
# ══════════════════════════════════════════════════════════
_usuario_actual_id = None
_nombre_usuario_actual = None
_rol_actual = None


def set_usuario_actual(usuario_id, rol=None, nombre_usuario=None) -> None:
    """Marca qué usuario está usando la app (y con qué rol). Se llama
    automáticamente al validar credenciales correctas."""
    global _usuario_actual_id, _rol_actual, _nombre_usuario_actual
    _usuario_actual_id = usuario_id
    _rol_actual = roles.normalizar_rol(rol) if usuario_id is not None else None
    _nombre_usuario_actual = nombre_usuario


def usuario_actual_id():
    """Devuelve el id del usuario con sesión iniciada (o None)."""
    return _usuario_actual_id


def rol_actual():
    """Rol del usuario con sesión iniciada ('Administrador' u 'Operador'),
    o None si no hay sesión."""
    return _rol_actual


def nombre_usuario_actual():
    """nombre_usuario de la sesión actual (o None)."""
    return _nombre_usuario_actual


def cerrar_sesion() -> None:
    set_usuario_actual(None)


def _resolver_usuario_id(usuario_id):
    uid = usuario_id if usuario_id is not None else _usuario_actual_id
    if uid is None:
        raise DBError("No hay una sesión activa. Inicia sesión antes de guardar datos.")
    return uid


# ══════════════════════════════════════════════════════════
#  OPERACIONES SOBRE usuarios (login / registro)
# ══════════════════════════════════════════════════════════
def usuario_existe(nombre_usuario: str) -> bool:
    """True si ya existe ese nombre_usuario en la tabla."""
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM usuarios WHERE nombre_usuario = ? LIMIT 1",
            (nombre_usuario,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def crear_usuario(nombre_usuario: str, password: str, nombre_completo: str,
                   rol: str = roles.ROL_OPERADOR) -> None:
    """Inserta un nuevo usuario con la contraseña hasheada con bcrypt.
    Solo un Administrador con sesión iniciada puede crear usuarios.
    Por defecto se crean como Operador."""
    roles.requiere("administrar_usuarios")
    rol = roles.normalizar_rol(rol)
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    contrasena_hash = hash_bytes.decode("utf-8")

    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO usuarios (nombre_usuario, contrasena_hash, nombre_completo, rol)
            VALUES (?, ?, ?, ?)
            """,
            (nombre_usuario, contrasena_hash, nombre_completo, rol),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        if _es_duplicado(e):  # UNIQUE nombre_usuario
            raise DBError("Ese usuario ya existe, elige otro.") from e
        raise DBError("No se pudo crear la cuenta. Intenta de nuevo.") from e
    finally:
        conn.close()


def listar_usuarios() -> list[dict]:
    """Lista los usuarios del sistema (solo Administrador)."""
    roles.requiere("administrar_usuarios")
    conn = obtener_conexion()
    try:
        cur = _cursor_dict(conn)
        cur.execute(
            """
            SELECT id, nombre_usuario, nombre_completo, rol, activo, ultimo_login
            FROM usuarios
            ORDER BY rol, nombre_usuario
            """
        )
        filas = cur.fetchall()
        for f in filas:
            if isinstance(f["ultimo_login"], str):
                try:
                    f["ultimo_login"] = datetime.fromisoformat(f["ultimo_login"])
                except ValueError:
                    f["ultimo_login"] = None
        return filas
    finally:
        conn.close()


def validar_credenciales(nombre_usuario: str, password: str) -> bool:
    """Verifica usuario/contraseña contra la tabla usuarios.
    Si son correctas y la cuenta está activa, actualiza ultimo_login
    y deja la sesión abierta (set_usuario_actual) para que el resto
    de la app (cuentas/asientos/partidas) sepa para quién guardar."""
    conn = obtener_conexion()
    try:
        cur = _cursor_dict(conn)
        cur.execute(
            """
            SELECT id, nombre_usuario, contrasena_hash, activo, rol
            FROM usuarios
            WHERE nombre_usuario = ?
            """,
            (nombre_usuario,),
        )
        fila = cur.fetchone()
        if not fila:
            return False

        if not fila["activo"]:
            return False

        hash_guardado = fila["contrasena_hash"].encode("utf-8")
        if not bcrypt.checkpw(password.encode("utf-8"), hash_guardado):
            return False

        cur2 = conn.cursor()
        cur2.execute(
            "UPDATE usuarios SET ultimo_login = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fila["id"]),
        )
        conn.commit()
        set_usuario_actual(fila["id"], fila["rol"], fila["nombre_usuario"])
        return True
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
#  PROYECTOS
# ══════════════════════════════════════════════════════════
def listar_proyectos(usuario_id=None) -> list[dict]:
    """Devuelve TODOS los proyectos del sistema: se comparten entre
    Administrador y Operador (es el mismo libro contable de la empresa).
    `usuario_id` se conserva solo por compatibilidad con quien ya lo
    llamaba; ya no filtra resultados."""
    conn = obtener_conexion()
    try:
        cur = _cursor_dict(conn)
        cur.execute("SELECT id, nombre FROM proyectos ORDER BY fecha_creacion, nombre")
        return cur.fetchall()
    finally:
        conn.close()


def crear_proyecto(proyecto_id: str, nombre: str, usuario_id=None) -> None:
    """Crea un proyecto visible para todos los usuarios. `usuario_id`
    (o la sesión activa) queda guardado solo como registro de quién lo
    creó, no restringe quién puede verlo o usarlo después."""
    uid = _resolver_usuario_id(usuario_id)
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO proyectos (id, usuario_id, nombre) VALUES (?, ?, ?)",
            (proyecto_id, uid, nombre),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        if _es_duplicado(e):
            raise DBError("Ya existe un proyecto con ese nombre.") from e
        raise DBError("No se pudo guardar el proyecto.") from e
    finally:
        conn.close()


def renombrar_proyecto(proyecto_id: str, nombre: str) -> None:
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE proyectos SET nombre = ? WHERE id = ?", (nombre, proyecto_id))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        if _es_duplicado(e):
            raise DBError("Ya existe un proyecto con ese nombre.") from e
        raise DBError("No se pudo renombrar el proyecto.") from e
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
#  CUENTAS
# ══════════════════════════════════════════════════════════
def listar_cuentas(proyecto_id: str, usuario_id=None) -> list[dict]:
    """Devuelve las cuentas de un proyecto, compartidas entre todos los
    usuarios que trabajan en él, como lista de dicts listas para
    reconstruir objetos Cuenta(**fila) en modelos.py."""
    conn = obtener_conexion()
    try:
        cur = _cursor_dict(conn)
        cur.execute(
            """
            SELECT id, nombre, codigo, naturaleza, saldo_inicial, descripcion, fecha
            FROM cuentas
            WHERE proyecto_id = ?
            ORDER BY fecha, nombre
            """,
            (proyecto_id,),
        )
        filas = cur.fetchall()
        for f in filas:
            f["saldo_inicial"] = float(f["saldo_inicial"] or 0)
            f["codigo"] = f["codigo"] or ""
            if f["fecha"] is not None:
                f["fecha"] = str(f["fecha"])
        return filas
    finally:
        conn.close()


def existe_nombre_cuenta(nombre: str, proyecto_id: str, excepto_id: str = None, usuario_id=None) -> bool:
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre FROM cuentas WHERE proyecto_id = ?",
            (proyecto_id,),
        )
        objetivo = (nombre or "").casefold()
        return any(fid != excepto_id and (n or "").casefold() == objetivo
                   for (fid, n) in cur.fetchall())
    finally:
        conn.close()


def guardar_cuenta(cuenta_id: str, nombre: str, naturaleza: str, saldo_inicial: float,
                    descripcion: str, fecha: str, usuario_id=None,
                    codigo: str = "", proyecto_id: str = None) -> None:
    """Inserta la cuenta si el id no existe todavía, o la actualiza si
    ya existe (UPSERT) — cubre tanto 'agregar_cuenta' como 'editar_cuenta'."""
    uid = _resolver_usuario_id(usuario_id)
    if proyecto_id is None:
        raise DBError("No hay un proyecto activo para guardar la cuenta.")
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cuentas (id, usuario_id, proyecto_id, codigo, nombre, naturaleza,
                                 saldo_inicial, descripcion, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                codigo = excluded.codigo,
                nombre = excluded.nombre,
                naturaleza = excluded.naturaleza,
                saldo_inicial = excluded.saldo_inicial,
                descripcion = excluded.descripcion
            """,
            (cuenta_id, uid, proyecto_id, (codigo or None), nombre, naturaleza,
             saldo_inicial, descripcion, fecha),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        if _es_duplicado(e):
            raise DBError("Ya existe una cuenta con ese nombre.") from e
        raise DBError("No se pudo guardar la cuenta.") from e
    finally:
        conn.close()


def eliminar_cuenta(cuenta_id: str) -> None:
    """Elimina la cuenta. Las partidas que la referencian se eliminan
    en cascada (igual que hace modelos.py en memoria)."""
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM cuentas WHERE id = ?", (cuenta_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DBError("No se pudo eliminar la cuenta.") from e
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
#  ASIENTOS + PARTIDAS
# ══════════════════════════════════════════════════════════
def siguiente_numero_asiento(proyecto_id: str, usuario_id=None) -> int:
    """Siguiente número correlativo del proyecto (compartido: sigue la
    numeración aunque el asiento anterior lo haya creado otro usuario)."""
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT MAX(numero) FROM asientos WHERE proyecto_id = ?",
            (proyecto_id,),
        )
        (maximo,) = cur.fetchone()
        return (maximo or 0) + 1
    finally:
        conn.close()


def listar_asientos(proyecto_id: str, usuario_id=None) -> list[dict]:
    """Devuelve los asientos de un proyecto, compartidos entre todos los
    usuarios que trabajan en él, cada uno con su lista de partidas
    anidada, listos para reconstruir Asiento/Partida en modelos.py."""
    conn = obtener_conexion()
    try:
        cur = _cursor_dict(conn)
        cur.execute(
            """
            SELECT id, numero AS num, fecha, descripcion
            FROM asientos
            WHERE proyecto_id = ?
            ORDER BY numero
            """,
            (proyecto_id,),
        )
        asientos = cur.fetchall()
        for a in asientos:
            a["fecha"] = str(a["fecha"])

        cur2 = _cursor_dict(conn)
        cur2.execute(
            """
            SELECT p.id, p.asiento_id, p.cuenta_id AS cuenta, p.tipo, p.monto, p.descripcion
            FROM partidas p
            INNER JOIN asientos a ON a.id = p.asiento_id
            WHERE a.proyecto_id = ?
            """,
            (proyecto_id,),
        )
        partidas_por_asiento: dict = {}
        for p in cur2.fetchall():
            p["monto"] = float(p["monto"] or 0)
            partidas_por_asiento.setdefault(p["asiento_id"], []).append(
                {"id": p["id"], "cuenta": p["cuenta"], "tipo": p["tipo"],
                 "monto": p["monto"], "descripcion": p["descripcion"]}
            )

        for a in asientos:
            a["partidas"] = partidas_por_asiento.get(a["id"], [])
        return asientos
    finally:
        conn.close()


def registrar_asiento(asiento_id: str, numero: int, fecha: str, descripcion: str,
                       partidas: list, usuario_id=None, proyecto_id: str = None) -> None:
    """Inserta el encabezado del asiento y todas sus partidas en una
    sola transacción (o todo se guarda, o nada — así nunca queda un
    asiento a medias si algo falla a mitad de camino).

    `partidas` es una lista de objetos/dicts con: id, cuenta, tipo, monto, descripcion
    (coincide con el dataclass Partida de modelos.py)."""
    uid = _resolver_usuario_id(usuario_id)
    if proyecto_id is None:
        raise DBError("No hay un proyecto activo para registrar el asiento.")
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO asientos (id, usuario_id, proyecto_id, numero, fecha, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (asiento_id, uid, proyecto_id, numero, fecha, descripcion),
        )
        for p in partidas:
            # admite tanto dataclass Partida como dict
            p_id = getattr(p, "id", None) or p["id"]
            p_cuenta = getattr(p, "cuenta", None) or p["cuenta"]
            p_tipo = getattr(p, "tipo", None) or p["tipo"]
            p_monto = getattr(p, "monto", None) if hasattr(p, "monto") else p["monto"]
            p_desc = getattr(p, "descripcion", None) if hasattr(p, "descripcion") else p.get("descripcion", "")
            cur.execute(
                """
                INSERT INTO partidas (id, asiento_id, cuenta_id, tipo, monto, descripcion)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (p_id, asiento_id, p_cuenta, p_tipo, p_monto, p_desc),
            )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DBError("No se pudo registrar el asiento.") from e
    finally:
        conn.close()


def actualizar_asiento(asiento_id: str, fecha: str, descripcion: str, partidas: list) -> None:
    """Actualiza la fecha/descripción de un asiento y reemplaza todas sus
    partidas, en una sola transacción (todo o nada)."""
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE asientos SET fecha = ?, descripcion = ? WHERE id = ?",
            (fecha, descripcion, asiento_id),
        )
        cur.execute("DELETE FROM partidas WHERE asiento_id = ?", (asiento_id,))
        for p in partidas:
            cur.execute(
                """
                INSERT INTO partidas (id, asiento_id, cuenta_id, tipo, monto, descripcion)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (p.id, asiento_id, p.cuenta, p.tipo, p.monto, p.descripcion),
            )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DBError("No se pudo actualizar el asiento.") from e
    finally:
        conn.close()


def eliminar_asiento(asiento_id: str) -> None:
    """Elimina un asiento y, en cascada, todas sus partidas."""
    conn = obtener_conexion()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM asientos WHERE id = ?", (asiento_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DBError("No se pudo eliminar el asiento.") from e
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
#  CARGA COMPLETA (para almacenamiento.py al arrancar la app)
# ══════════════════════════════════════════════════════════
def cargar_proyectos_completos(usuario_id=None) -> list[dict]:
    """Trae todos los proyectos compartidos del sistema (los ve
    cualquier usuario con sesión iniciada, sea Administrador u
    Operador), y dentro de cada uno sus cuentas y asientos (con sus
    partidas). Antes de leer, actualiza la estructura de la base si
    hace falta."""
    asegurar_esquema()
    resultado = []
    for p in listar_proyectos():
        resultado.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "cuentas": listar_cuentas(p["id"]),
            "asientos": listar_asientos(p["id"]),
        })
    return resultado
