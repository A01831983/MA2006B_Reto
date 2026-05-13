# Reto: Uso de álgebras modernas para seguridad y criptografía, Grupo 603, Equipo 2

## Integrantes
| Nombre                            | Matrícula |
| --------------------------------- | --------- |
| Alberto Boughton Reyes            | A01178500 |
| Diego Octavio Arias Incháustegui  | A00838285 |
| Fernando Daniel Saucedo Hernández | A01385490 |
| Valencia Arciga Valencia          | A01737555 |
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
Antes de la primera ejecución, se tiene que ejecutar `python examples/generate_user_cert.py`,
`python examples/generate_server_cert.py` y `python examples/create_dummy_db.py`.
Después, para iniciar el servidor, solo se tiene que ejecutar `python src/backend/main.py`.
Entonces la página web está disponible en `http://localhost:8000/api`.

### Interfaz para debugging
Hay una interfaz para debugging que también incluye documentación en `http://localhost:8000/docs`.
