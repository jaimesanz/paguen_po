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
    Returns the "id" field of an instance of EstadoGasto with value
    "pendiente". If it doesn't exist, it creates it first.
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
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a pending state
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_pending_estadoGasto())

    def get_gastos_pagados(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a paid state.
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_done_estadoGato())

    def get_gastos(self):
        """
        Returns a Tuple with:
        - QuerySet with the Gastos associated with the Vivienda,
        and with a pending state
        - QuerySet with the Gastos associated with the Vivienda,
        and with a paid state
        """
        return self.get_gastos_pendientes(), self.get_gastos_pagados()

    def get_categorias(self):
        """
        Returns a QuerySet with all Categoria objects related to the Vivienda.
        For now it just returns all existant Categoria objects, because
        they are (as of the time when this was written) global.
        """
        return Categoria.objects.all()

    def get_total_expenses_categoria_period(self, categoria, year_month):
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            categoria=categoria,
            estado__estado="pagado").values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_total_expenses_period(self, year_month):
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            estado__estado="pagado").values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_total_expenses_per_active_user(self):
        """
        Returns a dictionary where the keys are the names of the users
        and the values are the total expenses of said user
        """
        active_users = ViviendaUsuario.objects.filter(
            vivienda=self,
            estado="activo")
        user_expenses = {}
        for u in active_users:
            user_expenses[u.user]=0
        gastos_pagados = self.get_gastos_pagados()
        for gasto in gastos_pagados:
            user_that_paid = gasto.usuario.user
            user_expenses[user_that_paid]+= gasto.monto
        return user_expenses

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
        """
        Changes the state of the ViviendaUsuario to "inactivo", and sets the
        "fecha_abandono" as the current datetime.
        """
        if self.is_active():
            self.estado = "inactivo"
            self.fecha_abandono = timezone.now()
            self.save()

    def is_active(self):
        """
        Returns True if the ViviendaUsuario's state is active, or
        False otherwise
        """
        return self.estado == "activo"

    def get_gastos_vivienda(self):
        """
        If the user is active, returns a Tuple with:
        - QuerySet with the Gastos associated with the Vivienda,
        and with a pending state
        - QuerySet with the Gastos associated with the Vivienda,
        and with a paid state

        If the user is not active, returns a Tuple of empty QuerySets
        """
        if self.is_active():
            return self.vivienda.get_gastos()
        else:
            # returns empty queryset
            empty_queryset = Gasto.objects.none()
            return (empty_queryset, empty_queryset)

    def pagar(self, gasto):
        """
        Sets the state of the given Gasto as "pagado", and it's usuario field
        as the ViviendaUsuario.
        """
        gasto.usuario = self
        gasto.fecha_pago = timezone.now()
        gasto.year_month = get_current_yearMonth_obj()
        estado_gasto, created = EstadoGasto.objects.get_or_create(
            estado="pagado")
        gasto.estado = estado_gasto
        gasto.save()

    def sent_invite(self, invite):
        """
        Returns True if the given Invite was sent by the ViviendaUsuario's
        User, or False otherwise.
        """
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
        """
        Changes the state of the Invitacion to "aceptada" and creates an
        instance of ViviendaUsuario using the Vivienda of the "invitado_por"
        field, and the "invitado" field as the User
        """
        self.estado = "aceptada"
        self.save()
        ViviendaUsuario.objects.create(
            user=self.invitado, vivienda=self.invitado_por.vivienda)

    def reject(self):
        """
        Changes the state of the Invitacion to "rechazada"
        """
        self.estado = "rechazada"
        self.save()

    def is_cancelled(self):
        """
        Returns True if the state of the Invitacion is "cancelada", or
        False otherwise
        """
        return self.estado == "cancelada"

    def cancel(self):
        """
        Changes the state of the Invitacion to "cancelada"
        """
        self.estado = "cancelada"
        self.save()

    def is_invited_user(self, user):
        """
        Returns True if the given User is the one that's being invited
        """
        return self.invitado == user

    def is_invited_by_user(self, user):
        """
        Returns True if the given user is the one who sent the Invitacion
        """
        return user.sent_invite(self)


class SolicitudAbandonarVivienda(models.Model):
    creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=100)

    def __str__(self):
        return str(self.creada_por) + "__" + str(self.fecha)


class Categoria(models.Model):

    class Meta:
        ordering = ['nombre']
    nombre = models.CharField(max_length=100, primary_key=True)
    vivienda = models.ForeignKey(
        Vivienda,
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Item(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    unidad_medida = models.CharField(max_length=255, default="unidad")

    def __str__(self):
        return str(self.nombre) + " (" + str(self.unidad_medida) + ")"

    def is_in_lista(self, lista):
        """
        Returns True if the Item is in the given ListaCompras, or
        False otherwise
        """
        return ItemLista.objects.filter(item=self, lista=lista).exists()


class YearMonth(models.Model):

    class Meta:
        unique_together = (('year', 'month'),)
    year = models.IntegerField()
    month = models.IntegerField()

    def get_next_period(self):
        """
        Returns a Tuple of Integers with:
        - the year of the period following this YearMonth
        - the month of the period following this YearMonth
        """
        next_month = self.month + 1
        next_year = self.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        return (next_year, next_month)

    def get_prev_period(self):
        """
        Returns a Tuple of Integers with:
        - the year of the period previous to this YearMonth
        - the month of the period previous to this YearMonth
        """
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
        return "".join((
            str(self.vivienda),
            "__",
            str(self.categoria),
            "__",
            str(self.year_month)))

    def get_total_expenses(self):
        """
        Returns the sum of all paid Gastos of the Presupuesto's Categoria in
        the Presupuesto's YearMonth for the Presupuesto's Vivienda
        """
        return self.vivienda.get_total_expenses_categoria_period(
            self.categoria,
            self.year_month)


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

    def get_item_by_name(self, item_name):
        """
        Given an item name, returns the Item instance
        """
        return Item.objects.filter(nombre=item_name).first()

    def add_item(self, item, quantity):
        """
        Creates and returns an instance of ItemLista with the given Item and
        quantity, and links it to the ListaCompras.
        If the Item is already in the ListaCompras, it doesn't do anything,
        and returns None.
        """
        if item is not None and item.id > 0 and not item.is_in_lista(self):
            new_list_item = ItemLista.objects.create(
                item=item,
                lista=self,
                cantidad_solicitada=quantity)
            return new_list_item
        else:
            return None

    def add_item_by_name(self, item_name, quantity):
        """
        Same as add_item, but receives the Item's name instead of it's id
        """
        item = self.get_item_by_name(item_name)
        return self.add_item(item, quantity)

    def get_items(self):
        """
        Returns a QuerySet with all ItemLista objects linked to this
        ListaCompras.
        """
        return ItemLista.objects.filter(lista=self)

    def count_items(self):
        """
        Returns the number of ItemLista objects linked to this ListaCompras.
        """
        this_list_items = self.get_items()
        return len(this_list_items)

    def allow_user(self, usuario):
        """
        Returns True if the user is active in the Vivienda of the
        Viviendausuario that created the ListaCompras. Otherwise, it returns
        False.
        """
        vivienda_usuario = usuario.get_vu()
        return (vivienda_usuario is not None and
                self.usuario_creacion.vivienda == vivienda_usuario.vivienda)

    def is_done(self):
        """
        Returns True if the state is "pagada", or False otherwise.
        """
        return self.estado == "pagada"

    def set_done_state(self):
        """
        If the state is not "pagada", it changes the state to "pagada" and
        returns True. If the state is already "pagada", doesn't do anything
        and returns False.
        """
        if not self.is_done():
            self.estado = "pagada"
            self.save()
            return True
        return False

    def buy_item(self, item, quantity):
        """
        Changes the state of the ItemLista linked to the given Item and the
        current ListaCompras to "comprado", and sets it's "cantidad_comprada"
        field to the given quantity
        """
        il = ItemLista.objects.get(id=item)
        return il.buy(quantity)

    def buy_list(self, item_list, monto_total, vivienda_usuario):
        """
        Receives a list of tuples (item_id, quantity), and changes
        the state of the ItemLista linked to each item_id to "comprado", and
        sets the "cantidad comprada" field to thr given quantity.
        Then, changes the state of the ListaCompras to "pagada", and creates
        a new Gasto object linked to this ListaCompras.
        It sets the usuario field of the Gasto with the given
        vivienda_usuario. The Categoria of the Gasto is set to
        "Supermercado".
        Returns the newly created Gasto object.
        """
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
        """
        Returns the Gasto object linked to the ListaCompras.
        If there's no Gasto linked to it, returns None.
        """
        gastos = Gasto.objects.filter(lista_compras=self)
        if len(gastos) == 0 or len(gastos) > 1:
            # TODO raise error
            return None
        else:
            return gastos.first()

    def get_missing_items(self):
        """
        Returns a QuerySet with all ItemLista objects linked to the
        ListaCompras that have a pending state
        """
        return ItemLista.objects.filter(lista=self, estado="pendiente")

    def has_missing_items(self):
        """
        Returns True if there's at least 1 ItemLista object with a
        pending state linked to the ListaCompras.
        """
        return len(self.get_missing_items()) > 0

    def rescue_items(self, vivienda_usuario):
        """
        Creates and returns a new ListaComrpas using the pending Items
        form the current ListaCompras. If there are no pending Itemista
        objects, it returns None
        """
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
        """
        Deletes all ItemLista with a pending stateobjects linked
        to the ListaCompras
        """
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
        """
        Changes the state to "comprado"
        """
        self.estado = "comprado"
        self.save()

    def is_pending(self):
        """
        Returns True if the state is "pendiente"
        """
        return self.estado == "pendiente"

    def get_state(self):
        """
        Returns the state
        """
        return self.estado

    def buy(self, quantity):
        """
        Changes the state to "comprado" and sets the cantidad_comprada
        to the given quantity
        """
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
        """
        Returns True is the state is "pendiente"
        """
        return self.estado == "pendiente"

    def is_paid(self):
        """
        Returns True is the state is "pagado"
        """
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

    def pagar(self, user):
        """
        It receives a User or a ViviendaUsuario object and changes the
        state of the Gasto to "pagado" by the given User/ViviendaUsuario.
        """
        user.pagar(self)

    def is_pending(self):
        """
        Returns True if the state is "pendiente"
        """
        return self.estado.is_pending()

    def is_paid(self):
        """
        Returns True if the state is "pagado"
        """
        return self.estado.is_paid()

    def allow_user(self, user):
        """
        Returns True if the User is active in the Vivienda linked
        to the Gasto
        """
        return (user.has_vivienda() and
                user.get_vivienda() == self.creado_por.vivienda)
