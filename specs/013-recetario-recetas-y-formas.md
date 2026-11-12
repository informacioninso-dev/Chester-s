# 013 · Recetario: recetas y formas administrables

**Estado:** hecha
**Fecha:** 2026-11-12

## Qué y por qué

Hoy las dos recetas (Carne y puré; Manzana, zanahoria y yogur) y las dos formas (Huesito, Redondo) están fijas en el código. Agregar un pastel nuevo obliga a programar, y el cocinero no tiene en ningún lado la receta que debe seguir.

Proponemos un **Recetario** dentro del gestor, donde la familia de Chester:

- crea, edita y pausa **recetas** y **formas** sin tocar código;
- escribe en cada una **la receta que sigue el cocinero**: ingredientes, pasos y alérgenos;
- decide qué ve el cliente: nombre, descripción corta y si está disponible.

El configurador y el chat muestran solo lo disponible. El cocinero ve la receta y la forma **dentro del detalle de cada pedido**, junto a las alergias del perrito, para no tener que buscarlas.

## Criterios de aceptación

### Recetario (gestor)

- [x] El gestor tiene una tercera sección en la cabecera: **Pedidos · Perritos · Recetario**.
- [x] El Recetario lista las recetas y las formas. Cada una muestra:
  - su nombre;
  - si está **disponible** para clientes;
  - cuántos pedidos la usan.
- [x] **Cada receta tiene:**
  - para el cliente: nombre y descripción corta, por ejemplo "Contundente y casera";
  - para el cocinero: **ingredientes** (uno por línea), **pasos** (uno por línea, se muestran numerados), **contiene** (alérgenos, por ejemplo "Lácteos (yogur)") y notas;
  - si está disponible y en qué orden aparece.
- [x] **Cada forma tiene:**
  - para el cliente: nombre, descripción corta y cómo se dice en el mensaje de WhatsApp (por ejemplo "en forma de huesito");
  - para el cocinero: **cómo armarla** (molde, decoración) y notas;
  - si está disponible y en qué orden aparece.
- [x] Crean y editan **Atención de pedidos** y el superusuario. **Cocina y Reparto** solo leen.
- [x] **No se borra lo que ya se usó:** una receta o forma con pedidos no se puede borrar, solo dejar de estar disponible, para que el historial siga intacto.

### Cliente (configurador y chat)

- [x] El configurador y el chat ofrecen solo las recetas y formas **disponibles**, en su orden, con su nombre y descripción.
- [x] Las dos recetas actuales conservan su dibujo. Las nuevas usan un dibujo genérico de pastel.
- [x] Si no hay ninguna receta o ninguna forma disponible, el pedido no se rompe: el configurador y el chat explican que por ahora no se toman pedidos y ofrecen escribir por WhatsApp.
- [x] El mensaje de WhatsApp usa el nombre de la receta y la frase de la forma configurada.

### Cocina

- [x] El detalle del pedido muestra **"Cómo se hace"**: ingredientes, pasos numerados y "Contiene", con las alergias del perrito al lado. Si la receta contiene algo y el perrito tiene alergias anotadas, se muestra un **aviso para revisar** antes de cocinar.

### Datos

- [x] Los pedidos que ya existen quedan enlazados a sus recetas y formas (migración). Binn sigue recibiendo `receta`, `receta_nombre`, `estilo` y `estilo_nombre` como hoy.

## Fuera de alcance

- Fotos de recetas o formas, precios, porciones por tamaño, inventario y costos.
- Combinaciones prohibidas entre receta y forma.

## Decisiones del dueño (12-nov-2026)

1. El Recetario va **en el gestor, como una pestaña más** (Pedidos · Perritos · Recetario).
2. Una receta nueva **nace pausada** y la ven los clientes cuando se marca "Disponible para clientes". Además va al final de la lista.

## Notas técnicas

- **Modelos nuevos:** `Receta` y `Forma`.
  - Campos: `clave` (slug fijo), `nombre`, `descripcion`, `disponible`, `orden`, `notas` y `creado_en`.
  - Solo `Receta`: `ingredientes`, `pasos` y `contiene`.
  - Solo `Forma`: `frase_mensaje` y `como_armarla`.
- **Cambios en `Cotizacion`:** `receta` y `estilo` pasan a `ForeignKey(PROTECT)`, con la clave como valor del formulario. La migración crea las 4 actuales con las mismas claves y enlaza los pedidos.
- **Formularios:** `PedidoForm` usa `ModelChoiceField` sobre las disponibles. Desaparecen `Receta`/`Estilo` (TextChoices) y `FRASE_ESTILO`.
- **Favoritas de la ficha:** se calculan sobre las FK.
- **Riesgo:** es el cambio más grande desde el configurador. Toca el modelo de pedidos, el configurador, el chat, el mensaje de WhatsApp, Binn y el gestor. Se cubre con tests de punta a punta y respaldo de la base antes de migrar.

## Resultado

- **123 tests:** 10 nuevos en `RecetarioTests`. Se ajustaron 3 de las specs anteriores porque los pedidos ahora apuntan a una receta y una forma, y el mensaje dice "Elige una forma".
- **Migración probada con datos reales:** la base de prueba tenía 5 pedidos y todos quedaron enlazados a su receta y su forma (Luna conservó Manzana y Redondo).
- **Probado de punta a punta en Chrome** emulando un celular de 375 px:
  - se creó "Pollo y arroz" con ingredientes, pasos y "Contiene", y se marcó disponible;
  - el cliente la ve en el configurador con el dibujo genérico;
  - el detalle del pedido muestra "Cómo se hace" con los pasos numerados.
  - Sin scroll lateral, sin textos de menos de 12 px y sin errores de JavaScript.
