# ═══════════════════════════════════════════════════════════
# timeline.py — Página "Historial". Vista cronológica de los
# asientos registrados. Equivalente a renderTimeline() en app24.js.
# ═══════════════════════════════════════════════════════════
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea

from utilidades import fmt


class PaginaTimeline(QWidget):
    def __init__(self, estado):
        super().__init__()
        self.estado = estado
        self._construir_ui()
        self.estado.cambiado.connect(self.refrescar)

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Historial de Transacciones"); titulo.setProperty("class", "pageTitle")
        subt = QLabel("Visualización cronológica"); subt.setProperty("class", "pageSubtitle")
        raiz.addWidget(titulo); raiz.addWidget(subt)

        self.area = QScrollArea(); self.area.setWidgetResizable(True)
        self.contenido = QWidget()
        self.lay_contenido = QVBoxLayout(self.contenido)
        self.area.setWidget(self.contenido)
        raiz.addWidget(self.area)

        self.refrescar()

    def refrescar(self):
        while self.lay_contenido.count():
            item = self.lay_contenido.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        asientos = sorted(self.estado.asientos, key=lambda a: a.fecha, reverse=True)
        if not asientos:
            self.lay_contenido.addWidget(QLabel("⏱️ Sin transacciones"))
            return

        for a in asientos:
            total = sum(p.monto for p in a.partidas if p.tipo == "Debe")
            marco = QFrame(); marco.setProperty("class", "card")
            marco.setStyleSheet("QFrame { border-left: 3px solid #4f8ef7; }")
            lay = QVBoxLayout(marco)
            lay.addWidget(QLabel(f"<b>{a.fecha}</b> — Asiento #{a.num}"))
            lbl_desc = QLabel(a.descripcion); lbl_desc.setWordWrap(True)
            lay.addWidget(lbl_desc)
            lay.addWidget(QLabel(f"<span style='color:#64748b;font-size:11px'>"
                                  f"{len(a.partidas)} partidas · {fmt(total)}</span>"))
            fila_partidas = QHBoxLayout()
            for p in a.partidas:
                c = next((x for x in self.estado.cuentas if x.id == p.cuenta), None)
                color = "#ef4444" if p.tipo == "Debe" else "#06d6a0"
                lbl = QLabel(f"<span style='color:{color}'>{p.tipo}</span> "
                             f"{c.nombre if c else '?'} {fmt(p.monto)}")
                lbl.setStyleSheet("font-size:10px;margin-right:8px;")
                fila_partidas.addWidget(lbl)
            fila_partidas.addStretch()
            lay.addLayout(fila_partidas)
            self.lay_contenido.addWidget(marco)

        self.lay_contenido.addStretch()
