# Requisitos del Sistema de Gestión para Peluquería

## 1. Introducción

### 1.1 Propósito

El sistema tiene como propósito facilitar y centralizar la gestión operativa y administrativa de la peluquería, integrando en una única plataforma la administración de clientes, peluqueros, citas, inventario, ventas, gastos, caja, marketing y gestión financiera.

Uno de los objetivos principales del sistema es garantizar que la información y relación con los clientes pertenezca al negocio y no quede ligada exclusivamente a un peluquero determinado. El sistema deberá mantener la información de los clientes dentro de la base de datos de la peluquería, independientemente del peluquero que los atienda habitualmente.

De esta manera, ante la finalización de la relación laboral o comercial con un peluquero, la peluquería conservará el registro e historial de sus clientes, permitiendo continuar gestionando su atención, comunicación y fidelización desde el negocio.

### 1.2 Alcance del sistema

El sistema permitirá centralizar y gestionar las principales operaciones de la peluquería, incluyendo:

* Registro y administración de clientes.
* Gestión de peluqueros y usuarios del sistema.
* Gestión de servicios ofrecidos por la peluquería.
* Gestión de citas y turnos.
* Registro de los servicios realizados por los peluqueros.
* Gestión y control del inventario.
* Registro de productos vendidos.
* Registro de insumos utilizados en los servicios.
* Gestión de ingresos y gastos.
* Control y cuadre de caja.
* Gestión de promociones y campañas de marketing.
* Comunicación con clientes mediante canales digitales.
* Gestión de convenios con organizaciones externas.
* Generación de reportes y estadísticas para la administración.

El registro de clientes deberá poder realizarse directamente por los propios clientes, evitando que la información dependa exclusivamente del personal de la peluquería.

Las citas podrán ser solicitadas mediante canales digitales o mediante WhatsApp. El canal definitivo para la gestión de citas deberá definirse posteriormente durante el diseño del sistema.

Inicialmente, los pagos serán registrados en el establecimiento mediante los métodos de pago disponibles en el local. El procesamiento de pagos en línea se considera una funcionalidad para una etapa futura.

La gestión financiera inicial estará orientada al control de ingresos, gastos, caja y ganancias. La integración con sistemas de facturación electrónica y servicios del SRI queda fuera del alcance inicial y podrá incorporarse en una futura versión.

El sistema deberá permitir el envío de comunicaciones y promociones a los clientes mediante WhatsApp y correo electrónico, sujeto a la disponibilidad e integración de los servicios necesarios.

El inventario deberá contemplar tanto productos destinados a la venta como insumos utilizados durante la prestación de los servicios.

### 1.3 Objetivos

#### Objetivo general

Centralizar y automatizar la gestión operativa y administrativa de la peluquería mediante un sistema que permita administrar clientes, peluqueros, citas, inventario, ventas y gestión financiera, manteniendo la información de los clientes como propiedad del negocio.

#### Objetivos específicos

* Centralizar la información de los clientes en una base de datos perteneciente al negocio.
* Permitir que los clientes puedan registrarse directamente en el sistema.
* Registrar y gestionar las citas y turnos de los clientes.
* Mantener un historial de los servicios realizados a cada cliente.
* Registrar los servicios realizados por cada peluquero.
* Registrar las ventas de productos realizadas por los peluqueros.
* Controlar el stock de productos e insumos.
* Diferenciar los ingresos provenientes de servicios de los provenientes de productos.
* Registrar y clasificar los gastos del negocio.
* Facilitar el cuadre y control de caja.
* Permitir la creación y gestión de promociones.
* Facilitar el envío de comunicaciones mediante WhatsApp y correo electrónico.
* Gestionar convenios con organizaciones externas.
* Proporcionar información estadística y financiera para apoyar la toma de decisiones.
* Diseñar el sistema de manera modular para facilitar su mantenimiento y futuras ampliaciones.

## 2. Descripción general del sistema

### 2.1 Contexto

La peluquería requiere una plataforma que permita centralizar la información y automatizar parte de sus procesos operativos y administrativos.

Actualmente, determinadas actividades se realizan mediante comunicación directa por WhatsApp y atención presencial, mientras que el control de clientes, ventas, inventario y finanzas requiere una mayor centralización.

El sistema busca establecer una fuente única de información para el negocio, evitando que los datos relevantes dependan de un peluquero específico.

El sistema deberá contemplar inicialmente un flujo aproximado de 10 clientes diarios y 224 cortes mensuales, además del volumen variable generado por la venta de productos y los convenios externos.

### 2.2 Actores del sistema

Los actores iniciales identificados son:

#### Administrador

Responsable de la gestión general del negocio y del sistema.

Podrá gestionar:

* Clientes.
* Peluqueros.
* Servicios.
* Inventario.
* Ventas.
* Gastos.
* Caja.
* Promociones.
* Convenios.
* Reportes.
* Configuración general del negocio.

#### Peluquero

Utiliza el sistema para registrar y gestionar las actividades relacionadas con los servicios que realiza.

Podrá:

* Consultar sus citas y turnos.
* Registrar los servicios realizados.
* Registrar productos vendidos.
* Consultar información necesaria para atender al cliente.
* Consultar la información relacionada con sus pagos o remuneración, según las reglas definidas por el administrador.

#### Cliente

Interactúa directamente con el sistema para:

* Registrarse.
* Consultar o solicitar citas.
* Consultar información relacionada con sus citas.
* Recibir comunicaciones y promociones.
* Mantener su información personal asociada al negocio.

#### Mantenimiento

Responsable de tareas técnicas y de configuración relacionadas con el funcionamiento de la plataforma.

Sus permisos deberán estar restringidos a las funciones técnicas que sean necesarias y no deberán otorgarle automáticamente acceso a información financiera o administrativa sensible.

### 2.3 Módulos principales

El sistema estará compuesto inicialmente por los siguientes módulos:

1. **Usuarios y roles**
2. **Clientes**
3. **Servicios**
4. **Citas y turnos**
5. **Inventario**
6. **Ventas**
7. **Gastos**
8. **Caja**
9. **Marketing y fidelización**
10. **Convenios**
11. **Reportes y estadísticas**

Los módulos podrán ampliarse o dividirse posteriormente de acuerdo con las necesidades detectadas durante el desarrollo.

## 3. Requisitos funcionales

### 3.1 Gestión de usuarios y roles

### 3.2 Gestión de clientes

### 3.3 Gestión de servicios

### 3.4 Gestión de citas y turnos

### 3.5 Gestión de inventario

### 3.6 Gestión de ventas

### 3.7 Gestión de gastos

### 3.8 Gestión de caja

### 3.9 Gestión de promociones y fidelización

### 3.10 Gestión de convenios

### 3.11 Reportes y estadísticas

## 4. Requisitos no funcionales

### 4.1 Seguridad

### 4.2 Rendimiento

### 4.3 Disponibilidad

### 4.4 Mantenibilidad

### 4.5 Escalabilidad

### 4.6 Usabilidad

### 4.7 Respaldo y recuperación

## 5. Reglas de negocio

## 6. Restricciones

## 7. Supuestos

## 8. Riesgos iniciales

## 9. Criterios de aceptación
