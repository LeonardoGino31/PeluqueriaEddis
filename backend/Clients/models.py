from django.db import models

# Create your models here.
class Cliente(models.Model):
    nombre=models.CharField(max_length=100)
    telefono=models.CharField(max_length=12, unique=True)
    correo = models.EmailField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre