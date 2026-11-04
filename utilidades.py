# ═══════════════════════════════════════════════════════════
# utilidades.py — Funciones y constantes compartidas por toda
# la aplicación (equivalente a la sección UTILS de app24.js)
# ═══════════════════════════════════════════════════════════
import os
import sys
import uuid
from datetime import date

from PySide6.QtWidgets import QInputDialog, QLineEdit, QDialog

def recurso(nombre: str) -> str:
    """Ruta ABSOLUTA de un archivo incluido con el programa (p. ej. logo.png).
    Funciona tanto ejecutando los .py como dentro del .exe (PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


# Ruta ABSOLUTA del logo, para que se vea sin importar desde qué carpeta
# se ejecute el programa (ni si corre desde el .exe).
RUTA_LOGO = recurso("logo.png")


def fmt(n) -> str:
    """Formatea un número como moneda en córdobas: 'C$ 1,234.50'"""
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        n = 0.0
    return f"C$ {n:,.2f}"


def fmt_num(n) -> str:
    """Formatea un número plano con dos decimales y separador de miles."""
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        n = 0.0
    return f"{n:,.2f}"


def nuevo_id() -> str:
    """Genera un identificador único (equivalente a uid() en JS)."""
    return uuid.uuid4().hex[:12]


def hoy() -> str:
    """Fecha actual en formato ISO YYYY-MM-DD (equivalente a today())."""
    return date.today().isoformat()


# ── PALETA DE COLORES (equivalente a las variables CSS :root) ─────
PALETA_OSCURA = {
    "bg_main": "#0a0d14",
    "bg_card": "#111622",
    "bg_card2": "#161d2e",
    "accent": "#4f8ef7",
    "accent2": "#7c3aed",
    "accent3": "#06d6a0",
    "danger": "#ef4444",
    "warn": "#f59e0b",
    "text": "#e2e8f0",
    "text_muted": "#64748b",
    "border": "#1e293b",
}

PALETA_CLARA = {
    "bg_main": "#f0f4f8",
    "bg_card": "#ffffff",
    "bg_card2": "#f8fafc",
    "accent": "#2563eb",
    "accent2": "#7c3aed",
    "accent3": "#059669",
    "danger": "#dc2626",
    "warn": "#d97706",
    "text": "#0f172a",
    "text_muted": "#64748b",
    "border": "#e2e8f0",
}

NATURALEZAS = ["Activo", "Pasivo", "Patrimonio", "Ingreso", "Egreso"]

# Color de badge por naturaleza (usado en tablas de cuentas)
COLOR_NATURALEZA = {
    "Activo": "#4f8ef7",
    "Pasivo": "#ef4444",
    "Patrimonio": "#7c3aed",
    "Ingreso": "#06d6a0",
    "Egreso": "#f59e0b",
}


def generar_qss(paleta: dict) -> str:
    """Construye la hoja de estilos Qt (QSS) a partir de una paleta de colores.
    Es el equivalente en escritorio al cambio de variables CSS del toggle de tema."""
    p = paleta
    return f"""
    QWidget {{
        background-color: {p['bg_main']};
        color: {p['text']};
        font-family: 'Segoe UI', 'Poppins', sans-serif;
        font-size: 13px;
    }}
    QFrame#sidebar {{
        background-color: {p['bg_card']};
        border-right: 1px solid {p['border']};
    }}
    QLabel#navSection {{
        color: {p['text_muted']};
        font-size: 10px;
        font-weight: 600;
        padding: 10px 14px 4px;
        letter-spacing: 1px;
    }}
    QPushButton#navItem {{
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-left: 3px solid transparent;
        color: {p['text_muted']};
        font-size: 13px;
        font-weight: 500;
        background: transparent;
    }}
    QPushButton#navItem:hover {{
        background: rgba(79,142,247,0.10);
        color: {p['text']};
    }}
    QPushButton#navItem:checked {{
        background: rgba(79,142,247,0.15);
        color: {p['accent']};
        border-left: 3px solid {p['accent']};
        font-weight: 600;
    }}
    QFrame.card {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}
    QLabel.pageTitle {{
        font-size: 20px;
        font-weight: 700;
    }}
    QLabel.pageSubtitle {{
        color: {p['text_muted']};
        font-size: 12px;
    }}
    QLabel.cardTitle {{
        font-size: 13px;
        font-weight: 600;
    }}
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
        background-color: {p['bg_main']};
        border: 1px solid {p['border']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {p['text']};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
        border: 1px solid {p['accent']};
    }}
    QPushButton.btnPrimary {{
        background-color: {p['accent']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 9px 16px;
        font-weight: 600;
    }}
    QPushButton.btnPrimary:hover {{ background-color: {p['accent2']}; }}
    QPushButton.btnGhost {{
        background-color: transparent;
        border: 1px solid {p['border']};
        color: {p['text_muted']};
        border-radius: 6px;
        padding: 8px 14px;
    }}
    QPushButton.btnGhost:hover {{ border-color: {p['accent']}; color: {p['accent']}; }}
    QPushButton.btnDanger {{
        background-color: {p['danger']};
        color: white; border: none; border-radius: 6px; padding: 6px 12px;
    }}
    QPushButton.btnExcel {{
        background-color: {p['accent3']};
        color: white; border: none; border-radius: 6px; padding: 8px 14px; font-weight: 600;
    }}
    QTableWidget {{
        background-color: {p['bg_card']};
        gridline-color: {p['border']};
        border: 1px solid {p['border']};
        border-radius: 8px;
    }}
    QHeaderView::section {{
        background-color: {p['bg_card2']};
        color: {p['text_muted']};
        padding: 6px;
        border: none;
        font-weight: 600;
        font-size: 11px;
    }}
    QListWidget#listaCiclos {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QListWidget#listaCiclos::item {{
        padding: 10px 12px;
        border-radius: 6px;
        color: {p['text']};
    }}
    QListWidget#listaCiclos::item:hover {{ background-color: {p['bg_card2']}; }}
    QListWidget#listaCiclos::item:selected {{
        background-color: rgba(79,142,247,0.18);
        color: {p['accent']};
    }}
    QTabWidget::pane {{ border: 1px solid {p['border']}; border-radius: 8px; }}
    """


# ═══════════════════════════════════════════════════════════
# VALIDACIÓN DE NOMBRES
# Solo letras (con tildes, ñ) y espacios. No se permiten números
# ni símbolos, y la primera letra de cada palabra (al inicio y
# después de cada espacio) se convierte en MAYÚSCULA.
# ═══════════════════════════════════════════════════════════
def formatear_nombre(texto: str, cursor: int = None):
    """Limpia un texto de nombre y devuelve (texto_limpio, nueva_posicion_cursor)."""
    resultado = []
    nueva_pos = 0
    inicio_palabra = True
    for i, c in enumerate(texto):
        if cursor is not None and i == cursor:
            nueva_pos = len(resultado)
        if c.isalpha():
            resultado.append(c.upper() if inicio_palabra else c)
            inicio_palabra = False
        elif c == " " and resultado and resultado[-1] != " ":
            resultado.append(c)          # un solo espacio entre palabras
            inicio_palabra = True
        # cualquier otro carácter (números, símbolos) se descarta
    if cursor is not None and cursor >= len(texto):
        nueva_pos = len(resultado)
    return "".join(resultado), nueva_pos


def configurar_campo_nombre(campo: QLineEdit, max_len: int = 60):
    """Activa la validación de nombres en un QLineEdit mientras se escribe
    (también al pegar texto)."""
    campo.setMaxLength(max_len)

    def _filtrar(texto):
        nuevo, pos = formatear_nombre(texto, campo.cursorPosition())
        if nuevo != texto:
            campo.setText(nuevo)
            campo.setCursorPosition(pos)

    campo.textEdited.connect(_filtrar)


def error_nombre(texto: str, etiqueta: str = "El nombre") -> str:
    """Devuelve un mensaje de error si el nombre no es válido, o '' si está bien."""
    t = (texto or "").strip()
    if not t:
        return f"{etiqueta} no puede estar vacío."
    if any(not (c.isalpha() or c == " ") for c in t):
        return f"{etiqueta} solo puede tener letras y espacios (sin números)."
    if sum(c.isalpha() for c in t) < 2:
        return f"{etiqueta} debe tener al menos 2 letras."
    if any(not palabra[0].isupper() for palabra in t.split()):
        return f"{etiqueta}: cada palabra debe empezar con mayúscula."
    return ""


def pedir_nombre(parent, titulo: str, etiqueta: str, texto: str = ""):
    """Como QInputDialog.getText, pero con la validación de nombres.
    Devuelve (texto, ok)."""
    dlg = QInputDialog(parent)
    dlg.setInputMode(QInputDialog.TextInput)
    dlg.setWindowTitle(titulo)
    dlg.setLabelText(etiqueta)
    dlg.setTextValue(texto)
    campo = dlg.findChild(QLineEdit)
    if campo is not None:
        configurar_campo_nombre(campo)
    ok = dlg.exec() == QDialog.Accepted
    return dlg.textValue(), ok
