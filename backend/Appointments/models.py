from django.db import models, transaction
from Clients.models import Cliente
from Barbers.models import Peluquero
from Services.models import Servicio
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Count

class Cita(models.Model):
    ESTADOS = {
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    }

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

            cita = cls(
                servicio=servicio,
                peluquero= peluquero,
                fecha=fecha,
                hora=hora
            )

            if cita.esta_disponible():
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
        if not peluqueros:
            return None

        mejor_peluquero =None
        menor_cantidad =None

        for peluquero in peluqueros:

            cantidad_citas = cls.objects.filter(
                peluquero=peluquero,
                fecha = fecha
            ).exclude(
                estado ='CANCELADA'
            ).count()

            if(
                menor_cantidad is None
                or cantidad_citas < menor_cantidad
            ):
                mejor_peluquero= peluquero
                menor_cantidad = cantidad_citas
        return mejor_peluquero

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

        if not peluquero.activo:
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
    def crear_cita(
        cls,
        cliente,
        servicio,
        fecha,
        hora,
        tipo_peluquero = 'CUALQUIERA',
        peluquero=None
    ):
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
                if not cls.peluquero_especifico_disponible(
                    peluquero,
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
                estado='PENDIENTE'
            )
            return cita

    def clean(self):
        if self.peluquero and not self.esta_disponible():
            raise ValidationError(
                'El peluquero ya tiene una cita en ese horario.'
            )


        
    def __str__(self):
        return f"{self.cliente} - {self.fecha} {self.hora}"