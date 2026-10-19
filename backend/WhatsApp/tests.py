import hashlib
import hmac
import json
from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings

from Appointments.models import Cita
from Appointments.tests import AHORA, MARTES, ConDatosDePrueba
from Clients.models import Cliente

from .bot import procesar_mensaje
from .models import ConversacionWhatsApp, MensajeProcesado


TELEFONO_ANA = '0997776666'
MENU = ['AGENDAR', 'MIS_CITAS', 'CANCELAR']


def ids(respuesta):
    return [id_opcion for id_opcion, _ in respuesta.get('opciones', [])]


class BotTests(ConDatosDePrueba):

    def enviar(self, *mensajes):
        respuestas = None
        for mensaje in mensajes:
            respuestas = procesar_mensaje(TELEFONO_ANA, mensaje, 'Ana')
        return respuestas

    def ana(self):
        return Cliente.objects.get(telefono='593997776666')

    def agendar_hasta_la_hora(self):
        self.enviar(
            'hola',
            'AGENDAR',
            f'SERVICIO_{self.servicio.pk}',
            'DIA_2026-10-13',
            'MANANA',
            'HORA_10:00',
        )

    def test_hola_muestra_menu_y_crea_cliente(self):
        respuestas = self.enviar('hola')

        self.assertEqual(ids(respuestas[-1]), MENU)
        self.assertEqual(self.ana().nombre, 'Ana')

    def test_flujo_completo_crea_la_cita(self):
        self.agendar_hasta_la_hora()
        self.enviar('CUALQUIERA', 'CONFIRMAR')

        self.assertTrue(
            Cita.objects.filter(
                cliente=self.ana(), fecha=MARTES, hora=time(10, 0)
            ).exists()
        )
        conversacion = ConversacionWhatsApp.objects.get(cliente=self.ana())
        self.assertEqual(conversacion.datos, {})

    def test_turno_ganado_ofrece_otras_horas(self):
        self.agendar_hasta_la_hora()
        self.enviar('ESPECIFICO', f'PELUQUERO_{self.carlos.pk}')

        # Otro cliente le gana el turno a Carlos antes de que Ana confirme
        Cita.crear_cita(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha=MARTES,
            hora=time(10, 0),
            tipo_peluquero='ESPECIFICO',
            peluquero=self.carlos,
        )

        respuestas = self.enviar('CONFIRMAR')

        self.assertEqual(respuestas[-1]['tipo'], 'lista')
        self.assertFalse(Cita.objects.filter(cliente=self.ana()).exists())

    def test_respuesta_no_reconocida_repite_la_pregunta(self):
        respuestas = self.enviar('hola', 'AGENDAR', 'cualquier cosa')

        self.assertIn(f'SERVICIO_{self.servicio.pk}', ids(respuestas[-1]))

    def test_conversacion_expirada_vuelve_al_menu(self):
        self.enviar('hola', 'AGENDAR')
        ConversacionWhatsApp.objects.filter(cliente=self.ana()).update(
            actualizado=AHORA - timedelta(hours=1)
        )

        respuestas = self.enviar(f'SERVICIO_{self.servicio.pk}')

        self.assertEqual(ids(respuestas[-1]), MENU)

    def test_cancelar_desde_el_bot(self):
        self.enviar('hola')
        cita = Cita.crear_cita(
            cliente=self.ana(), servicio=self.servicio,
            fecha=MARTES, hora=time(10, 0),
        )

        self.enviar('CANCELAR', f'CITA_{cita.pk}', 'SI_CANCELAR')

        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'CANCELADA')

    def test_no_puede_cancelar_cita_de_otro_cliente(self):
        self.enviar('hola')
        Cita.crear_cita(
            cliente=self.ana(), servicio=self.servicio,
            fecha=MARTES, hora=time(11, 0),
        )
        ajena = Cita.crear_cita(
            cliente=self.cliente, servicio=self.servicio,
            fecha=MARTES, hora=time(10, 0),
        )

        self.enviar('CANCELAR', f'CITA_{ajena.pk}', 'SI_CANCELAR')

        ajena.refresh_from_db()
        self.assertEqual(ajena.estado, 'PENDIENTE')


SECRETO = 'secreto-de-prueba'
VERIFY_TOKEN = 'verify-de-prueba'


def mensaje_de_meta(texto, wamid='wamid.PRUEBA1', telefono='593991112222'):
    return {
        'object': 'whatsapp_business_account',
        'entry': [{
            'changes': [{
                'field': 'messages',
                'value': {
                    'contacts': [{'profile': {'name': 'Pedro'}, 'wa_id': telefono}],
                    'messages': [{
                        'from': telefono,
                        'id': wamid,
                        'type': 'text',
                        'text': {'body': texto},
                    }],
                },
            }],
        }],
    }


@override_settings(
    WHATSAPP_VERIFY_TOKEN=VERIFY_TOKEN,
    WHATSAPP_APP_SECRET=SECRETO,
)
class WebhookTests(TestCase):

    def setUp(self):
        envio = patch('WhatsApp.views.enviar_respuesta')
        self.enviar_respuesta = envio.start()
        self.addCleanup(envio.stop)

    def post(self, datos, firma=None):
        cuerpo = json.dumps(datos).encode()

        if firma is None:
            firma = 'sha256=' + hmac.new(
                SECRETO.encode(), cuerpo, hashlib.sha256
            ).hexdigest()

        return self.client.post(
            '/whatsapp/webhook/',
            data=cuerpo,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=firma,
        )

    def test_verificacion_con_token_correcto(self):
        r = self.client.get('/whatsapp/webhook/', {
            'hub.mode': 'subscribe',
            'hub.verify_token': VERIFY_TOKEN,
            'hub.challenge': '12345',
        })

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b'12345')

    def test_verificacion_con_token_incorrecto(self):
        r = self.client.get('/whatsapp/webhook/', {
            'hub.mode': 'subscribe',
            'hub.verify_token': 'otro',
            'hub.challenge': '12345',
        })

        self.assertEqual(r.status_code, 403)

    def test_mensaje_valido_se_procesa_y_responde(self):
        r = self.post(mensaje_de_meta('hola'))

        self.assertEqual(r.status_code, 200)
        self.enviar_respuesta.assert_called()
        self.assertTrue(Cliente.objects.filter(telefono='593991112222').exists())

    def test_sin_firma_se_rechaza(self):
        r = self.post(mensaje_de_meta('hola'), firma='')

        self.assertEqual(r.status_code, 403)
        self.enviar_respuesta.assert_not_called()
        self.assertFalse(Cliente.objects.exists())

    def test_firma_falsa_se_rechaza(self):
        r = self.post(mensaje_de_meta('hola'), firma='sha256=falsa')

        self.assertEqual(r.status_code, 403)
        self.enviar_respuesta.assert_not_called()

    def test_mensaje_duplicado_se_procesa_una_sola_vez(self):
        self.post(mensaje_de_meta('hola'))
        envios_primera_vez = self.enviar_respuesta.call_count

        r = self.post(mensaje_de_meta('hola'))

        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.enviar_respuesta.call_count, envios_primera_vez)
        self.assertEqual(MensajeProcesado.objects.count(), 1)

    def test_aviso_de_estado_se_ignora(self):
        aviso = {
            'entry': [{
                'changes': [{
                    'value': {'statuses': [{'id': 'wamid.X', 'status': 'delivered'}]},
                }],
            }],
        }

        r = self.post(aviso)

        self.assertEqual(r.status_code, 200)
        self.enviar_respuesta.assert_not_called()