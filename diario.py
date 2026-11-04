# ═══════════════════════════════════════════════════════════
# diario.py — Página "Libro Diario". Registro de asientos con
# líneas Debe/Haber dinámicas y verificación de cuadre.
# Equivalente a la sección DIARIO de app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QLineEdit, QComboBox, QDoubleSpinBox, QPushButton,
                                QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                                QCheckBox, QDialog, QMessageBox)
from PySide6.QtCore import Qt, QDate

from utilidades import fmt, hoy, nuevo_id
from modelos import Partida
import db


class FilaPartida:
    """Agrupa los widgets de una línea Debe/Haber del formulario de asiento."""

    def __init__(self, pagina, indice):
        self.pagina = pagina
        self.contenedor = QFrame()
        lay = QHBoxLayout(self.contenedor)
        lay.setContentsMargins(0, 0, 0, 0)

        self.combo_cuenta = QComboBox()
        self.combo_cuenta.addItem("-- Seleccionar --", "")
        for c in pagina.estado.cuentas:
            self.combo_cuenta.addItem(c.nombre, c.id)
        self.combo_cuenta.currentIndexChanged.connect(pagina.verificar_cuadre)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Debe", "Haber"])
        self.combo_tipo.currentIndexChanged.connect(pagina.verificar_cuadre)

        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0, 999999999); self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("C$ ")
        self.spin_monto.valueChanged.connect(pagina.verificar_cuadre)

        self.in_desc = QLineEdit(); self.in_desc.setPlaceholderText("Descripción de la línea")

        self.btn_quitar = QPushButton("✕"); self.btn_quitar.setFixedWidth(28)
        self.btn_quitar.clicked.connect(lambda: pagina.quitar_partida(self))

        for w in (self.combo_cuenta, self.combo_tipo, self.spin_monto, self.in_desc, self.btn_quitar):
            lay.addWidget(w)

    def cargar(self, partida):
        """Rellena la fila con los datos de una partida existente (modo edición)."""
        i = self.combo_cuenta.findData(partida.cuenta)
        if i >= 0:
            self.combo_cuenta.setCurrentIndex(i)
        self.combo_tipo.setCurrentText(partida.tipo)
        self.spin_monto.setValue(float(partida.monto))
        self.in_desc.setText(partida.descripcion or "")

    def a_partida(self):
        return Partida(id=nuevo_id(), cuenta=self.combo_cuenta.currentData(),
                        tipo=self.combo_tipo.currentText(), monto=self.spin_monto.value(),
                        descripcion=self.in_desc.text().strip())


class DialogoEditarAsiento(QDialog):
    """Ventana para modificar un asiento ya registrado. Reutiliza FilaPartida,
    por eso expone lo mismo que la página: `estado`, `verificar_cuadre` y
    `quitar_partida`."""

    def __init__(self, estado, asiento, padre=None):
        super().__init__(padre)
        self.estado = estado
        self.asiento = asiento
        self.filas_partidas: list[FilaPartida] = []
        self.setWindowTitle(f"Editar asiento N° {asiento.num}")
        self.setMinimumWidth(760)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"✏️ Editar Asiento N° {asiento.num}"))

        fila_cab = QHBoxLayout()
        self.in_fecha = QDateEdit(QDate.fromString(asiento.fecha, "yyyy-MM-dd"))
        self.in_fecha.setCalendarPopup(True)
        self.in_desc = QLineEdit(asiento.descripcion)
        for lbl, w in (("Fecha", self.in_fecha), ("Descripción / Concepto", self.in_desc)):
            col = QVBoxLayout(); col.addWidget(QLabel(lbl)); col.addWidget(w)
            fila_cab.addLayout(col)
        lay.addLayout(fila_cab)

        self.lbl_cuadre = QLabel("")
        self.lbl_error = QLabel("")

        self.contenedor_partidas = QVBoxLayout()
        lay.addLayout(self.contenedor_partidas)
        for p in asiento.partidas:
            self.agregar_partida(p)
        while len(self.filas_partidas) < 2:
            self.agregar_partida()

        btn_agregar = QPushButton("➕ Agregar línea"); btn_agregar.setProperty("class", "btnGhost")
        btn_agregar.clicked.connect(lambda: self.agregar_partida())
        lay.addWidget(btn_agregar)

        lay.addWidget(self.lbl_cuadre)
        lay.addWidget(self.lbl_error)

        fila_btns = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar cambios"); btn_guardar.setProperty("class", "btnPrimary")
        btn_guardar.clicked.connect(self.guardar)
        btn_cancelar = QPushButton("Cancelar"); btn_cancelar.setProperty("class", "btnGhost")
        btn_cancelar.clicked.connect(self.reject)
        fila_btns.addStretch(); fila_btns.addWidget(btn_cancelar); fila_btns.addWidget(btn_guardar)
        lay.addLayout(fila_btns)
        self.verificar_cuadre()

    def agregar_partida(self, partida=None):
        fila = FilaPartida(self, len(self.filas_partidas))
        if partida is not None:
            fila.cargar(partida)
        self.filas_partidas.append(fila)
        self.contenedor_partidas.addWidget(fila.contenedor)
        self.verificar_cuadre()

    def quitar_partida(self, fila):
        if len(self.filas_partidas) <= 2:
            return
        self.filas_partidas.remove(fila)
        self.contenedor_partidas.removeWidget(fila.contenedor)
        fila.contenedor.deleteLater()
        self.verificar_cuadre()

    def verificar_cuadre(self):
        debe = sum(f.spin_monto.value() for f in self.filas_partidas if f.combo_tipo.currentText() == "Debe")
        haber = sum(f.spin_monto.value() for f in self.filas_partidas if f.combo_tipo.currentText() == "Haber")
        if abs(debe - haber) > 0.01:
            self.lbl_cuadre.setText(f"⚠️ Desbalanceado — Debe: {fmt(debe)} | Haber: {fmt(haber)}")
            self.lbl_cuadre.setStyleSheet("color:#f59e0b;font-weight:600;padding:6px;")
        else:
            self.lbl_cuadre.setText(f"✅ Cuadrado — Debe: {fmt(debe)} | Haber: {fmt(haber)}")
            self.lbl_cuadre.setStyleSheet("color:#06d6a0;font-weight:600;padding:6px;")

    def _error(self, msg):
        self.lbl_error.setText(msg)
        self.lbl_error.setStyleSheet("padding:6px;color:#ef4444;font-weight:600;")

    def guardar(self):
        desc = self.in_desc.text().strip()
        if not desc:
            return self._error("⚠️ Ingresa una descripción.")
        partidas = [f.a_partida() for f in self.filas_partidas
                    if f.combo_cuenta.currentData() and f.spin_monto.value() > 0]
        if len(partidas) < 2:
            return self._error("⚠️ Necesitas al menos dos partidas.")
        debe = sum(p.monto for p in partidas if p.tipo == "Debe")
        haber = sum(p.monto for p in partidas if p.tipo == "Haber")
        if abs(debe - haber) > 0.01:
            return self._error("❌ El asiento no está balanceado (Debe ≠ Haber).")
        fecha = self.in_fecha.date().toString("yyyy-MM-dd")
        try:
            self.estado.editar_asiento(self.asiento.id, fecha, desc, partidas)
        except (db.DBError, PermissionError) as e:
            return self._error(f"❌ {e}")
        self.accept()


class PaginaDiario(QWidget):
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self.filas_partidas: list[FilaPartida] = []
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar_tabla)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Libro Diario"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Registro cronológico de asientos contables"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        self.lbl_alerta = QLabel(""); raiz.addWidget(self.lbl_alerta)

        # ── Formulario nuevo asiento ──
        marco = QFrame(); marco.setProperty("class", "card")
        lay = QVBoxLayout(marco)
        lay.addWidget(QLabel("✏️ Nuevo Asiento Contable"))

        fila_cab = QHBoxLayout()
        self.in_fecha = QDateEdit(QDate.currentDate()); self.in_fecha.setCalendarPopup(True)
        self.in_desc = QLineEdit(); self.in_desc.setPlaceholderText("Ej. Compra de mercancía al contado")
        self.lbl_num = QLabel(str(self.estado.next_asiento_num))
        for lbl, w in (("Fecha", self.in_fecha), ("Descripción / Concepto", self.in_desc),
                       ("N° Asiento", self.lbl_num)):
            col = QVBoxLayout(); col.addWidget(QLabel(lbl)); col.addWidget(w)
            fila_cab.addLayout(col)
        lay.addLayout(fila_cab)

        self.contenedor_partidas = QVBoxLayout()
        lay.addLayout(self.contenedor_partidas)

        btn_agregar = QPushButton("➕ Agregar línea"); btn_agregar.setProperty("class", "btnGhost")
        btn_agregar.clicked.connect(lambda: self.agregar_partida())
        lay.addWidget(btn_agregar)

        self.lbl_cuadre = QLabel(""); lay.addWidget(self.lbl_cuadre)

        fila_btns = QHBoxLayout()
        btn_guardar = QPushButton("💾 Registrar Asiento"); btn_guardar.setProperty("class", "btnPrimary")
        btn_guardar.clicked.connect(self.guardar_asiento)
        btn_limpiar = QPushButton("🗑️ Limpiar"); btn_limpiar.setProperty("class", "btnGhost")
        btn_limpiar.clicked.connect(self.limpiar_asiento)
        fila_btns.addWidget(btn_guardar); fila_btns.addWidget(btn_limpiar); fila_btns.addStretch()
        lay.addLayout(fila_btns)
        raiz.addWidget(marco)

        # ── Tabla de asientos ──
        marco_tabla = QFrame(); marco_tabla.setProperty("class", "card")
        lay_tabla = QVBoxLayout(marco_tabla)
        cab = QHBoxLayout()
        cab.addWidget(QLabel("📋 Asientos Registrados"))
        cab.addStretch()
        self.in_f1 = QDateEdit(QDate.currentDate()); self.in_f1.setCalendarPopup(True)
        self.in_f2 = QDateEdit(QDate.currentDate()); self.in_f2.setCalendarPopup(True)
        self.chk_filtro = QCheckBox("Filtrar")
        self.chk_filtro.toggled.connect(lambda _: self.refrescar_tabla())
        self.in_f1.dateChanged.connect(self.refrescar_tabla)
        self.in_f2.dateChanged.connect(self.refrescar_tabla)
        btn_excel = QPushButton("📊 Excel"); btn_excel.setProperty("class", "btnExcel")
        btn_excel.clicked.connect(self.exportar_excel)
        cab.addWidget(self.chk_filtro)
        cab.addWidget(QLabel("Desde")); cab.addWidget(self.in_f1)
        cab.addWidget(QLabel("Hasta")); cab.addWidget(self.in_f2)
        cab.addWidget(btn_excel)
        lay_tabla.addLayout(cab)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["#", "Fecha", "Descripción", "Cuenta", "Debe", "Haber", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        lay_tabla.addWidget(self.tabla)
        raiz.addWidget(marco_tabla)

        self.iniciar_diario()

    # ── Partidas dinámicas ──────────────────────────────────
    def iniciar_diario(self):
        self.in_fecha.setDate(QDate.currentDate())
        self.lbl_num.setText(str(self.estado.next_asiento_num))
        for f in list(self.filas_partidas):
            self.contenedor_partidas.removeWidget(f.contenedor)
            f.contenedor.deleteLater()
        self.filas_partidas = []
        self.agregar_partida(tipo_defecto="Debe")
        self.agregar_partida(tipo_defecto="Haber")

    def agregar_partida(self, tipo_defecto="Debe"):
        fila = FilaPartida(self, len(self.filas_partidas))
        fila.combo_tipo.setCurrentText(tipo_defecto)
        self.filas_partidas.append(fila)
        self.contenedor_partidas.addWidget(fila.contenedor)
        self.verificar_cuadre()

    def quitar_partida(self, fila):
        if len(self.filas_partidas) <= 2:
            return
        self.filas_partidas.remove(fila)
        self.contenedor_partidas.removeWidget(fila.contenedor)
        fila.contenedor.deleteLater()
        self.verificar_cuadre()

    def verificar_cuadre(self):
        debe = sum(f.spin_monto.value() for f in self.filas_partidas if f.combo_tipo.currentText() == "Debe")
        haber = sum(f.spin_monto.value() for f in self.filas_partidas if f.combo_tipo.currentText() == "Haber")
        if debe != haber and (debe > 0 or haber > 0):
            self.lbl_cuadre.setText(f"⚠️ Desbalanceado — Debe: {fmt(debe)} | Haber: {fmt(haber)}")
            self.lbl_cuadre.setStyleSheet("color:#f59e0b;font-weight:600;padding:6px;")
        else:
            self.lbl_cuadre.setText("")

    # ── Acciones ─────────────────────────────────────────────
    def mostrar_alerta(self, msg, tipo="error"):
        color = "#06d6a0" if tipo == "success" else "#ef4444"
        self.lbl_alerta.setText(msg)
        self.lbl_alerta.setStyleSheet(f"padding:6px;color:{color};font-weight:600;")

    def guardar_asiento(self):
        fecha = self.in_fecha.date().toString("yyyy-MM-dd")
        desc = self.in_desc.text().strip()
        if not desc:
            return self.mostrar_alerta("⚠️ Ingresa una descripción.")

        partidas = [f.a_partida() for f in self.filas_partidas
                    if f.combo_cuenta.currentData() and f.spin_monto.value() > 0]
        if len(partidas) < 2:
            return self.mostrar_alerta("⚠️ Necesitas al menos dos partidas.")

        debe = sum(p.monto for p in partidas if p.tipo == "Debe")
        haber = sum(p.monto for p in partidas if p.tipo == "Haber")
        if abs(debe - haber) > 0.01:
            return self.mostrar_alerta("❌ El asiento no está balanceado (Debe ≠ Haber).")

        self.estado.registrar_asiento(fecha, desc, partidas)
        self.mostrar_alerta("✅ Asiento registrado.", "success")
        self.limpiar_asiento()

    def limpiar_asiento(self):
        self.in_desc.clear()
        self.iniciar_diario()

    def editar_asiento(self, asiento_id):
        a = next((x for x in self.estado.asientos if x.id == asiento_id), None)
        if a is None:
            return
        dlg = DialogoEditarAsiento(self.estado, a, self)
        if dlg.exec() == QDialog.Accepted:
            self.mostrar_alerta(f"✅ Asiento N° {a.num} actualizado.", "success")

    def exportar_excel(self):
        from exportar_excel import exportar_diario_excel
        exportar_diario_excel(self.estado, self)

    # ── Render ───────────────────────────────────────────────
    def refrescar_tabla(self):
        asientos = sorted(self.estado.asientos, key=lambda a: a.num)
        if self.chk_filtro.isChecked():
            desde = self.in_f1.date().toString("yyyy-MM-dd")
            hasta = self.in_f2.date().toString("yyyy-MM-dd")
            asientos = [a for a in asientos if desde <= a.fecha <= hasta]
        filas_html = []
        for a in asientos:
            for p in a.partidas:
                filas_html.append((a, p))

        self.tabla.clearSpans()  # quita la fusión del mensaje "Sin asientos"
        self.tabla.clearContents()  # limpia también los botones de la actualización anterior
        self.tabla.setRowCount(len(filas_html))
        fila_i = 0
        asiento_anterior = None
        for a, p in filas_html:
            c = next((x for x in self.estado.cuentas if x.id == p.cuenta), None)
            if a is not asiento_anterior:
                self.tabla.setItem(fila_i, 0, QTableWidgetItem(str(a.num)))
                self.tabla.setItem(fila_i, 1, QTableWidgetItem(a.fecha))
                self.tabla.setItem(fila_i, 2, QTableWidgetItem(a.descripcion))
                btn_editar = QPushButton("✏️ Editar"); btn_editar.setProperty("class", "btnGhost")
                btn_editar.clicked.connect(lambda _=False, aid=a.id: self.editar_asiento(aid))
                self.tabla.setCellWidget(fila_i, 6, btn_editar)
                asiento_anterior = a
            nombre_cuenta = ("    " if p.tipo == "Haber" else "") + (c.nombre if c else "?")
            self.tabla.setItem(fila_i, 3, QTableWidgetItem(nombre_cuenta))
            self.tabla.setItem(fila_i, 4, QTableWidgetItem(fmt(p.monto) if p.tipo == "Debe" else ""))
            self.tabla.setItem(fila_i, 5, QTableWidgetItem(fmt(p.monto) if p.tipo == "Haber" else ""))
            fila_i += 1

        if not filas_html:
            self.tabla.setRowCount(1)
            self.tabla.setItem(0, 0, QTableWidgetItem("📝 Sin asientos registrados"))
            self.tabla.setSpan(0, 0, 1, 7)
