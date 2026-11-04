# ═══════════════════════════════════════════════════════════
# exportar_excel.py — Exportación a Excel (openpyxl) y PDF (Qt).
# Diseño ejecutivo: Times New Roman, paleta sobria (azul marino y
# grises) y pie de página con proyecto, numeración y fecha.
# ═══════════════════════════════════════════════════════════
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.properties import PageSetupProperties
from PySide6.QtWidgets import QFileDialog, QMessageBox

from utilidades import hoy

# ── Tipografía y paleta ejecutiva (sobria, sin colores llamativos) ──
FUENTE = "Times New Roman"
NAVY = "1F2A44"          # título principal
PIZARRA = "44546A"       # encabezados de tabla
GRIS_OSCURO = "595959"   # textos secundarios
GRIS_CLARO = "F2F2F2"    # subtotales / filas de apoyo
GRIS_BORDE = "BFBFBF"
TEXTO = "262626"
BLANCO = "FFFFFF"

# Secciones (tonos apagados)
SEC_ACTIVO = "2F3E5C"
SEC_PASIVO = "595959"
SEC_PATRIMONIO = "44546A"
SEC_INGRESO = "4F6355"
SEC_EGRESO = "6B5B4B"
FONDO_UTILIDAD = "E8ECE9"
FONDO_PERDIDA = "EEE7E5"

FMT_MONEDA = '"C$ "#,##0.00'

_LINEA = Side(style="thin", color=GRIS_BORDE)
_LINEA_OSC = Side(style="thin", color=GRIS_OSCURO)
_DOBLE = Side(style="double", color=GRIS_OSCURO)
BORDE_FINO = Border(left=_LINEA, right=_LINEA, top=_LINEA, bottom=_LINEA)
BORDE_INFERIOR = Border(bottom=_LINEA)
BORDE_TOTAL = Border(top=_LINEA_OSC)
BORDE_TOTAL_GENERAL = Border(top=_LINEA_OSC, bottom=_DOBLE)


def _fnt(bold=False, italic=False, size=11, color=TEXTO):
    return Font(name=FUENTE, bold=bold, italic=italic, size=size, color=color)


def _relleno(color):
    return PatternFill("solid", fgColor=color)


def _nombre_proyecto(estado) -> str:
    p = next((x for x in estado.proyectos if x.id == estado.proyecto_actual_id), None)
    return p.nombre if p else "Proyecto"


# ── Encabezado y configuración de impresión ────────────────
def _configurar_pagina(ws, estado, horizontal=False):
    """Orientación, márgenes, ajuste al ancho y PIE DE PÁGINA."""
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape" if horizontal else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_options.horizontalCentered = True
    ws.page_margins = PageMargins(left=0.7, right=0.7, top=0.75, bottom=0.9,
                                  header=0.3, footer=0.4)

    proyecto = _nombre_proyecto(estado).replace("&", "&&")
    pie = ws.oddFooter
    pie.left.text = f"Sistema Contable — {proyecto}"
    pie.center.text = "Página &P de &N"
    pie.right.text = f"Generado: {hoy()}"
    for parte in (pie.left, pie.center, pie.right):
        parte.font = f"{FUENTE},Italic"
        parte.size = 9
        parte.color = GRIS_OSCURO


def _estilo_cabecera_hoja(ws, estado, titulo, subtitulo, num_cols, horizontal=False):
    _configurar_pagina(ws, estado, horizontal)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    c = ws.cell(row=1, column=1, value=titulo)
    c.font = _fnt(bold=True, size=15, color=BLANCO)
    c.fill = _relleno(NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    for col in range(1, num_cols + 1):
        ws.cell(row=1, column=col).fill = _relleno(NAVY)
    ws.row_dimensions[1].height = 30

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=num_cols)
    c2 = ws.cell(row=2, column=1, value=_nombre_proyecto(estado))
    c2.font = _fnt(bold=True, size=11, color=NAVY)
    c2.alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=num_cols)
    c3 = ws.cell(row=3, column=1, value=subtitulo)
    c3.font = _fnt(italic=True, size=10, color=GRIS_OSCURO)
    c3.alignment = Alignment(horizontal="center")
    for col in range(1, num_cols + 1):
        ws.cell(row=3, column=col).border = BORDE_INFERIOR
    return 5  # próxima fila libre


def _fila_encabezados(ws, fila, encabezados):
    for i, h in enumerate(encabezados, start=1):
        c = ws.cell(row=fila, column=i, value=h)
        c.font = _fnt(bold=True, size=11, color=BLANCO)
        c.fill = _relleno(PIZARRA)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDE_FINO
    ws.row_dimensions[fila].height = 20
    return fila + 1


def _fila_seccion(ws, fila, texto, color, num_cols):
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=num_cols)
    c = ws.cell(row=fila, column=1, value=texto)
    c.font = _fnt(bold=True, size=11, color=BLANCO)
    c.fill = _relleno(color)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for col in range(1, num_cols + 1):
        ws.cell(row=fila, column=col).fill = _relleno(color)
    ws.row_dimensions[fila].height = 20
    return fila + 1


def _celda_monto(ws, fila, col, valor, bold=False, size=11, borde=BORDE_FINO, fondo=None):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font = _fnt(bold=bold, size=size)
    c.number_format = FMT_MONEDA
    c.alignment = Alignment(horizontal="right", vertical="top")
    c.border = borde
    if fondo:
        c.fill = _relleno(fondo)
    return c


def _celda_texto(ws, fila, col, valor, bold=False, italic=False, size=11,
                 borde=BORDE_FINO, fondo=None, horizontal="left", wrap=False):
    c = ws.cell(row=fila, column=col, value=valor)
    c.font = _fnt(bold=bold, italic=italic, size=size)
    c.alignment = Alignment(horizontal=horizontal, vertical="top", wrap_text=wrap)
    c.border = borde
    if fondo:
        c.fill = _relleno(fondo)
    return c


def _anchos(ws, anchos):
    for col, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(col)].width = ancho


def _pedir_ruta(parent, nombre_sugerido) -> str:
    ruta, _ = QFileDialog.getSaveFileName(parent, "Guardar archivo Excel",
                                           f"{nombre_sugerido}.xlsx", "Excel (*.xlsx)")
    return ruta


def _avisar_exito(parent, ruta):
    if ruta:
        QMessageBox.information(parent, "Exportación completa", f"Archivo guardado en:\n{ruta}")


# ── HOJA: CATÁLOGO DE CUENTAS ──────────────────────────────
def _hoja_cuentas(wb, estado):
    ws = wb.create_sheet("Catálogo de Cuentas")
    fila = _estilo_cabecera_hoja(ws, estado, "CATÁLOGO DE CUENTAS", f"Generado el {hoy()}", 6,
                                 horizontal=True)
    fila = _fila_encabezados(ws, fila, ["Código", "Nombre", "Naturaleza", "Descripción",
                                        "Saldo Inicial", "Saldo Actual"])
    ws.freeze_panes = ws.cell(row=fila, column=1)
    ws.print_title_rows = f"{fila - 1}:{fila - 1}"
    for cta in estado.cuentas:
        saldo = estado.saldo_cuenta(cta.id)
        _celda_texto(ws, fila, 1, cta.codigo or "—", horizontal="center")
        _celda_texto(ws, fila, 2, cta.nombre)
        _celda_texto(ws, fila, 3, cta.naturaleza, horizontal="center")
        _celda_texto(ws, fila, 4, cta.descripcion or "—", wrap=True)
        _celda_monto(ws, fila, 5, cta.saldo_inicial or 0)
        _celda_monto(ws, fila, 6, saldo)
        fila += 1
    _anchos(ws, [12, 30, 15, 36, 18, 18])
    return ws


# ── HOJA: LIBRO DIARIO ─────────────────────────────────────
def _hoja_diario(wb, estado):
    ws = wb.create_sheet("Libro Diario")
    fila = _estilo_cabecera_hoja(ws, estado, "LIBRO DIARIO", f"Generado el {hoy()}", 5)
    fila = _fila_encabezados(ws, fila, ["N°", "Fecha", "Cuenta", "Debe", "Haber"])
    ws.freeze_panes = ws.cell(row=fila, column=1)
    ws.print_title_rows = f"{fila - 1}:{fila - 1}"
    for a in sorted(estado.asientos, key=lambda x: x.num):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=5)
        c = ws.cell(row=fila, column=1, value=f"Asiento N.° {a.num} — {a.fecha} — {a.descripcion}")
        c.font = _fnt(bold=True, italic=True, color=NAVY)
        c.alignment = Alignment(horizontal="left", indent=1)
        for col in range(1, 6):
            ws.cell(row=fila, column=col).fill = _relleno(GRIS_CLARO)
            ws.cell(row=fila, column=col).border = BORDE_FINO
        fila += 1
        for p in a.partidas:
            cta = next((x for x in estado.cuentas if x.id == p.cuenta), None)
            _celda_texto(ws, fila, 1, a.num, horizontal="center")
            _celda_texto(ws, fila, 2, a.fecha, horizontal="center")
            _celda_texto(ws, fila, 3, cta.nombre if cta else "?")
            _celda_monto(ws, fila, 4, p.monto if p.tipo == "Debe" else None)
            _celda_monto(ws, fila, 5, p.monto if p.tipo == "Haber" else None)
            fila += 1
    _anchos(ws, [8, 13, 34, 18, 18])
    return ws


# ── HOJA: LIBRO MAYOR ───────────────────────────────────────
def _hoja_mayor(wb, estado):
    ws = wb.create_sheet("Libro Mayor")
    fila = _estilo_cabecera_hoja(ws, estado, "LIBRO MAYOR", f"Generado el {hoy()}", 4)
    for cta in estado.cuentas:
        fila = _fila_seccion(ws, fila, f"{cta.nombre}  ({cta.naturaleza})", SEC_PATRIMONIO, 4)
        for i, h in enumerate(["Descripción", "Debe", "Descripción", "Haber"], start=1):
            c = ws.cell(row=fila, column=i, value=h)
            c.font = _fnt(bold=True, color=NAVY)
            c.fill = _relleno(GRIS_CLARO)
            c.alignment = Alignment(horizontal="center")
            c.border = BORDE_FINO
        fila += 1
        movs_d = [(a.descripcion, p.monto) for a in estado.asientos for p in a.partidas
                  if p.cuenta == cta.id and p.tipo == "Debe"]
        movs_h = [(a.descripcion, p.monto) for a in estado.asientos for p in a.partidas
                  if p.cuenta == cta.id and p.tipo == "Haber"]
        for i in range(max(len(movs_d), len(movs_h))):
            d = movs_d[i] if i < len(movs_d) else (None, None)
            h = movs_h[i] if i < len(movs_h) else (None, None)
            _celda_texto(ws, fila, 1, d[0], wrap=True)
            _celda_monto(ws, fila, 2, d[1])
            _celda_texto(ws, fila, 3, h[0], wrap=True)
            _celda_monto(ws, fila, 4, h[1])
            fila += 1
        saldo = estado.saldo_cuenta(cta.id)
        _celda_texto(ws, fila, 1, "SALDO", bold=True, borde=BORDE_TOTAL, fondo=GRIS_CLARO)
        _celda_monto(ws, fila, 2, saldo, bold=True, borde=BORDE_TOTAL, fondo=GRIS_CLARO)
        _celda_texto(ws, fila, 3, None, borde=BORDE_TOTAL, fondo=GRIS_CLARO)
        _celda_texto(ws, fila, 4, None, borde=BORDE_TOTAL, fondo=GRIS_CLARO)
        fila += 2
    _anchos(ws, [28, 18, 28, 18])
    return ws


# ── Utilidades para Balance / Estado de Resultados ─────────
def _linea_cuenta(ws, fila, nombre, valor):
    _celda_texto(ws, fila, 1, None, borde=BORDE_INFERIOR)
    _celda_texto(ws, fila, 2, nombre, borde=BORDE_INFERIOR)
    _celda_monto(ws, fila, 3, valor, borde=BORDE_INFERIOR)


def _linea_total(ws, fila, etiqueta, valor, general=False, size=11, fondo=None):
    borde = BORDE_TOTAL_GENERAL if general else BORDE_TOTAL
    _celda_texto(ws, fila, 1, None, borde=borde, fondo=fondo)
    _celda_texto(ws, fila, 2, etiqueta, bold=True, size=size, borde=borde, fondo=fondo)
    _celda_monto(ws, fila, 3, valor, bold=True, size=size, borde=borde, fondo=fondo)


# ── HOJA: BALANCE GENERAL ──────────────────────────────────
def _hoja_balance(wb, estado):
    ws = wb.create_sheet("Balance General")
    fila = _estilo_cabecera_hoja(ws, estado, "BALANCE GENERAL", f"Al {hoy()}", 3)
    b = estado.calcular_balance()

    def bloque(titulo, color, cuentas_lista, total_label, total_val):
        nonlocal fila
        fila = _fila_seccion(ws, fila, titulo, color, 3)
        for c in cuentas_lista:
            _linea_cuenta(ws, fila, c.nombre, estado.saldo_cuenta(c.id))
            fila += 1
        _linea_total(ws, fila, total_label, total_val)
        fila += 1

    bloque("ACTIVOS CORRIENTES", SEC_ACTIVO, b["act_corrientes"], "Total Corrientes", b["t_ac"])
    bloque("ACTIVOS NO CORRIENTES", SEC_ACTIVO, b["act_no_corrientes"], "Total No Corrientes", b["t_anc"])
    _linea_total(ws, fila, "TOTAL ACTIVOS", b["total_activos"], general=True, size=12, fondo=GRIS_CLARO)
    fila += 2

    bloque("PASIVOS CORRIENTES", SEC_PASIVO, b["pas_corrientes"], "Total Corrientes", b["t_pc"])
    bloque("PASIVOS NO CORRIENTES", SEC_PASIVO, b["pas_no_corrientes"], "Total No Corrientes", b["t_pnc"])
    _linea_total(ws, fila, "TOTAL PASIVOS", b["total_pasivos"], general=True, size=12, fondo=GRIS_CLARO)
    fila += 2

    bloque("PATRIMONIO", SEC_PATRIMONIO, b["patrimonio"], "Total Patrimonio + Utilidad",
           b["total_patrimonio_util"])
    fila += 1
    _linea_total(ws, fila, "TOTAL PASIVO + PATRIMONIO", b["total_pas_patr"], general=True,
                 size=12, fondo=GRIS_CLARO)

    _anchos(ws, [3, 46, 22])
    return ws


# ── HOJA: ESTADO DE RESULTADOS ─────────────────────────────
def _hoja_er(wb, estado):
    ws = wb.create_sheet("Estado de Resultados")
    fila = _estilo_cabecera_hoja(ws, estado, "ESTADO DE RESULTADOS", f"Al {hoy()}", 3)
    ingresos = [c for c in estado.cuentas if c.naturaleza == "Ingreso"]
    egresos = [c for c in estado.cuentas if c.naturaleza == "Egreso"]
    tI = sum(estado.saldo_cuenta(c.id) for c in ingresos)
    tE = sum(estado.saldo_cuenta(c.id) for c in egresos)
    util = tI - tE

    fila = _fila_seccion(ws, fila, "INGRESOS", SEC_INGRESO, 3)
    for c in ingresos:
        _linea_cuenta(ws, fila, c.nombre, estado.saldo_cuenta(c.id)); fila += 1
    _linea_total(ws, fila, "TOTAL INGRESOS", tI)
    fila += 2

    fila = _fila_seccion(ws, fila, "EGRESOS", SEC_EGRESO, 3)
    for c in egresos:
        _linea_cuenta(ws, fila, c.nombre, estado.saldo_cuenta(c.id)); fila += 1
    _linea_total(ws, fila, "TOTAL EGRESOS", tE)
    fila += 2

    etiqueta = "UTILIDAD NETA" if util >= 0 else "PÉRDIDA NETA"
    _linea_total(ws, fila, etiqueta, abs(util), general=True, size=12,
                 fondo=(FONDO_UTILIDAD if util >= 0 else FONDO_PERDIDA))

    _anchos(ws, [3, 46, 22])
    return ws


# ── FUNCIONES PÚBLICAS DE EXPORTACIÓN (llamadas desde las páginas) ──
def exportar_cuentas_excel(estado, parent=None):
    wb = Workbook(); wb.remove(wb.active)
    _hoja_cuentas(wb, estado)
    ruta = _pedir_ruta(parent, "catalogo_cuentas")
    if ruta:
        wb.save(ruta); _avisar_exito(parent, ruta)


def exportar_diario_excel(estado, parent=None):
    wb = Workbook(); wb.remove(wb.active)
    _hoja_diario(wb, estado)
    ruta = _pedir_ruta(parent, "libro_diario")
    if ruta:
        wb.save(ruta); _avisar_exito(parent, ruta)


def exportar_mayor_excel(estado, parent=None):
    wb = Workbook(); wb.remove(wb.active)
    _hoja_mayor(wb, estado)
    ruta = _pedir_ruta(parent, "libro_mayor")
    if ruta:
        wb.save(ruta); _avisar_exito(parent, ruta)


def exportar_balance_excel(estado, parent=None):
    wb = Workbook(); wb.remove(wb.active)
    _hoja_balance(wb, estado)
    ruta = _pedir_ruta(parent, "balance_general")
    if ruta:
        wb.save(ruta); _avisar_exito(parent, ruta)


def exportar_er_excel(estado, parent=None):
    wb = Workbook(); wb.remove(wb.active)
    _hoja_er(wb, estado)
    ruta = _pedir_ruta(parent, "estado_resultados")
    if ruta:
        wb.save(ruta); _avisar_exito(parent, ruta)


def exportar_todo_excel(estado, parent=None):
    """Genera un único libro con todas las hojas (equivalente a exportarTodoExcel())."""
    wb = Workbook(); wb.remove(wb.active)
    _hoja_cuentas(wb, estado)
    _hoja_diario(wb, estado)
    _hoja_mayor(wb, estado)
    _hoja_balance(wb, estado)
    _hoja_er(wb, estado)
    ruta = _pedir_ruta(parent, f"reporte_contable_completo_{hoy()}")
    if ruta:
        wb.save(ruta); _avisar_exito(parent, ruta)


# ── PDF ─────────────────────────────────────────────────────
def _escribir_pdf_con_pie(html, ruta, proyecto):
    """Convierte HTML a PDF tamaño carta, con pie de página en cada hoja
    (proyecto · Página X de N · fecha de generación)."""
    from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
    from PySide6.QtGui import (QColor, QFont, QPageLayout, QPageSize, QPainter,
                               QPdfWriter, QPen, QTextDocument)

    writer = QPdfWriter(ruta)
    writer.setPageSize(QPageSize(QPageSize.Letter))
    writer.setPageMargins(QMarginsF(22, 20, 22, 18), QPageLayout.Millimeter)
    writer.setResolution(300)
    writer.setTitle(f"{proyecto} — Balance General")

    area = writer.pageLayout().paintRectPixels(writer.resolution())
    ancho, alto = float(area.width()), float(area.height())
    alto_pie = 0.45 * 300           # ~1,1 cm reservados para el pie
    alto_cuerpo = alto - alto_pie

    doc = QTextDocument()
    doc.documentLayout().setPaintDevice(writer)
    doc.setDefaultFont(QFont(FUENTE, 11))
    doc.setPageSize(QSizeF(ancho, alto_cuerpo))
    doc.setHtml(html)
    doc.setPageSize(QSizeF(ancho, alto_cuerpo))
    paginas = max(1, doc.pageCount())

    painter = QPainter(writer)
    fuente_pie = QFont(FUENTE, 9)
    fuente_pie.setItalic(True)
    for i in range(paginas):
        if i:
            writer.newPage()
        painter.save()
        painter.setClipRect(QRectF(0, 0, ancho, alto_cuerpo))
        painter.translate(0, -i * alto_cuerpo)
        doc.drawContents(painter, QRectF(0, i * alto_cuerpo, ancho, alto_cuerpo))
        painter.restore()

        # Pie de página
        y = alto_cuerpo + 0.12 * 300
        painter.setPen(QPen(QColor("#" + GRIS_BORDE), 3))
        painter.drawLine(0, int(y), int(ancho), int(y))
        painter.setPen(QColor("#" + GRIS_OSCURO))
        painter.setFont(fuente_pie)
        caja = QRectF(0, y + 12, ancho, alto_pie - 20)
        painter.drawText(caja, Qt.AlignLeft | Qt.AlignVCenter, f"Sistema Contable — {proyecto}")
        painter.drawText(caja, Qt.AlignHCenter | Qt.AlignVCenter, f"Página {i + 1} de {paginas}")
        painter.drawText(caja, Qt.AlignRight | Qt.AlignVCenter, f"Generado: {hoy()}")
    painter.end()


def exportar_balance_pdf(estado, parent=None):
    """Exporta el Balance General a PDF (con detalle de cuentas)."""
    b = estado.calcular_balance()
    proyecto = _nombre_proyecto(estado)
    borde = f"1px solid #{GRIS_BORDE}"

    def filas(cuentas):
        if not cuentas:
            return (f"<tr><td colspan='2' style='color:#{GRIS_OSCURO}'><i>— Sin cuentas —</i></td></tr>")
        return "".join(
            f"<tr><td style='border-bottom:{borde}'>{c.nombre}</td>"
            f"<td align='right' style='border-bottom:{borde}'>C$ {estado.saldo_cuenta(c.id):,.2f}</td></tr>"
            for c in cuentas)

    def tot(txt, val, grande=False):
        fondo = f"background-color:#{GRIS_CLARO};" if grande else ""
        tam = "font-size:12pt;" if grande else ""
        return (f"<tr><td style='border-top:1px solid #{GRIS_OSCURO};{fondo}{tam}'><b>{txt}</b></td>"
                f"<td align='right' style='border-top:1px solid #{GRIS_OSCURO};{fondo}{tam}'>"
                f"<b>C$ {val:,.2f}</b></td></tr>")

    def sec(txt, color):
        return (f"<tr><td colspan='2' style='background-color:#{color};color:#ffffff'>"
                f"<b>&nbsp;{txt}</b></td></tr>")

    def sub(txt):
        return (f"<tr><td colspan='2' style='color:#{NAVY}'><i>{txt}</i></td></tr>")

    html = f"""
    <div style="font-family:'{FUENTE}'; color:#{TEXTO};">
    <h1 align='center' style='color:#{NAVY}; font-size:20pt; margin-bottom:0'>BALANCE GENERAL</h1>
    <p align='center' style='font-size:12pt; margin:0'><b>{proyecto}</b></p>
    <p align='center' style='color:#{GRIS_OSCURO}; font-size:10pt; margin-top:2px'><i>Al {hoy()}</i></p>
    <hr>
    <table width='100%' cellspacing='0' cellpadding='4' style='font-size:11pt'>
    {sec('ACTIVOS', SEC_ACTIVO)}
    {sub('Activos Corrientes')}
    {filas(b['act_corrientes'])}{tot('Total Corrientes', b['t_ac'])}
    {sub('Activos No Corrientes')}
    {filas(b['act_no_corrientes'])}{tot('Total No Corrientes', b['t_anc'])}
    {tot('TOTAL ACTIVOS', b['total_activos'], True)}
    <tr><td colspan='2'>&nbsp;</td></tr>
    {sec('PASIVOS', SEC_PASIVO)}
    {sub('Pasivos Corrientes')}
    {filas(b['pas_corrientes'])}{tot('Total Corrientes', b['t_pc'])}
    {sub('Pasivos No Corrientes')}
    {filas(b['pas_no_corrientes'])}{tot('Total No Corrientes', b['t_pnc'])}
    {tot('TOTAL PASIVOS', b['total_pasivos'], True)}
    <tr><td colspan='2'>&nbsp;</td></tr>
    {sec('PATRIMONIO', SEC_PATRIMONIO)}
    {filas(b['patrimonio'])}
    <tr><td style='border-bottom:{borde}'>Utilidad/Pérdida del Ejercicio</td>
        <td align='right' style='border-bottom:{borde}'>C$ {b['utilidad']:,.2f}</td></tr>
    {tot('TOTAL PATRIMONIO', b['total_patrimonio_util'])}
    {tot('TOTAL PASIVO + PATRIMONIO', b['total_pas_patr'], True)}
    </table>
    </div>"""

    ruta, _ = QFileDialog.getSaveFileName(parent, "Guardar PDF", "balance_general.pdf", "PDF (*.pdf)")
    if not ruta:
        return
    _escribir_pdf_con_pie(html, ruta, proyecto)
    _avisar_exito(parent, ruta)
