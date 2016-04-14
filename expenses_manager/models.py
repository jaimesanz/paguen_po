# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# helper functions
def get_current_yearMonth_obj():
    """
    Returns the current YearMonth period.
    If the YarMonth doesn't exist, it creates it.
    """
    today = timezone.now()
    year_month, creted = YearMonth.objects.get_or_create(
        year=today.year, month=today.month)
    return year_month


def get_current_yearMonth():
    """
    Returns the current YearMonth period's ID field.
    If it doesn't exist, it creates it.
    """
    return get_current_yearMonth_obj().id


def get_default_estadoGasto():
    """
    Returns the "id" field of an instance of EstadoGasto with value "pendiente".
    If it doesn't exist, it creates it first.
    """
    estado_gasto, created = EstadoGasto.objects.get_or_create(
        estado="pendiente")
    return estado_gasto.id


def get_done_estadoGato():
    """
    Returns an instance of EstadoGasto with value "pagado".
    If it doesn't exist, it creates it first.
    """
    return EstadoGasto.objects.get_or_create(estado="pagado")[0]


def get_pending_estadoGasto():
    """
    Returns an instance of EstadoGasto with value "pendiente".
    If it doesn't exist, it creates it first.
    """
    return EstadoGasto.objects.get_or_create(estado="pendiente")[0]


# proxy user. This is used to add methods to the default django User class
# without altering it
class ProxyUser(User):

    class Meta:
        proxy = True

    def get_vu(self):
        """
        Returns the user's current active vivienda, or None if it doens't have
        one.
        """
        return ViviendaUsuario.objects.filter(
            user=self,
            estado="activo").first()

    def has_vivienda(self):
        """
        Returns True if the user has an active Vivienda.
        Otherwise, it returns False.
        """
        return ViviendaUsuario.objects.filter(
            user=self,
            estado="activo").exists()

    def get_vivienda(self):
        """
        Returns the active vivienda of the user, or None if it doesn't
        have any.
        """
        vivienda_usuario = self.get_vu()
        if vivienda_usuario is not None:
            return vivienda_usuario.vivienda
        else:
            return None

    def get_roommates(self):
        """
        Returns a list of all active members of the Vivienda,
        including the User that calls the method.
        If there's no active vivienda, returns None
        """
        return ViviendaUsuario.objects.filter(
            vivienda=self.get_vivienda(),
            estado="activo")

    def get_invites(self):
        """
        Returns a Tuple consisting of:
        - QuerySet with pending invites the user has received, or None
        - QuerySet with pending invites the user has sent, or None
        """
        invites_in = Invitacion.objects.filter(
            invitado=self, estado="pendiente")
        invites_out = Invitacion.objects.filter(
            invitado_por__user=self, estado="pendiente")
        return invites_in, invites_out

    def pagar(self, gasto):
        """
        Sets the state of the given Gasto as "pagado", and it's usuario field
        as the User's active ViviendaUsuario.
        If the user has no active Vivienda, returns None and does nothing.
        """
        if self.has_vivienda():
            self.get_vu().pagar(gasto)

    def sent_invite(self, invite):
        """
        Returns True if the given Invite was sent by the User, or False
        otherwise.
        """
        return invite.invitado_por.user == self


class Vivienda(models.Model):
    alias = models.CharField(max_length=200)

    def get_gastos_pendientes(self):
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_pending_estadoGasto())

    def get_gastos_pagados(self):
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_done_estadoGato())

    def get_gastos(self):
        return self.get_gastos_pendientes(), self.get_gastos_pagados()

    def __str__(self):
        return self.alias


class ViviendaUsuario(models.Model):

    class Meta:
        unique_together = (('vivienda', 'user', 'estado', 'fecha_creacion'),)
    vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=200, default="activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_abandono = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self):
        return str(self.vivienda) + "__" + str(self.user)

    def leave(self):
        self.estado = "inactivo"
        self.fecha_abandono = timezone.now()
        self.save()

    def is_active(self):
        return self.estado == "activo"

    def get_gastos_vivienda(self):
        if self.is_active():
            return self.vivienda.get_gastos()
        else:
            # returns empty queryset
            empty_queryset = Gasto.objects.none()
            return (empty_queryset, empty_queryset)

    def pagar(self, gasto):
        gasto.usuario = self
        gasto.fecha_pago = timezone.now()
        gasto.year_month = get_current_yearMonth_obj()
        estado_gasto, created = EstadoGasto.objects.get_or_create(
            estado="pagado")
        gasto.estado = estado_gasto
        gasto.save()

    def sent_invite(self, invite):
        return invite.invitado_por.user == self.user


class Invitacion(models.Model):
    # this key can be null if you invite an account-less user. In this case
    # the invitation is sent to the email.
    invitado = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
    email = models.EmailField()
    estado = models.CharField(max_length=200, default="pendiente")
    # estado es pendiente, rechazada o aceptada

    def __str__(self):
        return str(self.invitado_por) + "__invited__" + str(self.invitado)

    def accept(self):
        self.estado = "aceptada"
        self.save()
        ViviendaUsuario.objects.create(
            user=self.invitado, vivienda=self.invitado_por.vivienda)

    def reject(self):
        self.estado = "rechazada"
        self.save()

    def is_cancelled(self):
        return self.estado == "cancelada"

    def cancel(self):
        self.estado = "cancelada"
        self.save()
    # return True if the given user is the one that's being invited

    def is_invited_user(self, user):
        return self.invitado == user
    # returns True if the given user is the one who sent the invitation

    def is_invited_by_user(self, user):
        return user.sent_invite(self)


class SolicitudAbandonarVivienda(models.Model):
    creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=100)

    def __str__(self):
        return str(self.creada_por) + "__" + str(self.fecha)


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, primary_key=True)

    def __str__(self):
        return self.nombre


class Item(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    unidad_medida = models.CharField(max_length=255, default="unidad")

    def __str__(self):
        return str(self.nombre) + " (" + str(self.unidad_medida) + ")"

    def is_in_lista(self, lista):
        return ItemLista.objects.filter(item=self, lista=lista).exists()


class YearMonth(models.Model):

    class Meta:
        unique_together = (('year', 'month'),)
    year = models.IntegerField()
    month = models.IntegerField()

    # returns a tuple with the next year-month period
    def get_next_period(self):
        next_month = (self.month + 1) % 12
        next_year = self.year
        if next_month < self.month:
            next_year += 1
        return (next_year, next_month)

    # returns a tuple with the previous year-month period
    def get_prev_period(self):
        prev_month = self.month - 1
        prev_year = self.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        return (prev_year, prev_month)

    def __str__(self):
        return str(self.year) + "-" + str(self.month)


class Presupuesto(models.Model):

    class Meta:
        unique_together = (('categoria', 'vivienda', 'year_month'),)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
    year_month = models.ForeignKey(
        YearMonth, on_delete=models.CASCADE, default=get_current_yearMonth)
    monto = models.IntegerField(default=0)

    def __str__(self):
        return "".join(
            str(self.vivienda,
                "__",
                str(self.categoria),
                "__",
                str(self.year_month)))


class ListaCompras(models.Model):
    usuario_creacion = models.ForeignKey(
        ViviendaUsuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=255, default="pendiente")

    def __str__(self):
        return "".join(
            (str(self.usuario_creacion),
                "__",
                str(self.fecha),
                "__",
                str(self.estado)))
    # given an item name, returns the Item instance

    def get_item_by_name(self, item_name):
        return Item.objects.filter(nombre=item_name).first()
    # creates an instance of ItemLista with the given Item and quantity, where
    # the list is self

    def add_item(self, item, quantity):
        if item is not None and item.id > 0 and not item.is_in_lista(self):
            new_list_item = ItemLista.objects.create(
                item=item,
                lista=self,
                cantidad_solicitada=quantity)
            return new_list_item
        else:
            return None
    # same as add_item, but receives the item's name instead of ID

    def add_item_by_name(self, item_name, quantity):
        item = self.get_item_by_name(item_name)
        return self.add_item(item, quantity)

    def get_items(self):
        return ItemLista.objects.filter(lista=self)

    def count_items(self):
        this_list_items = self.get_items()
        return len(this_list_items)

    def allow_user(self, usuario):
        vivienda_usuario = usuario.get_vu()
        return (vivienda_usuario is not None and
                self.usuario_creacion.vivienda == vivienda_usuario.vivienda)

    def is_done(self):
        return self.estado == "pagada"

    def set_done_state(self):
        if not self.is_done():
            self.estado = "pagada"
            self.save()
            return True
        return False
    # mark item as bought

    def buy_item(self, item, quantity):
        il = ItemLista.objects.get(id=item)
        return il.buy(quantity)

    def buy_list(self, item_list, monto_total, vivienda_usuario):
        # mark items as bought
        if item_list is None or len(item_list) < 1:
            return None
        for item_id, quantity in item_list:
            self.buy_item(item_id, quantity)
        self.set_done_state()
        # create new Gasto
        nuevo_gasto = Gasto.objects.create(
            monto=monto_total,
            creado_por=vivienda_usuario,
            categoria=Categoria.objects.get_or_create(
                nombre="Supermercado")[0],
            lista_compras=self)
        nuevo_gasto.pagar(vivienda_usuario)
        return nuevo_gasto

    def get_gasto(self):
        gastos = Gasto.objects.filter(lista_compras=self)
        if len(gastos) == 0 or len(gastos) > 1:
            # TODO raise error
            return None
        else:
            return gastos.first()

    def get_missing_items(self):
        return ItemLista.objects.filter(lista=self, estado="pendiente")

    def has_missing_items(self):
        return len(self.get_missing_items()) > 0

    # creates a new Lista using the pending Items form the current Lista
    def rescue_items(self, vivienda_usuario):
        cond1 = self.has_missing_items()
        cond2 = self.count_items() != self.get_missing_items().count()
        if (cond1 and cond2):
            nueva_lista = ListaCompras.objects.create(
                usuario_creacion=vivienda_usuario)
            for item in self.get_missing_items():
                item.lista = nueva_lista
                item.save()
            return nueva_lista

    def discard_items(self):
        for item in self.get_missing_items():
            item.delete()


class ItemLista(models.Model):

    class Meta:
        unique_together = (('item', 'lista'),)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    lista = models.ForeignKey(ListaCompras, on_delete=models.CASCADE)
    cantidad_solicitada = models.IntegerField()
    cantidad_comprada = models.IntegerField(null=True, blank=True, default=0)
    estado = models.CharField(max_length=255, default="pendiente")

    def __str__(self):
        return "".join((str(self.item),
                        "__",
                        str(self.estado),
                        "__",
                        str(self.lista)))

    def set_done_state(self):
        self.estado = "comprado"
        self.save()

    def is_pending(self):
        return self.estado == "pendiente"

    def get_state(self):
        return self.estado

    def buy(self, quantity):
        if quantity > 0 and self.is_pending():
            self.cantidad_comprada = quantity
            self.set_done_state()
            self.save()
        return self


class EstadoGasto(models.Model):
    estado = models.CharField(max_length=255)

    def __str__(self):
        return str(self.estado)

    def is_pending(self):
        return self.estado == "pendiente"

    def is_paid(self):
        return self.estado == "pagado"


class Gasto(models.Model):
    monto = models.IntegerField()
    creado_por = models.ForeignKey(
        ViviendaUsuario, on_delete=models.CASCADE, related_name="creado_por")
    usuario = models.ForeignKey(
        ViviendaUsuario, on_delete=models.CASCADE, null=True, blank=True)
    # TODO categoria should default to "Supermercado"
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    year_month = models.ForeignKey(YearMonth,
                                   on_delete=models.CASCADE,
                                   null=True,
                                   blank=True)
    lista_compras = models.ForeignKey(
        ListaCompras, on_delete=models.CASCADE, blank=True, null=True)
    estado = models.ForeignKey(
        EstadoGasto,
        on_delete=models.CASCADE,
        default=get_default_estadoGasto,
        blank=True)

    def __str__(self):
        return "".join((str(self.usuario),
                        "__",
                        str(self.categoria),
                        "__",
                        str(self.year_month)))
    # receives a User or a ViviendaUsuario instance, and makes use of double
    # dispatch to pay it

    def pagar(self, user):
        user.pagar(self)

    def is_pending(self):
        return self.estado.is_pending()

    def is_paid(self):
        return self.estado.is_paid()

    def allow_user(self, user):
        # check that user is active in the vivienda
        return (user.has_vivienda() and
                user.get_vivienda() == self.creado_por.vivienda)
