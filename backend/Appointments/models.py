from django.db import models, transaction
from Clients.models import Cliente
from Barbers.models import Peluquero
from Services.models import Servicio
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q


class Cita(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    ]

    HORAS_MINIMAS_CANCELACION = 2

    TIPOS_PELUQUERO = [
    ('ESPECIFICO', 'Peluquero específico'),
    ('CUALQUIERA', 'Cualquier peluquero'),
    ]
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete = models.PROTECT,
        related_name ='citas'
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete= models.PROTECT,
        related_name= 'citas'
    )

    peluquero= models.ForeignKey(
        Peluquero, 
        on_delete= models.SET_NULL,
        null=True,
        blank=True,
        related_name= 'citas'
    )

    tipo_peluquero = models.CharField(
    max_length=20,
    choices=TIPOS_PELUQUERO,
    default='CUALQUIERA'
)
    
    fecha = models.DateField()
    hora = models.TimeField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    observaciones = models.TextField(blank=True)

    def hora_fin(self):
        inicio = datetime.combine(self.fecha, self.hora)
        fin = inicio + timedelta(minutes=self.servicio.duracion_minutos)
        return fin.time()

    def cancelar(self):
        if self.estado not in ['PENDIENTE', 'CONFIRMADA']:
            raise ValidationError(
                'Solo se pueden cancelar citas pendientes o confirmadas.'
            )

        if self.es_turno_pasado(self.fecha, self.hora):
            raise ValidationError(
                'No se puede cancelar una cita que ya ha pasado.'
            )
        inicio= timezone.make_aware(
            datetime.combine(self.fecha, self.hora)
        )
        limite = inicio - timedelta(hours=self.HORAS_MINIMAS_CANCELACION)

        if timezone.now() > limite:
            raise ValidationError(
                f'No se puede cancelar una cita con menos de '
                f'{self.HORAS_MINIMAS_CANCELACION} horas de anticipación.'
            )

        self.estado = 'CANCELADA'
        self.save(update_fields=['estado'])
    

    def esta_disponible(self):
        if not self.peluquero:
            return True

        if self.estado == 'CANCELADA':
            return True

        inicio_nueva = datetime.combine(
            self.fecha,
            self.hora
        )

        fin_nueva = inicio_nueva + timedelta(
            minutes=self.servicio.duracion_minutos
        )

        citas = Cita.objects.filter(
            peluquero=self.peluquero,
            fecha=self.fecha
        ).exclude(
            estado='CANCELADA'
        )

        if self.pk:
            citas = citas.exclude(pk=self.pk)

        for cita in citas:
            inicio_existente = datetime.combine(
                cita.fecha,
                cita.hora
            )

            fin_existente = inicio_existente + timedelta(
                minutes=cita.servicio.duracion_minutos
            )

            if (
                inicio_nueva < fin_existente
                and fin_nueva > inicio_existente
            ):
                return False

        return True


    @staticmethod
    def es_turno_pasado(fecha, hora):
        inicio = timezone.make_aware(
            datetime.combine(fecha, hora)
        )
        return inicio <= timezone.now()

    @classmethod
    def buscar_peluqueros_disponibles(
        cls,
        fecha,
        hora,
        servicio
    ):
        peluqueros_disponibles= []

        peluqueros = Peluquero.objects.filter(
            activo=True
        )

        for peluquero in peluqueros:

            if cls.peluquero_especifico_disponible(
                peluquero,
                fecha,
                hora,
                servicio
            ):
                peluqueros_disponibles.append(peluquero)


        return peluqueros_disponibles

    @classmethod
    def asignar_peluquero_disponible(
        cls,
        fecha,
        hora,
        servicio
    ):
        peluqueros = cls.buscar_peluqueros_disponibles(
            fecha,
            hora,
            servicio
        )

        peluqueros_con_carga = []

        for peluquero in peluqueros:

            cantidad_citas = cls.objects.filter(
                peluquero=peluquero,
                fecha=fecha
            ).exclude(
                estado='CANCELADA'
            ).count()

            peluqueros_con_carga.append((cantidad_citas, peluquero))

        peluqueros_con_carga.sort(key=lambda item: item[0])

        return [peluquero for cantidad, peluquero in peluqueros_con_carga]

    @classmethod
    def hay_plazas_disponibles(
        cls,
    fecha,
    hora,
    servicio
    ):
        return bool(
            cls.buscar_peluqueros_disponibles(
            fecha,
            hora,
            servicio
            )
        )
    
    @classmethod
    def peluquero_especifico_disponible(
        cls,
        peluquero,
        fecha,
        hora,
        servicio
        ):    

        if cls.es_turno_pasado(fecha, hora):
            return False
        
        if not peluquero.activo:
            return False


        if not cls.peluquero_trabaja_en(
            peluquero,
            fecha,
            hora,
            servicio
        ):
            return False

        
        cita = cls(
            servicio=servicio,
            peluquero=peluquero,
            fecha=fecha,
            hora=hora
        )

        return cita.esta_disponible()

    @classmethod
    def obtener_opciones_peluquero(
        cls,
        tipo_peluquero,
        peluquero,
        fecha,
        hora,
        servicio

    ):
        if tipo_peluquero == 'ESPECIFICO':
            if not peluquero:
                return []
            if cls.peluquero_especifico_disponible(
               peluquero,
               fecha,
               hora, 
               servicio 
            ):
                return[peluquero]
            return []
        if tipo_peluquero== 'CUALQUIERA':

            return cls.buscar_peluqueros_disponibles(
                fecha,
                hora,
                servicio
            )
        return []

    @classmethod
    def validar_turno(cls, fecha, hora, servicio):
        if cls.es_turno_pasado(fecha, hora):
            raise ValidationError(
                'No se pueden agendar citas en una fecha u hora pasada.'
            )

        horario= HorarioAtencion.para_fecha(fecha)

        if not horario:
            raise ValidationError(
                'No hay horario de atención para ese día.'
            )

        inicio = datetime.combine(fecha, hora)
        fin = inicio + timedelta(minutes=servicio.duracion_minutos)

        apertura = datetime.combine(fecha, horario.hora_apertura)
        cierre = datetime.combine(fecha, horario.hora_cierre)

        if not (apertura <= inicio and fin <= cierre):
            raise ValidationError(
                f'Ese día atendemos de {horario.hora_apertura:%H:%M} '
                f'a {horario.hora_cierre:%H:%M}.'
            )
    
    @classmethod
    def crear_cita(
        cls,
        cliente,
        servicio,
        fecha,
        hora,
        tipo_peluquero = 'CUALQUIERA',
        peluquero=None,
        observaciones=''
    ):
        cls.validar_turno(fecha, hora, servicio)

        with transaction.atomic():
            if tipo_peluquero =='ESPECIFICO':
                if not peluquero:
                    raise ValidationError(
                        'Debe seleccionar un peluquero.'
                    )

                peluquero_bloqueado = (
                Peluquero.objects
                .select_for_update()
                .get(pk=peluquero.pk)
            )
                if not peluquero_bloqueado.activo:
                    raise ValidationError(
                        'El peluquero ya no está atendiendo.'
                    )
                
                if not cls.peluquero_especifico_disponible(
                    peluquero_bloqueado,
                    fecha,
                    hora,
                    servicio
                ):
                    raise ValidationError(
                        'El peluquero no está disponible en ese horario.'
                    )
                peluquero=peluquero_bloqueado

            elif tipo_peluquero =='CUALQUIERA':
                peluqueros= cls.asignar_peluquero_disponible(
                    fecha,
                    hora,
                    servicio
                )
                if not peluqueros:
                    raise ValidationError(
                        'No hay peluqueros disponibles en ese horario.'
                    )
                peluquero =None
                for peluquero_candidato in peluqueros:

                    peluquero_bloqueado = (
                        Peluquero.objects
                        .select_for_update()
                        .get(pk=peluquero_candidato.pk)
                    )

                    # Volvemos a comprobar después del bloqueo
                    if cls.peluquero_especifico_disponible(
                        peluquero_bloqueado,
                        fecha,
                        hora,
                        servicio
                    ):
                        peluquero = peluquero_bloqueado
                        break

                if not peluquero:
                    raise ValidationError(
                        'No hay peluqueros disponibles en ese horario.'
                    )               

            else:
                raise ValidationError(
                    'Tipo de peluquero no válido.'
                )
            cita = cls.objects.create(
                cliente= cliente,
                servicio=servicio,
                peluquero=peluquero,
                fecha=fecha,
                hora=hora,
                tipo_peluquero=tipo_peluquero,
                estado='PENDIENTE',
                observaciones=observaciones
            )
            return cita
    @classmethod
    def peluquero_trabaja_en(
        cls,
        peluquero,
        fecha,
        hora,
        servicio
    ):
        horario=HorarioAtencion.para_fecha(fecha)
        
        if not horario:
            return False

        inicio = datetime.combine(fecha, hora)
        fin = inicio + timedelta(minutes=servicio.duracion_minutos)

        apertura = datetime.combine(fecha, horario.hora_apertura)
        cierre = datetime.combine(fecha, horario.hora_cierre)

        return apertura <= inicio and fin <= cierre

    @classmethod
    def horarios_disponibles(   
        cls,
        fecha,
        servicio,
        tipo_peluquero='CUALQUIERA',
        peluquero=None
    ):
        horario= HorarioAtencion.para_fecha(fecha)

        if not horario:
            return []

        duracion= timedelta(minutes=servicio.duracion_minutos)
        turno = datetime.combine(fecha, horario.hora_apertura)
        cierre = datetime.combine(fecha, horario.hora_cierre)

        horarios = []

        while turno + duracion <= cierre:
            hora = turno.time()
            opciones_peluquero = cls.obtener_opciones_peluquero(    
                tipo_peluquero,
                peluquero,
                fecha,
                hora,
                servicio
            )

            if opciones_peluquero:
                horarios.append(hora)

            turno += duracion

        return horarios

    @classmethod
    def citas_proximas(cls, cliente):
        ahora = timezone.localtime()
        hoy = ahora.date()
        hora_actual = ahora.time()

        return( 
            cls.objects.filter(
                cliente=cliente,
                estado__in=['PENDIENTE', 'CONFIRMADA'],
            ).filter(
                Q(fecha__gt=hoy) | Q(fecha=hoy, hora__gte=hora_actual)
            )
            .select_related('servicio', 'peluquero')
            .order_by('fecha', 'hora')

        )

    
    def clean(self):
        if self.peluquero and not self.esta_disponible():
            raise ValidationError(
                'El peluquero ya tiene una cita en ese horario.'
            )


        
    def __str__(self):
        return f"{self.cliente} - {self.fecha} {self.hora}"


class HorarioAtencion(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    dia_semana = models.PositiveSmallIntegerField(
        choices=DIAS_SEMANA,
        unique=True
    )
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()

    class Meta:
        ordering = ['dia_semana']
        verbose_name = 'Horario de atención'
        verbose_name_plural = 'Horarios de atención'

    def clean(self):
        if self.hora_apertura >= self.hora_cierre:
            raise ValidationError(
                'La hora de apertura debe ser antes de la hora de cierre.'
            )

    @classmethod
    def para_fecha(cls, fecha):
        return cls.objects.filter(
            dia_semana=fecha.weekday()
        ).first()

    def __str__(self):
        return (
            f"{self.get_dia_semana_display()}: "
            f"{self.hora_apertura:%H:%M} - {self.hora_cierre:%H:%M}"
        )