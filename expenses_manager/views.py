# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from expenses_manager.forms import *
from django.contrib.auth.decorators import login_required
from expenses_manager.models import *
from django.forms.models import model_to_dict
import json
from django.utils import timezone
from django.contrib import messages
from expenses_manager.helper_functions import *
from expenses_manager.custom_decorators import request_passes_test
from django.db import IntegrityError
from django.utils.dateparse import parse_date


def home(request):
    return render(request, 'general/home.html', locals())


def about(request):
    return render(request, "general/about.html", locals())


def error(request):
    return render(request, "general/error.html", locals())

######################################################
# from here on, everything must have @login_required
######################################################

#######################
# AJAX dispatchers
#######################


@login_required
def get_gastos_graph(request):
    """
    Receives a POST of the form:
    {
        periods : "['2016-4', ..., '2017-2']",
        categorias : "['cat1', 'cat2', ...]",
        include_total : 0 (or 1)
    }
    Note that the values of the keys are STRNGS, not lists.

    Returns a dict of the form {String : [int, ...] , ...} where
    the string represents the name of the categoría, and the array of Integers
    represents the total amount of expenses for that categoria in that period
    of time (The index of the value represents the period of time)
    """

    periods_json = request.POST.get("periods", None)
    categorias_json = request.POST.get("categorias", None)
    if periods_json is None or categorias_json is None:
        return HttpResponse(json.dumps({}))
    periods = json.loads(periods_json)
    categorias = json.loads(categorias_json)
    vivienda = request.user.get_vivienda()
    year_months = [YearMonth.objects.get(
        year=p.split("-")[0], month=p.split("-")[1]) for p in periods]

    res = {}
    # total values
    if (request.POST.get("include_total", None) and
            int(request.POST.get("include_total", None)) > 0):
        total_values = []
        for ym in year_months:
            total_values.append(vivienda.get_total_expenses_period(ym))
        res["total"] = total_values

    # values per categoria
    for c in categorias:
        values = []
        for ym in year_months:
            values.append(
                vivienda.get_total_expenses_categoria_period(
                    c,
                    ym))
        res[c] = values
    return HttpResponse(json.dumps(res))


@login_required
def get_items_autocomplete(request):
    if 'term' in request.GET:
        items = Item.objects.filter(
            vivienda=request.user.get_vivienda(),
            nombre__istartswith=request.GET['term'])
        return HttpResponse(
            json.dumps(
                [(item.nombre, item.unidad_medida) for item in items]))


@login_required
def get_old_presupuesto(request):
    ans = []
    categoria = request.POST.get("categoria", None)
    year_month = request.POST.get("year_month", None)
    if categoria is not None and year_month is not None:
        presupuesto = Presupuesto.objects.filter(
            categoria=categoria,
            year_month=year_month,
            vivienda=request.user.get_vivienda()).first()
        if presupuesto is not None:
            ans.append((
                presupuesto.categoria.nombre,
                presupuesto.year_month.id,
                presupuesto.monto))
    return HttpResponse(json.dumps(ans))


#######################
# Views
#######################


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
        if start_date is not None:
            kwargs['start_date'] = parse_date(start_date)
        if end_date is not None:
            kwargs['end_date'] = parse_date(end_date)
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
    # TODO add custom error 404 page
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
    user_expenses = vivienda.get_total_expenses_per_active_user()
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
                nuevo_gasto.pagar(request.user)
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
    gasto_form = GastoForm()
    gasto_form.fields["categoria"].queryset = vu.vivienda.get_categorias()
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
        if gasto.is_paid():
            messages.error(
                request,
                "El gasto ya se encuentra pagado")
            return HttpResponseRedirect("/error")
        messages.success(
            request,
            "El gasto fue pagado con éxito")
        gasto.pagar(request.user)
        return HttpResponseRedirect("/detalle_gasto/%d/" % (gasto.id))
    return render(request, "gastos/detalle_gasto.html", locals())


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
