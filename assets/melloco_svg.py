"""Genera el dibujo de Melloco (pedidos/static/pedidos/img/melloco.svg) en el estilo de Chester.

Referencias: assets/melloco-frente.png (de frente) y assets/melloco-original.png.
Melloco es mestizo, no terrier, medio mechudo y con un copete al centro de la
cabeza. Rasgos que tiene que conservar: pecas color café
claro en la frente y sobre el hocico, orejas blancas con bordes crema, ojos grandes
y brillantes, cara redonda y
ancha con hocico corto, mejillas esponjosas, pelo blanco despeinado pero suave,
orejas crema dobladas que caen a los lados, ojos oscuros redondos y separados con
el borde algo oscuro, nariz grande café rosada con una mancha rosa abajo, collar rojo con
y, como Director de Calidad, una corbatita de moño (pedido del dueño: sin gorrito).

Uso:
    python assets/melloco_svg.py pedidos/static/pedidos/img/melloco.svg
"""
import math
import random
import re
import sys

TINTA = "#1E1B18"
PELO = "#FFFDF8"
SOMBRA = "#E6DFD5"
TRAZO_SOMBRA = "#CFC6BA"
CREMA = "#E6C48F"          # bordes y puntas de las orejas
CREMA_SOMBRA = "#FAF3E7"   # parte blanca de la oreja, junto a la cabeza
PECA = "#C99868"
ROJO = "#E2342D"


# --------------------------------------------------------------------------- utilidades

def catmull_rom(puntos, n):
    """Curva cerrada suave que pasa por `puntos`, muestreada en `n` puntos."""
    salida = []
    k = len(puntos)
    for i in range(n):
        t_global = i / n * k
        j = int(t_global)
        t = t_global - j
        p0, p1, p2, p3 = (puntos[(j + d) % k] for d in (-1, 0, 1, 2))
        t2, t3 = t * t, t * t * t
        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                   + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
        y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                   + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        salida.append((x, y))
    return salida


def mechones(base, amplitud, semilla, cerrar=True, inclinacion=0.45, redondos=False):
    """Contorno de pelo de alambre: entre cada par de puntos de `base` sale un mechón
    en punta, curvo e irregular (largo y caída al azar, con semilla fija)."""
    azar = random.Random(semilla)
    n = len(base)
    tramos = n if cerrar else n - 1
    d = f"M{base[0][0]:.1f} {base[0][1]:.1f}"
    for i in range(tramos):
        a, b = base[i], base[(i + 1) % n]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        tx, ty = b[0] - a[0], b[1] - a[1]
        largo = math.hypot(tx, ty) or 1
        # normal hacia afuera (la curva va en sentido horario en pantalla)
        nx, ny = ty / largo, -tx / largo
        amp = amplitud(mx, my) * (0.6 + 0.8 * azar.random())
        caida = (azar.random() - 0.5) * inclinacion * amp
        px, py = mx + nx * amp + tx / largo * caida, my + ny * amp + ty / largo * caida
        if redondos:  # pelo suave: un bulto redondeado por mechón
            d += f"Q{px + nx * amp * 0.6:.1f} {py + ny * amp * 0.6:.1f} {b[0]:.1f} {b[1]:.1f}"
            continue
        c1x, c1y = (a[0] + px) / 2 + nx * amp * 0.15, (a[1] + py) / 2 + ny * amp * 0.15
        c2x, c2y = (px + b[0]) / 2 - nx * amp * 0.05, (py + b[1]) / 2 - ny * amp * 0.05
        d += f"Q{c1x:.1f} {c1y:.1f} {px:.1f} {py:.1f}Q{c2x:.1f} {c2y:.1f} {b[0]:.1f} {b[1]:.1f}"
    return d + ("Z" if cerrar else "")


def espejo(puntos):
    return [(480 - x, y) for x, y in puntos]


def ruta(puntos, cerrar=True):
    d = f"M{puntos[0][0]:.1f} {puntos[0][1]:.1f}" + "".join(f"L{x:.1f} {y:.1f}" for x, y in puntos[1:])
    return d + ("Z" if cerrar else "")


def suave(puntos, n=40):
    return ruta(catmull_rom(puntos, n))


# --------------------------------------------------------------------------- formas

# Cabeza alargada de terrier: coronilla algo plana, mejillas y barba que se abren hacia abajo.
CONTORNO_CABEZA = [
    (240, 122), (296, 128), (338, 156), (358, 204), (364, 258), (362, 310), (344, 352),
    (308, 384), (272, 398), (240, 402), (208, 398), (172, 384), (136, 352), (118, 310),
    (116, 258), (122, 204), (142, 156), (184, 128),
]


def amplitud_cabeza(x, y):
    if y > 330:
        return 15  # barba
    if y > 260:
        return 14  # mejillas mechudas
    if y < 165:
        return 12  # coronilla
    return 8


cabeza = mechones(catmull_rom(CONTORNO_CABEZA, 40), amplitud_cabeza, semilla=7, redondos=True, inclinacion=0.9)

# Zona gris del hocico, como la barba sombreada de Chester.
HOCICO = [(240, 266), (288, 276), (316, 304), (312, 344), (282, 372), (240, 382), (198, 372), (168, 344), (164, 304), (192, 276)]
hocico = mechones(catmull_rom(HOCICO, 22), lambda x, y: 9 if y > 330 else 5, semilla=3, redondos=True)

# Pecho de pelo de alambre (solo se ve abajo, a los lados de la barba).
PECHO = [(84, 480), (96, 440), (130, 404), (180, 386), (240, 382), (300, 386), (350, 404), (384, 440), (396, 480)]
pecho = mechones(PECHO, lambda x, y: 10, semilla=11, cerrar=False, redondos=True) + "Z"

# Oreja corta, doblada hacia adelante, que cae junto al ojo (izquierda; la derecha es el espejo).
OREJA = [(186, 130), (150, 122), (112, 136), (94, 162), (98, 192), (110, 224), (124, 256), (140, 276), (154, 264), (160, 228), (168, 186), (184, 152)]
OREJA_SOMBRA = [(146, 136), (118, 152), (112, 178), (122, 212), (134, 244), (146, 254), (150, 222), (156, 180), (156, 150)]

# Bigote: trazos de pelo que caen desde los lados de la nariz.
BIGOTE = [
    "M222 340c-10 8-16 18-18 30", "M212 334c-14 6-24 16-30 28",
    "M258 340c10 8 16 18 18 30", "M268 334c14 6 24 16 30 28",
]


def ojo(cx, cy, lado):
    """Ojo almendrado y algo caído: párpado de pelo que tapa la parte de arriba."""
    return f"""
  <circle cx="{cx}" cy="{cy}" r="24" fill="#9A8F88"/>
  <circle cx="{cx}" cy="{cy}" r="20" fill="#1F140F" stroke="{TINTA}" stroke-width="3"/>
  <circle cx="{cx - 6 * lado}" cy="{cy - 7}" r="7" fill="#FFFFFF"/>
  <circle cx="{cx + 7 * lado}" cy="{cy + 7}" r="2.6" fill="#FFFFFF"/>
  <path d="M{cx - 22} {cy - 17}Q{cx} {cy - 25} {cx + 22} {cy - 17}" fill="none" stroke="{TINTA}" stroke-width="3.5" stroke-linecap="round" opacity=".55"/>"""


def ceja(cx, cy, lado):
    """Mechón de ceja despeinado que sube hacia afuera."""
    pts = [(cx + lado * 22, cy + 6), (cx + lado * 8, cy + 4), (cx - lado * 6, cy + 4), (cx - lado * 18, cy + 7)]
    d = mechones(pts, lambda x, y: 8, semilla=int(cx), cerrar=False, inclinacion=0.2)
    return d + f"Q{cx:.0f} {cy + 13:.0f} {cx + lado * 22:.0f} {cy + 6:.0f}Z"


# --------------------------------------------------------------------------- dibujo

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" role="img" aria-labelledby="t">
  <title id="t">Melloco, perrito mestizo blanco con pecas, collar rojo y corbatita de moño</title>
  <rect width="480" height="480" fill="#F2E5D3"/>

  <!-- Pecho y collar -->
  <path d="{pecho}" fill="{PELO}" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>
  <path d="M146 420C196 444 284 444 334 420L338 438C286 464 194 464 142 438Z" fill="{ROJO}" stroke="{TINTA}" stroke-width="6" stroke-linejoin="round"/>
  <g fill="#FFFFFF" opacity=".85">
    <circle cx="160" cy="433" r="2.6"/><circle cx="178" cy="441" r="2.6"/><circle cx="302" cy="441" r="2.6"/><circle cx="320" cy="433" r="2.6"/>
  </g>

  <!-- Cabeza de pelo de alambre -->
  <path d="{cabeza}" fill="{PELO}" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>
  <path d="{hocico}" fill="{SOMBRA}"/>

  <!-- Textura del pelo -->
  <g fill="none" stroke="{TRAZO_SOMBRA}" stroke-width="4" stroke-linecap="round">
    <path d="M170 280c-4 14-4 28 2 40"/><path d="M310 280c4 14 4 28-2 40"/>
    <path d="M196 382l-6 16"/><path d="M220 390l-3 16"/><path d="M260 390l3 16"/><path d="M284 382l6 16"/>
    <path d="M212 160c8-8 18-10 28-8"/><path d="M252 150c10-2 20 2 26 8"/>
    <path d="M214 270c8 4 14 10 16 18"/><path d="M266 270c-8 4-14 10-16 18"/>
  </g>

  <!-- Orejas dobladas hacia adelante -->
  <g stroke="{TINTA}" stroke-width="7" stroke-linejoin="round">
    <path d="{suave(OREJA)}" fill="{CREMA}"/>
    <path d="{suave(espejo(OREJA))}" fill="{CREMA}"/>
  </g>
  <path d="{suave(OREJA_SOMBRA)}" fill="{CREMA_SOMBRA}"/>
  <path d="{suave(espejo(OREJA_SOMBRA))}" fill="{CREMA_SOMBRA}"/>

  <!-- Copete al centro de la cabeza -->
  <path d="M210 140C206 124 212 110 222 102Q226 114 234 120C232 106 240 92 252 86Q254 102 262 114C266 106 274 100 284 98C280 112 276 126 272 140Q240 150 210 140Z"
        fill="{PELO}" stroke="{TINTA}" stroke-width="6" stroke-linejoin="round"/>
  <path d="M206 141Q240 152 274 141L272 150Q240 160 208 150Z" fill="{PELO}"/>
  <g fill="none" stroke="{TRAZO_SOMBRA}" stroke-width="3.5" stroke-linecap="round">
    <path d="M228 130c2-6 4-10 8-14"/><path d="M252 126c2-8 4-14 8-18"/>
  </g>

  <!-- Mechones sueltos en las mejillas -->
  <g fill="none" stroke="{TRAZO_SOMBRA}" stroke-width="4" stroke-linecap="round">
    <path d="M140 300c-6 8-8 16-8 26"/><path d="M152 336c-4 10-4 18-2 26"/>
    <path d="M340 300c6 8 8 16 8 26"/><path d="M328 336c4 10 4 18 2 26"/>
  </g>

  <!-- Pecas color café claro: frente, coronilla y sobre el hocico -->
  <g fill="{PECA}">
    <circle cx="230" cy="168" r="4.5"/><circle cx="252" cy="158" r="3.2"/><circle cx="246" cy="182" r="3.8"/>
    <circle cx="264" cy="176" r="2.6"/><circle cx="216" cy="184" r="2.8"/><circle cx="286" cy="150" r="3"/>
    <circle cx="200" cy="150" r="2.4"/><circle cx="238" cy="206" r="2.6"/>
    <ellipse cx="240" cy="262" rx="9" ry="6"/><circle cx="256" cy="270" r="3"/><circle cx="224" cy="272" r="2.4"/>
  </g>

  <!-- Ojos grandes y brillantes -->
  {ojo(190, 236, 1)}
  {ojo(290, 236, -1)}

  <!-- Cejas -->
  <g fill="{PELO}" stroke="{TINTA}" stroke-width="5" stroke-linejoin="round">
    <path d="{ceja(188, 192, -1)}"/><path d="{ceja(292, 192, 1)}"/>
  </g>

  <!-- Nariz grande rosada-café -->
  <path d="M202 300C202 278 278 278 278 300C278 324 262 340 240 340C218 340 202 324 202 300Z" fill="#8A5A54" stroke="{TINTA}" stroke-width="6" stroke-linejoin="round"/>
  <path d="M226 330C230 320 254 318 260 328C256 336 248 339 240 339C234 339 229 336 226 330Z" fill="#DDA5A1"/>
  <ellipse cx="228" cy="291" rx="12" ry="5" fill="#B88780"/>
  <path d="M220 312c4-3 10-2 11 2M260 312c-4-3-10-2-11 2" fill="none" stroke="#4E2E2B" stroke-width="5" stroke-linecap="round"/>

  <!-- Bigote que cae a los lados -->
  <g fill="none" stroke="{TRAZO_SOMBRA}" stroke-width="4.5" stroke-linecap="round">
    {"".join(f'<path d="{b}"/>' for b in BIGOTE)}
  </g>
  <path d="M240 340v8M228 352c7 4 17 4 24 0" fill="none" stroke="{TINTA}" stroke-width="4.5" stroke-linecap="round"/>

  <!-- Corbatita de moño de Director de Calidad, sobre el collar -->
  <g stroke="{TINTA}" stroke-width="6" stroke-linejoin="round">
    <path d="M240 450L190 424Q178 450 190 476Z" fill="#24406E"/>
    <path d="M240 450L290 424Q302 450 290 476Z" fill="#24406E"/>
  </g>
  <g fill="none" stroke="#1A2F52" stroke-width="3.5" stroke-linecap="round">
    <path d="M206 438l14 8M206 462l14-8"/><path d="M274 438l-14 8M274 462l-14-8"/>
  </g>
  <g fill="#FFFFFF">
    <circle cx="198" cy="440" r="3"/><circle cx="200" cy="462" r="3"/><circle cx="214" cy="451" r="3"/>
    <circle cx="282" cy="440" r="3"/><circle cx="280" cy="462" r="3"/><circle cx="266" cy="451" r="3"/>
  </g>
  <rect x="228" y="437" width="24" height="26" rx="7" fill="#2E5089" stroke="{TINTA}" stroke-width="6"/>
</svg>
"""
svg = re.sub(r"\s*<!--.*?-->", "", svg, flags=re.S)  # el archivo publicado va sin comentarios internos
open(sys.argv[1], "w", encoding="utf-8", newline="\n").write(svg)
print(len(svg), "bytes")
