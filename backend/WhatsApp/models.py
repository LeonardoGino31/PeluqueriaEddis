from django.db import models
from datetime import timedelta
from django.utils import timezone

from Clients.models import Cliente

class ConversacionWhatsApp(models.Model):
    PASOS = [
        ('INICIO', 'Inicio'),
        ('MENU', 'Menú principal'),
        ('SERVICIOS', 'Elegir servicios'),
        ('ELEGIR_DIA', 'Elegir día'),
        ('ELEGIR_FRANJA', 'Elegir mañana o tarde'),
        ('ELEGIR_HORA', 'Elegir hora'),
        ('ELEGIR_TIPO_PELUQUERO', 'Elegir tipo de peluquero'),
        ('ELEGIR_PELUQUERO', 'Elegir peluquero'),
        ('CONFIRMAR_CITA', 'Confirmar cita'),
        ('ELEGIR_CITA_CANCELAR', 'Elegir cita a cancelar'),
        ('CONFIRMAR_CANCELACION', 'Confirmar cancelación'),
    ]

    MINUTOS_EXPIRACION = 30

    cliente= models.OneToOneField(
        Cliente,
        on_delete=models.CASCADE,
        related_name='conversacion_whatsapp'
    )

    paso = models.CharField(
        max_length=30,
        choices=PASOS,
        default='INICIO'
    )

    datos = models.JSONField(default=dict, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversación de WhatsApp"
        verbose_name_plural = "Conversaciones de WhatsApp" 

    def avanzar(self, paso, **nuevos_datos):
        self.paso = paso
        self.datos.update(nuevos_datos)
        self.save()

    def reiniciar(self):
        self.paso = 'INICIO'
        self.datos = {}
        self.save()

    def ha_expirado(self):
        return timezone.now() > self.actualizado + timedelta(minutes=self.MINUTOS_EXPIRACION)

    def __str__(self):
        return f"Conversación de {self.cliente.nombre} ({self.cliente.telefono}) - Paso: {self.get_paso_display()}"

    