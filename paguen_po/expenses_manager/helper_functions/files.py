# -*- coding: utf-8 -*-
import xlwt


def add_row(ws, row_index, elements, style=xlwt.XFStyle()):
    """
    Given a list of elements to write and a row index, writes all elements in
    said row, in order. Creates a column per element.
    :param ws: XLWT worksheet
    :param row_index: Integer
    :param elements: List( String )
    :param style: XLWT style
    :return: None
    """
    for idx, e in enumerate(elements):
        ws.write(row_index, idx, str(e), style)


def add_header(ws, elements):
    """
    Adds first row to worksheet using XLWT styles.
    :param ws: empty XLWT worksheet
    :param elements: List( String )
    :return: None
    """
    style = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                        'font: colour white, bold True;')
    add_row(ws, 0, elements, style)


def write_gastos_to_xls_sheet(ws, gastos):
    """
    For each gasto in gastos parameter, adds a new row to the worksheet.
    :param ws: empty XLWT Worksheet
    :param gastos: List( Gasto )
    :return: Integer
    """
    add_header(ws, get_gasto_headers())
    for idx, gasto in enumerate(gastos):
        add_row(ws, idx + 1, get_gasto_row_data(gasto))


def get_gasto_headers():
    """
    Returns the headers for a Gasto XLS worksheet
    :return: List( String )
    """
    return [
        "Fecha creación",
        "Año pago",
        "Mes pago",
        "Día pago",
        "Categoría",
        "Pagado por",
        "Monto"
    ]


def get_gasto_row_data(gasto):
    """
    Returns the data that will be written to the Gasto worksheet row.
    :param gasto: Gasto
    :return: List( String )
    """
    if not gasto.is_pending():
        data = [
            gasto.fecha_creacion,
            gasto.fecha_pago.year,
            gasto.fecha_pago.month,
            gasto.fecha_pago.day,
            gasto.categoria,
            gasto.usuario.user,
            gasto.monto
        ]
    else:
        data = [
            gasto.fecha_creacion,
            "-",
            "-",
            "-",
            gasto.categoria,
            "-",
            gasto.monto
        ]
    return data
