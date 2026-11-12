# 014 · Equipo: agregar personas sin tecnicismos

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

Para crear un usuario hoy hay que entrar al panel de Django, pasar por dos pantallas y entender "staff", "grupos" y "permisos". El dueño de Chester’s y su gente no son muy tecnológicos. El administrador necesita agregar a alguien en un minuto, desde el celular, y mandarle sus datos de acceso por WhatsApp.

## Criterios de aceptación

- [x] El gestor tiene una pestaña **Equipo** que solo ve el administrador (superusuario).
- [x] **Equipo** lista a cada persona con:
  - su nombre;
  - lo que hace: *Atiende pedidos*, *Cocina* o *Reparte*;
  - si tiene acceso o no;
  - cuándo entró por última vez ("Nunca ha entrado" si no ha entrado).
- [x] **Agregar persona** pide solo:
  - el **nombre**;
  - **qué hace**: casillas con una explicación corta de cada rol, al menos una.
- [x] El **usuario** se crea solo a partir del nombre (`carla`, `carla2`…).
- [x] La **contraseña** se genera sola y es fácil de dictar (palabras y números, por ejemplo `galleta-pelota-siesta-482`).
- [x] Al crearla, la pantalla muestra **una sola vez** el usuario, la contraseña y un **mensaje listo** con el enlace de ingreso, con un botón **"Copiar mensaje"** para pegarlo en WhatsApp.
- [x] En cada persona se puede:
  - cambiar el nombre y lo que hace;
  - **"Nueva contraseña"**, que se muestra una vez, igual que al crear;
  - **"Quitar acceso"** y **"Devolver acceso"**. No se borra a nadie, porque su nombre está en el historial de los pedidos.
- [x] El administrador no puede quitarse el acceso a sí mismo, y a los otros administradores no se les edita desde aquí.
- [x] **Ingresar** no distingue mayúsculas ni espacios en el usuario: "Carla " entra como `carla`.
- [x] Todo queda en el historial de cambios.
- [x] En 375 px no hay scroll lateral, los botones miden 44 px o más y los campos tienen 16 px.

## Fuera de alcance

- Que cada persona cambie su propia contraseña. Por ahora la renueva el administrador.
- Bloqueo por intentos fallidos de ingreso: va en la spec 015 (producción).
- Correos de invitación.

## Notas técnicas

- **Vistas:** en `views_equipo.py`, bajo `/equipo/personas/`, solo para superusuario.
- **Roles:** son los grupos existentes "Atención de pedidos", "Cocina" y "Reparto".
- **Personas nuevas:** no son staff; el gestor no lo necesita.
- **Contraseña:** 3 palabras de una lista de 64 más 3 dígitos, generadas con `secrets`. Unas 262 millones de combinaciones, más el hash de Django.
- **Mostrarla una sola vez:** se guarda un instante en la sesión, se muestra en la página siguiente y se borra.
- **Ingreso:** `AuthenticationForm` con `clean` que busca el usuario sin distinguir mayúsculas (`username__iexact`).

## Resultado

- **130 tests:** 7 nuevos en `EquipoPersonasTests`.
- **Probado en Chrome** emulando un celular de 375 px:
  - ingresar como " JEFE " entra al gestor;
  - al agregar a "Rosa Pérez" en Cocina se crea el usuario `rosa` con una contraseña tipo `pastel-vela-huesito-167` y el mensaje listo para copiar;
  - la ficha de Rosa ofrece "Nueva contraseña" y "Quitar acceso";
  - las cuatro pestañas caben en la cabecera;
  - sin scroll lateral, sin textos de menos de 12 px y sin errores de JavaScript.
