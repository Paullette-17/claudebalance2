# -*- coding: utf-8 -*-
"""
Cloud Balance - Contabilidad Digital
Ventana "Crear usuario" (PySide6) — SOLO para el Administrador.

Se abre desde la página Usuarios (usuarios.py) dentro del sistema.
Conectado a SQLite (archivo `cloud_balance.db`, tabla `usuarios`)
a través de db.py: al crear la cuenta, se inserta ahí con la
contraseña hasheada con bcrypt.

Requisitos:
    pip install PySide6 bcrypt

No se ejecuta sola: requiere una sesión de Administrador.
"""

import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QGraphicsDropShadowEffect
)

import db
from db import DBError
from utilidades import RUTA_LOGO, configurar_campo_nombre, error_nombre

# ══════════════════════════════════════════════════════════
#  PALETA — igual que login.py, tema oscuro de Cloud Balance
# ══════════════════════════════════════════════════════════
BG_MAIN = "#0a0d14"
BG_CARD = "#111622"
BG_INPUT = "#0d121c"
ACCENT = "#4f8ef7"
ACCENT2 = "#7c3aed"
ACCENT3 = "#06d6a0"
DANGER = "#ef4444"
TEXT = "#e2e8f0"
TEXT_MUTED = "#64748b"
BORDER = "#1e293b"


class RegistroWindow(QWidget):
    """Ventana de creación de cuenta."""

    cuenta_creada = Signal(str, str)  # usuario, password

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cloud Balance — Crear usuario")
        self.setMinimumSize(960, 620)
        self.resize(1020, 660)
        self.setStyleSheet(f"background-color:{BG_MAIN};")

        self._build_ui()
        self._apply_shadow(self.card)

    # ────────────────────────────────────────────────────
    #  UI
    # ────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_panel_izquierdo(), 5)
        root.addWidget(self._build_panel_derecho(), 4)

    # -- Panel izquierdo: mismo branding que login.py ----------------------
    def _build_panel_izquierdo(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0d14, stop:0.5 #101a33, stop:1 #1a1030
                );
                border-right: 1px solid {BORDER};
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(60, 50, 60, 50)
        lay.setSpacing(20)
        lay.addStretch(1)

        logo = QLabel()
        logo.setPixmap(self._logo_pixmap(340))
        logo.setStyleSheet("background: transparent;")
        lay.addWidget(logo, 0, Qt.AlignHCenter)

        titulo = QLabel("Contabilidad Digital")
        titulo.setStyleSheet(f"color:{TEXT}; background: transparent;")
        titulo.setFont(QFont("Poppins", 26, QFont.DemiBold))
        titulo.setAlignment(Qt.AlignCenter)
        lay.addWidget(titulo, 0, Qt.AlignHCenter)

        sub = QLabel(
            "Crea tu cuenta y empieza a llevar tu\n"
            "contabilidad de forma ordenada y segura."
        )
        sub.setStyleSheet(f"color:{TEXT_MUTED}; background: transparent; font-size:13px;")
        sub.setFont(QFont("Poppins", 11))
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub, 0, Qt.AlignHCenter)

        lay.addStretch(2)

        pie = QLabel("Proyecto Integrador II — Equipo Contabilidad")
        pie.setStyleSheet(f"color:{TEXT_MUTED}; background: transparent; font-size:11px;")
        pie.setAlignment(Qt.AlignCenter)
        lay.addWidget(pie, 0, Qt.AlignHCenter)

        return panel

    def _logo_pixmap(self, width: int) -> QPixmap:
        pix = QPixmap(RUTA_LOGO)
        if pix.isNull():
            pix = QPixmap(width, 80)
            pix.fill(Qt.transparent)
            return pix
        return pix.scaledToWidth(width, Qt.SmoothTransformation)

    # -- Panel derecho: formulario de registro -----------------------------
    def _build_panel_derecho(self):
        panel = QFrame()
        panel.setStyleSheet(f"background:{BG_MAIN};")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)

        self.card = QFrame()
        self.card.setFixedWidth(400)
        self.card.setObjectName("card")
        self.card.setStyleSheet(f"""
            QFrame#card {{
                background:{BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)

        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(34, 32, 34, 26)
        cl.setSpacing(6)

        titulo = QLabel("Crear usuario")
        titulo.setFont(QFont("Poppins", 19, QFont.Bold))
        titulo.setStyleSheet(f"color:{TEXT}; background:transparent;")
        cl.addWidget(titulo)

        sub = QLabel("Registra un nuevo usuario (rol Operador)")
        sub.setFont(QFont("Poppins", 10))
        sub.setStyleSheet(f"color:{TEXT_MUTED}; background:transparent;")
        cl.addWidget(sub)
        cl.addSpacing(18)

        # -- Nombre completo
        cl.addWidget(self._campo_label("Nombre completo"))
        self.input_nombre = self._campo_input("Ej. María López")
        configurar_campo_nombre(self.input_nombre)
        cl.addWidget(self.input_nombre)
        cl.addSpacing(12)

        # -- Usuario
        cl.addWidget(self._campo_label("Usuario"))
        self.input_usuario = self._campo_input("Elige un usuario")
        configurar_campo_nombre(self.input_usuario)
        cl.addWidget(self.input_usuario)
        cl.addSpacing(12)

        # -- Contraseña
        cl.addWidget(self._campo_label("Contraseña"))
        pass_row, self.input_password, _ = self._campo_password("Mínimo 6 caracteres")
        cl.addWidget(pass_row)
        cl.addSpacing(12)

        # -- Confirmar contraseña
        cl.addWidget(self._campo_label("Confirmar contraseña"))
        pass_row2, self.input_password2, _ = self._campo_password("Repite la contraseña")
        cl.addWidget(pass_row2)
        cl.addSpacing(14)

        # -- Mensaje de error / éxito
        self.lbl_msg = QLabel("")
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setStyleSheet(f"color:{DANGER}; font-size:11px; background:transparent;")
        self.lbl_msg.setVisible(False)
        cl.addWidget(self.lbl_msg)

        # -- Botón crear cuenta
        self.btn_crear = QPushButton("Crear usuario")
        self.btn_crear.setCursor(Qt.PointingHandCursor)
        self.btn_crear.setFixedHeight(42)
        self.btn_crear.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT}, stop:1 {ACCENT2});
                color: white; font-weight:600; font-size:13px;
                border:none; border-radius:8px;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
            QPushButton:pressed {{ background: {ACCENT2}; }}
        """)
        self.btn_crear.clicked.connect(self._on_crear_cuenta)
        cl.addWidget(self.btn_crear)

        cl.addSpacing(12)

        # Enter para enviar el formulario
        self.input_password2.returnPressed.connect(self._on_crear_cuenta)

        row.addWidget(self.card)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)
        return panel

    def _campo_label(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color:{TEXT}; font-size:11px; font-weight:600; background:transparent;")
        return lbl

    def _campo_input(self, placeholder):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(38)
        inp.setStyleSheet(self._input_style())
        return inp

    def _input_style(self):
        return f"""
            QLineEdit {{
                background:{BG_INPUT};
                border:1px solid {BORDER};
                border-radius:8px;
                padding:0 12px;
                color:{TEXT};
                font-size:12.5px;
            }}
            QLineEdit:focus {{
                border:1px solid {ACCENT};
            }}
        """

    def _campo_password(self, placeholder):
        wrap = QFrame()
        wrap.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setEchoMode(QLineEdit.Password)
        inp.setFixedHeight(38)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background:{BG_INPUT};
                border:1px solid {BORDER};
                border-top-left-radius:8px; border-bottom-left-radius:8px;
                border-right: none;
                padding:0 12px;
                color:{TEXT};
                font-size:12.5px;
            }}
            QLineEdit:focus {{ border:1px solid {ACCENT}; border-right:none; }}
        """)

        btn = QPushButton("👁")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(38, 38)
        btn.setCheckable(True)
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG_INPUT};
                border:1px solid {BORDER};
                border-top-right-radius:8px; border-bottom-right-radius:8px;
                color:{TEXT_MUTED};
            }}
            QPushButton:checked {{ color:{ACCENT}; }}
        """)
        btn.toggled.connect(lambda checked: inp.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))

        lay.addWidget(inp, 1)
        lay.addWidget(btn, 0)
        return wrap, inp, btn

    def _apply_shadow(self, widget):
        efecto = QGraphicsDropShadowEffect(self)
        efecto.setBlurRadius(40)
        efecto.setOffset(0, 12)
        efecto.setColor(QColor(0, 0, 0, 160))
        widget.setGraphicsEffect(efecto)

    # ────────────────────────────────────────────────────
    #  LÓGICA
    # ────────────────────────────────────────────────────
    def _on_crear_cuenta(self):
        nombre = self.input_nombre.text().strip()
        usuario = self.input_usuario.text().strip()
        password = self.input_password.text()
        password2 = self.input_password2.text()

        if not all([nombre, usuario, password, password2]):
            self._mostrar_msg("Completa todos los campos.", error=True)
            return

        for valor, etiqueta in ((nombre, "El nombre completo"), (usuario, "El usuario")):
            msg = error_nombre(valor, etiqueta)
            if msg:
                self._mostrar_msg(msg, error=True)
                return

        if len(password) < 6:
            self._mostrar_msg("La contraseña debe tener al menos 6 caracteres.", error=True)
            return

        if password != password2:
            self._mostrar_msg("Las contraseñas no coinciden.", error=True)
            return

        self.btn_crear.setEnabled(False)
        try:
            if db.usuario_existe(usuario):
                self._mostrar_msg("Ese usuario ya existe, elige otro.", error=True)
                return

            db.crear_usuario(usuario, password, nombre)
        except (DBError, PermissionError) as e:
            self._mostrar_msg(str(e), error=True)
            return
        finally:
            self.btn_crear.setEnabled(True)

        self._mostrar_msg("Usuario creado correctamente.", error=False)
        self.cuenta_creada.emit(usuario, password)
        self.close()

    def _mostrar_msg(self, texto: str, error: bool = True):
        color = DANGER if error else ACCENT3
        self.lbl_msg.setStyleSheet(f"color:{color}; font-size:11px; background:transparent;")
        self.lbl_msg.setText(texto)
        self.lbl_msg.setVisible(bool(texto))
