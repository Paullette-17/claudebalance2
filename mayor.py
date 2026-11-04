# ═══════════════════════════════════════════════════════════
# mayor.py — Página "Libro Mayor". Muestra una cuenta T por
# cada cuenta del catálogo. Equivalente a renderMayor() en app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QComboBox, QLineEdit, QPushButton, QScrollArea,
                                QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt

from utilidades import fmt, NATURALEZAS


class PaginaMayor(QWidget):
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Libro Mayor"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Cuentas T individuales por cuenta"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        cab = QHBoxLayout()
        self.combo_nat = QComboBox(); self.combo_nat.addItem("Todas las Naturalezas", "")
        for n in NATURALEZAS:
            self.combo_nat.addItem(n, n)
        self.combo_nat.currentIndexChanged.connect(self.refrescar)
        self.in_buscar = QLineEdit(); self.in_buscar.setPlaceholderText("🔍 Buscar cuenta...")
        self.in_buscar.textChanged.connect(self.refrescar)
        btn_excel = QPushButton("📊 Excel"); btn_excel.setProperty("class", "btnExcel")
        btn_excel.clicked.connect(self.exportar_excel)
        cab.addWidget(self.combo_nat); cab.addWidget(self.in_buscar); cab.addStretch(); cab.addWidget(btn_excel)
        raiz.addLayout(cab)

        self.area = QScrollArea(); self.area.setWidgetResizable(True)
        self.contenido = QWidget()
        self.grid = QGridLayout(self.contenido)
        self.area.setWidget(self.contenido)
        raiz.addWidget(self.area)

        self.refrescar()

    def exportar_excel(self):
        from exportar_excel import exportar_mayor_excel
        exportar_mayor_excel(self.estado, self)

    def _cuenta_t(self, c):
        marco = QFrame(); marco.setProperty("class", "card")
        lay = QVBoxLayout(marco)
        lay.addWidget(QLabel(f"<b>{c.nombre}</b><br><small style='color:#94a3b8'>{c.naturaleza}</small>"))

        movimientos_debe, movimientos_haber = [], []
        for a in self.estado.asientos:
            for p in a.partidas:
                if p.cuenta == c.id:
                    item = (a.descripcion[:20], float(p.monto))
                    (movimientos_debe if p.tipo == "Debe" else movimientos_haber).append(item)

        fila_cols = QHBoxLayout()
        for titulo_col, color, movs in (("DEBE", "#ef4444", movimientos_debe),
                                         ("HABER", "#06d6a0", movimientos_haber)):
            col = QVBoxLayout()
            lbl = QLabel(titulo_col); lbl.setStyleSheet(f"color:{color};font-weight:700;font-size:11px;")
            col.addWidget(lbl)
            if movs:
                for desc, monto in movs:
                    fila = QHBoxLayout()
                    fila.addWidget(QLabel(desc))
                    lbl_m = QLabel(fmt(monto)); lbl_m.setStyleSheet(f"color:{color};")
                    fila.addWidget(lbl_m)
                    col.addLayout(fila)
            else:
                lbl_vacio = QLabel("—"); lbl_vacio.setStyleSheet("color:#64748b;font-size:11px;")
                col.addWidget(lbl_vacio)
            fila_cols.addLayout(col)
        lay.addLayout(fila_cols)

        total_debe = sum(m for _, m in movimientos_debe)
        total_haber = sum(m for _, m in movimientos_haber)
        saldo = self.estado.saldo_cuenta(c.id)
        naturaleza_saldo = ("Deudor" if saldo >= 0 else "Acreedor") if c.naturaleza in ("Activo", "Egreso") \
            else ("Acreedor" if saldo >= 0 else "Deudor")
        pie = QLabel(f"D:{fmt(total_debe)}  H:{fmt(total_haber)}   "
                     f"Saldo {naturaleza_saldo}: {fmt(abs(saldo))}")
        pie.setStyleSheet(f"color:{'#06d6a0' if saldo>=0 else '#ef4444'};font-weight:700;font-size:11px;"
                           f"border-top:1px solid #334155;padding-top:6px;margin-top:6px;")
        lay.addWidget(pie)
        return marco

    def refrescar(self):
        nat = self.combo_nat.currentData()
        buscar = self.in_buscar.text().lower()
        filtradas = [c for c in self.estado.cuentas
                     if (not nat or c.naturaleza == nat) and buscar in c.nombre.lower()]

        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not filtradas:
            self.grid.addWidget(QLabel("📒 No hay cuentas"), 0, 0)
            return

        columnas = 3
        for i, c in enumerate(filtradas):
            self.grid.addWidget(self._cuenta_t(c), i // columnas, i % columnas)
