from django.contrib import admin
from .models import Cita, HorarioAtencion

admin.site.register(Cita)


@admin.register(HorarioAtencion)
class HorarioAtencionAdmin(admin.ModelAdmin):
    list_display = ('dia_semana', 'hora_apertura', 'hora_cierre')
