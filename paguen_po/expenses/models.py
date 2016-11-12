# -*- coding: utf-8 -*-
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile
from django.db import models

# Create your models here.
from django.utils import timezone

from core.utils import rm_not_active_at_date, rm_users_out_at_date
from periods.models import YearMonth


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
    categoria = models.ForeignKey(
        "categories.Categoria", on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_pago = models.DateField(null=True, blank=True)
    year_month = models.ForeignKey(
        "periods.YearMonth",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    lista_compras = models.ForeignKey(
        "groceries.ListaCompras", on_delete=models.CASCADE, blank=True, null=True)
    estado = models.ForeignKey(
        EstadoGasto,
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
    gasto = models.ForeignKey(Gasto, on_delete=models.CASCADE)
