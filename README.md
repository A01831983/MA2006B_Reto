# Reto: Uso de álgebras modernas para seguridad y criptografía, Grupo 603, Equipo 2

## Integrantes
| Nombre                            | Matrícula |
| --------------------------------- | --------- |
| Alberto Boughton Reyes            | A01178500 |
| Diego Octavio Arias Incháustegui  | A00838285 |
| Fernando Daniel Saucedo Hernández | A01385490 |
| Valeria Arciga Valencia           | A01737555 |
| Ximena Montes Bautista            | A01737949 |
| Henning Arvid Ladewig             | A01831983 |

## Descripción breve
Este proyecto es el reto del curso MA2006B durante FJ26 en Tec de Monterrey, Campus Monterrey.
El objetivo es desarrollar un sistema de gestion de identidades para el Socio Formador, Casa Monarca.

## Arquitectura
Nuestra arquitectura involucra el servidor facilitando el backend en combinación con las funciones
criptográficas, mientras que el frontend dar la interfaz del usuario.

## Requisitos de instalación
### Instalación de las bibliotecas de Python necesarias
Se recomienda usar Python 3.6.13 porque es la versión utilizada para las pruebas.
Ejecuta el comando `pip install -r requirements.txt` en la terminal.

## Ejecución
### Generación de ejemplos
Para generar datos de ejemplos con que se puede iniciar el servidor, ejecuta
`python examples/create_dummy_data.py`.
Entonces, entre otros, hay los archivos `examples/dummy.json` como banco de datos,
`examples/srv_cert.pem` como certificado del servidor, y `examples/srv_key.pem` como clave
privada del servidor.

### Ejecución del servidor
Para iniciar el servidor, solo se tiene que ejecutar
`python run.py --db <database file> --cert <certificate file> --key <private key file>`.
Entonces la página web está disponible en `http://localhost:8000/`.
Para fines de prueba, se puede usar los archivos mencionados (generados por `examples/create_dummy_data.py`).

### Interfaz para debugging y documentación
Hay una interfaz para debugging que también incluye documentación en `http://localhost:8000/api/docs`.
