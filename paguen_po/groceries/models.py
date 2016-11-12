from django.db import models

# Create your models here.
from categories.models import Categoria
from expenses_manager.models import Gasto


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