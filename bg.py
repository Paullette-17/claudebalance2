# ═══════════════════════════════════════════════════════════
# bg.py — Página "Balance General". Activos = Pasivos + Patrimonio.
# Equivalente a renderBalance() en app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QPushButton)
from PySide6.QtCore import Qt

from utilidades import fmt, hoy


def _fila(nombre, valor, estilo=""):
    fila = QFrame()
    lay = QHBoxLayout(fila); lay.setContentsMargins(6, 3, 6, 3)
    lbl_n = QLabel(nombre); lbl_v = QLabel(valor)
    lbl_v.setAlignment(Qt.AlignRight)
    if estilo:
        lbl_n.setStyleSheet(estilo); lbl_v.setStyleSheet(estilo)
    lay.addWidget(lbl_n); lay.addStretch(); lay.addWidget(lbl_v)
    return fila


def _seccion(titulo, color="#4f8ef7"):
    lbl = QLabel(titulo)
    lbl.setStyleSheet(f"background:{color};color:white;font-weight:700;"
                       f"padding:6px 10px;border-radius:4px;font-size:11px;letter-spacing:1px;")
    return lbl


def _vacio():
    lbl = QLabel("— Sin cuentas —")
    lbl.setStyleSheet("background:transparent;color:#64748b;padding-left:6px;")
    return lbl


def _subgrupo(texto):
    lbl = QLabel(f"<i>{texto}</i>")
    lbl.setStyleSheet("background:transparent;font-weight:600;margin-top:6px;")
    return lbl


def _subtotal(nombre, valor, color="#334155"):
    fila = QFrame()
    fila.setStyleSheet(f"QFrame{{background:{color};border-radius:4px;}}"
                       f"QLabel{{background:transparent;color:white;}}")
    lay = QHBoxLayout(fila); lay.setContentsMargins(8, 5, 8, 5)
    lbl_n = QLabel(f"<b>{nombre}</b>"); lbl_v = QLabel(f"<b>{valor}</b>")
    lbl_v.setAlignment(Qt.AlignRight)
    lay.addWidget(lbl_n); lay.addStretch(); lay.addWidget(lbl_v)
    return fila


class PaginaBG(QWidget):
    """Página del Balance General (BG)."""

    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Balance General"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Activos = Pasivos + Patrimonio"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        cab = QHBoxLayout()
        cab.addStretch()
        btn_excel = QPushButton("📊 Excel"); btn_excel.setProperty("class", "btnExcel")
        btn_excel.clicked.connect(self.exportar_excel)
        btn_pdf = QPushButton("📄 PDF"); btn_pdf.setProperty("class", "btnGhost")
        btn_pdf.clicked.connect(self.exportar_pdf)
        cab.addWidget(btn_excel); cab.addWidget(btn_pdf)
        raiz.addLayout(cab)

        self.contenedor = QVBoxLayout()
        raiz.addLayout(self.contenedor)
        raiz.addStretch()
        self.refrescar()

    def exportar_excel(self):
        from exportar_excel import exportar_balance_excel
        exportar_balance_excel(self.estado, self)

    def exportar_pdf(self):
        from exportar_excel import exportar_balance_pdf
        exportar_balance_pdf(self.estado, self)

    def refrescar(self):
        while self.contenedor.count():
            item = self.contenedor.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._limpiar_layout(item.layout())

        b = self.estado.calcular_balance()
        marco = QFrame(); marco.setProperty("class", "card")
        lay = QVBoxLayout(marco)

        lbl_periodo = QLabel(f"<b>BALANCE GENERAL</b><br><small style='color:#94a3b8'>Al {hoy()}</small>")
        lbl_periodo.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_periodo)

        cols = QHBoxLayout()
        cols.setAlignment(Qt.AlignTop)

        # ── Columna ACTIVOS ──
        col_a = QVBoxLayout()
        col_a.addWidget(_seccion("ACTIVOS", "#2563eb"))
        col_a.addWidget(_subgrupo("Activos Corrientes"))
        for c in b["act_corrientes"]:
            col_a.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id))))
        if not b["act_corrientes"]:
            col_a.addWidget(_vacio())
        col_a.addWidget(_subtotal("Total Corrientes", fmt(b["t_ac"])))
        col_a.addWidget(_subgrupo("Activos No Corrientes"))
        for c in b["act_no_corrientes"]:
            col_a.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id))))
        if not b["act_no_corrientes"]:
            col_a.addWidget(_vacio())
        col_a.addWidget(_subtotal("Total No Corrientes", fmt(b["t_anc"])))
        col_a.addWidget(_subtotal("TOTAL ACTIVOS", fmt(b["total_activos"]), color="#1e3a5f"))
        col_a.addStretch()
        cols.addLayout(col_a, 1)

        # ── Columna PASIVO + PATRIMONIO ──
        col_p = QVBoxLayout()
        col_p.addWidget(_seccion("PASIVOS", "#dc2626"))
        col_p.addWidget(_subgrupo("Pasivos Corrientes"))
        for c in b["pas_corrientes"]:
            col_p.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id))))
        if not b["pas_corrientes"]:
            col_p.addWidget(_vacio())
        col_p.addWidget(_subtotal("Total Corrientes", fmt(b["t_pc"])))
        col_p.addWidget(_subgrupo("Pasivos No Corrientes"))
        for c in b["pas_no_corrientes"]:
            col_p.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id))))
        if not b["pas_no_corrientes"]:
            col_p.addWidget(_vacio())
        col_p.addWidget(_subtotal("Total No Corrientes", fmt(b["t_pnc"])))
        col_p.addWidget(_subtotal("TOTAL PASIVOS", fmt(b["total_pasivos"]), color="#7f1d1d"))

        col_p.addWidget(_seccion("PATRIMONIO", "#7c3aed"))
        for c in b["patrimonio"]:
            col_p.addWidget(_fila(c.nombre, fmt(self.estado.saldo_cuenta(c.id))))
        if not b["patrimonio"]:
            col_p.addWidget(_vacio())
        col_p.addWidget(_fila("Utilidad/Pérdida del Ejercicio", fmt(b["utilidad"])))
        col_p.addWidget(_subtotal("TOTAL PATRIMONIO", fmt(b["total_patrimonio_util"]), color="#4c1d95"))
        col_p.addWidget(_subtotal("TOTAL PASIVO + PATRIMONIO", fmt(b["total_pas_patr"]), color="#1e3a5f"))
        col_p.addStretch()
        cols.addLayout(col_p, 1)
        cols.setSpacing(24)

        lay.addLayout(cols)

        cuadrado = abs(b["total_activos"] - b["total_pas_patr"]) < 0.01
        alerta = QLabel(
            f"✅ Balance cuadrado — Activos ({fmt(b['total_activos'])}) = "
            f"Pasivo + Patrimonio ({fmt(b['total_pas_patr'])})" if cuadrado else
            f"⚠️ Balance descuadrado — diferencia de "
            f"{fmt(abs(b['total_activos'] - b['total_pas_patr']))}")
        alerta.setStyleSheet(f"padding:8px;border-radius:6px;margin-top:10px;"
                              f"background:{'#052e1e' if cuadrado else '#3f1d1d'};"
                              f"color:{'#06d6a0' if cuadrado else '#f59e0b'};")
        lay.addWidget(alerta)

        self.contenedor.addWidget(marco)

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._limpiar_layout(item.layout())
