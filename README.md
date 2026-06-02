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

### Interfaz para debugging y documentación
Hay una interfaz para debugging que también incluye documentación en `http://localhost:8000/api/docs`.

## Notas sobre los datos generados por examples/create_dummy_data.py
Los usuarios creados por el script `create_dummy_data.py` no tienen contraseña asignada en la
tabla de autenticación, por lo que no pueden iniciar sesión directamente. Sólo el administrador
inicial puede iniciar sesión inmediatamente con la contraseña `admin123`. Desde la interfaz web,
el administrador puede crear y gestionar nuevos usuarios.