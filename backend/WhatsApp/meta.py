import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

LIMITE_TEXTO = 4096
LIMITE_CUERPO_INTERACTIVO = 1024
LIMITE_TITULO_BOTON = 20
LIMITE_TITULO_FILA = 24


def url_mensajes():
    return (
        f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/'
        f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'
    )


def armar_payload(telefono, respuesta):
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': telefono,
    }

    if respuesta['tipo'] == 'botones':
        payload['type'] = 'interactive'
        payload['interactive'] = {
            'type': 'button',
            'body': {'text': respuesta['texto'][:LIMITE_CUERPO_INTERACTIVO]},
            'action': {
                'buttons': [
                    {
                        'type': 'reply',
                        'reply': {
                            'id': id_opcion,
                            'title': titulo[:LIMITE_TITULO_BOTON],
                        },
                    }
                    for id_opcion, titulo in respuesta['opciones'][:3]
                ]
            },
        }
        return payload

    if respuesta['tipo'] == 'lista':
        payload['type'] = 'interactive'
        payload['interactive'] = {
            'type': 'list',
            'body': {'text': respuesta['texto'][:LIMITE_CUERPO_INTERACTIVO]},
            'action': {
                'button': 'Ver opciones',
                'sections': [
                    {
                        'title': 'Opciones',
                        'rows': [
                            {'id': id_opcion, 'title': titulo[:LIMITE_TITULO_FILA]}
                            for id_opcion, titulo in respuesta['opciones'][:10]
                        ],
                    }
                ],
            },
        }
        return payload

    payload['type'] = 'text'
    payload['text'] = {'body': respuesta['texto'][:LIMITE_TEXTO]}
    return payload


def enviar_respuesta(telefono, respuesta):
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}',
        'Content-Type': 'application/json',
    }

    try:
        r = requests.post(
            url_mensajes(),
            json=armar_payload(telefono, respuesta),
            headers=headers,
            timeout=10,
        )
    except requests.RequestException:
        logger.exception('No se pudo conectar con la API de WhatsApp')
        return False

    if r.status_code >= 400:
        logger.error('WhatsApp respondió %s: %s', r.status_code, r.text)
        return False

    return True