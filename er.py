# ═══════════════════════════════════════════════════════════
# er.py — Página "Estado de Resultados". Utilidad o Pérdida
# del ejercicio. Equivalente a renderResultados() en app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt

from utilidades import fmt, hoy
from bg import _fila, _seccion, _subtotal  # reutilizamos los helpers visuales de bg.py


class PaginaER(QWidget):
    """Página del Estado de Resultados (ER)."""

    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Estado de Resultados"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Utilidad o Pérdida del Ejercicio"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        cab = QHBoxLayout()
        cab.addStretch()
        btn_excel = QPushButton("📊 Excel"); btn_excel.setProperty("class", "btnExcel")
        btn_excel.clicked.connect(self.exportar_excel)
        cab.addWidget(btn_excel)
        raiz.addLayout(cab)

        self.contenedor = QVBoxLayout()
        raiz.addLayout(self.contenedor)
        raiz.addStretch()
        self.refrescar()

    def exportar_excel(self):
        from exportar_excel import exportar_er_excel
        exportar_er_excel(self.estado, self)

    def refrescar(self):
        while self.contenedor.count():
            item = self.contenedor.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ingresos = [c for c in self.estado.cuentas if c.naturaleza == "Ingreso"]
        egresos = [c for c in self.estado.cuentas if c.naturaleza == "Egreso"]
        tI = sum(self.estado.saldo_cuenta(c.id) for c in ingresos)
        tE = sum(self.estado.saldo_cuenta(c.id) for c in egresos)
        util = tI - tE

        marco = QFrame(); marco.setProperty("class", "card")
        lay = QVBoxLayout(marco)

        lbl_periodo = QLabel(f"<b>ESTADO DE RESULTADOS</b><br><small style='color:#94a3b8'>Período al {hoy()}</small>")
        lbl_periodo.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_periodo)

        lay.addWidget(_seccion("INGRESOS", "#059669"))
        for c in ingresos:
            lay.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id)), "color:#06d6a0;"))
        if not ingresos:
            lay.addWidget(QLabel("<span style='color:#64748b'>Sin ingresos</span>"))
        lay.addWidget(_subtotal("TOTAL INGRESOS", fmt(tI), color="#065f46"))

        lay.addWidget(_seccion("EGRESOS", "#d97706"))
        for c in egresos:
            lay.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id)), "color:#ef4444;"))
        if not egresos:
            lay.addWidget(QLabel("<span style='color:#64748b'>Sin egresos</span>"))
        lay.addWidget(_subtotal("TOTAL EGRESOS", fmt(tE), color="#92400e"))

        color_res = "#065f46" if util >= 0 else "#7f1d1d"
        lay.addWidget(_subtotal("UTILIDAD NETA" if util >= 0 else "PÉRDIDA NETA",
                                 fmt(abs(util)), color=color_res))

        mensaje = (f"✅ Utilidad neta de {fmt(util)}. Los ingresos superan los egresos en el período."
                   if util >= 0 else
                   f"⚠️ Pérdida neta de {fmt(abs(util))}. Los egresos superan los ingresos.")
        alerta = QLabel(mensaje)
        alerta.setWordWrap(True)
        alerta.setStyleSheet(f"padding:8px;border-radius:6px;margin-top:10px;"
                              f"background:{'#052e1e' if util>=0 else '#3f1d1d'};"
                              f"color:{'#06d6a0' if util>=0 else '#f59e0b'};")
        lay.addWidget(alerta)

        self.contenedor.addWidget(marco)
