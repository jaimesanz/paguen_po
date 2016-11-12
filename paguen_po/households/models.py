# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models

from django.db.models import Q
from django.utils import timezone

from expenses.models import get_paid_state_gasto, get_pending_state_gasto, \
    get_pending_confirmation_state_gasto, EstadoGasto, Gasto, ConfirmacionGasto
from groceries.models import Item, ListaCompras
from periods.models import YearMonth
from vacations.models import UserIsOut
from categories.models import get_default_others_categoria, Categoria
from expenses_manager.utils import compute_balance


class Vivienda(models.Model):

    alias = models.CharField(max_length=200)

    def add_global_items(self):
        """
        For each global Item (an Item with no related Vivienda),
        creates an Item instance with that Items fields,
        but with a foreign key to this Vivienda.
        If the global item already exists, it doesn't create it again.
        """
        global_items = Item.objects.filter(vivienda=None)
        for item in global_items:
            Item.objects.get_or_create(
                nombre=item.nombre,
                unidad_medida=item.unidad_medida,
                descripcion=item.descripcion,
                vivienda=self)

    def get_active_users(self):
        """
        Returns all currently active ViviendaUsuario instances in the Vivienda
        :return: QuerySet( ViviendaUsuario )
        """
        return ViviendaUsuario.objects.filter(
            vivienda=self,
            estado="activo"
        )

    def get_gastos_pendientes(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a pending state
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_pending_state_gasto(),
            categoria__is_transfer=False)

    def get_pending_confirmation_gastos(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a pending_confirmation state
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_pending_confirmation_state_gasto())

    def get_gastos_pagados(self):
        """
        Returns a QuerySet with the Gastos associated with the Vivienda,
        and with a paid state.
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            creado_por__vivienda=self,
            estado=get_paid_state_gasto(),
            categoria__is_transfer=False)

    def get_categorias(self):
        """
        Returns a QuerySet with all Categoria objects related to the Vivienda
        that are not hidden
        :return: QuerySet( Categoria )
        """
        return Categoria.objects.filter(
            vivienda=self,
            hidden=False,
            is_transfer=False)

    def get_items(self):
        """
        Returns a QuerySet with all Items related to this Vivienda
        :return: QuerySet( Item )
        """
        return self.item_set.order_by('nombre')

    def get_all_vivienda_categorias_with_is_hidden_field(self):
        """
        Returns a QuerySet with all Categoria objects related to the Vivienda,
        including the hidden Categoria instances
        :return: QuerySet( Categoria )
        """
        return Categoria.objects.filter(vivienda=self, is_transfer=False)

    def get_hidden_total(self, year_month):
        """
        Returns the sum of all Gastos' montos with a Categoria that's
        hidden
        :param year_month: YearMonth
        :return: Integer
        """
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            categoria__vivienda=self,
            categoria__is_transfer=False,
            categoria__hidden=True,
            estado__estado="pagado").values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_total_expenses_categoria_period(self, categoria, year_month):
        """
        Returns the total sum of all Gastos made during the given YearMonth
        for the given Categoria in this Vivienda. If the Categoria is the
        default "other" Categoria, it takes into account that Categoria, plus
        all hidden Categorias related to the Vivienda.
        :param categoria: Categoria
        :param year_month: YearMonth
        :return: Integer
        """
        categoria = Categoria.objects.get(
            nombre=categoria,
            vivienda=self)
        if categoria.nombre == get_default_others_categoria().nombre:
            # TODO it's not adding the Gastos with "Otros" as categoria,
            # because it's just adding up the Categorias that are hidden,
            # and "Otros" is not always hidden!
            return self.get_hidden_total(year_month)
        if categoria.is_hidden():
            return 0
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
        """
        Returns the sum of all Gastos made during the given YearMonth
        regardless of Categoria
        :param year_month: YearMonth
        :return: Integer
        """
        montos = Gasto.objects.filter(
            creado_por__vivienda=self,
            year_month=year_month,
            estado__estado="pagado",
            categoria__is_transfer=False).values("monto")
        total = 0
        for d in montos:
            total += d["monto"]
        return total

    def get_transferencias(self):
        """
        Returns all Gasto instances that:
        - it's Categoria's is_transfer field is True
        - were created by active users
        :return: QuerySet( Gasto )
        """
        return Gasto.objects.filter(
            categoria__is_transfer=True,
            creado_por__vivienda=self,
            creado_por__estado="activo")

    def add_categoria(self, nombre):
        """
        Takes a String representing the name of a new custom Categoria
        the user wants to create. If there's no Categoria with that name,
        a new one is created using the user's Vivienda and the given String
        as the Categoria's "nombre" field.
        Returns a tuple (Categoria, String):
        - the first element is the newly created Categoria, or None
        if there was any error creating it
        - the String is a message explaining what happened (it
        failed for some reason / it finished successfully)
        :param nombre: String
        :return: Pair( Categoria, String)
        """
        categoria, created = Categoria.objects.get_or_create(
            nombre=nombre,
            vivienda=self)
        if not created and categoria.is_global():
            # it's trying to override a global categoria
            return (None,
                    "El nombre ingresado corresponde a una categoría global")
        if created:
            return (categoria, "¡Categoría agregada!")
        return (None, "La categoría ya esta asociada a su vivienda")

    def get_vivienda_global_categorias(self):
        """
        Returns the global Categorias related to this Vivienda
        :return: QuerySet( Categoria )
        """
        global_cats = Categoria.objects.filter(vivienda=None).values("nombre")
        this_viv_global = Categoria.objects.filter(
            vivienda=self,
            nombre__in=global_cats)
        return this_viv_global

    def get_vivienda_custom_categorias(self):
        """
        Returns the custom Categorias related to this Vivienda
        :return: QuerySet( Categoria )
        """
        global_cats = Categoria.objects.filter(vivienda=None).values("nombre")
        custom_cats = Categoria.objects.filter(
            Q(vivienda=self) & ~Q(nombre__in=global_cats))
        return custom_cats

    def get_pending_list(self):
        """
        Returns the pending list related to the Vivienda, if there  is one
        :return: ListaCompras
        """
        return ListaCompras.objects.filter(
            usuario_creacion__vivienda=self,
            estado="pendiente"
        ).first()

    def has_pending_list(self):
        """
        Returns True if the vivienda has a pending list, or False otherwise
        :return: Boolean
        """
        return ListaCompras.objects.filter(
            usuario_creacion__vivienda=self,
            estado="pendiente"
        ).exists()

    def get_vacations_after_date(self, date):
        """
        Returns all UserIsOut instances that:
        - happened after the given date, ie, the end date comes
        after the given date (read *NOTE*)
        - is related to a vivienda_usuario related to this Vivienda

        *NOTE*: since the "fecha_fin" field always comes after the
        "fecha_inicio" field, it suffices to say that if the "fecha_fin"
        comes after the given date, the vacation should be returned.
        :param date: Date
        :return: QuerySet( UserIsOut )
        """

        # select_related so that database is not hit again when asking for
        # vivienda_usuario's user
        return UserIsOut.objects.filter(
            vivienda_usuario__vivienda=self,
            fecha_fin__gte=date).select_related("vivienda_usuario__user")

    def get_smart_gasto_dict(self, active_users, all_users, vacations):
        """
        Given a set with currently active ViviendaUsuario instances,
        another Set with all ViviendaUsuario instances related to the
        Vivienda and a set of Vacations, this method returns a dict
        of the form:
        {
            Gasto: (
                currently_active_users_that_should_pay_this_Gasto,
                users_active_at_the_time_of_Gasto_that_had_to_pay_it
            )
        }
        The keys are Gasto instances payed by Users that are currently active,
        and the values are tuples of Sets. Note that these Sets:
        - don't necessarily contain the same set of Users
        - are not necessarily of the same length
        - always have at least 1 user in common (the one who payed the Gasto)
        :param active_users: Set( ViviendaUsuario )
        :param all_users: Set( ViviendaUsuario )
        :param vacations: Set( UserIsOut )
        :return: Dict(
            Gasto : Pair( Set(ViviendaUsuario), Set(ViviendaUsuario) )
        )
        """
        # get dict "user" -> [UserIsOut1, UserIsOut2, ...]
        vac_dict = dict()
        for vu in all_users:
            vac_dict[vu] = []
        for vacation in vacations:
            vac_dict[vacation.vivienda_usuario].append(vacation)
        gastos = Gasto.objects.filter(
            creado_por__vivienda=self,
            usuario__estado="activo",
            categoria__is_shared=True,
            estado__estado="pagado")

        gastos_users_dict = dict()

        for gasto in gastos:
            should_have_payed_then = gasto.get_responsible_users(
                all_users,
                vac_dict)
            pay_active_today = set.intersection(
                set(active_users),
                should_have_payed_then)
            gastos_users_dict[gasto] = (
                pay_active_today, should_have_payed_then)

        return gastos_users_dict

    def get_reversed_user_totals_dict(self, gastos_users_dict):
        """
        Converts a dict of the form:
        {
            Gasto: (
                currently_active_users_that_should_pay_this_Gasto,
                users_active_at_the_time_of_Gasto_that_had_to_pay_it
            )
        }
        to 2 dicts: actual_total_per_user and expected_total_per_user.
        Both dicts are of the form:
        {User: Integer}
        The first dict represents how much the User has spent in Gastos that
        are shared with the active users, and the second dict represents how
        much the user should've spent.

        IMPORTANT Explanation:
        Q: why are the actual totals per user LESS than the "naive" approach
        of just adding up every Gasto payed by each currently active user?

        A: Suppose there was a time when users A and B were sharing expenses,
        but user C was not a part of the Vivienda yet. Furthermore, say B
        left a couple of weeks ago, and is no longer a part of the Vivienda.
        Thus, if A spent money when only A and B were roommates, C should not
        PERCEIVE this Gasto.

        If A was awarded that whole Gasto's monto, then this would unbalance
        the total amounts per user, because this would mean C is ALSO
        responsible for a portion of that Gasto.

        C should perceive that A spent that money at that time, but only half
        of it was meant for himself (because it was shared with B).
        Then, user A should be awarded part of that expense: the portion of it
        that was shared with users that are still active TODAY.

        Let's look at another example: suppose there was a time when users A,
        B and C shared the Vivienda, and A made a Gasto for 1000. However,
        today only A, C and D share the Vivienda. This would mean that 2/3 of
        that Gasto's monto should be added to the total of A.
        Why?
        Because A and C (2 users) perceived that Gasto, but it was
        also split with B at the time (3 users), meaning it was split
        into 3 parts. However, only 2 of those 3 users are still active
        => only 2/3 parts of the monto should be added to A.
        The other 1/3 part is assumed to have been balanced with B before
        she/he left.
        :param gastos_users_dict: Dict(
            Gasto : Pair( Set(ViviendaUsuario), Set(ViviendaUsuario) )
        )
        :return: Pair( Dict(User: Integer), Dict(User: Integer) )
        """
        actual_total_per_user = dict()
        expected_total_per_user = dict()
        active_users = ViviendaUsuario.objects.filter(
            vivienda=self,
            estado="activo")
        for vu in active_users:
            actual_total_per_user[vu] = 0
            expected_total_per_user[vu] = 0
        for gasto in gastos_users_dict:
            today_users, past_users = gastos_users_dict[gasto]
            user_that_payed = gasto.usuario
            shared_portion = len(today_users) / len(past_users)
            share = gasto.monto * shared_portion
            actual_total_per_user[user_that_payed] += share
            for vu in today_users:
                expected_total_per_user[vu] += share / len(today_users)

        return actual_total_per_user, expected_total_per_user

    def get_smart_totals(self):
        """
        Returns a tuple with:
        - a dict with the actual totals each active user has spent
        - a dict with the expected totals for each active user
        :return: Pair( Dict(User: Integer), Dict(User: Integer) )
        """
        all_users = ViviendaUsuario.objects.filter(
            vivienda=self)
        active_users = all_users.filter(estado="activo")
        # get the earliest user that is still active in the Vivienda
        dates = set()
        for vu in active_users:
            dates.add(vu.fecha_creacion)
        start_date = min(dates)
        vacations = self.get_vacations_after_date(start_date)
        gasto_user_dict = self.get_smart_gasto_dict(
            active_users=active_users,
            all_users=all_users,
            vacations=vacations)

        return self.get_reversed_user_totals_dict(gasto_user_dict)

    def get_disbalance_dict(self):
        """
        Returns a dict of the form:
        {
            User: Integer
        }
        where the Integer represents how much the User ows to other users
        (Integer is negative, meaning he has spent too little), or how much the
        User is owed (if the Integer is positive, meaning he has spent too
        much)
        :return: Dict(User: Integer)
        """
        act, exp = self.get_smart_totals()
        disbalance_dict = dict()
        for user in act:
            diff = act[user] - exp[user]
            if abs(diff) < 5:
                diff = 0
            disbalance_dict[user] = diff
        return disbalance_dict

    def get_smart_balance(self):
        """
        Computes the instructions for users to balance out their shared
        expenses
        :return: Dict(User: List( Pair( User, Integer ) )
        """
        (actual_totals,
         expected_totals) = self.get_smart_totals()

        return compute_balance(actual_totals, expected_totals)

    def __str__(self):
        return self.alias


class ViviendaUsuario(models.Model):

    class Meta:
        unique_together = (('vivienda', 'user', 'estado', 'fecha_creacion'),)
    vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=200, default="activo")
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_abandono = models.DateField(null=True, blank=True, default=None)

    def __str__(self):
        return str(self.vivienda) + "__" + str(self.user)

    def leave(self):
        """
        Changes the state of the ViviendaUsuario to "inactivo", and sets the
        "fecha_abandono" as the current datetime, and then returns True.
        If this ViviendaUsuario was not active, does nothing and returns False
        :return: Boolean
        """
        if self.is_active():
            self.estado = "inactivo"
            self.fecha_abandono = timezone.now()
            self.save()
            return True
        return False

    def is_active(self):
        """
        Returns True if the ViviendaUsuario's state is active, or
        False otherwise
        :return: Boolean
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
        :return: Pair( QuerySet( Gasto ), QuerySet( Gasto ) )
        """
        if self.is_active():
            return (self.vivienda.get_gastos_pendientes(),
                    self.vivienda.get_gastos_pagados())
        else:
            # returns empty queryset
            empty_queryset = Gasto.objects.none()
            return (empty_queryset, empty_queryset)

    def pay(self, gasto, fecha_pago=timezone.now().date()):
        """
        Sets the state of the given Gasto as "pendiente_confirmacion", and it's
        "usuario" field as the ViviendaUsuario. Also creates a
        ConfirmacionUsuario instance per active user in the Vivienda.
        :param gasto: Gasto
        :param fecha_pago: Date
        """
        gasto.usuario = self
        gasto.fecha_pago = fecha_pago
        ym, __ = YearMonth.objects.get_or_create(
            year=fecha_pago.year,
            month=fecha_pago.month)
        gasto.year_month = ym
        gasto.set_pending_confirmation_state()
        gasto.save()
        for vu in self.vivienda.get_active_users():
            ConfirmacionGasto.objects.create(vivienda_usuario=vu, gasto=gasto)
        # the user that pays immediately confirms the payment
        self.confirm(gasto)

    def confirm(self, gasto):
        """
        Finds a ConfirmacionGasto instance realted to the given Gasto and
        this ViviendaUsuario, and changes it's "confirmed" field to True.
        If, after the change, all ConfirmacionGasto instances related to the
        given Gasto are confirmed, changes the state to the
        confirmed_paid_state
        """
        gasto_confirmation = ConfirmacionGasto.objects.filter(
            gasto=gasto, vivienda_usuario=self).first()
        if gasto_confirmation is not None:
            gasto_confirmation.confirmed = True
            gasto_confirmation.save()
            if not ConfirmacionGasto.objects.filter(
                    gasto=gasto,
                    confirmed=False).exists():
                # all users have confirmed
                gasto.set_confirmed_paid_state()

    def confirm_pay(self, gasto, fecha_pago=timezone.now().date()):
        """
        Sets the state of the given Gasto as "pagado", and it's "usuario" field
        as the ViviendaUsuario.

        This method is used for TESTING purposes, because it skips the
        confirmation phase of paying a Gasto. However, this should never
        happen in the actual application.

        :param gasto: Gasto
        :param fecha_pago: Date
        """
        gasto.usuario = self
        gasto.fecha_pago = fecha_pago
        ym, __ = YearMonth.objects.get_or_create(
            year=fecha_pago.year,
            month=fecha_pago.month)
        gasto.year_month = ym
        estado_gasto, created = EstadoGasto.objects.get_or_create(
            estado="pagado")
        gasto.estado = estado_gasto
        gasto.save()

    def sent_invite(self, invite):
        """
        Returns True if the given Invite was sent by the ViviendaUsuario's
        User, or False otherwise.
        :param invite: Invitacion
        :return: Boolean
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
        :return: Boolean
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
        :param user: User
        :return: Boolean
        """
        return self.invitado == user

    def is_invited_by_user(self, user):
        """
        Returns True if the given user is the one who sent the Invitacion
        :param user: User
        :return: Boolean
        """
        return user.sent_invite(self)