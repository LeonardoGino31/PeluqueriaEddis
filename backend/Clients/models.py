from django.db import models
import re
from django.core.exceptions import ValidationError

# Create your models here.
class Cliente(models.Model):
    nombre=models.CharField(max_length=100)
    telefono=models.CharField(max_length=15, unique=True)
    correo = models.EmailField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    @staticmethod
    def normalizar_telefono(telefono):
        digitos = re.sub(r'\D', '', telefono or '') 

        if digitos.startswith('5939') and len(digitos) == 12:
            return digitos

        if digitos.startswith('09') and len(digitos) == 10:
            return '593' + digitos[1:]

        if digitos.startswith('9') and len(digitos) == 9:
            return '593' + digitos

        raise ValidationError("Número de teléfono inválido. Debe ser un número válido de Ecuador.")

    @classmethod
    def obtener_o_crear_por_telefono(cls, telefono, nombre=''):
        telefono = cls.normalizar_telefono(telefono)
        cliente, creado = cls.objects.get_or_create(telefono=telefono, defaults={'nombre': nombre})
        return cliente, creado

    def clean(self):
        try:
            self.telefono = self.normalizar_telefono(self.telefono)
        except ValidationError as e:
            raise ValidationError({'telefono': e.message})


    def save(self, *args, **kwargs):
        self.telefono = self.normalizar_telefono(self.telefono)
        super().save(*args, **kwargs)
          
