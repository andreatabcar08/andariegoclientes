# # ✈️ Andariego — Sistema de Gestión de Viajes

## Proyecto Final — BI para decisiones estratégicas 2026-1

## Integrantes

* Andrea Tabares Cardona
* Mateo Londoño Arango


# Descripción del sistema

**Andariego** es una aplicación de gestión de viajes el cual permite administrar reservas turísticas integrando vuelos, hoteles, transporte terrestre y pagos dentro de una base de datos Oracle.

La solución cuenta con:

* Base de datos relacional en Oracle SQL.
* Aplicación web desarrollada en Streamlit.
* Gestión de clientes y reservas.
* Panel administrativo para la agencia.
* Persistencia de información mediante Oracle Cloud.

El objetivo principal es centralizar la operación de una agencia de viajes mediante una arquitectura de datos estructurada y reglas de negocio implementadas directamente en la base de datos.

---

# Dominio del negocio

El dominio escogido corresponde a una **agencia de viajes y turismo**.

La aplicación permite:

* Registrar clientes.
* Gestionar destinos turísticos.
* Administrar vuelos y transporte terrestre.
* Gestionar hoteles y habitaciones.
* Crear reservas completas.
* Registrar pagos.
* Consultar información de clientes y reservas.

Este dominio fue seleccionado porque requiere múltiples relaciones entre entidades, manejo de integridad referencial y validaciones de negocio complejas, lo que permite aplicar adecuadamente los conceptos trabajados durante el curso.

---

# Arquitectura de la base de datos

La base de datos fue diseñada bajo un modelo relacional normalizado.

## Principales tablas

| Tabla                     | Descripción                         |
| ------------------------- | ----------------------------------- |
| av_paises                 | Catálogo de países disponibles      |
| av_ciudades               | Ciudades asociadas a un país        |
| av_aerolineas             | Aerolíneas registradas              |
| av_aeropuertos            | Aeropuertos asociados a ciudades    |
| av_clientes               | Información de clientes             |
| av_hoteles                | Hoteles disponibles                 |
| av_habitaciones           | Habitaciones de cada hotel          |
| av_vuelos                 | Vuelos disponibles                  |
| av_transportes_terrestres | Transporte terrestre                |
| av_reservas               | Reserva principal del cliente       |
| av_reserva_pasajeros      | Pasajeros asociados a una reserva   |
| av_reserva_vuelos         | Vuelos incluidos en la reserva      |
| av_reserva_hospedajes     | Hospedajes incluidos en la reserva  |
| av_reserva_transportes    | Transportes incluidos en la reserva |
| av_pagos                  | Pagos realizados                    |
| av_notas_cancelacion      | Registro de cancelaciones           |

---

# Restricciones y reglas de negocio implementadas

## Restricciones NOT NULL

Se implementaron para garantizar información obligatoria del negocio.

Ejemplos:

* Nombre de cliente.
* Número de documento.
* Fecha de salida de vuelos.
* Precio de servicios.
* País asociado a una ciudad.

### Justificación

Estas restricciones aseguran que no existan registros incompletos que afecten la operación del sistema.

---

## Restricciones UNIQUE

Se utilizaron para evitar duplicados.

Ejemplos:

* Código ISO de países.
* Código IATA de aeropuertos.
* Documento del cliente.
* Número de habitación por hotel.

### Justificación

Garantizan la unicidad de entidades clave dentro del sistema.

---

## Restricciones CHECK

Se implementaron validaciones de negocio.

Ejemplos:

* Estados válidos: ACTIVO / INACTIVO.
* Continentes permitidos.
* Tipos de documento válidos.
* Rango de estrellas para hoteles.
* Valores permitidos para tipos de transporte.

### Justificación

Permiten controlar la calidad y consistencia de los datos almacenados.

---

## Integridad referencial

Se implementaron múltiples claves foráneas para garantizar consistencia entre tablas.

Ejemplos:

* Un cliente pertenece a un país.
* Un hotel pertenece a una ciudad.
* Una reserva pertenece a un cliente.
* Un vuelo pertenece a una aerolínea.
* Los pagos pertenecen a una reserva.

### Justificación

Evita registros huérfanos y asegura relaciones válidas entre entidades.

---

# Datos de prueba

El proyecto incluye scripts DML con datos de prueba representativos.

Los datos cargados permiten:

* Crear reservas reales.
* Visualizar vuelos y hoteles.
* Registrar pagos.
* Consultar clientes y reservas.
* Probar restricciones y validaciones.

Cada tabla principal contiene al menos 5 registros coherentes.

---

# Aplicación en Streamlit

La aplicación fue desarrollada en Streamlit y conectada a Oracle Cloud mediante la librería `oracledb`.

## Vista del cliente

La vista del cliente permite:

* Registro e inicio de sesión.
* Exploración de destinos.
* Consulta de vuelos.
* Consulta de hoteles.
* Consulta de transporte terrestre.
* Creación de reservas.
* Visualización de reservas propias.
* Registro de pagos.

### Funcionalidades principales

| Funcionalidad    | Descripción                                  |
| ---------------- | -------------------------------------------- |
| Lectura de datos | Consultas SELECT con filtros y visualización |
| Escritura        | Registro de clientes, reservas y pagos       |
| Validaciones     | Fechas válidas, saldos, acompañantes         |
| Interfaz         | Navegación mediante menú lateral             |

---

## Vista administrativa

La vista administrativa permite gestionar la operación de la agencia.

### Funcionalidades

* Gestión de países.
* Gestión de ciudades.
* Gestión de aeropuertos.
* Gestión de aerolíneas.
* Gestión de hoteles y habitaciones.
* Gestión de vuelos.
* Gestión de transporte terrestre.
* Consulta de clientes.
* Consulta y eliminación de reservas.
* Consulta y eliminación de pagos.
* Dashboard con KPIs.

### KPIs implementados

* Número de países.
* Número de hoteles.
* Número de vuelos.
* Número de clientes.
* Total de reservas.
* Reservas activas.
* Ingresos recaudados.

---


# Dificultades encontradas

Durante el desarrollo del proyecto se presentaron diferentes retos técnicos:

* Configuración de Oracle Instant Client.
* Manejo de claves foráneas y restricciones.
* Diseño correcto de relaciones entre reservas y servicios.
* Control de transacciones en Oracle.
* Manejo de errores en Streamlit.
* Conexión entre Python y Oracle Cloud.

También fue necesario realizar pruebas constantes para garantizar que los scripts DDL y DML pudieran ejecutarse desde cero sin errores.

---

# Aprendizajes del proyecto

El desarrollo del sistema permitió aplicar de manera práctica los conceptos vistos en clase:

* Modelado relacional.
* Integridad referencial.
* Restricciones SQL.
* Programación en Python.
* Integración entre frontend y base de datos.
* Gestión de transacciones.
* Desarrollo de aplicaciones de datos.
* Trabajo colaborativo con GitHub.

Además, el proyecto permitió comprender cómo una base de datos bien diseñada soporta procesos reales de negocio y facilita la toma de decisiones.
✔️ Documentación en GitHub
