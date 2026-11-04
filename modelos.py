# ═══════════════════════════════════════════════════════════
# modelos.py — Estado de la aplicación y reglas contables.
# Es el equivalente Python a la sección STATE + SALDOS + BALANCE
# GENERAL (calcBalance) de app24.js.
# ═══════════════════════════════════════════════════════════
from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtCore import QObject, Signal

from utilidades import nuevo_id, hoy
import db
import roles


@dataclass
class Cuenta:
    id: str
    nombre: str
    naturaleza: str          # Activo | Pasivo | Patrimonio | Ingreso | Egreso
    saldo_inicial: float = 0.0
    descripcion: str = ""
    fecha: str = field(default_factory=hoy)
    codigo: str = ""         # código del catálogo de cuentas (ej. 1101), opcional


@dataclass
class Partida:
    id: str
    cuenta: str               # id de la Cuenta
    tipo: str                 # 'Debe' | 'Haber'
    monto: float
    descripcion: str = ""


@dataclass
class Asiento:
    id: str
    num: int
    fecha: str
    descripcion: str
    partidas: list  # list[Partida]


@dataclass
class Proyecto:
    id: str
    nombre: str
    cuentas: list = field(default_factory=list)     # list[Cuenta]
    asientos: list = field(default_factory=list)    # list[Asiento]
    next_asiento_num: int = 1


# Palabras clave usadas para clasificar Activo/Pasivo corriente vs no
# corriente, igual que en calcBalance() del JS original.
KEYWORDS_CORRIENTE_ACTIVO = [
    "caja", "bancos", "mercancías", "mercancia", "clientes",
    "documentos por cobrar", "inventario", "deudores", "papelería",
    "papeleria", "anticipos", "iva", "efectivo",
    "por cobrar", "pagado por anticipado", "pagados por anticipado", "anticipado",
    "cuentas por cobrar", "documentos por cobrar", "intereses por cobrar",
    "suministros", "útiles", "utiles", "materiales", "materia prima",
    "productos terminados", "inversiones temporales", "deudores",
]
KEYWORDS_CORRIENTE_PASIVO = [
    "proveedores", "cuentas por pagar", "iva por pagar", "ir por pagar",
    "anticipos de clientes", "gastos por pagar", "gastos acumulados",
    "gastos pendientes", "dividendos por pagar", "préstamos a corto",
    "prestamos a corto",
    "por pagar", "acreedores", "documentos por pagar", "sueldos", "salarios",
    "inss", "impuestos por pagar", "intereses por pagar", "corto plazo",
    "ingresos diferidos", "cobrados por anticipado", "cobrado por anticipado",
    "sobregiro", "retenciones",
]


class EstadoApp(QObject):
    """Contenedor central del estado contable. Emite `cambiado` cada vez
    que los datos se modifican, para que todas las páginas puedan
    refrescarse (equivalente a llamar renderX() tras cada acción en JS)."""

    cambiado = Signal()

    def __init__(self):
        super().__init__()
        self.cuentas: list[Cuenta] = []
        self.asientos: list[Asiento] = []
        self.next_asiento_num: int = 1
        self.proyectos: list[Proyecto] = []
        self.proyecto_actual_id: Optional[str] = None
        self.tema: str = "oscuro"  # 'oscuro' | 'claro'
        self._init_proyectos()

    # ── PROYECTOS ──────────────────────────────────────────
    def _init_proyectos(self):
        if not self.proyectos:
            p1 = Proyecto(id=nuevo_id(), nombre="Proyecto 1")
            self.proyectos.append(p1)
            self.proyecto_actual_id = p1.id

    def guardar_proyecto_actual(self):
        p = self._buscar_proyecto(self.proyecto_actual_id)
        if not p:
            return
        p.cuentas = list(self.cuentas)
        p.asientos = list(self.asientos)
        p.next_asiento_num = self.next_asiento_num

    def cargar_proyecto(self, proyecto_id: str):
        self.guardar_proyecto_actual()
        p = self._buscar_proyecto(proyecto_id)
        if not p:
            return
        self.proyecto_actual_id = p.id
        self.cuentas = list(p.cuentas)
        self.asientos = list(p.asientos)
        self.next_asiento_num = p.next_asiento_num
        self.cambiado.emit()

    def nombre_proyecto_existe(self, nombre: str, excepto_id: Optional[str] = None) -> bool:
        return any(p.nombre.lower() == nombre.strip().lower() and p.id != excepto_id
                   for p in self.proyectos)

    def agregar_proyecto(self, nombre: str) -> Proyecto:
        """Crea un proyecto con el nombre dado, lo guarda en SQLite y lo deja
        como proyecto activo. Lanza db.DBError si no se pudo guardar."""
        nombre = nombre.strip()
        if not nombre:
            raise db.DBError("Escribe un nombre para el proyecto.")
        if self.nombre_proyecto_existe(nombre):
            raise db.DBError("Ya existe un proyecto con ese nombre.")
        p = Proyecto(id=nuevo_id(), nombre=nombre)
        db.crear_proyecto(p.id, p.nombre)   # si falla, no se cambia nada en memoria
        self.guardar_proyecto_actual()
        self.proyectos.append(p)
        self.proyecto_actual_id = p.id
        self.cuentas = []
        self.asientos = []
        self.next_asiento_num = 1
        self.cambiado.emit()
        return p

    def renombrar_proyecto(self, proyecto_id: str, nuevo_nombre: str):
        p = self._buscar_proyecto(proyecto_id)
        if p and nuevo_nombre.strip():
            db.renombrar_proyecto(proyecto_id, nuevo_nombre.strip())
            p.nombre = nuevo_nombre.strip()
            if proyecto_id == self.proyecto_actual_id:
                self.guardar_proyecto_actual()
            self.cambiado.emit()

    def eliminar_proyecto(self, proyecto_id: str) -> bool:
        if len(self.proyectos) <= 1:
            return False
        self.proyectos = [p for p in self.proyectos if p.id != proyecto_id]
        if self.proyecto_actual_id == proyecto_id:
            p = self.proyectos[0]
            self.proyecto_actual_id = p.id
            self.cuentas = list(p.cuentas)
            self.asientos = list(p.asientos)
            self.next_asiento_num = p.next_asiento_num
        self.cambiado.emit()
        return True

    def _buscar_proyecto(self, proyecto_id) -> Optional[Proyecto]:
        return next((p for p in self.proyectos if p.id == proyecto_id), None)

    # ── CUENTAS ────────────────────────────────────────────
    def agregar_cuenta(self, nombre, naturaleza, saldo_inicial, descripcion, codigo="") -> Cuenta:
        roles.requiere("gestionar_cuentas")
        c = Cuenta(id=nuevo_id(), nombre=nombre, naturaleza=naturaleza,
                   saldo_inicial=saldo_inicial, descripcion=descripcion, fecha=hoy(),
                   codigo=(codigo or "").strip())
        self.cuentas.append(c)
        try:
            db.guardar_cuenta(c.id, c.nombre, c.naturaleza, c.saldo_inicial, c.descripcion, c.fecha,
                              codigo=c.codigo, proyecto_id=self.proyecto_actual_id)
        except db.DBError as e:
            print(f"No se pudo guardar la cuenta en la base de datos: {e}")
        self.cambiado.emit()
        return c

    def editar_cuenta(self, cuenta_id, nombre, naturaleza, saldo_inicial, descripcion, codigo=None):
        roles.requiere("gestionar_cuentas")
        c = next((x for x in self.cuentas if x.id == cuenta_id), None)
        if c:
            c.nombre, c.naturaleza = nombre, naturaleza
            c.saldo_inicial, c.descripcion = saldo_inicial, descripcion
            if codigo is not None:          # None = dejar el código como estaba
                c.codigo = codigo.strip()
            try:
                db.guardar_cuenta(c.id, c.nombre, c.naturaleza, c.saldo_inicial, c.descripcion, c.fecha,
                                  codigo=c.codigo, proyecto_id=self.proyecto_actual_id)
            except db.DBError as e:
                print(f"No se pudo actualizar la cuenta en la base de datos: {e}")
            self.cambiado.emit()

    def eliminar_cuenta(self, cuenta_id):
        roles.requiere("gestionar_cuentas")
        self.cuentas = [c for c in self.cuentas if c.id != cuenta_id]
        for a in self.asientos:
            a.partidas = [p for p in a.partidas if p.cuenta != cuenta_id]
        try:
            db.eliminar_cuenta(cuenta_id)
        except db.DBError as e:
            print(f"No se pudo eliminar la cuenta en la base de datos: {e}")
        self.cambiado.emit()

    def nombre_existe(self, nombre: str, excepto_id: Optional[str] = None) -> bool:
        return any(c.nombre.lower() == nombre.lower() and c.id != excepto_id for c in self.cuentas)

    def codigo_existe(self, codigo: str, excepto_id: Optional[str] = None) -> bool:
        """True si otra cuenta del proyecto ya usa ese código (vacío no cuenta)."""
        codigo = (codigo or "").strip().lower()
        if not codigo:
            return False
        return any((c.codigo or "").strip().lower() == codigo and c.id != excepto_id
                   for c in self.cuentas)

    # ── ASIENTOS ───────────────────────────────────────────
    def registrar_asiento(self, fecha, descripcion, partidas: list[Partida]) -> Asiento:
        a = Asiento(id=nuevo_id(), num=self.next_asiento_num, fecha=fecha,
                    descripcion=descripcion, partidas=partidas)
        self.asientos.append(a)
        self.next_asiento_num += 1
        try:
            db.registrar_asiento(a.id, a.num, a.fecha, a.descripcion, a.partidas,
                                 proyecto_id=self.proyecto_actual_id)
        except db.DBError as e:
            print(f"No se pudo guardar el asiento en la base de datos: {e}")
        self.cambiado.emit()
        return a

    def editar_asiento(self, asiento_id, fecha, descripcion, partidas: list[Partida]) -> Asiento:
        """Modifica un asiento existente (fecha, descripción y partidas).
        Guarda primero en SQLite; si falla lanza db.DBError y NO cambia nada
        en memoria. Al terminar emite `cambiado`, así Mayor, Balance General,
        Estado de Resultados, etc. se recalculan solos."""
        roles.requiere("registrar_asientos")
        a = next((x for x in self.asientos if x.id == asiento_id), None)
        if a is None:
            raise db.DBError("No se encontró el asiento.")
        db.actualizar_asiento(a.id, fecha, descripcion, partidas)
        a.fecha, a.descripcion, a.partidas = fecha, descripcion, partidas
        self.cambiado.emit()
        return a

    # ── SALDOS (equivalente a getSaldoCuenta / getTotNat) ──
    def saldo_cuenta(self, cuenta_id: str) -> float:
        c = next((x for x in self.cuentas if x.id == cuenta_id), None)
        if not c:
            return 0.0
        debe = haber = 0.0
        for a in self.asientos:
            for p in a.partidas:
                if p.cuenta == cuenta_id:
                    if p.tipo == "Debe":
                        debe += float(p.monto)
                    else:
                        haber += float(p.monto)
        # El saldo inicial es solo referencia; no se suma automáticamente
        # (igual que en el original — el usuario debe registrar el asiento
        # de apertura manualmente si quiere que se refleje).
        if c.naturaleza in ("Activo", "Egreso"):
            return debe - haber
        return haber - debe

    def total_naturaleza(self, naturaleza: str) -> float:
        return sum(self.saldo_cuenta(c.id) for c in self.cuentas if c.naturaleza == naturaleza)

    # ── BALANCE GENERAL (equivalente a calcBalance) ────────
    def calcular_balance(self) -> dict:
        utilidad = self.total_naturaleza("Ingreso") - self.total_naturaleza("Egreso")

        act_corrientes = [c for c in self.cuentas if c.naturaleza == "Activo"
                           and any(k in c.nombre.lower() for k in KEYWORDS_CORRIENTE_ACTIVO)]
        act_no_corrientes = [c for c in self.cuentas if c.naturaleza == "Activo"
                              and c not in act_corrientes]
        pas_corrientes = [c for c in self.cuentas if c.naturaleza == "Pasivo"
                           and any(k in c.nombre.lower() for k in KEYWORDS_CORRIENTE_PASIVO)]
        pas_no_corrientes = [c for c in self.cuentas if c.naturaleza == "Pasivo"
                              and c not in pas_corrientes]
        patrimonio = [c for c in self.cuentas if c.naturaleza == "Patrimonio"]

        t_ac = sum(self.saldo_cuenta(c.id) for c in act_corrientes)
        t_anc = sum(self.saldo_cuenta(c.id) for c in act_no_corrientes)
        t_pc = sum(self.saldo_cuenta(c.id) for c in pas_corrientes)
        t_pnc = sum(self.saldo_cuenta(c.id) for c in pas_no_corrientes)
        t_pat = sum(self.saldo_cuenta(c.id) for c in patrimonio)

        total_activos = t_ac + t_anc
        total_pasivos = t_pc + t_pnc
        total_patrimonio_util = t_pat + utilidad
        total_pas_patr = total_pasivos + total_patrimonio_util

        return {
            "act_corrientes": act_corrientes, "act_no_corrientes": act_no_corrientes,
            "pas_corrientes": pas_corrientes, "pas_no_corrientes": pas_no_corrientes,
            "patrimonio": patrimonio,
            "t_ac": t_ac, "t_anc": t_anc, "t_pc": t_pc, "t_pnc": t_pnc, "t_pat": t_pat,
            "utilidad": utilidad,
            "total_activos": total_activos, "total_pasivos": total_pasivos,
            "total_patrimonio_util": total_patrimonio_util,
            "total_pas_patr": total_pas_patr,
        }
