# ═══════════════════════════════════════════════════════════
# usuarios.py — Página "Usuarios". SOLO el Administrador la ve.
# Lista los usuarios del sistema y permite crear nuevos
# (abre registro.py). Los usuarios nuevos quedan como Operador.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)

import db
from registro import RegistroWindow


class PaginaUsuarios(QWidget):
    def __init__(self):
        super().__init__()
        self.registro = None  # referencia a la ventana "Crear usuario"
        self._construir_ui()

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Usuarios"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Crea y consulta las cuentas de acceso al sistema")
        subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        self.lbl_alerta = QLabel("")
        raiz.addWidget(self.lbl_alerta)

        marco = QFrame(); marco.setProperty("class", "card")
        lay = QVBoxLayout(marco)
        cab = QHBoxLayout()
        cab.addWidget(QLabel("👥 Usuarios del sistema"))
        cab.addStretch()
        btn_nuevo = QPushButton("➕ Crear usuario"); btn_nuevo.setProperty("class", "btnPrimary")
        btn_nuevo.clicked.connect(self.abrir_registro)
        cab.addWidget(btn_nuevo)
        lay.addLayout(cab)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Usuario", "Nombre completo", "Rol", "Estado", "Último acceso"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.tabla)
        raiz.addWidget(marco)

    # ── Acciones ────────────────────────────────────────────
    def mostrar_alerta(self, msg, tipo="error"):
        color = "#06d6a0" if tipo == "success" else "#ef4444"
        self.lbl_alerta.setText(msg)
        self.lbl_alerta.setStyleSheet(f"padding:6px;color:{color};font-weight:600;")

    def abrir_registro(self):
        if self.registro is None or not self.registro.isVisible():
            self.registro = RegistroWindow()
            self.registro.cuenta_creada.connect(self._on_usuario_creado)
        self.registro.show()
        self.registro.raise_()
        self.registro.activateWindow()

    def _on_usuario_creado(self, usuario, _password):
        self.mostrar_alerta(f'✅ Usuario "{usuario}" creado como Operador.', "success")
        self.refrescar()

    # ── Render ──────────────────────────────────────────────
    def refrescar(self):
        try:
            filas = db.listar_usuarios()
        except (db.DBError, PermissionError) as e:
            self.mostrar_alerta(f"⚠️ {e}")
            return

        self.tabla.clearSpans()
        self.tabla.setRowCount(len(filas))
        for i, u in enumerate(filas):
            ultimo = u["ultimo_login"].strftime("%Y-%m-%d %H:%M") if u["ultimo_login"] else "—"
            valores = (u["nombre_usuario"], u["nombre_completo"] or "—", u["rol"],
                       "Activo" if u["activo"] else "Inactivo", ultimo)
            for col, v in enumerate(valores):
                self.tabla.setItem(i, col, QTableWidgetItem(str(v)))
