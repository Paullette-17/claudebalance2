# ═══════════════════════════════════════════════════════════
# cuentas.py — Página "Cuentas". Alta / edición / eliminación
# del catálogo de cuentas. Equivalente a la sección CUENTAS
# de app24.js (guardarCuenta, renderCuentas, abrirModal, etc.)
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QLineEdit, QComboBox, QDoubleSpinBox, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QMessageBox, QDialog, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt

from utilidades import fmt, NATURALEZAS, COLOR_NATURALEZA


class DialogoEditarCuenta(QDialog):
    """Ventana modal para editar una cuenta existente (equivalente a #modal-editar)."""

    def __init__(self, cuenta, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Editar Cuenta")
        self.cuenta = cuenta
        form = QFormLayout(self)

        self.ed_codigo = QLineEdit(cuenta.codigo or ""); self.ed_codigo.setMaxLength(20)
        self.ed_nombre = QLineEdit(cuenta.nombre)
        self.ed_naturaleza = QComboBox(); self.ed_naturaleza.addItems(NATURALEZAS)
        self.ed_naturaleza.setCurrentText(cuenta.naturaleza)
        self.ed_saldo = QDoubleSpinBox(); self.ed_saldo.setRange(-999999999, 999999999)
        self.ed_saldo.setDecimals(2); self.ed_saldo.setValue(cuenta.saldo_inicial or 0)
        self.ed_desc = QLineEdit(cuenta.descripcion or "")

        form.addRow("Código", self.ed_codigo)
        form.addRow("Nombre", self.ed_nombre)
        form.addRow("Naturaleza", self.ed_naturaleza)
        form.addRow("Saldo Inicial", self.ed_saldo)
        form.addRow("Descripción", self.ed_desc)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        form.addRow(botones)

    def valores(self):
        return (self.ed_nombre.text().strip(), self.ed_naturaleza.currentText(),
                self.ed_saldo.value(), self.ed_desc.text().strip(),
                self.ed_codigo.text().strip())


class PaginaCuentas(QWidget):
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self.editando_id = None
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestión de Cuentas"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Registra y administra el catálogo de cuentas"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        self.lbl_alerta = QLabel(""); self.lbl_alerta.setStyleSheet("padding:6px;")
        raiz.addWidget(self.lbl_alerta)

        # ── Formulario ──
        marco_form = QFrame(); marco_form.setProperty("class", "card")
        lay_form = QVBoxLayout(marco_form)
        self.lbl_form_titulo = QLabel("➕ Nueva Cuenta"); self.lbl_form_titulo.setProperty("class", "cardTitle")
        lay_form.addWidget(self.lbl_form_titulo)

        fila1 = QHBoxLayout()
        self.in_codigo = QLineEdit(); self.in_codigo.setPlaceholderText("Ej. 1101")
        self.in_codigo.setMaxLength(20); self.in_codigo.setMaximumWidth(140)
        self.in_nombre = QLineEdit(); self.in_nombre.setPlaceholderText("Ej. Caja")
        self.in_naturaleza = QComboBox(); self.in_naturaleza.addItem("-- Seleccionar --", "")
        for n in NATURALEZAS:
            self.in_naturaleza.addItem(n, n)
        self.in_saldo = QDoubleSpinBox(); self.in_saldo.setRange(0, 999999999); self.in_saldo.setDecimals(2)
        self.in_saldo.setPrefix("C$ ")
        for lbl, w in (("Código", self.in_codigo), ("Nombre de la Cuenta", self.in_nombre),
                       ("Naturaleza", self.in_naturaleza),
                       ("Saldo Inicial", self.in_saldo)):
            col = QVBoxLayout()
            col.addWidget(QLabel(lbl))
            col.addWidget(w)
            fila1.addLayout(col)
        lay_form.addLayout(fila1)

        self.in_desc = QLineEdit(); self.in_desc.setPlaceholderText("Descripción breve")
        col_desc = QVBoxLayout(); col_desc.addWidget(QLabel("Descripción")); col_desc.addWidget(self.in_desc)
        lay_form.addLayout(col_desc)

        fila_btns = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar Cuenta"); btn_guardar.setProperty("class", "btnPrimary")
        btn_guardar.clicked.connect(self.guardar_cuenta)
        btn_cancelar = QPushButton("Cancelar"); btn_cancelar.setProperty("class", "btnGhost")
        btn_cancelar.clicked.connect(self.cancelar_edicion)
        fila_btns.addWidget(btn_guardar); fila_btns.addWidget(btn_cancelar); fila_btns.addStretch()
        lay_form.addLayout(fila_btns)
        raiz.addWidget(marco_form)

        # ── Tabla ──
        marco_tabla = QFrame(); marco_tabla.setProperty("class", "card")
        lay_tabla = QVBoxLayout(marco_tabla)
        cab = QHBoxLayout()
        cab.addWidget(QLabel("📋 Cuentas Registradas"))
        cab.addStretch()
        self.in_buscar = QLineEdit(); self.in_buscar.setPlaceholderText("🔍 Buscar...")
        self.in_buscar.textChanged.connect(self.refrescar)
        self.in_buscar.setFixedWidth(200)
        btn_excel = QPushButton("📊 Excel"); btn_excel.setProperty("class", "btnExcel")
        btn_excel.clicked.connect(self.exportar_excel)
        cab.addWidget(self.in_buscar); cab.addWidget(btn_excel)
        lay_tabla.addLayout(cab)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Código", "Nombre", "Naturaleza", "Descripción", "Saldo Inicial", "Saldo Actual", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        lay_tabla.addWidget(self.tabla)
        raiz.addWidget(marco_tabla)

        self.refrescar()

    # ── Acciones ────────────────────────────────────────────
    def mostrar_alerta(self, msg, tipo="error"):
        color = "#06d6a0" if tipo == "success" else "#ef4444"
        self.lbl_alerta.setText(msg)
        self.lbl_alerta.setStyleSheet(f"padding:6px;color:{color};font-weight:600;")

    def guardar_cuenta(self):
        codigo = self.in_codigo.text().strip()
        nombre = self.in_nombre.text().strip()
        nat = self.in_naturaleza.currentData()
        saldo = self.in_saldo.value()
        desc = self.in_desc.text().strip()

        if not nombre:
            return self.mostrar_alerta("⚠️ Ingresa el nombre de la cuenta.")
        if not nat:
            return self.mostrar_alerta("⚠️ Selecciona la naturaleza.")
        if self.estado.nombre_existe(nombre, excepto_id=self.editando_id):
            return self.mostrar_alerta("⚠️ Ya existe una cuenta con ese nombre.")
        if self.estado.codigo_existe(codigo, excepto_id=self.editando_id):
            return self.mostrar_alerta("⚠️ Ya existe una cuenta con ese código.")

        if self.editando_id:
            self.estado.editar_cuenta(self.editando_id, nombre, nat, saldo, desc, codigo)
            self.editando_id = None
            self.lbl_form_titulo.setText("➕ Nueva Cuenta")
        else:
            self.estado.agregar_cuenta(nombre, nat, saldo, desc, codigo)
            self.mostrar_alerta(f'✅ Cuenta "{nombre}" registrada.', "success")

        self.in_codigo.clear(); self.in_nombre.clear(); self.in_naturaleza.setCurrentIndex(0)
        self.in_saldo.setValue(0); self.in_desc.clear()

    def cancelar_edicion(self):
        self.editando_id = None
        self.lbl_form_titulo.setText("➕ Nueva Cuenta")
        self.in_codigo.clear(); self.in_nombre.clear(); self.in_naturaleza.setCurrentIndex(0)
        self.in_saldo.setValue(0); self.in_desc.clear()

    def abrir_edicion(self, cuenta_id):
        c = next((x for x in self.estado.cuentas if x.id == cuenta_id), None)
        if not c:
            return
        dlg = DialogoEditarCuenta(c, self)
        if dlg.exec() == QDialog.Accepted:
            nombre, nat, saldo, desc, codigo = dlg.valores()
            if self.estado.codigo_existe(codigo, excepto_id=cuenta_id):
                QMessageBox.warning(self, "Código repetido",
                                    f"Ya existe otra cuenta con el código '{codigo}'.")
                return
            self.estado.editar_cuenta(cuenta_id, nombre, nat, saldo, desc, codigo)

    def eliminar(self, cuenta_id):
        c = next((x for x in self.estado.cuentas if x.id == cuenta_id), None)
        nombre = c.nombre if c else ""
        if any(p.cuenta == cuenta_id for a in self.estado.asientos for p in a.partidas):
            QMessageBox.warning(self, "No se puede eliminar",
                                f"La cuenta '{nombre}' tiene movimientos en el Libro Diario.\n"
                                "Eliminarla dejaría asientos descuadrados.")
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Eliminar la cuenta '{nombre}'?")
        if resp == QMessageBox.Yes:
            self.estado.eliminar_cuenta(cuenta_id)

    def exportar_excel(self):
        from exportar_excel import exportar_cuentas_excel
        exportar_cuentas_excel(self.estado, self)

    # ── Render ──────────────────────────────────────────────
    def refrescar(self):
        buscar = self.in_buscar.text().lower()
        filtradas = [c for c in self.estado.cuentas
                     if buscar in c.nombre.lower() or buscar in c.naturaleza.lower()
                     or buscar in (c.codigo or "").lower()]
        self.tabla.clearSpans()  # quita la fusión del mensaje "No hay cuentas"
        self.tabla.setRowCount(len(filtradas))
        for fila, c in enumerate(filtradas):
            saldo = self.estado.saldo_cuenta(c.id)
            self.tabla.setItem(fila, 0, QTableWidgetItem(c.codigo or "—"))
            self.tabla.setItem(fila, 1, QTableWidgetItem(c.nombre))
            item_nat = QTableWidgetItem(c.naturaleza)
            item_nat.setForeground(Qt.GlobalColor.white)
            item_nat.setBackground(Qt.GlobalColor.transparent)
            self.tabla.setItem(fila, 2, item_nat)
            self.tabla.setItem(fila, 3, QTableWidgetItem(c.descripcion or "—"))
            self.tabla.setItem(fila, 4, QTableWidgetItem(fmt(c.saldo_inicial or 0)))
            item_saldo = QTableWidgetItem(fmt(saldo))
            item_saldo.setForeground(Qt.GlobalColor.green if saldo >= 0 else Qt.GlobalColor.red)
            self.tabla.setItem(fila, 5, item_saldo)

            cont = QWidget(); lay = QHBoxLayout(cont); lay.setContentsMargins(2, 2, 2, 2)
            btn_editar = QPushButton("✏️"); btn_editar.setFixedWidth(30)
            btn_editar.clicked.connect(lambda _, cid=c.id: self.abrir_edicion(cid))
            btn_borrar = QPushButton("🗑️"); btn_borrar.setFixedWidth(30)
            btn_borrar.clicked.connect(lambda _, cid=c.id: self.eliminar(cid))
            lay.addWidget(btn_editar); lay.addWidget(btn_borrar)
            self.tabla.setCellWidget(fila, 6, cont)

        if not filtradas:
            self.tabla.setRowCount(1)
            item = QTableWidgetItem("📂 No hay cuentas registradas")
            self.tabla.setItem(0, 0, item)
            self.tabla.setSpan(0, 0, 1, 7)
