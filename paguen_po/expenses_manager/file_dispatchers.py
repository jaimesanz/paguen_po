# -*- coding: utf-8 -*-
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from expenses_manager.custom_decorators import request_passes_test
from expenses_manager.utils import write_gastos_to_xls_sheet, user_has_vivienda
from .helper_functions.views import user_has_vivienda


@login_required(redirect_field_name='gastos')
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def get_gastos_xls(request):
    # compute gastos
    vu = request.user.get_vu()
    gastos_pendientes, gastos_pagados = vu.get_gastos_vivienda()
    gastos_pendientes_confirmacion = \
        vu.vivienda.get_pending_confirmation_gastos()

    # create XLS file
    wb = xlwt.Workbook()
    # create each worksheet and write to them
    write_gastos_to_xls_sheet(
        wb.add_sheet('Gastos Pagados'),
        gastos_pagados)
    write_gastos_to_xls_sheet(
        wb.add_sheet('Gastos Pendientes Confirmación'),
        gastos_pendientes_confirmacion)
    write_gastos_to_xls_sheet(
        wb.add_sheet('Gastos Pendientes'),
        gastos_pendientes)

    # create response object with said file
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=gastos.xls'
    wb.save(response)
    return response
