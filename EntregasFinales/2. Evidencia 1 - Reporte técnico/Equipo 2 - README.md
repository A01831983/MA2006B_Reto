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
criptográficas, mientras que el frontend dar la interfaz del usuario. El sistema cuenta con un
módulo de autenticación basado en JWT y control de acceso por roles (RBAC) con cuatro niveles
jerárquicos (Administrador, Coordinador, Operativo, Captura).

## Requisitos de instalación
### Instalación de las bibliotecas de Python necesarias
Se recomienda usar Python 3.6.13 porque es la versión utilizada para las pruebas.
Ejecuta el comando `pip install -r requirements.txt` en la terminal.

### Configuración del entorno de autenticación
Antes de la primera ejecución, ejecuta `python setup_auth.py`. Este script genera un archivo
`.env` con una clave secreta aleatoria utilizada para firmar los tokens JWT. El archivo `.env`
se excluye del repositorio por seguridad, así que cada miembro del equipo debe generar el suyo.

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

### Primer acceso al sistema
La primera vez que se inicia el servidor sin credenciales registradas en la tabla de
autenticación, el sistema asigna automáticamente una contraseña inicial al usuario administrador:

- **Correo:** `admin@casamonarca.mx`
- **Contraseña:** `admin123`

Si la base de datos ya contiene un usuario con el correo `admin@casamonarca.mx` (por ejemplo,
si se usó `examples/create_dummy_data.py` para generar datos de ejemplo), el sistema reutiliza
ese usuario y le asigna la contraseña inicial. En caso contrario, crea un nuevo administrador
con ese correo.

Por motivos de seguridad, el sistema obliga a cambiar esta contraseña en el primer inicio de
sesión. La página web está disponible en `http://localhost:8000/login`.

### Registro de nuevos usuarios
Desde el panel del administrador (o coordinador), al registrar un nuevo usuario el sistema
genera automáticamente una contraseña temporal aleatoria y la muestra en pantalla. El
administrador debe comunicarla al nuevo usuario, quien estará obligado a cambiarla en su primer
inicio de sesión. La contraseña no se vuelve a mostrar después de cerrar el aviso.

### Permisos por nivel
El sistema implementa control de acceso por roles. Las acciones permitidas dependen del nivel
del usuario que las solicita:

| Rol                  | Crea usuarios          | Edita usuarios                                  | Elimina | Revoca certificados |
| -------------------- | ---------------------- | ----------------------------------------------- | ------- | ------------------- |
| Administrador (N1)   | Cualquier nivel        | Cualquiera                                      | Sí      | Sí                  |
| Coordinador (N2)     | Solo Operativo/Captura | Solo Operativo/Captura de su mismo departamento | No      | No                  |
| Operativo (N3)       | No                     | No                                              | No      | No                  |
| Captura (N4)         | No                     | No                                              | No      | No                  |

Estas restricciones se aplican tanto en la interfaz (ocultando opciones no disponibles) como
en el backend (rechazando peticiones no autorizadas con un código 403). Los operativos y los
usuarios de captura sólo pueden consultar su propio perfil.

### Interfaz para debugging y documentación
Hay una interfaz para debugging que también incluye documentación en `http://localhost:8000/api/docs`.

## Notas sobre los datos generados por examples/create_dummy_data.py
Los usuarios creados por el script `create_dummy_data.py` no tienen contraseña asignada en la
tabla de autenticación, por lo que no pueden iniciar sesión directamente. Sólo el administrador
inicial puede iniciar sesión inmediatamente con la contraseña `admin123`. Desde la interfaz web,
el administrador puede crear y gestionar nuevos usuarios, que recibirán una contraseña temporal
generada automáticamente al momento del registro.