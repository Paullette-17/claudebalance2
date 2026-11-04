# ═══════════════════════════════════════════════════════════
# almacenamiento.py — Carga el estado desde SQLite al arrancar
# la app. El guardado de cada cambio (agregar/editar/eliminar
# cuenta, registrar asiento) ya ocurre al instante dentro de
# modelos.py (EstadoApp), llamando a db.py — por eso aquí ya
# no se escribe nada a disco.
#
# Los proyectos (modelos.Proyecto) también viven en SQLite: cada
# proyecto tiene sus propias cuentas y asientos, y son compartidos
# por todos los usuarios (Administrador y Operador) — al iniciar
# sesión se cargan todos los proyectos existentes en el sistema,
# no solo los del usuario que inició sesión.
# ═══════════════════════════════════════════════════════════
import db
from modelos import EstadoApp, Cuenta, Asiento, Partida, Proyecto


def guardar_en_storage(estado: EstadoApp):
    """Ya no hace falta un volcado manual: cada acción (agregar_cuenta,
    editar_cuenta, eliminar_cuenta, registrar_asiento) se guarda en
    SQLite en el momento en que ocurre, dentro de modelos.py. Se deja
    esta función para no romper las llamadas existentes en main.py."""
    estado.guardar_proyecto_actual()
    return True


def cargar_de_storage(estado: EstadoApp) -> bool:
    """Restaura todos los proyectos del sistema (compartidos entre
    Administrador y Operador) con sus cuentas y asientos desde SQLite.
    Requiere sesión iniciada (db.usuario_actual_id()) solo para poder
    leer. Devuelve True si había datos guardados. Si todavía no existe
    ningún proyecto en el sistema, guarda el "Proyecto 1" inicial."""
    if db.usuario_actual_id() is None:
        print("No hay sesión iniciada: no se cargan datos de la base de datos.")
        return False
    try:
        datos = db.cargar_proyectos_completos()
        if not datos:
            inicial = estado.proyectos[0]
            db.crear_proyecto(inicial.id, inicial.nombre)
            return False
    except db.DBError as e:
        print(f"No se pudo cargar desde la base de datos: {e}")
        return False

    proyectos = []
    for pd in datos:
        cuentas = [Cuenta(**cd) for cd in pd.get("cuentas", [])]
        asientos = []
        max_num = 0
        for ad in pd.get("asientos", []):
            partidas = [Partida(**ptd) for ptd in ad.get("partidas", [])]
            asientos.append(Asiento(id=ad["id"], num=ad["num"], fecha=ad["fecha"],
                                     descripcion=ad["descripcion"], partidas=partidas))
            max_num = max(max_num, ad["num"])
        proyectos.append(Proyecto(id=pd["id"], nombre=pd["nombre"], cuentas=cuentas,
                                   asientos=asientos, next_asiento_num=max_num + 1))

    estado.proyectos = proyectos
    actual = proyectos[0]
    estado.proyecto_actual_id = actual.id
    estado.cuentas = list(actual.cuentas)
    estado.asientos = list(actual.asientos)
    estado.next_asiento_num = actual.next_asiento_num
    return True
