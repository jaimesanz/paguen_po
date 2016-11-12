from django.db import models

# Create your models here.
class UserIsOut(models.Model):

    vivienda_usuario = models.ForeignKey(
        "households.ViviendaUsuario",
        on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()