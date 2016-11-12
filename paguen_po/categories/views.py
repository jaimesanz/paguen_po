# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from core.custom_decorators import request_passes_test
from core.utils import user_has_vivienda
from expenses.models import Gasto
from .forms import CategoriaForm, EditCategoriaForm
from .models import Categoria


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
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
            return redirect("categorias")
        else:
            messages.error(
                request,
                "Se produjo un error procesando la solicitud")
            return redirect("error")
    this_viv_global = vivienda.get_vivienda_global_categorias()
    custom_cats = vivienda.get_vivienda_custom_categorias()
    return render(request, "vivienda/categorias.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
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
                return redirect("nueva_categoria")
            else:
                messages.success(request, mensaje)
                return redirect("categorias")
        else:
            messages.error(request, "Debe ingresar un nombre de categoría")
            return redirect("nueva_categoria")
    form = CategoriaForm()
    return render(request, "vivienda/nueva_categoria.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
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
                return redirect("error")
            elif categoria.is_global():
                messages.error(request,
                               "No puede eliminar una categoría global")
                return redirect("categorias")
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

    return redirect("categorias")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    vivienda = request.user.get_vivienda()
    if categoria.vivienda != vivienda:
        messages.error(
            request,
            "No tiene permiso para ver esta página."
        )
        return redirect("error")
    if request.POST:
        form = EditCategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect("categorias")
    else:
        form = EditCategoriaForm(instance=categoria)
    return render(
        request,
        "vivienda/edit_category.html",
        {
            'form': form,
            'vivienda': vivienda,
            'categoria': categoria.nombre
        }
    )
