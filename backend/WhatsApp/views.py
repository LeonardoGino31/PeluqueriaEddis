from django.shortcuts import render
import json
import secrets
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging
from .models import MensajeProcesado
from .bot import procesar_mensaje, texto
from .meta import enviar_respuesta
import hashlib
import hmac

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(['GET','POST'])
def webhook(request):
    if request.method == 'GET':
        return verificar_webhook(request)

    return recibir_mensaje(request)

def verificar_webhook(request):
    modo = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token', '')
    desafio = request.GET.get('hub.challenge', '')

    token_valido = secrets.compare_digest(
        token,
        settings.WHATSAPP_VERIFY_TOKEN
    )

    if modo == 'subscribe' and token_valido:
        return HttpResponse(desafio, content_type='text/plain')

    return HttpResponse('Token de verificación inválido', status=403)

def recibir_mensaje(request):
    if not firma_valida(request):
        logger.warning('Webhook rechazado: firma inválida')
        return HttpResponse(status=403)
    
    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    for wamid, telefono, nombre, entrada in extraer_mensajes(datos):
        _, es_nuevo = MensajeProcesado.objects.get_or_create(wamid=wamid)

        if not es_nuevo:
            print(f'🔁 Mensaje duplicado ignorado: {wamid}')
            continue

        print(f'📩 {nombre} ({telefono}): {entrada}')

        try:
            atender_mensaje(telefono, nombre, entrada)
        except Exception:
            logger.exception('Error procesando mensaje de WhatsApp')
            
    return HttpResponse(status=200)


def extraer_mensajes(datos):
    for entrada_meta in datos.get('entry', []):
        for cambio in entrada_meta.get('changes', []):
            valor = cambio.get('value', {})

            nombres = {
                contacto.get('wa_id'): contacto.get('profile', {}).get('name', '')
                for contacto in valor.get('contacts', [])
            }

            for mensaje in valor.get('messages', []):
                telefono = mensaje.get('from')
                yield (
                    mensaje.get('id'),
                    telefono,
                    nombres.get(telefono, ''),
                    extraer_entrada(mensaje),
                )


def extraer_entrada(mensaje):
    tipo = mensaje.get('type')

    if tipo == 'text':
        return mensaje.get('text', {}).get('body', '')

    if tipo == 'interactive':
        interactivo = mensaje.get('interactive', {})

        if interactivo.get('type') == 'button_reply':
            return interactivo['button_reply']['id']

        if interactivo.get('type') == 'list_reply':
            return interactivo['list_reply']['id']

    return None


def atender_mensaje(telefono, nombre, entrada):
    if entrada is None:
        respuestas = [
            texto(
                'Por ahora solo puedo leer mensajes de texto y las opciones '
                'del menú. Escribe "menú" para empezar.'
            )
        ]
    else:
        respuestas = procesar_mensaje(telefono, entrada, nombre)

    for respuesta in respuestas:
        enviar_respuesta(telefono, respuesta)

def firma_valida(request):
    firma = request.headers.get('X-Hub-Signature-256', '')

    if not firma.startswith('sha256='):
        return False

    esperada = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        request.body,
        hashlib.sha256

    ).hexdigest()

    return secrets.compare_digest(firma.removeprefix('sha256='), esperada)

