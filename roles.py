# -*- coding: utf-8 -*-
"""
Cloud Balance - Contabilidad Digital
Roles y permisos (Administrador / Operador Contable).

Este módulo NO depende de la base de datos ni de PySide6: solo define
los roles, qué puede hacer cada uno y funciones para consultarlo.
La sesión (quién inició sesión y con qué rol) vive en db.py.

Uso típico:
    import roles
    if roles.puede("gestionar_cuentas"):
        ...
    roles.requiere("gestionar_cuentas")   # lanza PermissionError si no puede
"""

ROL_ADMIN = "Administrador"
ROL_OPERADOR = "Operador"          # "Operador Contable" en el informe
ROLES = (ROL_ADMIN, ROL_OPERADOR)

# Permisos por rol (sección 3.1.1 del informe, Tabla 1).
PERMISOS = {
    # Ambos roles
    "registrar_asientos":   {ROL_ADMIN, ROL_OPERADOR},
    "ver_libros":           {ROL_ADMIN, ROL_OPERADOR},   # Diario y Mayor
    "ver_reportes":         {ROL_ADMIN, ROL_OPERADOR},   # BG, ER, dashboard
    "exportar":             {ROL_ADMIN, ROL_OPERADOR},
    # Catálogo de cuentas: ahora disponible para ambos roles.
    "gestionar_cuentas":    {ROL_ADMIN, ROL_OPERADOR},   # RF-08, RF-09
    # Solo Administrador
    "administrar_usuarios": {ROL_ADMIN},
}

# Páginas de la barra lateral (claves de main.NAV_ITEMS) que exigen un permiso.
PAGINAS_RESTRINGIDAS = {
    "cuentas": "gestionar_cuentas",
    "usuarios": "administrar_usuarios",
}


def normalizar_rol(valor) -> str:
    """Convierte lo que haya en la columna `rol` a un rol válido.

    Cualquier valor desconocido (None, 'usuario', texto raro) se trata como
    Operador: ante la duda, el menor privilegio.
    """
    if isinstance(valor, str) and valor.strip().lower() in ("administrador", "admin"):
        return ROL_ADMIN
    return ROL_OPERADOR


def _rol_de_sesion():
    import db  # import diferido: db.py importa este módulo
    return db.rol_actual()


def es_admin(rol=None) -> bool:
    """True si el rol dado (o el de la sesión actual) es Administrador."""
    rol = rol if rol is not None else _rol_de_sesion()
    return normalizar_rol(rol) == ROL_ADMIN


def puede(permiso: str, rol=None) -> bool:
    """True si el rol dado (o el de la sesión actual) tiene el permiso.

    Sin sesión iniciada, el rol se considera Operador (sin privilegios extra).
    """
    rol = normalizar_rol(rol if rol is not None else _rol_de_sesion())
    return rol in PERMISOS.get(permiso, set())


def requiere(permiso: str) -> None:
    """Lanza PermissionError si la sesión actual no tiene el permiso."""
    if not puede(permiso):
        raise PermissionError(
            "Tu rol no tiene permiso para realizar esta acción "
            f"({permiso.replace('_', ' ')}). Solicítalo a un Administrador."
        )


def pagina_permitida(clave_pagina: str, rol=None) -> bool:
    """True si el rol puede abrir esa página de la barra lateral."""
    permiso = PAGINAS_RESTRINGIDAS.get(clave_pagina)
    return True if permiso is None else puede(permiso, rol)
