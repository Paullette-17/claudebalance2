# -*- coding: utf-8 -*-
"""
Cloud Balance - Contabilidad Digital
Pantalla de Login (PySide6)

Login conectado a SQLite (archivo `cloud_balance.db`, tabla
`usuarios`). Toda la lógica de conexión vive en db.py. La base se
crea sola la primera vez (usuario inicial: admin / Admin123).

Requisitos:
    pip install PySide6 bcrypt

Ejecutar:
    python login.py

Nota: aquí NO se pueden crear cuentas. Los usuarios los crea el
Administrador desde la página "Usuarios" dentro del sistema.
login.py, db.py y logo.png deben estar en la misma carpeta (src).
"""

import sys
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QComboBox, QGraphicsDropShadowEffect,
    QSizePolicy, QMainWindow, QGridLayout
)

import db
import roles
from db import DBError
from utilidades import RUTA_LOGO, configurar_campo_nombre, error_nombre

# ══════════════════════════════════════════════════════════
#  PALETA — tomada de styles.css (tema oscuro de Cloud Balance)
# ══════════════════════════════════════════════════════════
BG_MAIN = "#0a0d14"
BG_CARD = "#111622"
BG_CARD2 = "#161d2e"
BG_INPUT = "#0d121c"
ACCENT = "#4f8ef7"
ACCENT2 = "#7c3aed"
ACCENT3 = "#06d6a0"
DANGER = "#ef4444"
TEXT = "#e2e8f0"
TEXT_MUTED = "#64748b"
BORDER = "#1e293b"


class LoginWindow(QWidget):
    """Ventana de inicio de sesión."""

    login_exitoso = Signal(str)  # emite el nombre de usuario al loguearse

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cloud Balance — Iniciar sesión")
        self.setMinimumSize(960, 600)
        self.resize(1020, 640)
        self.setWindowState(self.windowState() | Qt.WindowMaximized)  # abre maximizada
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

    # -- Panel izquierdo: marca / branding contable -----------------------
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

        # -- Logo con más presencia
        logo = QLabel()
        logo.setPixmap(self._logo_pixmap(340))
        logo.setStyleSheet("background: transparent;")
        lay.addWidget(logo, 0, Qt.AlignHCenter)

        # -- Título simplificado: solo "Contabilidad Digital"
        titulo = QLabel("Contabilidad Digital")
        titulo.setStyleSheet(f"color:{TEXT}; background: transparent;")
        f = QFont("Poppins", 26, QFont.DemiBold)
        titulo.setFont(f)
        titulo.setAlignment(Qt.AlignCenter)
        lay.addWidget(titulo, 0, Qt.AlignHCenter)

        sub = QLabel(
            "Cuentas, Libro Diario, Libro Mayor, Balance General y\n"
            "Estado de Resultados en un solo lugar."
        )
        sub.setStyleSheet(f"color:{TEXT_MUTED}; background: transparent; font-size:13px;")
        sub.setFont(QFont("Poppins", 11))
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub, 0, Qt.AlignHCenter)

        lay.addSpacing(10)

        # -- Bloque de "presencia contable": mini indicadores tipo dashboard
        lay.addWidget(self._panel_indicadores_contables(), 0, Qt.AlignHCenter)

        lay.addStretch(2)

        pie = QLabel("Proyecto Integrador II — Equipo Contabilidad")
        pie.setStyleSheet(f"color:{TEXT_MUTED}; background: transparent; font-size:11px;")
        pie.setAlignment(Qt.AlignCenter)
        lay.addWidget(pie, 0, Qt.AlignHCenter)

        return panel

    def _panel_indicadores_contables(self):
        """Fila de mini-tarjetas que refuerzan visualmente el tema contable."""
        cont = QFrame()
        cont.setStyleSheet("background: transparent;")
        grid = QGridLayout(cont)
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        indicadores = [
            ("🧾", "Libro Diario"),
            ("📊", "Balance General"),
            ("💹", "Estado de Resultados"),
            ("📁", "Reportes"),
        ]

        for i, (icono, titulo) in enumerate(indicadores):
            item = QFrame()
            item.setStyleSheet("background: transparent;")
            il = QHBoxLayout(item)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(8)
            il.addStretch(1)

            lbl_icono = QLabel(icono)
            lbl_icono.setStyleSheet("background:transparent; font-size:16px;")
            il.addWidget(lbl_icono)

            lbl_titulo = QLabel(titulo)
            lbl_titulo.setStyleSheet(f"color:{TEXT}; background:transparent; font-size:12px; font-weight:600;")
            il.addWidget(lbl_titulo)
            il.addStretch(1)

            grid.addWidget(item, i // 2, i % 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return cont

    def _logo_pixmap(self, width: int) -> QPixmap:
        pix = QPixmap(RUTA_LOGO)
        if pix.isNull():
            # Si no se encuentra logo.png, se genera un pixmap vacío
            # para que la UI no truene.
            pix = QPixmap(width, 80)
            pix.fill(Qt.transparent)
            return pix
        return pix.scaledToWidth(width, Qt.SmoothTransformation)

    # -- Panel derecho: formulario ----------------------------------------
    def _build_panel_derecho(self):
        panel = QFrame()
        panel.setStyleSheet(f"background:{BG_MAIN};")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)

        self.card = QFrame()
        self.card.setFixedWidth(380)
        self.card.setStyleSheet(f"""
            QFrame#card {{
                background:{BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        self.card.setObjectName("card")

        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(34, 36, 34, 30)
        cl.setSpacing(6)

        titulo = QLabel("Bienvenido")
        titulo.setFont(QFont("Poppins", 19, QFont.Bold))
        titulo.setStyleSheet(f"color:{TEXT}; background:transparent;")
        cl.addWidget(titulo)

        sub = QLabel("Ingresa tus credenciales para continuar")
        sub.setFont(QFont("Poppins", 10))
        sub.setStyleSheet(f"color:{TEXT_MUTED}; background:transparent;")
        cl.addWidget(sub)
        cl.addSpacing(22)

        # -- Usuario
        cl.addWidget(self._campo_label("Usuario"))
        self.input_usuario = self._campo_input("Tu usuario")
        configurar_campo_nombre(self.input_usuario)  # sin números, mayúscula tras espacio
        cl.addWidget(self.input_usuario)
        cl.addSpacing(14)

        # -- Contraseña
        cl.addWidget(self._campo_label("Contraseña"))
        pass_row, self.input_password, self.btn_ver_pass = self._campo_password()
        cl.addWidget(pass_row)

        # -- Rol con el que se quiere ingresar
        cl.addSpacing(14)
        cl.addWidget(self._campo_label("Ingresar como"))
        self.combo_rol = QComboBox()
        self.combo_rol.setFixedHeight(38)
        self.combo_rol.addItem("🛡️  Administrador", roles.ROL_ADMIN)
        self.combo_rol.addItem("🧾  Usuario (Operador)", roles.ROL_OPERADOR)
        self.combo_rol.setCurrentIndex(1)  # por defecto: Usuario
        self.combo_rol.setStyleSheet(f"""
            QComboBox {{
                background:{BG_INPUT}; border:1px solid {BORDER};
                border-radius:8px; padding:0 12px; color:{TEXT}; font-size:12.5px;
            }}
            QComboBox:focus {{ border:1px solid {ACCENT}; }}
            QComboBox::drop-down {{ border:none; width:26px; }}
            QComboBox QAbstractItemView {{
                background:{BG_INPUT}; color:{TEXT}; border:1px solid {BORDER};
                selection-background-color:{ACCENT};
            }}
        """)
        cl.addWidget(self.combo_rol)

        # -- Olvidé contraseña
        opciones = QHBoxLayout()
        opciones.addStretch(1)
        link_olvide = QLabel('<a href="#" style="color:#4f8ef7; text-decoration:none;">¿Olvidaste tu contraseña?</a>')
        link_olvide.setStyleSheet("font-size:11px; background:transparent;")
        link_olvide.setOpenExternalLinks(False)
        opciones.addWidget(link_olvide)
        cl.addSpacing(10)
        cl.addLayout(opciones)
        cl.addSpacing(18)

        # -- Mensaje de error
        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet(f"color:{DANGER}; font-size:11px; background:transparent;")
        self.lbl_error.setVisible(False)
        cl.addWidget(self.lbl_error)

        # -- Botón login
        self.btn_login = QPushButton("Iniciar sesión")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(42)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {ACCENT}, stop:1 {ACCENT2});
                color: white; font-weight:600; font-size:13px;
                border:none; border-radius:8px;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
            QPushButton:pressed {{ background: {ACCENT2}; }}
            QPushButton:disabled {{ background: {BORDER}; color:{TEXT_MUTED}; }}
        """)
        self.btn_login.clicked.connect(self._on_login)
        cl.addWidget(self.btn_login)

        cl.addSpacing(14)

        # Enter para loguear
        self.input_usuario.returnPressed.connect(self._on_login)
        self.input_password.returnPressed.connect(self._on_login)

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

    def _campo_password(self):
        wrap = QFrame()
        wrap.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        inp = QLineEdit()
        inp.setPlaceholderText("••••••••")
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
    def _on_login(self):
        usuario = self.input_usuario.text().strip()
        password = self.input_password.text()

        if not usuario or not password:
            self._mostrar_error("Completa usuario y contraseña.")
            return

        msg = error_nombre(usuario, "El usuario")
        if msg:
            self._mostrar_error(msg)
            return

        if self.validar_credenciales(usuario, password):
            rol_elegido = self.combo_rol.currentData()
            if db.rol_actual() != rol_elegido:
                # La cuenta existe pero no tiene ese rol: se cierra la sesión.
                rol_real = db.rol_actual()
                db.cerrar_sesion()
                self._mostrar_error(
                    f"Tu cuenta es de tipo {rol_real}. "
                    f"Elige ese rol para ingresar.")
                return
            self._mostrar_error("")
            self.login_exitoso.emit(usuario)
        else:
            self._mostrar_error("Usuario o contraseña incorrectos.")

    def validar_credenciales(self, usuario: str, password: str) -> bool:
        """Valida usuario/contraseña contra la tabla `usuarios` en SQLite."""
        try:
            return db.validar_credenciales(usuario, password)
        except DBError as e:
            self._mostrar_error(str(e))
            return False

    def _mostrar_error(self, texto: str):
        self.lbl_error.setText(texto)
        self.lbl_error.setVisible(bool(texto))



# ══════════════════════════════════════════════════════════
#  Tras un login correcto se abre el sistema contable real
#  (VentanaPrincipal de main.py). db.validar_credenciales ya
#  dejó la sesión abierta (db.usuario_actual_id()), así que
#  VentanaPrincipal puede cargar las cuentas/asientos de ese
#  usuario desde SQLite apenas se construye.
# ══════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Poppins", 10))

    login = LoginWindow()

    def abrir_sistema(usuario):
        from main import VentanaPrincipal  # import diferido: evita ciclo de imports
        login.ventana_principal = VentanaPrincipal()
        login.ventana_principal.showMaximized()
        login.close()

    login.login_exitoso.connect(abrir_sistema)
    login.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()