# 018 · Seguridad: roles, datos personales y red

**Estado:** borrador
**Fecha:** 2026-11-12

## Qué y por qué

Revisión de seguridad pedida por el dueño (12-nov-2026) antes de abrir el gestor al equipo. Revisé:

- **Código:** roles, accesos, CSRF, XSS y redirecciones.
- **Producción:** cabeceras y cookies.
- **Servidor:** red de Docker, actualizaciones y respaldos.

## Lo que ya está bien

- Todo el gestor exige iniciar sesión y pertenecer al equipo. **Equipo** es solo para el superusuario y el **Recetario** solo lo editan Atención y el superusuario. "Soltar" un pedido funciona solo con los propios.
- Freno de intentos al ingresar al gestor y al panel (spec 016). El panel está en una dirección escondida y `/admin/` da 404.
- HTTPS obligatorio, con las cabeceras HSTS, X-Frame-Options DENY, nosniff, Referrer-Policy y COOP. Cookies `Secure` y `SameSite=Lax`.
- CSRF en todos los formularios y en HTMX. `csrf_exempt` solo está en la API de Binn, que exige token y hoy está apagada.
- Plantillas con escape automático. El único `mark_safe` es el JSON-LD, que ya está escapado. Las redirecciones van solo a direcciones propias.
- Formularios públicos con freno de envíos y campo trampa (spec 002).
- El contenedor corre sin root, con tope de memoria, y no expone puertos: solo lo alcanza Caddy. Los secretos están en `.env.production` con permisos 600.

## Hallazgos y propuesta

### Alta

1. **Red compartida con Licitar.** `chesters-web` está en la red `licitar_default`, junto a la base y el redis de Licitar. Docker permite el tráfico entre contenedores de la misma red, y el redis de Licitar no tiene contraseña. Si alguien comprometiera Chester’s, podría llegar a Licitar.
   - Propuesta: una red propia `chesters` donde solo estén Caddy y `chesters-web`; Caddy queda en las dos redes. Implica un cambio en el `docker-compose.prod.yml` de Licitar y reiniciar Caddy (unos segundos).
   - Como defensa adicional: contraseña en el redis de Licitar (es un cambio en Licitar).
   - No se pudo probar la conexión desde el contenedor (la herramienta lo bloqueó). La conclusión sale de la configuración.
2. **No hay respaldos automáticos.** Solo existen los respaldos manuales de cada despliegue, y están **en el mismo volumen** que la base.
   - Propuesta: respaldo diario fuera del volumen, con rotación, igual que Licitar.
3. **Actualización de seguridad del kernel pendiente.** El servidor tiene `linux-image-6.8.0-149` instalado y espera un reinicio.
   - Propuesta: reiniciar en horario de poco uso. Licitar y Chester’s quedan fuera de línea uno o dos minutos y vuelven solos.

### Media (roles y datos personales)

4. **Cocina y Reparto pueden cambiar cualquier estado:** confirmar pedidos nuevos, **cancelar** pedidos, cobrar y editar la entrega.
   - Propuesta: confirmar y cancelar solo para Atención y el superusuario. Cocina pasa el pedido a cocina; Reparto marca entregado y cobra.
5. **Cocina ve el teléfono y la dirección de las familias**, aunque no los necesita. La LOPDP pide minimizar el acceso a datos personales.
   - Propuesta: ocultarle a quien solo está en Cocina el teléfono, la dirección y el botón de WhatsApp.
6. **Las sesiones duran 2 semanas,** que es el valor por defecto de Django. En celulares o tablets compartidos de la cocina es mucho.
   - Propuesta: 12 horas, renovadas con el uso.
7. **No hay Content-Security-Policy.** Sería una segunda barrera contra XSS. Hay scripts en línea que habría que mover o firmar con un nonce.

### Baja

8. Subir HSTS de 30 días a 1 año cuando el dominio sea el definitivo.
9. La cabecera `Server: gunicorn` revela el software. Es cosmético.
10. Los respaldos manuales de hoy (`respaldo-antes-spec0xx.sqlite3`) tienen datos personales: rotarlos o borrarlos cuando exista el respaldo automático.
11. El freno de ingreso usa la caché local. Sirve mientras gunicorn tenga un solo proceso (anotado en MEMORY).

## Criterios de aceptación

Se definen al aprobar qué hallazgos se implementan.
