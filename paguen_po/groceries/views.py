# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from expenses_manager.custom_decorators import request_passes_test
from expenses_manager.forms import ItemForm, GastoForm, ItemListaForm, \
    BaseItemListaFormSet
from expenses_manager.utils import user_has_vivienda
from .models import Item, ListaCompras, ItemLista


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
