from .bot import procesar_mensaje


def mostrar_respuesta(respuesta):
    print(f"🤖 {respuesta['texto']}")

    if respuesta['tipo'] in ('botones', 'lista'):
        for id_opcion, titulo in respuesta['opciones']:
            print(f"   [{titulo}]  → {id_opcion}")


def simular(telefono, entrada, nombre='Cliente Prueba'):
    print(f"👤 {entrada}")

    for respuesta in procesar_mensaje(telefono, entrada, nombre):
        mostrar_respuesta(respuesta)

    print()


def chat(telefono, nombre='Cliente Prueba'):
    print("Chat simulado. Escribe 'exit' para terminar.\n")

    while True:
        entrada = input('👤 ')

        if entrada.strip().lower() == 'exit':
            break

        for respuesta in procesar_mensaje(telefono, entrada, nombre):
            mostrar_respuesta(respuesta)

        print()