# 016 · Freno de intentos al ingresar y panel en otra dirección

**Estado:** en curso
**Fecha:** 2026-11-12

## Qué y por qué

Antes de abrir el gestor al equipo y a clientes reales hay que cerrar dos huecos:

- **Contraseñas sin límite de intentos.** En el ingreso del gestor (`/equipo/ingresar/`) y en el del panel, un bot puede probar contraseñas sin límite.
- **El panel está en `/admin/`.** Es la primera dirección que prueban los bots en cualquier sitio Django.

## Criterios de aceptación

- [x] **Por conexión:** tras **10 intentos fallidos desde la misma conexión (IP)** en 15 minutos, el ingreso se bloquea para esa conexión durante 15 minutos, aunque luego escriba la contraseña correcta.
- [x] **Por usuario:** tras **20 intentos fallidos contra el mismo usuario** en 15 minutos, desde donde sea, ese usuario queda bloqueado 15 minutos.
- [x] **Mensaje claro:** "Demasiados intentos fallidos. Por seguridad, espera 15 minutos y vuelve a intentarlo. Si olvidaste tu contraseña, pídele al administrador una nueva."
- [x] **Ingreso correcto:** reinicia los contadores de esa conexión y de ese usuario.
- [x] **Alcance del freno:** aplica igual en el ingreso del gestor y en el del panel de Django.
- [x] **Usuario o contraseña equivocados:** el gestor muestra "Usuario o contraseña incorrectos. Revisa la contraseña y vuelve a intentarlo." (el usuario ya no distingue mayúsculas, spec 014).
- [x] **Panel en otra dirección:** en producción se sirve en una dirección propia y difícil de adivinar (`DJANGO_ADMIN_URL`, que ya existe). `/admin/` responde 404. El botón "Panel" del gestor apunta solo a la dirección nueva.

## Fuera de alcance

- Verificación en dos pasos y avisos por correo de ingresos sospechosos.

## Notas técnicas

- `pedidos/seguridad.py` escucha la señal `user_login_failed` y suma intentos en la caché por IP y por usuario. La IP sale de la misma función `_ip` de la spec 002, que lee la IP real detrás de Caddy.
- Un mixin en el formulario de ingreso revisa el bloqueo antes de autenticar. Lo usan `IngresoSinMayusculas` (gestor) y el formulario del panel (`admin.site.login_form`).
- La caché es la local de Django. Funciona porque gunicorn corre con un solo proceso (spec 008). Si se suben más procesos, hay que pasar a una caché compartida.
- La dirección del panel se fija en `/opt/chesters/.env.production` y no se guarda en el repo.

## Resultado

- **140 tests:** 4 nuevos en `FrenoDeIngresoTests`:
  - 10 fallos bloquean la conexión, incluso con la contraseña correcta, y otra conexión sí entra;
  - 20 fallos bloquean al usuario desde cualquier conexión;
  - entrar bien reinicia los contadores;
  - el panel frena igual.
- La dirección del panel en producción se fija al desplegar, en `.env.production` (pendiente).
