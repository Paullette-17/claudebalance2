# ═══════════════════════════════════════════════════════════
# ciclo_mensual.py — Ventana "Ciclo mensual".
# Muestra todas las carpetas (proyectos) creadas. Desde aquí se
# abre una carpeta, se crea una nueva o se renombra una existente.
# Se abre con el botón "Ciclo mensual" de la barra superior (main.py).
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt


class DialogoCicloMensual(QDialog):
    def __init__(self, ventana):
        super().__init__(ventana)
        self.ventana = ventana
        self.estado = ventana.estado
        self.setWindowTitle("Ciclo mensual")
        self.setMinimumSize(420, 440)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)

        titulo = QLabel("📅 Ciclo mensual")
        titulo.setProperty("class", "pageTitle")
        lay.addWidget(titulo)
        sub = QLabel("Elige una carpeta para abrirla (doble clic) o crea una nueva.")
        sub.setProperty("class", "pageSubtitle")
        lay.addWidget(sub)

        self.lista = QListWidget()
        self.lista.setObjectName("listaCiclos")
        self.lista.itemDoubleClicked.connect(lambda _: self._abrir())
        self.lista.itemSelectionChanged.connect(self._actualizar_botones)
        lay.addWidget(self.lista, stretch=1)

        fila = QHBoxLayout()
        self.btn_nueva = QPushButton("➕ Nueva carpeta")
        self.btn_nueva.setProperty("class", "btnPrimary")
        self.btn_nueva.clicked.connect(self._nueva)
        fila.addWidget(self.btn_nueva)
        self.btn_renombrar = QPushButton("✏️ Renombrar")
        self.btn_renombrar.setProperty("class", "btnGhost")
        self.btn_renombrar.clicked.connect(self._renombrar)
        fila.addWidget(self.btn_renombrar)
        fila.addStretch()
        self.btn_abrir = QPushButton("Abrir")
        self.btn_abrir.setProperty("class", "btnPrimary")
        self.btn_abrir.clicked.connect(self._abrir)
        fila.addWidget(self.btn_abrir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setProperty("class", "btnGhost")
        btn_cerrar.clicked.connect(self.reject)
        fila.addWidget(btn_cerrar)
        lay.addLayout(fila)

        self._llenar()

    # ── Lista ────────────────────────────────────────────────
    def _llenar(self, seleccionar_id=None):
        """Rellena la lista; selecciona `seleccionar_id` o, si no, la carpeta activa."""
        objetivo = seleccionar_id or self.estado.proyecto_actual_id
        self.lista.clear()
        fila_objetivo = 0
        for i, p in enumerate(self.estado.proyectos):
            activa = p.id == self.estado.proyecto_actual_id
            item = QListWidgetItem(f"📂 {p.nombre}" + ("   ✔ Abierta" if activa else ""))
            item.setData(Qt.UserRole, p.id)
            if activa:
                fuente = item.font(); fuente.setBold(True); item.setFont(fuente)
            self.lista.addItem(item)
            if p.id == objetivo:
                fila_objetivo = i
        self.lista.setCurrentRow(fila_objetivo)
        self._actualizar_botones()

    def _id_seleccionado(self):
        item = self.lista.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _actualizar_botones(self):
        hay = self._id_seleccionado() is not None
        self.btn_abrir.setEnabled(hay)
        self.btn_renombrar.setEnabled(hay)

    # ── Acciones ─────────────────────────────────────────────
    def _abrir(self):
        pid = self._id_seleccionado()
        if pid:
            self.ventana.abrir_proyecto(pid)
            self.accept()

    def _nueva(self):
        p = self.ventana.agregar_proyecto()   # crea y deja activa la nueva carpeta
        if p:
            self._llenar(p.id)

    def _renombrar(self):
        pid = self._id_seleccionado()
        if pid and self.ventana.editar_proyecto(pid):
            self._llenar(pid)
