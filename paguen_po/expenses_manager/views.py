# -*- coding: utf-8 -*-
import json
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.forms import inlineformset_factory
from django.forms.models import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from budgets.models import Presupuesto
from categories.models import Categoria
from expenses.models import Gasto, ConfirmacionGasto
from groceries.models import Item, ListaCompras, ItemLista
from periods.models import YearMonth, get_current_year_month_obj
from .custom_decorators import request_passes_test
from .forms import ItemForm, \
    GastoForm, EditGastoForm, ItemListaForm, BaseItemListaFormSet, \
    PresupuestoForm, PresupuestoEditForm
from .utils import get_periods, user_has_vivienda


def home(request):
    if request.user.is_authenticated() and request.user.has_vivienda():
        return redirect("vivienda")
    return render(request, 'general/home.html', locals())


def about(request):
    return render(request, "general/about.html", locals())


def error(request):
    return render(request, "general/error.html", locals())


######################################################
# from here on, everything must have @login_required
######################################################


@login_required
def login_post_process(request):
    # set session variables here
    request.session['user_has_vivienda'] = request.user.has_vivienda()
    return redirect("home")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def items(request):
    vivienda = request.user.get_vivienda()
    items = vivienda.get_items()
    return render(request, "vivienda/items.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def new_item(request):
    if request.POST:
        form = ItemForm(request.POST)
        if form.is_valid():
            try:
                new_item = form.save(commit=False)
                new_item.vivienda = request.user.get_vivienda()
                new_item.save()
                return redirect("items")
            except IntegrityError as e:
                messages.error(
                    request,
                    "Ya existe el Item '%s'" % (request.POST.get("nombre")))
                return redirect("new_item")
        else:
            messages.error(
                request,
                "Se produjo un error procesando los datos ingresados")
            return redirect("items")
    form = ItemForm()
    return render(request, "vivienda/new_item.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_item(request, item_name):
    item = get_object_or_404(
        Item,
        nombre=item_name,
        vivienda=request.user.get_vivienda())
    form = ItemForm(request.POST or None, instance=item)
    if request.POST:
        if form.is_valid():
            try:
                form.save()
                return redirect("items")
            except IntegrityError as e:
                messages.error(
                    request,
                    "Ya existe el Item '%s'" % (request.POST.get("nombre")))
                return redirect("edit_item", item_name)
        else:
            messages.error(
                request,
                "Se produjo un error procesando la solicitud")
            return redirect("edit_item", item_name)
    return render(request, "vivienda/edit_item.html", locals())


@login_required
def nuevo_gasto(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        form = GastoForm(request.POST, request.FILES)
        if form.is_valid():
            # if fecha_pago is a future one, don't create Gasto
            # and inform
            kwargs = {}
            fecha_pago_raw = request.POST.get("fecha_pago", None)
            if fecha_pago_raw is not None:
                try:
                    fecha_pago = datetime.strptime(
                        fecha_pago_raw,
                        settings.DATE_FORMAT).date()
                    if fecha_pago <= timezone.now().date():
                        kwargs["fecha_pago"] = fecha_pago
                    else:
                        messages.error(
                            request,
                            "No puede crear un Gasto para una fecha futura.")
                        return redirect("gastos")
                except ValueError:
                    # can't parse date, invalid format!
                    pass
            # set the user who created this
            nuevo_gasto = form.save(commit=False)
            nuevo_gasto.creado_por = request.user.get_vu()
            messages.success(
                request,
                "El gasto fue creado exitósamente")
            # check if it's paid
            is_paid = request.POST.get("is_paid", None)
            if is_paid == "yes":
                nuevo_gasto.pay(request.user.get_vu(), **kwargs)
            nuevo_gasto.save()
            return redirect("gastos")
        # form is not valid or missing/invalid "is_paid" field
        messages.error(request, "El formulario contiene errores")
        return redirect("gastos")
    return redirect("gastos")


@login_required
def gastos(request):
    vu = request.user.get_vu()
    if vu is None:
        return redirect("error")
    # get list of gastos
    gastos_pendientes_list, gastos_pagados_list = vu.get_gastos_vivienda()
    gastos_pendientes_confirmacion_list = \
        vu.vivienda.get_pending_confirmation_gastos()
    gasto_form = GastoForm()
    gasto_form.fields["categoria"].queryset = vu.vivienda.get_categorias()
    today = timezone.now().date().strftime(settings.DATE_FORMAT)
    gasto_form.fields["fecha_pago"].initial = today
    return render(request, "gastos/gastos.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def graph_gastos(request):
    vivienda = request.user.get_vivienda()
    today = timezone.now()
    current_year_month = get_current_year_month_obj()
    total_this_period = vivienda.get_total_expenses_period(current_year_month)
    categorias = vivienda.get_categorias()
    categoria_total = []
    for c in categorias:
        categoria_total.append((
            c,
            vivienda.get_total_expenses_categoria_period(
                c,
                current_year_month)))
    # TODO this window defines how far in the past the user can graph
    # it's set to 12 months, but in the future must be customizable
    # by the user. Also, the window should be measured in months
    window = 1  # year
    periods = ["%d-%d" % (y, m) for y, m in get_periods(
        today.year - window,
        today.month,
        today.year,
        today.month)]

    return render(
        request,
        "vivienda/graphs/gastos.html",
        {
            "periods": json.dumps(periods),
            "periods_indexes": json.dumps(
                [i for i in range(1, len(periods) + 1)]),
            "periods_indexes_max": len(periods),
            "vivienda": vivienda,
            "today": today,
            "current_year_month": current_year_month,
            "total_this_period": total_this_period,
            "categorias": categorias,
            "categoria_total": categoria_total,
            "window": window
        })


@login_required
def detalle_gasto(request, gasto_id):
    vivienda_usuario = request.user.get_vu()
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página")
        return redirect("error")
    gasto_form = GastoForm(model_to_dict(gasto))
    if request.POST:
        if gasto.is_paid() or gasto.is_pending_confirm():
            messages.error(
                request,
                "El gasto ya se encuentra pagado.")
            return redirect("error")
        messages.success(
            request,
            "El gasto fue pagado con éxito")
        gasto.pay(request.user.get_vu())
        return redirect("detalle_gasto", gasto.id)

    show_confirm_form = False
    if gasto.is_pending_confirm():
        # if it's confirmed, don't show the "confirm" button. Likewise,
        # if it's not confirmed, show the button
        show_confirm_form = not ConfirmacionGasto.objects.get(
            vivienda_usuario=request.user.get_vu(),
            gasto=gasto
        ).confirmed

    allowed_user = gasto.is_pending() or gasto.usuario == request.user.get_vu()
    show_edit_button = allowed_user and not gasto.categoria.is_transfer

    return render(request, "gastos/detalle_gasto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página.")
        return redirect("error")

    if gasto.categoria.is_transfer:
        messages.error(
            request,
            "Usted no está autorizado para ver esta página.")
        return redirect("detalle_gasto", gasto.id)

    if request.POST:
        new_monto = request.POST.get("monto", None)
        new_fecha = request.POST.get("fecha_pago", None)
        parsed_new_fecha = None
        parsed_new_monto = None
        # validate new_fecha
        try:
            parsed_new_fecha = datetime.strptime(
                new_fecha,
                settings.DATE_FORMAT).date()
            if parsed_new_fecha > timezone.now().date():
                messages.error(
                    request,
                    "No puede crear un Gasto para una fecha futura."
                )
                return redirect("edit_gasto", gasto.id)
        except ValueError:
            messages.error(
                request,
                "La fecha ingresada no es válida."
            )
            return redirect("edit_gasto", gasto.id)
        # validate new_monto
        try:
            parsed_new_monto = int(new_monto)
        except ValueError:
            pass
        if parsed_new_monto is None or parsed_new_monto <= 0:
            messages.error(
                request,
                "El monto ingresado debe ser un número mayor que 0."
            )
            return redirect("edit_gasto", gasto.id)

        msg = gasto.edit(request.user.get_vu(), new_monto, parsed_new_fecha)
        if msg == "No tiene permiso para editar este Gasto":
            messages.error(request, msg)
        else:
            messages.success(request, msg)
        return redirect("detalle_gasto", gasto.id)

    show_delete_button = gasto.is_pending() or \
        gasto.usuario == request.user.get_vu()

    if not show_delete_button:
        messages.error(
            request,
            "Usted no está autorizado para ver esta página."
        )
        return redirect("detalle_gasto", gasto.id)

    form = EditGastoForm(request.POST or None, instance=gasto)
    return render(request, "gastos/edit_gasto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def confirm_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página")
        return redirect("error")
    if request.POST:
        vu = request.user.get_vu()
        if ConfirmacionGasto.objects.get(
                gasto=gasto,
                vivienda_usuario=vu).confirmed:
            messages.error(request, "Usted ya confirmó este Gasto")
        else:
            vu.confirm(gasto)
            if gasto.is_paid():
                # this means everyone confirmed
                messages.success(
                    request,
                    "El gasto fue confirmado por todos los usuarios "
                    "pertinentes.")
            else:
                messages.success(
                    request,
                    "Gasto confirmado.")

    return redirect("detalle_gasto", gasto.id)


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def delete_gasto(request):
    if request.POST:
        gasto_id = request.POST.get("gasto", None)
        if gasto_id is not None:
            gasto = get_object_or_404(Gasto, id=gasto_id)
            if gasto.is_pending() or gasto.usuario == request.user.get_vu():
                messages.success(request, "Gasto eliminado.")
                gasto.delete()
            else:
                messages.error(
                    request,
                    "No tiene permiso para eliminar este Gasto")
                return redirect("detalle_gasto", gasto.id)

    # do nothing
    return redirect("gastos")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def lists(request):
    vivienda_usuario = request.user.get_vu()
    if vivienda_usuario.vivienda.has_pending_list():
        return redirect(
            "detalle_lista",
            vivienda_usuario.vivienda.get_pending_list().id
        )
    items = vivienda_usuario.vivienda.get_items()
    return render(request, "listas/lists.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def nueva_lista(request):
    if request.POST:
        max_item_index_post = request.POST.get("max_item_index", None)
        if max_item_index_post is None or max_item_index_post == "":
            messages.error(
                request,
                "La lista no puede estar vacía")
            return redirect("lists")
        max_item_index = int(max_item_index_post)

        # The post contains 2 inputs for each item
        # create array of pairs (item_name, quantity)
        if max_item_index > 0:
            item_quantity_dict = dict()
            for item_index in range(1, max_item_index + 1):
                # add items to list
                item_name = request.POST.get("item_" + str(item_index), None)
                quantity = request.POST.get(
                    "quantity_" + str(item_index), None)
                if (item_name is not None and
                        item_name != "" and
                        quantity is not None and
                        quantity != ""):
                    if item_quantity_dict.get(item_name, None) is not None:
                        # the item is already in the dict. this is an error!
                        messages.error(
                            request,
                            """
                            Una lista no puede contener varias veces el
                            mismo ítem
                            """)
                        return redirect("lists")
                    item_quantity_dict[item_name] = quantity
            # the list is OK
            if len(item_quantity_dict) == 0:
                messages.error(
                    request,
                    "La lista no puede estar vacía")
                return redirect("lists")
            nueva_lista = ListaCompras.objects.create(
                usuario_creacion=request.user.get_vu())
            for i, q in item_quantity_dict.items():
                try:
                    if int(q) > 0:
                        nueva_lista.add_item_by_name(i, q)
                except:
                    pass
            if nueva_lista.count_items() == 0:
                messages.error(
                    request,
                    "se produjo un error al crear la nueva lista"
                )
                nueva_lista.delete()
            return redirect("lists")
        else:
            messages.error(
                request,
                "La lista no puede estar vacía")
            return redirect("error")
    return redirect("lists")


@login_required
def detalle_lista(request, lista_id):
    vivienda_usuario = request.user.get_vu()
    lista = get_object_or_404(ListaCompras, id=lista_id)
    if lista.allow_user(request.user):
        if request.POST:
            if lista.is_done():
                messages.error(
                    request,
                    "La lista ya está pagada")
                return redirect("error")
            options = request.POST.get("options", None)
            rescatar_items = options == "rescatar_items"
            descartar_items = options == "descartar_items"
            monto_total = request.POST.get("monto_total", None)
            if monto_total is None:
                return redirect("error")
            # filter request.POST to get only the ids and values of the items
            # in the list
            item_list = []
            for key, value in request.POST.items():
                try:
                    item_id_int = int(key)
                    item_quantity = int(value)
                    item_list.append((item_id_int, item_quantity))
                except ValueError:
                    # TODO ???
                    pass
            nuevo_gasto = lista.buy_list(
                item_list, monto_total, vivienda_usuario)
            if nuevo_gasto == "monto_negativo":
                messages.error(
                    request,
                    "El monto ingresado debe ser un número mayor que 0.")
                return redirect("lists")
            if nuevo_gasto == "monto_invalido":
                messages.error(
                    request,
                    "El monto ingresado debe ser un número mayor que 0.")
                return redirect("lists")
            if nuevo_gasto is None:
                messages.error(
                    request,
                    "Debe seleccionar al menos 1 ítem")
                return redirect("error")
            if rescatar_items:
                nueva_lista = lista.rescue_items(vivienda_usuario)
            elif descartar_items:
                lista.discard_items()
            else:
                messages.error(
                    request,
                    "Hubo un error al procesar el pago")
                return redirect("error")
            if request.FILES.get("foto") is not None:
                nuevo_gasto.foto = request.FILES.get("foto")
                nuevo_gasto.save()
            return redirect("detalle_gasto", str(nuevo_gasto.id))
        else:
            # not post
            gasto_form = GastoForm()
            return render(request, "listas/detalle_lista.html", locals())
    else:
        # user is not allowed
        return redirect("error")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_list(request, lista_id):
    lista = get_object_or_404(ListaCompras, id=lista_id)
    if lista.allow_user(request.user):
        ListaComprasFormSet = inlineformset_factory(
            ListaCompras,
            ItemLista,
            form=ItemListaForm,
            formset=BaseItemListaFormSet,
            extra=0
        )
        if request.POST:

            formset = ListaComprasFormSet(
                request.user.get_vivienda().get_items(),
                request.POST,
                instance=lista
            )
            if formset.is_valid():
                formset.save()

                if lista.count_items() == 0:
                    lista.delete()
                    return redirect("lists")
                return redirect("detalle_lista", lista_id)

        else:
            formset = ListaComprasFormSet(
                valid_items_queryset=request.user.get_vivienda().get_items(),
                instance=lista
            )

        return render(request, "listas/edit_list.html", locals())
    else:
        # user cant see this
        return redirect("error")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def presupuestos(request):
    this_year_month = get_current_year_month_obj()
    return redirect("presupuestos_period", this_year_month.year, this_year_month.month)


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def presupuestos_period(request, year, month):
    vivienda_usuario = request.user.get_vu()
    this_period = get_object_or_404(
        YearMonth,
        year=year,
        month=month)
    presupuestos = Presupuesto.objects.filter(
        vivienda=request.user.get_vivienda(),
        year_month=this_period.id)
    next_year, next_month = this_period.get_next_period()
    prev_year, prev_month = this_period.get_prev_period()
    return render(request, "vivienda/presupuestos.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def nuevo_presupuesto(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        categoria_id = request.POST.get("categoria", None)
        if categoria_id is None:
            messages.error(request, 'Debe ingresar una categoría')
        period = request.POST.get("year_month", None)
        if period is None:
            messages.error(request, 'Debe ingresar un período')
        monto = request.POST.get("monto", None)
        if monto is None or int(monto) <= 0:
            messages.error(request, 'Debe ingresar un monto superior a 0')
        if any(val is None for val in [categoria_id,
                                       period,
                                       monto]):
            return redirect("nuevo_presupuesto")

        year_month = YearMonth.objects.get(
            id=request.POST.get("year_month", None))
        vivienda = vivienda_usuario.vivienda
        categoria = Categoria.objects.get(id=categoria_id)

        presupuesto, created = Presupuesto.objects.get_or_create(
            vivienda=vivienda,
            categoria=categoria,
            year_month=year_month)
        if not created:
            messages.error(request,
                           """
                Ya existe un presupuesto para el período seleccionado
                """)
            return redirect("nuevo_presupuesto")
        presupuesto.monto = monto
        presupuesto.save()
        messages.success(request,
                         """
                        El presupuesto fue creado exitósamente
                        """)
        return redirect(
            "presupuestos_period",
            year_month.year,
            year_month.month)
    form = PresupuestoForm()
    form.fields[
        "categoria"].queryset = vivienda_usuario.vivienda.get_categorias()
    return render(request, "vivienda/nuevo_presupuesto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def graphs_presupuestos(request):
    this_year_month = get_current_year_month_obj()
    return redirect("graphs_presupuestos_period", this_year_month.year, this_year_month.month)


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def graphs_presupuestos_period(request, year, month):
    this_period = get_object_or_404(
        YearMonth,
        year=year,
        month=month)
    presupuestos = Presupuesto.objects.filter(
        vivienda=request.user.get_vivienda(),
        year_month=this_period.id)
    next_year, next_month = this_period.get_next_period()
    prev_year, prev_month = this_period.get_prev_period()
    return render(request, "vivienda/graphs/presupuestos.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_presupuesto(request, year, month, categoria):
    vivienda = request.user.get_vivienda()
    categoria = get_object_or_404(
        Categoria,
        nombre=categoria,
        vivienda=vivienda)
    year_month = get_object_or_404(YearMonth, year=year, month=month)
    presupuesto = get_object_or_404(
        Presupuesto,
        year_month=year_month,
        categoria=categoria,
        vivienda=vivienda)
    if request.POST:
        def redirect_to_invalid_monto():
            messages.error(request, "Debe ingresar un monto mayor a 0")
            return redirect(
                "edit_presupuesto",
                int(year),
                int(month),
                categoria)

        form = PresupuestoEditForm(request.POST)
        if form.is_valid():
            nuevo_monto = request.POST.get("monto", None)
            try:
                nuevo_monto = int(nuevo_monto)
                if nuevo_monto <= 0:
                    return redirect_to_invalid_monto()
            except ValueError:
                return redirect_to_invalid_monto()

            presupuesto.monto = nuevo_monto
            presupuesto.save()
            messages.success(request, "Presupuesto modificado con éxito")
            return redirect(
                "graphs_presupuestos_period",
                year_month.year,
                year_month.month)
        else:
            return redirect_to_invalid_monto()

    form = PresupuestoEditForm(initial=presupuesto.__dict__)
    return render(request, "vivienda/edit_presupuesto.html", locals())


