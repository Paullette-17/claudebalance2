# ═══════════════════════════════════════════════════════════
# main.py — Punto de entrada del Sistema Contable (PySide6).
# Arma la ventana principal: barra lateral de navegación,
# QStackedWidget con cada página, toggle de tema claro/oscuro
# y persistencia local. Equivalente al <nav class="sidebar">
# + showPage() + toggleTheme() + DOMContentLoaded de index.html/app24.js.
# ═══════════════════════════════════════════════════════════
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget,
                                QScrollArea, QButtonGroup, QMessageBox,
                                QInputDialog)
from PySide6.QtCore import Qt

import db
import roles
from modelos import EstadoApp
from almacenamiento import guardar_en_storage, cargar_de_storage
from utilidades import (generar_qss, PALETA_OSCURA, PALETA_CLARA, RUTA_LOGO,
                        pedir_nombre, error_nombre)

from dashboard import PaginaDashboard
from cuentas import PaginaCuentas
from diario import PaginaDiario
from mayor import PaginaMayor
from bg import PaginaBG
from er import PaginaER
from analisis import PaginaAnalisis
from timeline import PaginaTimeline
from usuarios import PaginaUsuarios
from ciclo_mensual import DialogoCicloMensual
from PySide6.QtGui import QPixmap

NAV_ITEMS = [
    ("Principal", None),
    ("dashboard", "🏠 Inicio"),
    ("Registros", None),
    ("cuentas", "📁 Cuentas"),
    ("diario", "📝 Libro Diario"),
    ("usuarios", "👥 Usuarios"),
    ("Reportes", None),
    ("mayor", "📒 Libro Mayor"),
    ("bg", "⚖️ Balance General"),
    ("er", "📈 Estado de Resultados"),
    ("Análisis", None),
    ("analisis", "🔍 Análisis Financiero"),
    ("timeline", "⏱️ Historial"),
]


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rol = db.rol_actual() or roles.ROL_OPERADOR
        self.pagina_actual = None
        self.setWindowTitle(f"Sistema Contable — {self.rol}")
        self.resize(1280, 800)
        self.setWindowState(self.windowState() | Qt.WindowMaximized)  # abre maximizada

        self.estado = EstadoApp()
        recuperado = cargar_de_storage(self.estado)
        if not recuperado:
            guardar_en_storage(self.estado)

        central = QWidget()
        self.setCentralWidget(central)
        layout_raiz = QHBoxLayout(central)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        layout_raiz.addWidget(self._crear_sidebar())

        # ── Área principal con páginas apiladas ──
        contenedor_main = QWidget()
        lay_main = QVBoxLayout(contenedor_main)
        lay_main.setContentsMargins(28, 20, 28, 20)

        barra_superior = QHBoxLayout()
        # Carpeta (proyecto) abierta, solo como referencia
        self.lbl_proyecto_activo = QLabel()
        self.lbl_proyecto_activo.setProperty("class", "pageSubtitle")
        barra_superior.addWidget(self.lbl_proyecto_activo)
        barra_superior.addStretch()
        # Botón a la derecha, junto al tema: abre la ventana con todas las carpetas
        self.btn_ciclo_mensual = QPushButton("📅 Ciclo mensual")
        self.btn_ciclo_mensual.setProperty("class", "btnGhost")
        self.btn_ciclo_mensual.setToolTip("Ver, abrir o crear las carpetas de cada ciclo")
        self.btn_ciclo_mensual.clicked.connect(self.abrir_ciclo_mensual)
        barra_superior.addWidget(self.btn_ciclo_mensual)
        self.btn_tema = QPushButton("☀️ Claro")
        self.btn_tema.setProperty("class", "btnGhost")
        self.btn_tema.clicked.connect(self.alternar_tema)
        barra_superior.addWidget(self.btn_tema)
        self._actualizar_proyecto_activo()
        lay_main.addLayout(barra_superior)

        self.stack = QStackedWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(self.stack)
        lay_main.addWidget(scroll)
        layout_raiz.addWidget(contenedor_main, stretch=1)

        # ── Instanciar páginas (una por módulo) ──
        self.paginas = {
            "dashboard": PaginaDashboard(self.estado),
            "diario": PaginaDiario(self.estado),
            "mayor": PaginaMayor(self.estado),
            "bg": PaginaBG(self.estado),
            "er": PaginaER(self.estado),
            "analisis": PaginaAnalisis(self.estado),
            "timeline": PaginaTimeline(self.estado),
        }
        # Cuentas (catálogo): ahora disponible para Administrador y Operador.
        if roles.pagina_permitida("cuentas", self.rol):
            self.paginas["cuentas"] = PaginaCuentas(self.estado)
        # Usuarios (crear cuentas de acceso) solo lo ve el Administrador.
        if roles.pagina_permitida("usuarios", self.rol):
            self.paginas["usuarios"] = PaginaUsuarios()
        self.indices_stack = {}
        for clave, widget in self.paginas.items():
            self.indices_stack[clave] = self.stack.addWidget(widget)

        # Guardar automáticamente cada vez que cambian los datos
        self.estado.cambiado.connect(lambda: guardar_en_storage(self.estado))

        self._aplicar_tema()
        self.mostrar_pagina("dashboard")

    # ── Sidebar ──────────────────────────────────────────────
    def _crear_sidebar(self) -> QFrame:
        sidebar = QFrame(); sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 16, 0, 16)
        lay.setSpacing(2)

        logo = QLabel()
        pix_logo = QPixmap(RUTA_LOGO)
        if not pix_logo.isNull():
            logo.setPixmap(pix_logo.scaledToWidth(160, Qt.SmoothTransformation))
            logo.setAlignment(Qt.AlignCenter)
            logo.setStyleSheet("padding:10px 20px 16px;")
        else:
            # Si no se encuentra logo.png, se usa el texto de respaldo
            logo.setText("💼 Sistema\nContable")
            logo.setStyleSheet("font-size:16px;font-weight:700;color:#4f8ef7;padding:10px 20px 16px;")
        lay.addWidget(logo)

        # ── Insignia del usuario y su rol ──
        es_admin = roles.es_admin(self.rol)
        color_rol = "#f59e0b" if es_admin else "#4f8ef7"
        nombre = db.nombre_usuario_actual() or "Sin sesión"
        badge = QLabel(f"👤 {nombre}<br>"
                       f"<span style='color:{color_rol};font-weight:700;'>"
                       f"{'🛡️' if es_admin else '🧾'} {self.rol}</span>")
        badge.setTextFormat(Qt.RichText)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("padding:4px 12px 14px;font-size:12px;")
        lay.addWidget(badge)
 
        self.grupo_nav = QButtonGroup(self)
        self.grupo_nav.setExclusive(True)
        self.botones_nav = {}

        for clave, etiqueta in NAV_ITEMS:
            if etiqueta is None:
                lbl_sec = QLabel(clave.upper())
                lbl_sec.setObjectName("navSection")
                lay.addWidget(lbl_sec)
                continue
            if not roles.pagina_permitida(clave, self.rol):
                continue  # el rol no puede ver esta página
            btn = QPushButton(etiqueta)
            btn.setObjectName("navItem")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, c=clave: self.mostrar_pagina(c))
            self.grupo_nav.addButton(btn)
            self.botones_nav[clave] = btn
            lay.addWidget(btn)

        lay.addStretch()

        # ── Cerrar sesión, al final de la barra lateral ──
        self.btn_cerrar_sesion = QPushButton("🚪 Cerrar sesión")
        self.btn_cerrar_sesion.setProperty("class", "btnDanger")
        self.btn_cerrar_sesion.setToolTip("Salir y volver a la pantalla de inicio de sesión")
        self.btn_cerrar_sesion.clicked.connect(self.cerrar_sesion)
        contenedor_salir = QWidget()
        lay_salir = QVBoxLayout(contenedor_salir)
        lay_salir.setContentsMargins(16, 0, 16, 0)
        lay_salir.addWidget(self.btn_cerrar_sesion)
        lay.addWidget(contenedor_salir)

        return sidebar

    def mostrar_pagina(self, clave):
        if clave not in self.paginas or not roles.pagina_permitida(clave, self.rol):
            return
        self.pagina_actual = clave
        self.stack.setCurrentIndex(self.indices_stack[clave])
        if clave in self.botones_nav:
            self.botones_nav[clave].setChecked(True)
        # Refrescar la página al mostrarla (equivalente a los renderX() en showPage())
        pagina = self.paginas[clave]
        if hasattr(pagina, "refrescar"):
            pagina.refrescar()
        elif hasattr(pagina, "refrescar_tabla"):
            pagina.refrescar_tabla()
        if clave == "diario":
            pagina.iniciar_diario()

    # ── Proyectos (carpetas del ciclo mensual) ───────────────
    def _actualizar_proyecto_activo(self):
        """Muestra en la barra superior qué carpeta está abierta."""
        p = next((x for x in self.estado.proyectos
                  if x.id == self.estado.proyecto_actual_id), None)
        self.lbl_proyecto_activo.setText(f"📂 {p.nombre}" if p else "")

    def abrir_ciclo_mensual(self):
        """Abre la ventana con todas las carpetas creadas."""
        DialogoCicloMensual(self).exec()

    def agregar_proyecto(self):
        """Pide un nombre, crea el proyecto y lo abre. Devuelve el proyecto o None."""
        texto = ""
        while True:
            texto, ok = pedir_nombre(self, "Nueva carpeta",
                                    "Nombre de la nueva carpeta:", texto)
            if not ok:
                return None
            nombre = texto.strip()
            msg = error_nombre(nombre, "El nombre de la carpeta")
            if msg:
                QMessageBox.warning(self, "Nombre no válido", msg)
            elif self.estado.nombre_proyecto_existe(nombre):
                QMessageBox.warning(self, "Nombre repetido",
                                    f"Ya existe una carpeta llamada '{nombre}'. Elige otro nombre.")
            else:
                break
        try:
            p = self.estado.agregar_proyecto(nombre)
        except db.DBError as e:
            QMessageBox.critical(self, "No se pudo crear la carpeta", str(e))
            return None
        self._actualizar_proyecto_activo()
        self.mostrar_pagina(self.pagina_actual or "dashboard")
        return p

    def editar_proyecto(self, proyecto_id=None):
        """Renombra un proyecto (por defecto el activo). Devuelve True si se renombró."""
        proyecto_id = proyecto_id or self.estado.proyecto_actual_id
        p = next((x for x in self.estado.proyectos if x.id == proyecto_id), None)
        if not p:
            return False
        texto = p.nombre
        while True:
            texto, ok = pedir_nombre(self, "Renombrar carpeta",
                                    "Nuevo nombre de la carpeta:", texto)
            if not ok:
                return False
            nombre = texto.strip()
            msg = error_nombre(nombre, "El nombre de la carpeta")
            if msg:
                QMessageBox.warning(self, "Nombre no válido", msg)
            elif self.estado.nombre_proyecto_existe(nombre, excepto_id=proyecto_id):
                QMessageBox.warning(self, "Nombre repetido",
                                    f"Ya existe una carpeta llamada '{nombre}'. Elige otro nombre.")
            else:
                break
        self.estado.renombrar_proyecto(proyecto_id, nombre)
        self._actualizar_proyecto_activo()
        return True

    def abrir_proyecto(self, proyecto_id):
        """Cambia a la carpeta elegida y refresca la página abierta."""
        if not proyecto_id or proyecto_id == self.estado.proyecto_actual_id:
            return
        self.estado.cargar_proyecto(proyecto_id)
        self._actualizar_proyecto_activo()
        self.mostrar_pagina(self.pagina_actual or "dashboard")

    # ── Cerrar sesión ────────────────────────────────────────
    def cerrar_sesion(self):
        """Cierra la sesión actual y vuelve a la pantalla de login."""
        resp = QMessageBox.question(self, "Cerrar sesión",
                                    "¿Seguro que deseas cerrar sesión?")
        if resp != QMessageBox.Yes:
            return
        from login import LoginWindow  # import diferido: evita ciclo de imports

        # 1) Guardar mientras la sesión sigue activa
        guardar_en_storage(self.estado)

        # 2) El login usa sus propios estilos: quitar el QSS global del tema
        QApplication.instance().setStyleSheet("")

        # 3) Abrir el login ANTES de cerrar esta ventana (si no, la app se cierra)
        login = LoginWindow()

        def abrir_sistema(_usuario):
            nueva = VentanaPrincipal()
            nueva.showMaximized()
            login.ventana_principal = nueva
            login.close()

        login.login_exitoso.connect(abrir_sistema)
        login.showMaximized()
        self._login = login  # evitar que el recolector de basura lo destruya
        QApplication.instance()._login = login

        # 4) Cerrar esta ventana (closeEvent guarda) y recién ahí borrar la sesión
        self.close()
        db.cerrar_sesion()

    # ── Tema claro / oscuro ──────────────────────────────────
    def alternar_tema(self):
        self.estado.tema = "claro" if self.estado.tema == "oscuro" else "oscuro"
        self._aplicar_tema()
        guardar_en_storage(self.estado)

    def _aplicar_tema(self):
        paleta = PALETA_CLARA if self.estado.tema == "claro" else PALETA_OSCURA
        QApplication.instance().setStyleSheet(generar_qss(paleta))
        self.btn_tema.setText("🌙 Oscuro" if self.estado.tema == "claro" else "☀️ Claro")

    # ── Cierre: asegurar guardado ─────────────────────────────
    def closeEvent(self, event):
        guardar_en_storage(self.estado)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaPrincipal()
    ventana.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
