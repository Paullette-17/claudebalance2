# ═══════════════════════════════════════════════════════════
# dashboard.py — Página "Inicio". Tarjetas de resumen + 3 gráficas
# (barras, pastel, línea). Equivalente a renderDashboard() en app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QFrame, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from utilidades import fmt


def _tarjeta_stat(titulo, valor, sub, color) -> QFrame:
    marco = QFrame()
    marco.setProperty("class", "card")
    marco.setObjectName("statCard")
    marco.setStyleSheet(f"QFrame#statCard {{ border-left: 4px solid {color}; }}"
                        "QLabel { border: none; background: transparent; }")
    lay = QVBoxLayout(marco)
    l1 = QLabel(titulo); l1.setStyleSheet("font-size:11px;color:#94a3b8;font-weight:600;")
    l2 = QLabel(valor); l2.setStyleSheet(f"font-size:20px;font-weight:700;color:{color};")
    l3 = QLabel(sub); l3.setStyleSheet("font-size:10px;color:#64748b;")
    for w in (l1, l2, l3):
        lay.addWidget(w)
    return marco


class PaginaDashboard(QWidget):
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Inicio"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Resumen financiero en tiempo real"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        self.grid_stats = QGridLayout()
        for col in range(4):
            self.grid_stats.setColumnStretch(col, 1)
        raiz.addLayout(self.grid_stats)

        fila_charts = QHBoxLayout()
        self.fig_barras = Figure(figsize=(4, 3), facecolor="none")
        self.canvas_barras = FigureCanvasQTAgg(self.fig_barras)
        self.canvas_barras.setStyleSheet("background: transparent;")
        self.fig_pastel = Figure(figsize=(4, 3), facecolor="none")
        self.canvas_pastel = FigureCanvasQTAgg(self.fig_pastel)
        self.canvas_pastel.setStyleSheet("background: transparent;")
        for canvas, titulo_c in ((self.canvas_barras, "📊 Ingresos vs Gastos"),
                                  (self.canvas_pastel, "🥧 Composición del Balance")):
            marco = QFrame(); marco.setProperty("class", "card")
            lay = QVBoxLayout(marco)
            lbl = QLabel(titulo_c); lbl.setProperty("class", "cardTitle")
            lay.addWidget(lbl)
            lay.addWidget(canvas)
            fila_charts.addWidget(marco)
        raiz.addLayout(fila_charts)

        marco_linea = QFrame(); marco_linea.setProperty("class", "card")
        lay_linea = QVBoxLayout(marco_linea)
        lbl_linea = QLabel("📉 Evolución de Transacciones"); lbl_linea.setProperty("class", "cardTitle")
        lay_linea.addWidget(lbl_linea)
        self.fig_linea = Figure(figsize=(8, 3), facecolor="none")
        self.canvas_linea = FigureCanvasQTAgg(self.fig_linea)
        self.canvas_linea.setStyleSheet("background: transparent;")
        lay_linea.addWidget(self.canvas_linea)
        raiz.addWidget(marco_linea)
        raiz.addStretch()

        self.refrescar()

    def refrescar(self):
        e = self.estado
        tA = e.total_naturaleza("Activo")
        tP = e.total_naturaleza("Pasivo")
        tPa = e.total_naturaleza("Patrimonio")
        tI = e.total_naturaleza("Ingreso")
        tE = e.total_naturaleza("Egreso")
        util = tI - tE

        # limpiar tarjetas previas
        while self.grid_stats.count():
            item = self.grid_stats.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.grid_stats.addWidget(_tarjeta_stat("TOTAL ACTIVOS", fmt(tA), "Recursos de la empresa", "#4f8ef7"), 0, 0)
        self.grid_stats.addWidget(_tarjeta_stat("UTILIDAD NETA", fmt(util),
                                                 "Resultado positivo" if util >= 0 else "Pérdida neta",
                                                 "#06d6a0" if util >= 0 else "#ef4444"), 0, 1)
        self.grid_stats.addWidget(_tarjeta_stat("TOTAL PASIVOS", fmt(tP), "Obligaciones", "#f59e0b"), 0, 2)
        self.grid_stats.addWidget(_tarjeta_stat("PATRIMONIO + UTILIDAD", fmt(tPa + util),
                                                 "Capital propio neto", "#a78bfa"), 0, 3)

        self._dibujar_barras(tI, tE, util)
        self._dibujar_pastel(tA, tP, tPa + util)
        self._dibujar_linea()

    def _dibujar_barras(self, tI, tE, util):
        self.fig_barras.clear()
        self.fig_barras.patch.set_alpha(0)
        ax = self.fig_barras.add_subplot(111)
        etiquetas = ["Ingresos", "Egresos", "Utilidad"]
        valores = [tI, tE, max(0, util)]
        colores = ["#06d6a0", "#ef4444", "#4f8ef7"]
        ax.bar(etiquetas, valores, color=colores)
        ax.set_facecolor("none")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        self.canvas_barras.draw()

    def _dibujar_pastel(self, tA, tP, tPa_util):
        self.fig_pastel.clear()
        self.fig_pastel.patch.set_alpha(0)
        ax = self.fig_pastel.add_subplot(111)
        valores = [max(tA, 0.0), max(tP, 0.0), max(tPa_util, 0.0)]
        if sum(valores) <= 0:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", color="#64748b")
            ax.axis("off")
            self.canvas_pastel.draw()
            return
        ax.pie(valores, labels=["Activos", "Pasivos", "Patrimonio"],
               colors=["#4f8ef7", "#ef4444", "#7c3aed"],
               textprops={"color": "#94a3b8", "fontsize": 8}, wedgeprops={"width": 0.45})
        self.canvas_pastel.draw()

    def _dibujar_linea(self):
        e = self.estado
        self.fig_linea.clear()
        ax = self.fig_linea.add_subplot(111)
        ax.set_facecolor("none")          # sin fondo blanco
        self.fig_linea.patch.set_alpha(0)
        fechas = sorted({a.fecha for a in e.asientos})
        if not fechas:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", color="#64748b",
                    transform=ax.transAxes)
            ax.axis("off")                # vacío: sin ejes, cuadro ni números
            self.canvas_linea.draw()
            return
        else:
            acumI, acumE, dI, dE = 0.0, 0.0, [], []
            for f in fechas:
                for a in e.asientos:
                    if a.fecha == f:
                        for p in a.partidas:
                            c = next((x for x in e.cuentas if x.id == p.cuenta), None)
                            m = float(p.monto) if p.tipo == "Debe" else -float(p.monto)
                            if c and c.naturaleza == "Ingreso":
                                acumI -= m      # Haber suma, Debe resta
                            elif c and c.naturaleza == "Egreso":
                                acumE += m      # Debe suma, Haber resta
                dI.append(acumI); dE.append(acumE)
            ax.plot(fechas, dI, label="Ingresos acum.", color="#06d6a0", marker="o")
            ax.plot(fechas, dE, label="Egresos acum.", color="#ef4444", marker="o")
            ax.fill_between(fechas, dI, alpha=0.1, color="#06d6a0")
            ax.fill_between(fechas, dE, alpha=0.1, color="#ef4444")
            ax.legend(fontsize=8, facecolor="none", labelcolor="#94a3b8")
            ax.tick_params(colors="#94a3b8", labelsize=8, labelrotation=20)
            ax.grid(True, color="#334155", alpha=0.3, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        self.canvas_linea.draw()
