# -*- coding: utf-8 -*-
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .helper_functions.files import write_gastos_to_xls_sheet


@login_required
def get_gastos_xls(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=gastos.xls'

    vu = request.user.get_vu()
    gastos_pendientes_list, gastos_pagados_list = vu.get_gastos_vivienda()
    gastos_pendientes_confirmacion_list = \
        vu.vivienda.get_pending_confirmation_gastos()

    wb = xlwt.Workbook()

    ws_pagados = wb.add_sheet('Gastos Pagados')
    ws_pendientes_confirm = wb.add_sheet('Gastos Pendientes Confirmación')
    ws_pendientes = wb.add_sheet('Gastos Pendientes')

    write_gastos_to_xls_sheet(
        ws_pagados,
        gastos_pagados_list)
    write_gastos_to_xls_sheet(
        ws_pendientes_confirm,
        gastos_pendientes_confirmacion_list)
    write_gastos_to_xls_sheet(
        ws_pendientes,
        gastos_pendientes_list)

    wb.save(response)
    return response
