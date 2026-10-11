from Clients.models import Cliente
from Services.models import Servicio
from .models import ConversacionWhatsApp
from datetime import date, timedelta, time 
from django.utils import timezone
from Appointments.models import Cita
from django.core.exceptions import ValidationError
from Barbers.models import Peluquero

PALABRAS_REINICIO = ['hola', 'menu', 'menú', 'volver', 'inicio', 'salir']

OPCIONES_MENU = {
    'AGENDAR': 'AGENDAR',
    '1': 'AGENDAR',
    'AGENDAR CITA': 'AGENDAR',
    'MIS_CITAS': 'MIS_CITAS',
    '2': 'MIS_CITAS',
    'MIS CITAS': 'MIS_CITAS',
    'CANCELAR': 'CANCELAR',
    '3': 'CANCELAR',
    'CANCELAR CITA': 'CANCELAR',
}  

DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
         'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

DIAS_A_BUSCAR = 14
MAX_DIAS_OFRECIDOS = 7

FRANJAS = [
    ('MANANA', 'Mañana', time(0, 0), time(12, 0)),
    ('MEDIODIA', 'Mediodía', time(12, 0), time(15, 0)),
    ('TARDE', 'Tarde', time(15, 0), time(23, 59)),
]

OPCIONES_TIPO_PELUQUERO = [
    ('CUALQUIERA', 'Cualquiera'),
    ('ESPECIFICO', 'Elegir peluquero'),
]

OPCIONES_CONFIRMACION = [
    ('CONFIRMAR', 'Confirmar'),
    ('OTRA_HORA', 'Cambiar hora'),
    ('VOLVER', 'Volver al menú'),
]

OPCIONES_CANCELACION = [
    ('SI_CANCELAR', 'Sí, cancelar'),
    ('NO_CANCELAR', 'No, mantenerla'),
]

def texto(mensaje):
    return {'tipo': 'texto', 'texto': mensaje}

def botones(mensaje, opciones):
    return {'tipo': 'botones', 'texto': mensaje, 'opciones': opciones}

def lista(mensaje, opciones):
    return {'tipo': 'lista', 'texto': mensaje, 'opciones': opciones}

def elegir_opcion(entrada, opciones):
    entrada = entrada.strip().upper()

    for posicion, (id_opcion, titulo) in enumerate(opciones, start=1):
        if entrada in (id_opcion.upper(), titulo.upper(), str(posicion)):
            return id_opcion

    return None

def servicio_disponibles():
    return list(
        Servicio.objects.filter(
            activo=True
        ).order_by('nombre')[:10]
    )

def opciones_servicios(servicios):
    return [(f'SERVICIO_{s.pk}', s.nombre[:24]) for s in servicios]

def nombre_dia(fecha):
    if fecha == timezone.localdate():
        prefijo = 'Hoy'
    else :
        prefijo = DIAS_SEMANA[fecha.weekday()]

    return f"{prefijo} {fecha.day} {MESES[fecha.month - 1]}"

def servicio_elegido(conversacion):
    return Servicio.objects.filter(
        pk=conversacion.datos.get('servicio_id'),
        activo=True
    ).first()


def dias_disponibles(servicio):
    hoy = timezone.localdate()
    dias = []

    for i in range(DIAS_A_BUSCAR):
        fecha = hoy + timedelta(days=i)
        if Cita.horarios_disponibles(fecha, servicio):
            dias.append(fecha)

        if len(dias) >= MAX_DIAS_OFRECIDOS:
            break

    return dias

def opciones_dias(dias):
    return [(f'DIA_{d.isoformat()}', nombre_dia(d)) for d in dias]

def volver_al_menu(conversacion, mensaje):
    conversacion.reiniciar()
    return mostrar_menu(conversacion, encabezado=mensaje)


def fecha_elegida(conversacion):
    return date.fromisoformat(conversacion.datos['fecha'])


def horas_por_franja(fecha, servicio):
    horas = Cita.horarios_disponibles(fecha, servicio)
    resultado = {}

    for id_franja, _, inicio, fin in FRANJAS:
        en_franja = [h for h in horas if inicio <= h < fin]

        if en_franja:
            resultado[id_franja] = en_franja[:10]

    return resultado


def opciones_franjas(franjas):
    return [
        (id_franja, titulo)
        for id_franja, titulo, _, _ in FRANJAS
        if id_franja in franjas
    ]


def opciones_horas(horas):
    return [(f'HORA_{h:%H:%M}', f'{h:%H:%M}') for h in horas]

def hora_elegida(conversacion):
    return time.fromisoformat(conversacion.datos['hora'])


def peluqueros_libres(conversacion, servicio):
    return Cita.buscar_peluqueros_disponibles(
        fecha_elegida(conversacion),
        hora_elegida(conversacion),
        servicio
    )


def opciones_peluqueros(peluqueros):
    return [(f'PELUQUERO_{p.pk}', p.nombre[:24]) for p in peluqueros]

def describir_cita(cita):
    peluquero = cita.peluquero.nombre if cita.peluquero else 'por asignar'

    return (
        f'📅 {nombre_dia(cita.fecha)} · 🕐 {cita.hora:%H:%M}\n'
        f'✂️ {cita.servicio.nombre} con {peluquero}'
    )


def citas_del_cliente(conversacion):
    return list(Cita.citas_proximas(conversacion.cliente)[:10])


def opciones_citas(citas):
    return [
        (f'CITA_{c.pk}', f'{nombre_dia(c.fecha)} {c.hora:%H:%M}')
        for c in citas
    ]


def cita_elegida(conversacion):
    return Cita.objects.filter(
        pk=conversacion.datos.get('cita_id'),
        cliente=conversacion.cliente
    ).select_related('servicio', 'peluquero').first()

def procesar_mensaje(telefono, entrada, nombre=''):
    cliente, cliente_nuevo = Cliente.obtener_o_crear_por_telefono(telefono, nombre)

    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(cliente=cliente)

    entrada = (entrada or '').strip()

    if conversacion.ha_expirado() or entrada.lower() in PALABRAS_REINICIO:
        conversacion.reiniciar()

    if conversacion.paso == 'INICIO':
        return mostrar_menu(conversacion, cliente_nuevo)

    if conversacion.paso == 'MENU':
        return manejar_menu(conversacion, entrada)

    if conversacion.paso == 'SERVICIOS':
        return manejar_servicios(conversacion, entrada)

    if conversacion.paso == 'ELEGIR_DIA':
        return manejar_dia(conversacion, entrada)

    if conversacion.paso == 'ELEGIR_FRANJA':
        return manejar_franja(conversacion, entrada)

    if conversacion.paso == 'ELEGIR_HORA':
        return manejar_hora(conversacion, entrada)

    if conversacion.paso == 'ELEGIR_TIPO_PELUQUERO':
        return manejar_tipo_peluquero(conversacion, entrada)

    if conversacion.paso == 'ELEGIR_PELUQUERO':
        return manejar_peluquero(conversacion, entrada)

    if conversacion.paso == 'CONFIRMAR_CITA':
        return manejar_confirmacion(conversacion, entrada)

    if conversacion.paso == 'ELEGIR_CITA_CANCELAR':
        return manejar_cita_cancelar(conversacion, entrada)

    if conversacion.paso == 'CONFIRMAR_CANCELACION':
        return manejar_confirmar_cancelacion(conversacion, entrada)
    

    conversacion.reiniciar()
    return mostrar_menu(conversacion)


def mostrar_menu(conversacion, cliente_nuevo=False, encabezado=None):
    nombre = conversacion.cliente.nombre

    if encabezado:
        saludo = encabezado

    elif cliente_nuevo:
        saludo = f"¡Hola {nombre}! Bienvenido a Peluquería Eddis."

    elif nombre:
        saludo = f"¡Hola {nombre}! Bienvenido de nuevo a Peluquería Eddis."

    else:
        saludo = "¡Hola! Bienvenido a Peluquería Eddis."

    conversacion.avanzar('MENU')

    return [
        botones(
            f'{saludo}\n¿Qué deseas hacer?',
            [
                ('AGENDAR', 'Agendar cita'),
                ('MIS_CITAS', 'Mis citas'),
                ('CANCELAR', 'Cancelar cita'),
            ]

        )
    ]

def manejar_menu(conversacion, entrada):
    opcion = OPCIONES_MENU.get(entrada.upper())

    if opcion == 'AGENDAR':
        return mostrar_servicios(conversacion)

    elif opcion == 'MIS_CITAS':
        return mostrar_mis_citas(conversacion)


    elif opcion == 'CANCELAR':
        return mostrar_citas_cancelar(conversacion)

    return mostrar_menu(
             conversacion,
             encabezado="Lo siento, no entendí tu respuesta. Por favor, selecciona una opción del menú."
    )

def mostrar_servicios(conversacion, encabezado='¿Qué servicio deseas?'):
    servicios = servicio_disponibles()

    if not servicios:
       return mostrar_menu(
              conversacion,
              encabezado="Lo siento, no hay servicios disponibles en este momento."
         )
    detalle = '\n'.join(
        f'• {s.nombre}: ${s.precio} ({s.duracion_minutos} min)'
        for s in servicios
    )

    conversacion.avanzar('SERVICIOS')

    return [
        lista(f'{encabezado}\n\n{detalle}', opciones_servicios(servicios))
    ]

def manejar_servicios(conversacion, entrada):
    servicios = servicio_disponibles()
    elegido = elegir_opcion(entrada, opciones_servicios(servicios))

    if not elegido:
        return mostrar_servicios(
            conversacion,
            encabezado="Lo siento, no entendí tu respuesta. Por favor, selecciona un servicio de la lista."
        )

    servicio_id = int(elegido.split('_')[1])
    conversacion.avanzar('ELEGIR_DIA', servicio_id=servicio_id)

    return mostrar_dias(conversacion)


def mostrar_dias(conversacion, encabezado='¿Qué día te queda mejor?'):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        conversacion.reiniciar()
        return mostrar_menu(
            conversacion,
            encabezado='Ese servicio ya no está disponible.'
        )

    dias = dias_disponibles(servicio)
    if not dias:
        conversacion.reiniciar()
        return mostrar_menu(
            conversacion,
            encabezado='No hay turnos libres en los próximos días. 😕'
        )

    conversacion.avanzar('ELEGIR_DIA')

    return [lista(encabezado, opciones_dias(dias))]


def manejar_dia(conversacion, entrada):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        conversacion.reiniciar()
        return mostrar_menu(
            conversacion,
            encabezado='Ese servicio ya no está disponible.'
        )

    opciones = opciones_dias(dias_disponibles(servicio))
    elegido = elegir_opcion(entrada, opciones)

    if not elegido:
        return mostrar_dias(
            conversacion,
            encabezado="Lo siento, no entendí tu respuesta. Por favor, selecciona un día de la lista."
        )

    fecha = elegido.split('_')[1]
    conversacion.avanzar('ELEGIR_FRANJA', fecha=fecha)

    return mostrar_franjas(conversacion)

def mostrar_franjas(conversacion, encabezado='¿En qué parte del día?'):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    franjas = horas_por_franja(fecha_elegida(conversacion), servicio)

    if not franjas:
        return mostrar_dias(
            conversacion,
            encabezado='Ese día ya no tiene turnos libres. Elige otro:'
        )

    if len(franjas) == 1:
        unica = next(iter(franjas))
        conversacion.avanzar('ELEGIR_HORA', franja=unica)
        return mostrar_horas(conversacion)

    conversacion.avanzar('ELEGIR_FRANJA')

    return [botones(encabezado, opciones_franjas(franjas))]


def manejar_franja(conversacion, entrada):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    franjas = horas_por_franja(fecha_elegida(conversacion), servicio)
    elegido = elegir_opcion(entrada, opciones_franjas(franjas))

    if not elegido:
        return mostrar_franjas(
            conversacion,
            encabezado='No reconocí tu respuesta. Elige una opción:'
        )

    conversacion.avanzar('ELEGIR_HORA', franja=elegido)

    return mostrar_horas(conversacion)


def mostrar_horas(conversacion, encabezado='¿A qué hora?'):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    franjas = horas_por_franja(fecha_elegida(conversacion), servicio)
    horas = franjas.get(conversacion.datos.get('franja'))

    if not horas:
        return mostrar_franjas(
            conversacion,
            encabezado='Ya no quedan turnos en ese horario. Elige otro:'
        )

    conversacion.avanzar('ELEGIR_HORA')

    return [lista(encabezado, opciones_horas(horas))]


def manejar_hora(conversacion, entrada):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    franjas = horas_por_franja(fecha_elegida(conversacion), servicio)
    horas = franjas.get(conversacion.datos.get('franja'), [])
    elegido = elegir_opcion(entrada, opciones_horas(horas))

    if not elegido:
        return mostrar_horas(
            conversacion,
            encabezado='No reconocí esa hora. Elige una de la lista:'
        )

    hora = elegido.split('_')[1]
    conversacion.avanzar('ELEGIR_TIPO_PELUQUERO', hora=hora)

    return mostrar_tipo_peluquero(conversacion)


def mostrar_tipo_peluquero(conversacion,
                           encabezado='¿Tienes algún peluquero de preferencia?'):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    if not peluqueros_libres(conversacion, servicio):
        return mostrar_horas(
            conversacion,
            encabezado='Ese turno se acaba de ocupar. Elige otra hora:'
        )

    conversacion.avanzar('ELEGIR_TIPO_PELUQUERO')

    return [botones(encabezado, OPCIONES_TIPO_PELUQUERO)]


def manejar_tipo_peluquero(conversacion, entrada):
    elegido = elegir_opcion(entrada, OPCIONES_TIPO_PELUQUERO)

    if not elegido:
        return mostrar_tipo_peluquero(
            conversacion,
            encabezado='No reconocí tu respuesta. Elige una opción:'
        )

    if elegido == 'CUALQUIERA':
        conversacion.avanzar(
            'CONFIRMAR_CITA',
            tipo_peluquero='CUALQUIERA',
            peluquero_id=None
        )
        return mostrar_confirmacion(conversacion)

    conversacion.avanzar('ELEGIR_PELUQUERO', tipo_peluquero='ESPECIFICO')
    return mostrar_peluqueros(conversacion)


def mostrar_peluqueros(conversacion, encabezado='¿Con quién te quieres atender?'):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    peluqueros = peluqueros_libres(conversacion, servicio)

    if not peluqueros:
        return mostrar_horas(
            conversacion,
            encabezado='Ese turno se acaba de ocupar. Elige otra hora:'
        )

    conversacion.avanzar('ELEGIR_PELUQUERO')

    return [lista(encabezado, opciones_peluqueros(peluqueros))]


def manejar_peluquero(conversacion, entrada):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    peluqueros = peluqueros_libres(conversacion, servicio)
    elegido = elegir_opcion(entrada, opciones_peluqueros(peluqueros))

    if not elegido:
        return mostrar_peluqueros(
            conversacion,
            encabezado='No reconocí ese peluquero. Elige uno de la lista:'
        )

    peluquero_id = int(elegido.split('_')[1])
    conversacion.avanzar('CONFIRMAR_CITA', peluquero_id=peluquero_id)

    return mostrar_confirmacion(conversacion)


def mostrar_confirmacion(conversacion, encabezado='Revisa tu cita:'):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    datos = conversacion.datos

    if datos.get('tipo_peluquero') == 'ESPECIFICO':
        peluquero = Peluquero.objects.filter(pk=datos.get('peluquero_id')).first()

        if not peluquero:
            return mostrar_peluqueros(conversacion)

        texto_peluquero = peluquero.nombre
    else:
        texto_peluquero = 'El primero disponible'

    conversacion.avanzar('CONFIRMAR_CITA')

    resumen = (
        f'{encabezado}\n\n'
        f'✂️ {servicio.nombre}\n'
        f'📅 {nombre_dia(fecha_elegida(conversacion))}\n'
        f'🕐 {datos["hora"]}\n'
        f'💈 {texto_peluquero}\n'
        f'💵 ${servicio.precio}'
    )

    return [botones(resumen, OPCIONES_CONFIRMACION)]


def manejar_confirmacion(conversacion, entrada):
    elegido = elegir_opcion(entrada, OPCIONES_CONFIRMACION)

    if not elegido:
        return mostrar_confirmacion(
            conversacion,
            encabezado='No reconocí tu respuesta. Revisa tu cita:'
        )

    if elegido == 'VOLVER':
        return volver_al_menu(conversacion, 'Listo, no se agendó ninguna cita.')

    if elegido == 'OTRA_HORA':
        return mostrar_franjas(conversacion)

    return crear_cita_desde_conversacion(conversacion)


def crear_cita_desde_conversacion(conversacion):
    servicio = servicio_elegido(conversacion)

    if not servicio:
        return volver_al_menu(conversacion, 'Ese servicio ya no está disponible.')

    datos = conversacion.datos
    peluquero = None

    if datos.get('tipo_peluquero') == 'ESPECIFICO':
        peluquero = Peluquero.objects.filter(pk=datos.get('peluquero_id')).first()

    try:
        cita = Cita.crear_cita(
            cliente=conversacion.cliente,
            servicio=servicio,
            fecha=fecha_elegida(conversacion),
            hora=hora_elegida(conversacion),
            tipo_peluquero=datos.get('tipo_peluquero', 'CUALQUIERA'),
            peluquero=peluquero,
        )
    except ValidationError as e:
        return mostrar_horas(
            conversacion,
            encabezado=f'{e.messages[0]} Elige otra hora:'
        )

    conversacion.reiniciar()

    return [
        texto(
            '✅ ¡Listo! Tu cita quedó agendada.\n\n'
            f'✂️ {servicio.nombre}\n'
            f'📅 {nombre_dia(cita.fecha)}\n'
            f'🕐 {cita.hora:%H:%M}\n'
            f'💈 {cita.peluquero.nombre}\n\n'
            'Te esperamos. Escribe "menú" si necesitas algo más.'
        )
    ]

def mostrar_mis_citas(conversacion):
    citas = citas_del_cliente(conversacion)

    if not citas:
        return mostrar_menu(conversacion, encabezado='No tienes citas próximas.')

    detalle = '\n\n'.join(describir_cita(c) for c in citas)

    return (
        [texto(f'Tus próximas citas:\n\n{detalle}')]
        + mostrar_menu(conversacion, encabezado='¿Necesitas algo más?')
    )


def mostrar_citas_cancelar(conversacion,
                           encabezado='¿Qué cita quieres cancelar?'):
    citas = citas_del_cliente(conversacion)

    if not citas:
        return mostrar_menu(
            conversacion,
            encabezado='No tienes citas para cancelar.'
        )

    detalle = '\n\n'.join(describir_cita(c) for c in citas)
    conversacion.avanzar('ELEGIR_CITA_CANCELAR')

    return [lista(f'{encabezado}\n\n{detalle}', opciones_citas(citas))]


def manejar_cita_cancelar(conversacion, entrada):
    citas = citas_del_cliente(conversacion)
    elegido = elegir_opcion(entrada, opciones_citas(citas))

    if not elegido:
        return mostrar_citas_cancelar(
            conversacion,
            encabezado='No reconocí esa cita. Elige una de la lista:'
        )

    cita_id = int(elegido.split('_')[1])
    conversacion.avanzar('CONFIRMAR_CANCELACION', cita_id=cita_id)

    return mostrar_confirmar_cancelacion(conversacion)


def mostrar_confirmar_cancelacion(
        conversacion,
        encabezado='¿Seguro que quieres cancelar esta cita?'):
    cita = cita_elegida(conversacion)

    if not cita:
        return volver_al_menu(conversacion, 'No encontré esa cita.')

    conversacion.avanzar('CONFIRMAR_CANCELACION')

    return [
        botones(f'{encabezado}\n\n{describir_cita(cita)}', OPCIONES_CANCELACION)
    ]


def manejar_confirmar_cancelacion(conversacion, entrada):
    elegido = elegir_opcion(entrada, OPCIONES_CANCELACION)

    if not elegido:
        return mostrar_confirmar_cancelacion(
            conversacion,
            encabezado='No reconocí tu respuesta. ¿Cancelamos esta cita?'
        )

    if elegido == 'NO_CANCELAR':
        return volver_al_menu(conversacion, 'Perfecto, tu cita sigue en pie. 👍')

    cita = cita_elegida(conversacion)

    if not cita:
        return volver_al_menu(conversacion, 'No encontré esa cita.')

    try:
        cita.cancelar()
    except ValidationError as e:
        return volver_al_menu(
            conversacion,
            f'No se pudo cancelar: {e.messages[0]}'
        )

    return volver_al_menu(conversacion, '✅ Tu cita fue cancelada.')