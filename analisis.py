# ═══════════════════════════════════════════════════════════
# analisis.py — Página "Análisis Financiero". Ratios clave e
# interpretación textual. Equivalente a renderAnalisis() en app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout

from utilidades import fmt


def _tarjeta_ratio(etiqueta, valor, interpretacion, color="#e2e8f0"):
    marco = QFrame(); marco.setProperty("class", "card")
    lay = QVBoxLayout(marco)
    lbl_e = QLabel(etiqueta); lbl_e.setStyleSheet("color:#94a3b8;font-size:11px;font-weight:600;")
    lbl_v = QLabel(valor); lbl_v.setStyleSheet(f"font-size:22px;font-weight:700;color:{color};")
    lbl_i = QLabel(interpretacion); lbl_i.setStyleSheet("font-size:11px;color:#64748b;")
    lay.addWidget(lbl_e); lay.addWidget(lbl_v); lay.addWidget(lbl_i)
    return marco


class PaginaAnalisis(QWidget):
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Análisis Financiero"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Ratios e indicadores clave"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        self.grid = QGridLayout()
        raiz.addLayout(self.grid)

        self.marco_interp = QFrame(); self.marco_interp.setProperty("class", "card")
        lay_interp = QVBoxLayout(self.marco_interp)
        lay_interp.addWidget(QLabel("📝 Interpretación"))
        self.lbl_interp = QLabel(""); self.lbl_interp.setWordWrap(True)
        self.lbl_interp.setStyleSheet("font-size:12px;line-height:1.6;")
        lay_interp.addWidget(self.lbl_interp)
        raiz.addWidget(self.marco_interp)
        raiz.addStretch()

        self.refrescar()

    def refrescar(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        e = self.estado
        tA, tP, tPa = e.total_naturaleza("Activo"), e.total_naturaleza("Pasivo"), e.total_naturaleza("Patrimonio")
        tI, tE = e.total_naturaleza("Ingreso"), e.total_naturaleza("Egreso")
        util = tI - tE
        rent = (util / tI * 100) if tI > 0 else 0
        endeud = (tP / tA * 100) if tA > 0 else 0
        auton = ((tPa + util) / tA * 100) if tA > 0 else 0

        interp_rent = "✅ Excelente" if rent >= 20 else "🟡 Moderada" if rent >= 10 else "⚠️ Baja" if rent > 0 else "❌ Con pérdidas"
        interp_end = "✅ Bajo" if endeud <= 30 else "🟡 Moderado" if endeud <= 60 else "⚠️ Alto — revisar"
        color_end = "#ef4444" if endeud > 60 else "#f59e0b"

        tarjetas = [
            ("Rentabilidad Neta", f"{rent:.1f}%", interp_rent, "#e2e8f0"),
            ("Endeudamiento", f"{endeud:.1f}%", interp_end, color_end),
            ("Autonomía Financiera", f"{auton:.1f}%", "Activo financiado con recursos propios.", "#06d6a0"),
            ("Utilidad Neta", fmt(util), "Período rentable." if util >= 0 else "Período con pérdidas.",
             "#06d6a0" if util >= 0 else "#ef4444"),
            ("Total Activos", fmt(tA), "Recursos totales.", "#e2e8f0"),
            ("Pasivo / Patrimonio", f"{(tP/(tPa+util)):.2f}" if (tPa + util) > 0 else "N/A",
             "Deuda por cada C$ propio.", "#f59e0b"),
        ]
        for i, (et, val, inter, color) in enumerate(tarjetas):
            self.grid.addWidget(_tarjeta_ratio(et, val, inter, color), i // 3, i % 3)

        texto = (f"La empresa tiene activos de <b>{fmt(tA)}</b>, financiados {100-auton:.1f}% con deuda "
                 f"y {auton:.1f}% con capital propio. ")
        if util >= 0:
            texto += f"Se generó utilidad de <b>{fmt(util)}</b> (rentabilidad {rent:.1f}%). "
        else:
            texto += f"Se registró pérdida de <b>{fmt(abs(util))}</b>. "
        if endeud > 60:
            texto += "El endeudamiento es elevado; se recomienda revisar las obligaciones."
        self.lbl_interp.setText(texto)
