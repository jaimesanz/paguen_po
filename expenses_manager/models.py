# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
import datetime

# proxy user. This is used to add methods to the User class without altering the default django
class ProxyUser(User):
	class Meta:
		proxy = True

	# returns the user's current active vivienda, or None
	def get_vu(self):
		return ViviendaUsuario.objects.filter(user=self, estado="activo").first()

	# returns a boolean value indicating if the user has an active vivienda
	def has_vivienda(self):
		return self.get_vu() is not None

	# returns the vivienda of the user, or None
	def get_vivienda(self):
		vivienda_usuario = self.get_vu()
		if vivienda_usuario is not None:
			return vivienda_usuario.vivienda
		else:
			return None

	# return a list of all active members of the Vivienda, including the User that calls the method
	# if there's no active vivienda, returns None
	def get_roommates(self):
		if self.has_vivienda():
			return ViviendaUsuario.objects.filter(vivienda=self.get_vivienda(), estado="activo")
		else:
			return None

	# returns pending invites related to the user (received and sent invites)
	def get_invites(self):
		invites_in = Invitacion.objects.filter(invitado=self, estado="pendiente")
		invites_out = Invitacion.objects.filter(invitado_por__user=self, estado="pendiente")
		return invites_in,invites_out

class Vivienda(models.Model):
	alias = models.CharField(max_length=200)

	def get_gastos(self):
		gastos = Gasto.objects.filter(creado_por__vivienda=self)
		gastos_pendientes_list = []
		gastos_pagados_list = []
		for g in gastos:
			if g.is_pending():
				gastos_pendientes_list.append(g)
			elif g.is_paid():
				gastos_pagados_list.append(g)
		return gastos_pendientes_list, gastos_pagados_list
	def __unicode__(self):
		return self.alias

class ViviendaUsuario(models.Model):
	class Meta:
		unique_together = (('vivienda', 'user', 'estado', 'fecha_creacion'),)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	estado = models.CharField(max_length=200, default="activo")
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	def leave(self):
		self.estado = "inactivo"
		self.save()
	def is_active(self):
		return self.estado == "activo"
	def get_gastos_vivienda(self):
		if self.is_active():
			return self.vivienda.get_gastos()
		else:
			return None
	def __unicode__(self):
		return str(self.vivienda) + "__" + str(self.user)

class Invitacion(models.Model):
	# this key can be null if you invite an account-less user. In this case the invitation is sent to the email.
	invitado = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	email = models.EmailField()
	estado = models.CharField(max_length=200, default="pendiente")
	# estado es pendiente, rechazada o aceptada
	def __unicode__(self):
		return str(self.invitado_por) + "__invited__" + str(self.invitado)
	def accept(self):
		self.estado = "aceptada"
		self.save()
		return ViviendaUsuario(user=self.invitado, vivienda=self.invitado_por.vivienda)
	def reject(self):
		self.estado = "rechazada"
		self.save()
	def cancel(self):
		self.estado = "cancelada"
		self.save()

	# return True if the given user is the one that's beign invited
	def is_invited_user(self, user):
		return self.invitado == user
	# returns True if the given user is the one sendnf the invitation
	def is_invited_by_user(self, user):
		return self.invitado_por.user == user

class SolicitudAbandonarVivienda(models.Model):
	creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateTimeField(auto_now_add=True)
	estado = models.CharField(max_length=100)
	def __unicode__(self):
		return str(self.creada_por) + "__" + str(self.fecha)

class Categoria(models.Model):
	nombre = models.CharField(max_length=100, primary_key=True)
	def __unicode__(self):
		return self.nombre

class Item(models.Model):
	nombre = models.CharField(max_length=255)
	descripcion = models.CharField(max_length=255, blank=True, null=True)
	unidad_medida = models.CharField(max_length=255, default="unidad")
	def __unicode__(self):
		return str(self.nombre) + " (" + str(self.unidad_medida) + ")"

class YearMonth(models.Model):
	class Meta:
		unique_together = (('year', 'month'),)

	year = models.IntegerField()
	month = models.IntegerField()
	def __unicode__(self):
		return str(self.year) + "__" + str(self.month)

class Presupuesto(models.Model):
	class Meta:
		unique_together = (('categoria', 'vivienda', 'year_month'),)

	categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	year_month = models.ForeignKey(YearMonth, on_delete=models.CASCADE)
	def __unicode__(self):
		return "".join((str(self.vivienda), "__", str(self.categoria), "__", str(self.year_month)))

class ListaCompras(models.Model):
	usuario_creacion = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateTimeField(auto_now_add=True)
	estado = models.CharField(max_length=255, default="pendiente")
	# creates an instance of ItemLista with the given Item and quantity, where the list is self
	def add_item(self,item_id, quantity):
		if item_id>0 and item_id is not None:
			new_list_item = ItemLista(
				item=Item.objects.get(id=item_id), 
				lista=self, 
				cantidad_solicitada=quantity)
			new_list_item.save()
			return new_list_item
		else:
			print "nope"
			return None
	# same as add_item, but receives the item's name instead of ID
	def add_item_by_name(self,item_name, quantity):
		item_id = Item.objects.get(nombre=item_name).id
		self.add_item(item_id,quantity)
	def count_items(self):
		this_list_items = ItemLista.objects.filter(lista=self)
		return len(this_list_items)
	def allow_user(self, vivienda_usuario):
		return (vivienda_usuario is not None) and self.usuario_creacion.vivienda == vivienda_usuario.vivienda
	def __unicode__(self):
		return "".join((str(self.usuario_creacion), "__", str(self.fecha), "__", str(self.estado)))

class ItemLista(models.Model):
	class Meta:
		unique_together = (('item', 'lista'),)

	item = models.ForeignKey(Item, on_delete=models.CASCADE)
	lista = models.ForeignKey(ListaCompras, on_delete=models.CASCADE)
	cantidad_solicitada = models.IntegerField()
	cantidad_comprada = models.IntegerField(null=True, blank=True)
	estado = models.CharField(max_length=255, default="pendiente")
	def __unicode__(self):
		return str(self.item) + "__" + str(self.lista)

class EstadoGasto(models.Model):
	estado = models.CharField(max_length=255)
	def is_pending(self):
		return self.estado == "pendiente"
	def is_paid(self):
		return self.estado == "pagado"
	def __unicode__(self):
		return str(self.estado)

def get_current_yearMonth():
	today = datetime.datetime.now()
	year_month, creted = YearMonth.objects.get_or_create(year=today.year, month=today.month)
	return year_month

def get_default_estadoGasto():
	estado_gasto, created = EstadoGasto.objects.get_or_create(estado="pendiente")
	return estado_gasto.id

class Gasto(models.Model):
	monto = models.IntegerField()
	creado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE, related_name="creado_por")
	usuario = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE, null=True, blank=True)
	categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	fecha_pago = models.DateTimeField(null=True, blank=True)
	year_month = models.ForeignKey(YearMonth,
		on_delete=models.CASCADE,
		null=True,
		blank=True)
	lista_compras = models.ForeignKey(ListaCompras, on_delete=models.CASCADE, blank=True, null=True)
	estado = models.ForeignKey(EstadoGasto, on_delete=models.CASCADE, default=get_default_estadoGasto, blank=True)

	def pagar(self,user):
		self.usuario = user.get_vu()
		self.fecha_pago = datetime.datetime.now()
		self.year_month = get_current_yearMonth()
		estado_gasto, created = EstadoGasto.objects.get_or_create(estado="pagado")
		self.estado = estado_gasto
		self.save()

	def is_pending(self):
		return self.estado.is_pending()
	def is_paid(self):
		return self.estado.is_paid()
	def allow_user(self, user):
		# check that user is active in the vivienda
		return  user.has_vivienda() and user.get_vivienda() == self.creado_por.vivienda
	def __unicode__(self):
		return "".join((str(self.usuario), "__", str(self.categoria), "__", str(self.year_month)))