# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from expenses_manager.forms import *
from django.contrib.auth.decorators import login_required
from expenses_manager.models import *
from django.forms.models import model_to_dict
import json
from django.utils import timezone
from django.contrib import messages


def home(request):
    # locals() creates a dict() object with all the variables from the local
    # scope. We are passing it to the template
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
def invites_list(request):
    # get list of pending invites for this user
    invites_in, invites_out = request.user.get_invites()
    return render(request, "invites/invites_list.html", locals())


@login_required
def invite_user(request):
    vivienda_usuario = request.user.get_vu()
    if vivienda_usuario is None:
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
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
            new_viv = form.save()
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
def abandon(request):
    if request.POST:
        vu = get_object_or_404(
            ViviendaUsuario, user=request.user, estado="activo")
        vu.leave()
        request.session['user_has_vivienda'] = False
    return HttpResponseRedirect("/home")


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
            if request.POST.get("is_paid", None) is not None:
                nuevo_gasto.pagar(request.user)
                return HttpResponseRedirect("/gastos")
            elif request.POST.get("is_not_paid", None) is not None:
                return HttpResponseRedirect("/gastos")
            else:
                return HttpResponseRedirect("/error")
        else:
            # TODO redirect to error
            pass
    return HttpResponseRedirect("/gastos")


@login_required
def balance(request):
    vivienda_usuario = request.user.get_vu()
    return render(request, "balance.html", locals())


@login_required
def visualizations(request):
    vivienda_usuario = request.user.get_vu()
    return render(request, "visualizations.html", locals())


@login_required
def gastos(request):
    vu = request.user.get_vu()
    if vu is None:
        return HttpResponseRedirect("/error")
    # get list of gastos
    gastos_pendientes_list, gastos_pagados_list = vu.get_gastos_vivienda()
    gasto_form = GastoForm()
    return render(request, "gastos/gastos.html", locals())


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
def lists(request):
    vivienda_usuario = request.user.get_vu()
    if vivienda_usuario is None:
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
    listas_pendientes = ListaCompras.objects.filter(
        usuario_creacion__vivienda=request.user.get_vivienda(),
        estado="pendiente")
    return render(request, "listas/lists.html", locals())


@login_required
def nueva_lista(request):
    if request.POST:
        if not request.user.has_vivienda():
            messages.error(
                request,
                "Debe pertenecer a una vivienda para ver esta página")
            return HttpResponseRedirect("/error")
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


def get_items_autocomplete(request):
    if 'term' in request.GET:
        items = Item.objects.filter(nombre__istartswith=request.GET['term'])
        return HttpResponse(
            json.dumps(
                [(item.nombre, item.unidad_medida) for item in items]))

def get_old_presupuesto(request):
    ans = []
    categoria = request.POST.get("categoria", None)
    year_month = request.POST.get("year_month", None)
    print(categoria)
    print(year_month)
    if categoria is not None and year_month is not None:
        presupuesto = Presupuesto.objects.filter(
            categoria=categoria,
            year_month=year_month,
            vivienda=request.user.get_vivienda()).first()
        if presupuesto is not None:
            ans.append((
                presupuesto.categoria.nombre, 
                presupuesto.year_month.id,
                presupuesto.monto ))
    return HttpResponse( json.dumps( ans ) )

@login_required
def presupuestos(request):
    vivienda_usuario = request.user.get_vu()
    if vivienda_usuario is None:
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
    today = timezone.now()
    return HttpResponseRedirect(
        "/presupuestos/%d/%d" % (today.year, today.month))


@login_required
def presupuestos_period(request, year, month):
    vivienda_usuario = request.user.get_vu()
    if vivienda_usuario is None:
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
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
def nuevo_presupuesto(request):
    vivienda_usuario = request.user.get_vu()
    if vivienda_usuario is None:
        messages.error(
            request,
            "Para ver esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
    if request.POST:
        categoria_nombre = request.POST.get("categoria", None)
        if categoria_nombre is None:
            messages.error(request, 'Debe ingresar una categoría')
        period = request.POST.get("year_month", None)
        if period is None:
            messages.error(request, 'Debe ingresar un período')
        monto = request.POST.get("monto", None)
        if monto is None or int(monto) <= 0:
            messages.error(request, 'Debe ingresar un monto superior a 0')
        if any(val is None for val in [categoria_nombre,
                                       period,
                                       monto]):
            return HttpResponseRedirect("/presupuestos/new")

        year_month = YearMonth.objects.get(
            id=request.POST.get("year_month", None))
        categoria = Categoria.objects.get(nombre=categoria_nombre)

        presupuesto, created = Presupuesto.objects.get_or_create(
            vivienda=request.user.get_vivienda(),
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
    return render(request, "vivienda/nuevo_presupuesto.html", locals())


@login_required
def graphs_presupuestos(request):
    if not request.user.has_vivienda():
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
    today = timezone.now()
    return HttpResponseRedirect(
        "/graphs/presupuestos/%d/%d" % (today.year, today.month))

@login_required
def graphs_presupuestos_period(request, year, month):
    if not request.user.has_vivienda():
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
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
def edit_presupuesto(request, year, month, categoria):
    if not request.user.has_vivienda():
        messages.error(
            request,
            "Para tener acceso a esta página debe pertenecer a una vivienda")
        return HttpResponseRedirect("/error")
    year_month = get_object_or_404(YearMonth, year=year, month=month)
    presupuesto = get_object_or_404(
        Presupuesto,
        year_month=year_month,
        categoria=categoria,
        vivienda=request.user.get_vivienda())
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
