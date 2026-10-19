from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import Cita, HorarioAtencion


class CuandoFilter(admin.SimpleListFilter):
    title = 'cuándo'
    parameter_name = 'cuando'

    def lookups(self, request, model_admin):
        return [
            ('hoy', 'Hoy'),
            ('manana', 'Mañana'),
            ('proximas', 'Próximas'),
            ('pasadas', 'Pasadas'),
        ]

    def queryset(self, request, queryset):
        hoy = timezone.localdate()

        if self.value() == 'hoy':
            return queryset.filter(fecha=hoy)
        if self.value() == 'manana':
            return queryset.filter(fecha=hoy + timedelta(days=1))
        if self.value() == 'proximas':
            return queryset.filter(fecha__gte=hoy)
        if self.value() == 'pasadas':
            return queryset.filter(fecha__lt=hoy)

        return queryset


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'hora', 'cliente', 'telefono_cliente',
        'servicio', 'peluquero', 'estado',
    ]
    list_filter = [CuandoFilter, 'estado', 'peluquero']
    search_fields = ['cliente__nombre', 'cliente__telefono']
    date_hierarchy = 'fecha'
    ordering = ['fecha', 'hora']
    list_select_related = ['cliente', 'servicio', 'peluquero']
    list_per_page = 50
    actions = ['marcar_confirmadas', 'marcar_completadas', 'marcar_canceladas']

    @admin.display(description='Teléfono')
    def telefono_cliente(self, cita):
        return cita.cliente.telefono

    @admin.action(description='Marcar como confirmadas')
    def marcar_confirmadas(self, request, queryset):
        total = queryset.filter(estado='PENDIENTE').update(estado='CONFIRMADA')
        self.message_user(request, f'{total} cita(s) confirmadas.')

    @admin.action(description='Marcar como completadas')
    def marcar_completadas(self, request, queryset):
        total = queryset.filter(
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).update(estado='COMPLETADA')
        self.message_user(request, f'{total} cita(s) completadas.')

    @admin.action(description='Cancelar citas')
    def marcar_canceladas(self, request, queryset):
        total = queryset.filter(
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).update(estado='CANCELADA')
        self.message_user(request, f'{total} cita(s) canceladas.')


@admin.register(HorarioAtencion)
class HorarioAtencionAdmin(admin.ModelAdmin):
    list_display = ['dia_semana', 'hora_apertura', 'hora_cierre']