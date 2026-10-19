from datetime import date, datetime, time
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from Appointments.models import Cita, HorarioAtencion
from Barbers.models import Peluquero
from Clients.models import Cliente
from Services.models import Servicio


# "Ahora" congelado: lunes 12 de octubre de 2026, 08:00 (Guayaquil)
AHORA = timezone.make_aware(datetime(2026, 10, 12, 8, 0))

LUNES = date(2026, 10, 12)      # "hoy"
MARTES = date(2026, 10, 13)
DOMINGO = date(2026, 10, 18)    # cerrado
PASADO = date(2026, 10, 9)


class ConDatosDePrueba(TestCase):

    def setUp(self):
        reloj = patch('django.utils.timezone.now', return_value=AHORA)
        reloj.start()
        self.addCleanup(reloj.stop)

        for dia in range(6):  # lunes a sábado
            HorarioAtencion.objects.create(
                dia_semana=dia,
                hora_apertura=time(9, 0),
                hora_cierre=time(19, 0),
            )

        self.servicio = Servicio.objects.create(
            nombre='Corte clásico',
            precio=5,
            duracion_minutos=30,
            activo=True,
        )
        self.carlos = Peluquero.objects.create(nombre='Carlos', activo=True)
        self.andres = Peluquero.objects.create(nombre='Andrés', activo=True)
        self.miguel = Peluquero.objects.create(nombre='Miguel', activo=True)
        self.cliente = Cliente.objects.create(nombre='Juan', telefono='0991234567')


class CitaTests(ConDatosDePrueba):    
    def crear(self, fecha=MARTES, hora=time(10, 0), **extra):
        return Cita.crear_cita(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha=fecha,
            hora=hora,
            **extra,
        )

    # --- Crear citas ---

    def test_cualquiera_asigna_un_peluquero(self):
        cita = self.crear()

        self.assertIsNotNone(cita.peluquero)
        self.assertEqual(cita.estado, 'PENDIENTE')

    def test_misma_hora_asigna_otro_peluquero(self):
        primera = self.crear()
        segunda = self.crear()

        self.assertNotEqual(primera.peluquero, segunda.peluquero)

    def test_cualquiera_prefiere_al_de_menor_carga(self):
        self.crear(hora=time(9, 0), tipo_peluquero='ESPECIFICO', peluquero=self.carlos)

        cita = self.crear(hora=time(11, 0))

        self.assertNotEqual(cita.peluquero, self.carlos)

    def test_horario_lleno_rechaza(self):
        for _ in range(3):
            self.crear()

        with self.assertRaises(ValidationError):
            self.crear()

    def test_peluquero_inactivo_no_se_asigna(self):
        self.miguel.activo = False
        self.miguel.save()

        self.crear()
        self.crear()

        with self.assertRaises(ValidationError):
            self.crear()

    def test_especifico_ocupado_rechaza(self):
        self.crear(tipo_peluquero='ESPECIFICO', peluquero=self.carlos)

        with self.assertRaises(ValidationError):
            self.crear(tipo_peluquero='ESPECIFICO', peluquero=self.carlos)

    def test_especifico_sin_peluquero_rechaza(self):
        with self.assertRaises(ValidationError):
            self.crear(tipo_peluquero='ESPECIFICO')

    # --- Validación del turno ---

    def test_fecha_pasada_rechaza(self):
        with self.assertRaises(ValidationError):
            self.crear(fecha=PASADO)

    def test_hora_ya_pasada_de_hoy_rechaza(self):
        with self.assertRaises(ValidationError):
            self.crear(fecha=LUNES, hora=time(7, 30))

    def test_dia_cerrado_rechaza(self):
        with self.assertRaises(ValidationError):
            self.crear(fecha=DOMINGO)

    def test_antes_de_abrir_rechaza(self):
        with self.assertRaises(ValidationError):
            self.crear(hora=time(8, 30))

    def test_se_pasa_del_cierre_rechaza(self):
        with self.assertRaises(ValidationError):
            self.crear(hora=time(18, 45))

    def test_ultimo_turno_se_acepta(self):
        cita = self.crear(hora=time(18, 30))

        self.assertIsNotNone(cita.pk)

    # --- Horarios disponibles ---

    def test_horarios_de_un_dia_completo(self):
        horas = Cita.horarios_disponibles(MARTES, self.servicio)

        self.assertEqual(len(horas), 20)
        self.assertEqual(horas[0], time(9, 0))
        self.assertEqual(horas[-1], time(18, 30))

    def test_turno_lleno_no_se_ofrece(self):
        for _ in range(3):
            self.crear()

        horas = Cita.horarios_disponibles(MARTES, self.servicio)

        self.assertNotIn(time(10, 0), horas)
        self.assertEqual(len(horas), 19)

    def test_dia_cerrado_no_tiene_horarios(self):
        self.assertEqual(Cita.horarios_disponibles(DOMINGO, self.servicio), [])

    # --- Cancelar ---

    def test_cancelar_libera_el_turno(self):
        cita = self.crear(tipo_peluquero='ESPECIFICO', peluquero=self.carlos)

        cita.cancelar()

        self.assertEqual(cita.estado, 'CANCELADA')
        self.assertIn(
            time(10, 0),
            Cita.horarios_disponibles(MARTES, self.servicio, 'ESPECIFICO', self.carlos),
        )

    def test_no_se_cancela_dos_veces(self):
        cita = self.crear()
        cita.cancelar()

        with self.assertRaises(ValidationError):
            cita.cancelar()

    def test_no_se_cancela_con_menos_de_2_horas(self):
        cita = self.crear(fecha=LUNES, hora=time(9, 30))  # faltan 1.5 h

        with self.assertRaises(ValidationError):
            cita.cancelar()