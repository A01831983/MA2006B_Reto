# Changelog

Todos los cambios notables del proyecto Gestor de Identidades y Firma de Correos se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y el proyecto sigue una numeración de versiones por etapas del reto.

---

## [2.0.0] — 11 de junio de 2026

Segunda entrega del reto. Esta versión consolida el sistema como una plataforma integral que articula tres capacidades: gestión de identidades, autenticación de usuarios y firma criptográfica de comunicaciones institucionales con verificación pública.

### Added

- **Módulo de autenticación de usuarios** basado en tokens JWT (HS256, vigencia 8 horas) y resguardo de contraseñas con bcrypt (factor de costo 12). Incluye:
  - Endpoints `/auth/login`, `/auth/me`, `/auth/change-password`, `/auth/logout`.
  - Generación automática de contraseñas temporales criptográficamente seguras (12 caracteres sobre alfabeto de 56 caracteres).
  - Bandera `must_change_password` que fuerza el cambio de contraseña en el primer acceso.
  - Bootstrap automático del administrador inicial (`admin@casamonarca.mx` / `admin123`).
  - Script `setup_auth.py` para generación inicial del archivo `.env` con la llave secreta JWT.

- **Módulo de firma criptográfica de correos institucionales** (`mail_crypto.py`). Incluye:
  - Firma RSA-PKCS1v15 con SHA-256 calculada en el navegador del firmante mediante `jsrsasign`.
  - Canonicalización del cuerpo del mensaje implementada de manera idéntica en JavaScript y Python.
  - Firma independiente de cada archivo adjunto.
  - Cálculo de huella digital SHA-256 del certificado firmante.
  - Persistencia de mensajes con campos `body_raw` (firmado) y `body` (con pie de página visible).

- **Mecanismo de verificación pública con tokens efímeros.** Para correos enviados a destinatarios externos:
  - Generación de token aleatorio de 128 bits con vigencia 24 horas y un solo uso.
  - Endpoint público `/api/public/verify/<token>` accesible sin credenciales.
  - Plantilla `verify.html` que renderiza el resultado de verificación criptográfica.
  - Protección de confidencialidad: si el token expira o ya fue consumido, no se exponen datos del mensaje.

- **Distinción automática entre destinatarios internos y externos** en el flujo de envío de correos. Los correos internos se verifican desde el panel autenticado; los externos generan el enlace efímero.

- **Cambio automático de visibilidad del módulo de correos según el rol.** Solo Administrador (N1) y Coordinador (N2) pueden redactar y firmar correos.

- **Página de inicio de sesión** (`login.html`) con validaciones locales y manejo de credenciales inválidas.

- **Página de cambio obligatorio de contraseña** (`change_password.html`) con cuatro validaciones independientes.

- **Modal de descarga automática de credenciales** al momento de crear un usuario con privilegios criptográficos: la llave privada y el certificado se descargan al equipo del administrador en el mismo flujo de alta.

- **Función centralizada `canDo(acción, usuarioObjetivo)`** en el frontend para aplicación uniforme de la matriz RBAC.

- **Auth guard** en `index.html`: verificación de sesión JWT al cargar, con redirección automática al login si el token es inválido o expirado.

- **Helper `apiFetch`** que adjunta automáticamente el token Bearer en cada petición y maneja respuestas 401 redirigiendo al login.

- **Tres nuevas tablas en TinyDB:** `auth` (credenciales de autenticación), `mail_messages` (correos firmados con tokens efímeros), `mail_attachments` (adjuntos firmados independientemente).

- **Dependencias añadidas en `requirements.txt`:** PyJWT 1.7.1, bcrypt 3.1.7, python-dotenv 0.20.0.

### Changed

- **Modelo de emisión de certificados X.509:** los certificados ya no se generan en el backend. La emisión se realiza offline mediante la herramienta `gen_cert.py` ejecutada localmente por el administrador. El sistema solo registra el PEM cargado vía drag-and-drop.

- **Rol del módulo `ccore.py`:** transitó de generador interno de certificados a verificador. Sus funciones principales son ahora `extract_user_data` (extrae atributos del subject X.509) y `verify_cert` (valida la firma contra la lista de CAs internas reconocidas).

- **Matriz de permisos RBAC ajustada:**
  - Coordinador (N2) ahora solo puede crear y editar usuarios de niveles N3 y N4, y únicamente dentro de su mismo departamento.
  - Operativo (N3) y Captura (N4) ya no pueden crear usuarios. Solo consultan su propio perfil.
  - Eliminado el alias "voluntario" del enum `LevelEnum`.

- **Renombrado de `main.py` a `run.py`** como punto de entrada del servidor.

- **Panel de correos en `index.html`:** la visibilidad de los correos se ajusta según el rol del usuario en sesión. El administrador ve todos los correos del sistema; el coordinador ve solo aquellos en los que participa como remitente o destinatario.

### Security

- **Las llaves privadas de los usuarios nunca transitan por el servidor.** Tanto la emisión de certificados (offline con `gen_cert.py`) como la firma de correos (en el navegador con `jsrsasign`) operan bajo este principio.

- **Llave secreta JWT aislada del repositorio.** Se carga desde un archivo `.env` excluido del control de versiones; el servidor aborta con error explícito si la variable `JWT_SECRET` no está definida.

- **Doble validación cliente/servidor en todos los endpoints sensibles.** La capa de presentación oculta opciones no autorizadas, y el backend rechaza con código HTTP 403 cualquier operación incompatible con el rol del solicitante.

- **Lookup activo a la base de datos en endpoints sensibles** aunque el token JWT ya contenga el rol del usuario, garantizando que cambios de rol o departamento se reflejen inmediatamente sin esperar la expiración del token.

### Documentation

- Manual de Usuario actualizado a Versión 2 con cobertura de los nuevos flujos: login, cambio obligatorio de contraseña, redacción de correos firmados y verificación pública por destinatarios externos.
- Reporte técnico unificado que integra las Etapas 1 y 2.
- Reporte ejecutivo unificado que integra las Etapas 1 y 2.

---

## [1.0.0] — 15 de mayo de 2026

Primera entrega del reto. Versión fundacional con el módulo de gestión de identidades operativo.

### Added

- **Arquitectura cliente-servidor de tres capas:** presentación (HTML/CSS/JS nativo), lógica (Flask + flask-restx), persistencia (TinyDB).

- **Módulo de gestión de identidades** con operaciones CRUD sobre el padrón de usuarios:
  - Endpoints `/users` con búsqueda por expresiones regulares y rangos de fechas.
  - Validación estricta de sintaxis de correo electrónico mediante la biblioteca `validators`.
  - Validación de unicidad de correo en el padrón.

- **Módulo criptográfico** (`ccore.py`) con generación interna de certificados X.509 v3:
  - Pares de llaves asimétricas RSA configurables hasta 4096 bits.
  - Firma de certificados con SHA-256.
  - Cifrado de llaves privadas en formato PEM mediante AES con contraseña.

- **Endpoints `/certs`** para emisión, consulta y filtrado de certificados.

- **Modelo de Control de Acceso Basado en Roles (RBAC)** con cuatro niveles jerárquicos: Administrador, Coordinador, Operativo, Captura.

- **Enumeraciones estrictas** para departamentos (`DeptEnum`) y niveles jerárquicos (`LevelEnum`).

- **Panel administrativo** (`index.html`) con dashboard de métricas en tiempo real, tabla dinámica del directorio, modales de creación y edición, y visor de certificados.

- **Filtros del directorio** por estado de certificado (activos, revocados, próximos a expirar) y por nivel jerárquico.

- **Documentación interactiva de la API** mediante Swagger UI bajo `/api/docs`.

- **Soporte CORS** para comunicación entre la capa de presentación y el backend.

- **Script `examples/create_dummy_data.py`** para inicialización de la base de datos con datos de prueba (usuarios y certificados predefinidos).

- **Manual de Usuario Versión 1** con guía de instalación, uso del panel y operaciones del módulo de identidades.

- **Reporte técnico y ejecutivo** correspondientes a la Etapa 1.

### Stack tecnológico inicial

- Python 3.6.13 (constraint del hosting compartido HostGator).
- Flask 1.1.2, flask-restx 0.3.0, flask-swagger-ui 3.36.0, flask-cors 3.0.10.
- cryptography 3.4.7 para operaciones criptográficas.
- TinyDB 4.4.0 como base de datos basada en archivos JSON.
- validators 0.18.2 para validación de correos electrónicos.

---

## Próximas versiones

Líneas de trabajo identificadas para iteraciones futuras (no comprometidas a fecha específica):

- Persistencia de la Lista de Revocación de Certificados (CRL) en el backend.
- Cifrado obligatorio de llaves privadas distribuidas a los colaboradores.
- Autenticación Multifactor (MFA) mediante códigos TOTP.
- Rate limiting explícito en endpoints de autenticación.
- Validación de contraseñas contra listas públicas de credenciales comprometidas.
- Configuración del sistema para despliegue productivo en hosting compartido.
- Migración del motor de persistencia desde TinyDB hacia MySQL.
- Convergencia a largo plazo con tecnología Blockchain para auditorías inmutables.
