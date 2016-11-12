# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import BytesIO

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

from categories.models import Categoria
from periods.models import get_current_year_month, YearMonth
from .utils import rm_not_active_at_date, rm_users_out_at_date


def get_default_estado_gasto():
    """
    Returns the "id" field of an instance of EstadoGasto with value
    "pendiente". If it doesn't exist, it creates it first.
    :return: Integer
    """
    estado_gasto, __ = EstadoGasto.objects.get_or_create(
        estado="pendiente")
    return estado_gasto.id


def get_paid_state_gasto():
    """
    Returns an instance of EstadoGasto with value "pagado".
    If it doesn't exist, it creates it first.
    :return: EstadoGasto
    """
    return EstadoGasto.objects.get_or_create(estado="pagado")[0]


def get_pending_state_gasto():
    """
    Returns an instance of EstadoGasto with value "pendiente".
    If it doesn't exist, it creates it first.
    :return: EstadoGasto
    """
    return EstadoGasto.objects.get_or_create(estado="pendiente")[0]


def get_pending_confirmation_state_gasto():
    """
    Returns an instance of EstadoGasto with value "pendiente_confirmacion".
    If it doesn't exist, it creates it first.
    :return: EstadoGasto
    """
    return EstadoGasto.objects.get_or_create(
        estado="pendiente_confirmacion")[0]


def vivienda_gasto_directory_path(instance, filename):
    """
    file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    source: https://docs.djangoproject.com/ja/1.9/ref/models/fields/#django
    .db.models.FileField
    :param instance: Gasto
    :param filename: String
    :return: Path String
    """
    return 'gastos/vivienda_{0}/usuario_{1}/{2}'.format(
        instance.creado_por.vivienda.id,
        instance.creado_por.id,
        filename
    )


class Item(models.Model):

    class Meta:
        unique_together = ('nombre', 'vivienda')

    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="")
    unidad_medida = models.CharField(max_length=255, default="unidad")
    vivienda = models.ForeignKey(
        "households.Vivienda",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None)

    def __str__(self):
        return str(self.nombre) + " (" + str(self.unidad_medida) + ")"

    def is_in_lista(self, lista):
        """
        Returns True if the Item is in the given ListaCompras, or
        False otherwise
        :param lista: ListaCompras
        :return: Boolean
        """
        return ItemLista.objects.filter(item=self, lista=lista).exists()


class Presupuesto(models.Model):

    class Meta:
        unique_together = (('categoria', 'vivienda', 'year_month'),)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    vivienda = models.ForeignKey("households.Vivienda", on_delete=models.CASCADE)
    year_month = models.ForeignKey("periods.YearMonth", on_delete=models.CASCADE, default=get_current_year_month)
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
        :return: Integer
        """
        return self.vivienda.get_total_expenses_categoria_period(
            self.categoria,
            self.year_month)


class ListaCompras(models.Model):
    usuario_creacion = models.ForeignKey(
        "households.ViviendaUsuario", on_delete=models.CASCADE)
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
        Given an item name, returns the Item instance with that name that is
        related to this Lista's Vivienda
        :param item_name: String
        :return: Item
        """
        return Item.objects.filter(
            nombre=item_name,
            vivienda=self.usuario_creacion.vivienda).first()

    def add_item(self, item, quantity):
        """
        Creates and returns an instance of ItemLista with the given Item and
        quantity, and links it to the ListaCompras.
        If the Item is already in the ListaCompras, it doesn't do anything,
        and returns None.
        :param item: Item
        :param quantity: Integer
        :return: ItemLista
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
        :param item_name: String
        :param quantity: Integer
        :return: ItemLista
        """
        item = self.get_item_by_name(item_name)
        return self.add_item(item, quantity)

    def get_items(self):
        """
        Returns a QuerySet with all ItemLista objects linked to this
        ListaCompras.
        :return: QuerySet( ItemLista )
        """
        return ItemLista.objects.filter(lista=self)

    def count_items(self):
        """
        Returns the number of ItemLista objects linked to this ListaCompras.
        :return: Integer
        """
        this_list_items = self.get_items()
        return len(this_list_items)

    def allow_user(self, usuario):
        """
        Returns True if the user is active in the Vivienda of the
        Viviendausuario that created the ListaCompras. Otherwise, it returns
        False.
        :param usuario: User
        :return: Boolean
        """
        vivienda_usuario = usuario.get_vu()
        return (vivienda_usuario is not None and
                self.usuario_creacion.vivienda == vivienda_usuario.vivienda)

    def is_done(self):
        """
        Returns True if the state is "pagada".
        :return: Boolean
        """
        return self.estado == "pagada"

    def set_done_state(self):
        """
        If the state is not "pagada", it changes the state to "pagada" and
        returns True. If the state is already "pagada", doesn't do anything
        and returns False.
        :return: Boolean
        """
        if not self.estado == "pagada":
            self.estado = "pagada"
            self.save()
            return True
        return False

    def buy_item(self, item, quantity):
        """
        Changes the state of the ItemLista linked to the given Item and the
        current ListaCompras to "comprado", and sets it's "cantidad_comprada"
        field to the given quantity
        :param item: Item
        :param quantity: Integer
        :return: ItemLista
        """
        il = ItemLista.objects.get(id=item)
        return il.buy(quantity)

    def buy_list(self, item_list, monto_total, vivienda_usuario):
        """
        Receives a list of tuples (item_id, quantity), and changes
        the state of the ItemLista linked to each item_id to "comprado", and
        sets the "cantidad comprada" field to the given quantity.
        Then, changes the state of the ListaCompras to "pagada", and creates
        a new Gasto object linked to this ListaCompras.
        It sets the usuario field of the Gasto with the given
        vivienda_usuario. The Categoria of the Gasto is set to
        "Supermercado".
        Returns the newly created Gasto object.
        :param item_list: List( Pair( Integer, Integer ) )
        :param monto_total: Integer
        :param vivienda_usuario: ViviendaUsuario
        :return: Gasto
        """
        # mark items as bought
        if item_list is None or len(item_list) < 1:
            return None
        try:
            if int(monto_total) <= 0:
                return "monto_negativo"
        except ValueError:
            return "monto_invalido"
        for item_id, quantity in item_list:
            self.buy_item(item_id, quantity)
        self.set_done_state()
        # create new Gasto
        nuevo_gasto = Gasto.objects.create(
            monto=monto_total,
            creado_por=vivienda_usuario,
            categoria=Categoria.objects.get_or_create(
                nombre="Supermercado",
                vivienda=vivienda_usuario.vivienda)[0],
            lista_compras=self)
        nuevo_gasto.pay(vivienda_usuario)
        return nuevo_gasto

    def get_gasto(self):
        """
        Returns the Gasto object linked to the ListaCompras.
        If there's no Gasto linked to it, returns None.
        :return: Gasto
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
        :return: QuerySet( ItemLista )
        """
        return ItemLista.objects.filter(lista=self, estado="pendiente")

    def has_missing_items(self):
        """
        Returns True if there's at least 1 ItemLista object with a
        pending state linked to the ListaCompras.
        :return: Boolean
        """
        return len(self.get_missing_items()) > 0

    def rescue_items(self, vivienda_usuario):
        """
        Creates and returns a new ListaComrpas using the pending Items
        form the current ListaCompras. If there are no pending Itemista
        objects, it returns None
        :param vivienda_usuario: ViviendaUsuario
        :return: ListaCompras
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
        Deletes all ItemLista instances with a pending state linked
        to the ListaCompras
        """
        for item in self.get_missing_items():
            item.delete()


class ItemLista(models.Model):

    class Meta:
        unique_together = (('item', 'lista'),)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    lista = models.ForeignKey("ListaCompras", on_delete=models.CASCADE)
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_comprada = models.PositiveIntegerField(
        null=True, blank=True, default=0)
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
        :return: Boolean
        """
        return self.estado == "pendiente"

    def get_state(self):
        """
        Returns the state
        :return: String
        """
        return self.estado

    def buy(self, quantity):
        """
        Changes the state to "comprado" and sets the cantidad_comprada
        to the given quantity
        :param quantity: Integer
        :return: ItemLista
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
        :return: Boolean
        """
        return self.estado == "pendiente"

    def is_pending_confirm(self):
        """
        Returns True is the state is "pendiente_confirmacion"
        :return: Boolean
        """
        return self.estado == get_pending_confirmation_state_gasto().estado

    def is_paid(self):
        """
        Returns True is the state is "pagado"
        :return: Boolean
        """
        return self.estado == "pagado"


class Gasto(models.Model):
    monto = models.IntegerField()
    creado_por = models.ForeignKey(
        "households.ViviendaUsuario", on_delete=models.CASCADE, related_name="creado_por")
    usuario = models.ForeignKey(
        "households.ViviendaUsuario", on_delete=models.CASCADE, null=True, blank=True)
    categoria = models.ForeignKey("categories.Categoria", on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_pago = models.DateField(null=True, blank=True)
    year_month = models.ForeignKey(
        "periods.YearMonth",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    lista_compras = models.ForeignKey(
        "ListaCompras", on_delete=models.CASCADE, blank=True, null=True)
    estado = models.ForeignKey(
        "EstadoGasto",
        on_delete=models.CASCADE,
        default=get_default_estado_gasto,
        blank=True)

    foto = models.ImageField(
        upload_to=vivienda_gasto_directory_path, blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Override save method to resize image before saving it.
        source: http://stackoverflow.com/a/30435175
        """
        if self.foto:
            resized_image = Image.open(self.foto)
            if resized_image.width > 500 or resized_image.height > 500:
                # this IF is necessary because otherwise the image would be
                # updated (to the same image, no less) each time a user
                # edits, confirms or pays the Gasto.
                size = 500, 500
                resized_image.thumbnail(size, Image.ANTIALIAS)

                resized_image_io = BytesIO()
                resized_image.save(
                    resized_image_io, format=resized_image.format)

                temp_name = self.foto.name
                self.foto.delete(save=False)

                self.foto.save(
                    temp_name,
                    content=ContentFile(resized_image_io.getvalue()),
                    save=False
                )
        super(Gasto, self).save(*args, **kwargs)

    def __str__(self):
        return "".join((str(self.usuario),
                        "__",
                        str(self.categoria),
                        "__",
                        str(self.year_month)))

    def pay(self, vivienda_usuario, fecha_pago=timezone.now().date()):
        """
        It receives a ViviendaUsuario object and changes the state of the
        Gasto to "pendiente_confirmacion" and the "usuario" field to the given
        ViviendaUsuario.
        :param vivienda_usuario: ViviendaUsuario
        :param fecha_pago: Date
        """
        vivienda_usuario.pay(self, fecha_pago)

    def confirm_pay(self, vivienda_usuario, fecha_pago=timezone.now().date()):
        """
        It receives a ViviendaUsuario object and changes the state of the
        Gasto to "pagado" by the given ViviendaUsuario.
        :param vivienda_usuario: ViviendaUsuario
        :param fecha_pago: Date
        """
        vivienda_usuario.confirm_pay(self, fecha_pago)

    def edit(self, vivienda_usuario, new_monto, new_fecha):
        """
        Changes the fields of the Gasto with the given parameters
        :param vivienda_usuario: ViviendaUsuario
        :param new_monto: Integer
        :param new_fecha: Date
        :return: String
        """
        message = "Gasto editado."
        if not self.is_pending():
            if vivienda_usuario != self.usuario:
                return "No tiene permiso para editar este Gasto"
            # it's either confirmed_payed or pending_confirmation, meaning it
            #  has a not-None "usuario" field
            message = "Gasto editado. Se cambió el estado a pendiente."
            self.fecha_pago = new_fecha
            ym, __ = YearMonth.objects.get_or_create(
                year=new_fecha.year,
                month=new_fecha.month)
            self.year_month = ym
            self.set_pending_confirmation_state()
            for cg in self.confirmaciongasto_set.exclude(
                    vivienda_usuario=self.usuario):
                cg.confirmed = False
                cg.save()
        self.monto = new_monto
        self.save()

        return message

    def is_pending(self):
        """
        Returns True if the state is "pendiente"
        :return: Boolean
        """
        return self.estado.is_pending()

    def is_pending_confirm(self):
        """
        Returns True if the state is "pendiente_confirmacion"
        :return: Boolean
        """
        return self.estado.is_pending_confirm()

    def set_pending_confirmation_state(self):
        """
        Changes the state of the Gasto to "pendiente_confirmacion"
        """
        self.estado = get_pending_confirmation_state_gasto()
        self.save()

    def set_confirmed_paid_state(self):
        """
        Changes the state of the Gasto to "pagado"
        """
        self.estado = get_paid_state_gasto()
        self.save()

    def is_paid(self):
        """
        Returns True if the state is "pagado"
        :return: Boolean
        """
        return self.estado.is_paid()

    def allow_user(self, user):
        """
        Returns True if the User is active in the Vivienda linked
        to the Gasto
        :param user: User
        :return: Boolean
        """
        return (user.has_vivienda() and
                user.get_vivienda() == self.creado_por.vivienda)

    def get_responsible_users(self, all_users, vac_dict):
        """
        Returns all users that were supposed to pay for this Gasto.
        :param all_users: Set( ViviendaUsuario )
        :param vac_dict: Dict( ViviendaUsuario -> List( UserIsOut ) )
        :return: Set( ViviendaUsuario )
        """
        pay_date = self.fecha_pago
        # users active at the time that should have payed
        share_holders = rm_not_active_at_date(
            all_users,
            pay_date)
        if not self.categoria.is_shared_on_leave:
            share_holders = rm_users_out_at_date(
                share_holders,
                vac_dict,
                pay_date)
        # make sure the user that payed is always responsible
        share_holders.add(self.usuario)
        return share_holders

    def get_confirmed_users(self):
        """
        Returns all ViviendaUsuarios who have already confirmed this Gasto
        :return: List( Dict( "vivienda_usuario__user__username" -> String ) )
        """
        return self.confirmaciongasto_set.filter(
            confirmed=True).values("vivienda_usuario__user__username")

    def get_unconfirmed_users(self):
        """
        Returns all ViviendaUsuarios who are yet to confirm this Gasto
        :return: List( Dict( "vivienda_usuario__user__username" -> String ) )
        """
        return self.confirmaciongasto_set.filter(
            confirmed=False).values("vivienda_usuario__user__username")


class ConfirmacionGasto(models.Model):

    class Meta:
        unique_together = ('vivienda_usuario', 'gasto')

    vivienda_usuario = models.ForeignKey(
        "households.ViviendaUsuario",
        on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
    gasto = models.ForeignKey("Gasto", on_delete=models.CASCADE)
