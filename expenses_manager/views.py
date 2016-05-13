# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.conf import settings
from .forms import *
from .models import *
from .helper_functions.custom_decorators import *
from .helper_functions.views import *
from datetime import datetime
import json


def home(request):
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
    return HttpResponseRedirect("/home")


@login_required
def user_info(request):
    return render(request, "user_info.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def vacations(request):
    vacations = UserIsOut.objects.filter(
        vivienda_usuario__vivienda=request.user.get_vivienda(),
        vivienda_usuario__estado="activo")
    return render(request, "vivienda/vacations.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def new_vacation(request):
    """
    Displays new UserIsOut form. If it receives a post request, checks
    that it's valid, and creates a new UserIsOut instance if the POST
    is indeed valid. Otherwise, redirects to the same page and shows an error
    message.
    """
    if request.POST:
        start_date = request.POST.get("fecha_inicio", None)
        end_date = request.POST.get("fecha_fin", None)
        kwargs = {}
        bad_format_error = False
        if start_date is not None:
            try:
                parsed_start_date = datetime.strptime(
                    start_date,
                    settings.DATE_FORMAT).date()
                kwargs['start_date'] = parsed_start_date
            except ValueError:
                bad_format_error = True

        if end_date is not None:
            try:
                parsed_end_date = datetime.strptime(
                    end_date,
                    settings.DATE_FORMAT).date()
                kwargs['end_date'] = parsed_end_date
            except ValueError:
                bad_format_error = True

        if bad_format_error:
            # at least one of the given date strings has an invalid
            # date format
            messages.error(
                request,
                "Las fechas ingresadas no son válidas.")
            return redirect("new_vacation")

        vacation, msg = request.user.go_on_vacation(**kwargs)
        if not vacation:
            messages.error(request, msg)
            return redirect("new_vacation")
        else:
            messages.success(request, msg)
            return redirect("vacations")
    form = UserIsOutForm()
    return render(request, "vivienda/nueva_vacacion.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def edit_vacation(request, vacation_id):
    vacation = get_object_or_404(
        UserIsOut,
        id=vacation_id,
        vivienda_usuario__user=request.user)
    if request.POST:
        start_date = request.POST.get("fecha_inicio", None)
        end_date = request.POST.get("fecha_fin", None)
        kwargs = {}
        bad_format_error = False
        if start_date is not None:
            parsed_start_date = datetime.strptime(
                start_date, settings.DATE_FORMAT).date()
            bad_format_error = bad_format_error or parsed_start_date is None
            kwargs['start_date'] = parsed_start_date
        if end_date is not None:
            parsed_end_date = datetime.strptime(
                end_date, settings.DATE_FORMAT).date()
            bad_format_error = bad_format_error or parsed_end_date is None
            kwargs['end_date'] = parsed_end_date

        if bad_format_error:
            # at least one of the given date strings has an invalid
            # date format
            messages.error(
                request,
                "Las fechas ingresadas no son válidas.")
            return redirect("edit_vacation", vacation_id=int(vacation_id))

        # edit vacation
        edited_vacation, msg = request.user.update_vacation(vacation, **kwargs)
        if not edited_vacation:
            messages.error(request, msg)
            return redirect("edit_vacation", vacation_id=int(vacation_id))
        else:
            messages.success(request, msg)
            return redirect("vacations")

    form = UserIsOutForm(request.POST or None, instance=vacation)
    return render(request, "vivienda/editar_vacacion.html", locals())


@login_required
def invites_list(request):
    # get list of pending invites for this user
    invites_in, invites_out = request.user.get_invites()
    return render(request, "invites/invites_list.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def invite_user(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        post = request.POST.copy()
        post['invitado_por'] = vivienda_usuario
        form = InvitacionForm(post)
        if form.is_valid():
            # TODO check that no user with that mail is already in the Vivienda
            if post['email'] == request.user.email:
                messages.error(request, "¡No puede invitarse a usetd mismo!")
                return HttpResponseRedirect("/vivienda/")
            invited_user = User.objects.filter(email=post['email']).first()
            if invited_user is not None:
                invite = Invitacion(
                    email=post['email'],
                    invitado_por=vivienda_usuario,
                    invitado=invited_user)
                # TODO send email with link to register
            else:
                invite = Invitacion(
                    email=post['email'],
                    invitado_por=vivienda_usuario)
                # TODO send email with link accept/decline
            invite.save()
            return HttpResponseRedirect("/invites_list")
        else:
            return HttpResponseRedirect("/about")
    invite_form = InvitacionForm()
    return render(request, "invites/invite_user.html", locals())


@login_required
def invite(request, invite_id):
    invite = get_object_or_404(Invitacion, id=invite_id)
    invite_in = invite.is_invited_user(request.user)
    if invite_in:
        if invite.is_cancelled():
            return HttpResponseRedirect("/error")
        if request.POST:
            ans = request.POST['SubmitButton']
            if ans == "Aceptar":
                if request.user.has_vivienda():
                    messages.error(
                        request,
                        """Usted ya pertenece a una vivienda. Para aceptar la
                         invitación debe abandonar su vivienda actual.
                        """)
                    return HttpResponseRedirect("/error")
                invite.accept()
                request.session['user_has_vivienda'] = True
                messages.success(request, "La invitación fue aceptada.")
                return HttpResponseRedirect("/vivienda")
            elif ans == "Declinar":
                invite.reject()
                messages.success(request, "La invitación fue rechazada.")
                return HttpResponseRedirect("/home")
            messages.error(request, "Hubo un error al procesar la invitación")
            return HttpResponseRedirect("/error")

        return render(request, "invites/invite.html", locals())
    elif invite.is_invited_by_user(request.user):
        if request.POST:
            ans = request.POST['SubmitButton']
            if ans == "Cancelar":
                invite.cancel()
                return HttpResponseRedirect("/invites_list")

        return render(request, "invites/invite.html", locals())
    else:
        # redirect to page showing message "restricted"
        return HttpResponseRedirect("/error")


@login_required
def nueva_vivienda(request):
    if request.POST:
        form = ViviendaForm(request.POST)
        if form.is_valid():
            # process data
            # save new vivienda
            new_viv = create_new_vivienda(form)
            # create new viviendausuario
            vivienda_usuario = ViviendaUsuario(
                vivienda=new_viv, user=request.user)
            vivienda_usuario.save()
            request.session['user_has_vivienda'] = True
            return HttpResponseRedirect("/vivienda")

    vivienda_form = ViviendaForm()
    return render(request, "vivienda/nueva_vivienda.html", locals())


@login_required
def vivienda(request):
    vivienda_usuario = request.user.get_vu()
    roommates = request.user.get_roommates()
    return render(request, "vivienda/vivienda.html", locals())


@login_required
def manage_users(request):
    vivienda_usuario = request.user.get_vu()
    return render(request, "vivienda/manage_users.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def balance(request):
    vivienda = request.user.get_vivienda()
    users_disbalance = vivienda.get_disbalance_dict()
    instructions = get_instructions_from_balance(users_disbalance)
    form = TransferForm()
    form.fields["user"].queryset = request.user.get_roommates_users()
    return render(request, "vivienda/balance.html", locals())


@login_required
def abandon(request):
    if request.POST:
        vu = get_object_or_404(
            ViviendaUsuario, user=request.user, estado="activo")
        vu.leave()
        request.session['user_has_vivienda'] = False
    return HttpResponseRedirect("/home")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def categorias(request):
    vivienda = request.user.get_vivienda()
    if request.POST:
        categoria_nombre = request.POST.get("categoria", None)
        if categoria_nombre is not None and categoria_nombre != "":
            categoria = get_object_or_404(
                Categoria,
                nombre=categoria_nombre,
                vivienda=vivienda)
            categoria.toggle()
            return HttpResponseRedirect("/vivienda/categorias")
        else:
            messages.error(
                request,
                "Se produjo un error procesando la solicitud")
            return HttpResponseRedirect("/error")
    this_viv_global = vivienda.get_vivienda_global_categorias()
    custom_cats = vivienda.get_vivienda_custom_categorias()
    return render(request, "vivienda/categorias.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def nueva_categoria(request):
    vivienda = request.user.get_vivienda()
    if request.POST:
        nueva_categoria_nombre = request.POST.get("nombre", None)
        if nueva_categoria_nombre:
            nueva_categoria, mensaje = vivienda.add_categoria(
                nueva_categoria_nombre)
            if not nueva_categoria:
                messages.error(request, mensaje)
                return HttpResponseRedirect("/vivienda/categorias/new")
            else:
                messages.success(request, mensaje)
                return HttpResponseRedirect("/vivienda/categorias")
        else:
            messages.error(request, "Debe ingresar un nombre de categoría")
            return HttpResponseRedirect("/vivienda/categorias/new")
    form = CategoriaForm()
    return render(request, "vivienda/nueva_categoria.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def delete_categoria(request):
    if request.POST:
        categoria_id = request.POST.get("categoria", None)
        vivienda = request.user.get_vivienda()
        if categoria_id is not None:
            categoria = get_object_or_404(Categoria, id=categoria_id)
            if categoria.vivienda != vivienda:
                messages.error(request,
                               "No tiene permiso para editar esta Categoría")
                return HttpResponseRedirect("/error")
            elif categoria.is_global():
                messages.error(request,
                               "No puede eliminar una categoría global")
                return HttpResponseRedirect("/vivienda/categorias")
            else:
                gastos = Gasto.objects.filter(
                    categoria=categoria,
                    creado_por__vivienda=vivienda)
                otros_cat, __ = Categoria.objects.get_or_create(
                    nombre="Otros",
                    vivienda=vivienda)
                for gasto in gastos:
                    gasto.categoria = otros_cat
                    gasto.save()
                categoria.delete()
                messages.success(
                    request,
                    """
                    Categoría eliminada.
                    Los gastos asociados a ésta se traspasaron a la
                    categoría 'Otros'
                    """)

        else:
            messages.error(request,
                           "Debe especificar una categoría para eliminar")

    return HttpResponseRedirect("/vivienda/categorias")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def items(request):
    vivienda = request.user.get_vivienda()
    items = vivienda.get_items()
    return render(request, "vivienda/items.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def new_item(request):
    if request.POST:
        form = ItemForm(request.POST)
        if form.is_valid():
            try:
                new_item = form.save(commit=False)
                new_item.vivienda = request.user.get_vivienda()
                new_item.save()
                return HttpResponseRedirect("/vivienda/items")
            except IntegrityError as e:
                messages.error(
                    request,
                    "Ya existe el Item '%s'" % (request.POST.get("nombre")))
                return redirect("/vivienda/items/new/")
        else:
            messages.error(
                request,
                "Se produjo un error procesando los datos ingresados")
            return HttpResponseRedirect("/vivienda/items")
    form = ItemForm()
    return render(request, "vivienda/new_item.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
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
                return redirect("/vivienda/item/%s/" % (item_name))
        else:
            messages.error(
                request,
                "Se produjo un error procesando la solicitud")
            return redirect("/vivienda/item/%s/" % (item_name))
    return render(request, "vivienda/edit_item.html", locals())


@login_required
def nuevo_gasto(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        form = GastoForm(request.POST)
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
                        return HttpResponseRedirect("/gastos")
                except ValueError:
                    # can't parse date, invalid format!
                    pass
            # set the user who created this
            nuevo_gasto = form.save(commit=False)
            nuevo_gasto.creado_por = request.user.get_vu()
            nuevo_gasto.save()
            messages.success(
                request,
                "El gasto fue creado exitósamente")
            # check if it's paid
            is_paid = request.POST.get("is_paid", None)
            if is_paid == "yes":
                nuevo_gasto.pay(request.user.get_vu(), **kwargs)
                return HttpResponseRedirect("/gastos")
            elif is_paid == "no":
                return HttpResponseRedirect("/gastos")
        # form is not valid or missing/invalid "is_paid" field
        return HttpResponseRedirect("/error")
    return HttpResponseRedirect("/gastos")


@login_required
def gastos(request):
    vu = request.user.get_vu()
    if vu is None:
        return HttpResponseRedirect("/error")
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
                     login_url="/error/",
                     redirect_field_name=None)
def graph_gastos(request):
    vivienda = request.user.get_vivienda()
    today = timezone.now()
    current_year_month = YearMonth.objects.get(
        year=today.year,
        month=today.month)
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
        return HttpResponseRedirect("/error")
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
        return HttpResponseRedirect("/detalle_gasto/%d/" % (gasto.id))

    show_confirm_form = False
    if gasto.is_pending_confirm():
        # if it's confirmed, don't show the "confirm" button. Likewise,
        # if it's not confirmed, show the button
        show_confirm_form = not ConfirmacionGasto.objects.get(
            vivienda_usuario=request.user.get_vu(),
            gasto=gasto
        ).confirmed

    return render(request, "gastos/detalle_gasto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def edit_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página.")
        return HttpResponseRedirect("/error")
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
        except ValueError:
            messages.error(
                request,
                "La fecha ingresada no es válida."
            )
            return HttpResponseRedirect("/edit_gasto/%d/" % (gasto.id))
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
            return HttpResponseRedirect("/edit_gasto/%d/" % (gasto.id))

        msg = gasto.edit(request.user.get_vu(), new_monto, parsed_new_fecha)
        messages.success(request, msg)
        return HttpResponseRedirect("/detalle_gasto/%d/" % (gasto.id))

    form = EditGastoForm(request.POST or None, instance=gasto)
    return render(request, "gastos/edit_gasto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
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

    return redirect("/detalle_gasto/%d" % (gasto.id))


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def lists(request):
    vivienda_usuario = request.user.get_vu()
    listas_pendientes = ListaCompras.objects.filter(
        usuario_creacion__vivienda=request.user.get_vivienda(),
        estado="pendiente")
    return render(request, "listas/lists.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def nueva_lista(request):
    if request.POST:
        max_item_index_post = request.POST.get("max_item_index", None)
        if max_item_index_post is None or max_item_index_post == "":
            messages.error(
                request,
                "La lista no puede estar vacía")
            return HttpResponseRedirect("/lists")
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
                        return HttpResponseRedirect("/lists/")
                    item_quantity_dict[item_name] = quantity
            # the list is OK
            if len(item_quantity_dict) == 0:
                messages.error(
                    request,
                    "La lista no puede estar vacía")
                return HttpResponseRedirect("/lists")
            nueva_lista = ListaCompras.objects.create(
                usuario_creacion=request.user.get_vu())
            for i, q in item_quantity_dict.items():
                nueva_lista.add_item_by_name(i, q)
            return HttpResponseRedirect("/detalle_lista/%d" % (nueva_lista.id))
        else:
            messages.error(
                request,
                "La lista no puede estar vacía")
            return HttpResponseRedirect("/error")
    return HttpResponseRedirect("/lists")


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
                return HttpResponseRedirect("/error")
            rescatar_items = request.POST.get("rescatar_items", None)
            descartar_items = request.POST.get("descartar_items", None)
            monto_total = request.POST.get("monto_total", None)
            if monto_total is None:
                return HttpResponseRedirect("/error")
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
            if nuevo_gasto is None:
                messages.error(
                    request,
                    "Debe seleccionar al menos 1 ítem")
                return HttpResponseRedirect("/error")
            if rescatar_items:
                nueva_lista = lista.rescue_items(vivienda_usuario)
            elif descartar_items:
                lista.discard_items()
            else:
                messages.error(
                    request,
                    "Hubo un error al procesar el pago")
                return HttpResponseRedirect("/error")
            return HttpResponseRedirect(
                "/detalle_gasto/" + str(nuevo_gasto.id))
        else:
            # not post
            return render(request, "listas/detalle_lista.html", locals())
    else:
        # user is not allowed
        return HttpResponseRedirect("/error")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def presupuestos(request):
    vivienda_usuario = request.user.get_vu()
    today = timezone.now()
    return HttpResponseRedirect(
        "/presupuestos/%d/%d" % (today.year, today.month))


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
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
                     login_url="/error/",
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
            return HttpResponseRedirect("/presupuestos/new")

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
            return HttpResponseRedirect("/presupuestos/new")
        presupuesto.monto = monto
        presupuesto.save()
        messages.success(request,
                         """
                        El presupuesto fue creado exitósamente
                        """)
        return HttpResponseRedirect(
            "/presupuestos/%d/%d" % (year_month.year,
                                     year_month.month))
    form = PresupuestoForm()
    form.fields[
        "categoria"].queryset = vivienda_usuario.vivienda.get_categorias()
    return render(request, "vivienda/nuevo_presupuesto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def graphs_presupuestos(request):
    today = timezone.now()
    return HttpResponseRedirect(
        "/graphs/presupuestos/%d/%d" % (today.year, today.month))


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
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
                     login_url="/error/",
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
            return HttpResponseRedirect(
                "/presupuestos/%d/%d/%s/" % (int(year),
                                             int(month),
                                             categoria))
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
            return HttpResponseRedirect(
                "/graphs/presupuestos/%d/%d" % (
                    year_month.year,
                    year_month.month))
        else:
            return redirect_to_invalid_monto()

    form = PresupuestoEditForm(initial=presupuesto.__dict__)
    return render(request, "vivienda/edit_presupuesto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="/error/",
                     redirect_field_name=None)
def transfer(request):
    if request.POST:

        # validate user_id in POST
        user, msg = is_valid_transfer_to_user(
            request.POST.get("user", None),
            request.user)

        if user is None:
            # there are errors
            messages.error(request, msg)
            return redirect("transfer")

        # validate monto_raw in POST
        monto, msg = is_valid_transfer_monto(request.POST.get("monto", None))
        if monto is None:
            # there are errors
            messages.error(request, msg)
            return redirect("transfer")

        pos, neg = request.user.transfer(user, monto)
        if pos is not None and neg is not None:
            messages.success(
                request,
                "Transferencia realizada con éxito.")
            return redirect("balance")
        else:
            messages.error(
                request,
                "se produjo un error procesando la transferencia.")
            return redirect("transfer")

    form = TransferForm()
    form.fields["user"].queryset = request.user.get_roommates_users()
    return render(request, "transfer.html", locals())
