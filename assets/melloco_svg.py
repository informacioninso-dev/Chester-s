"""Genera el dibujo de Melloco (pedidos/static/pedidos/img/melloco.svg) en el estilo de Chester.

Referencia: assets/melloco-original.png. Rasgos que tiene que conservar:
cabeza alargada de terrier con hocico largo, pelo de alambre despeinado (mechones
en punta), orejas cortas dobladas hacia adelante color crema, ojos pequeños y
algo caídos, nariz grande rosada-café, bigote y barba largos, collar rojo con
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
CREMA = "#EED6AE"
CREMA_SOMBRA = "#DDBB86"
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


def mechones(base, amplitud, semilla, cerrar=True, inclinacion=0.45):
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
    (240, 120), (292, 124), (330, 146), (346, 190), (348, 240), (356, 288), (350, 336),
    (322, 378), (282, 402), (240, 412), (198, 402), (158, 378), (130, 336), (124, 288),
    (132, 240), (134, 190), (150, 146), (188, 124),
]


def amplitud_cabeza(x, y):
    if y > 330:
        return 19  # barba larga
    if y > 270:
        return 13  # mejillas y bigote
    if y < 160:
        return 19  # coronilla despeinada
    return 9


cabeza = mechones(catmull_rom(CONTORNO_CABEZA, 46), amplitud_cabeza, semilla=7)

# Zona gris del hocico, como la barba sombreada de Chester.
HOCICO = [(240, 262), (284, 274), (310, 306), (306, 352), (276, 384), (240, 394), (204, 384), (174, 352), (170, 306), (196, 274)]
hocico = mechones(catmull_rom(HOCICO, 24), lambda x, y: 14 if y > 330 else 7, semilla=3)

# Pecho de pelo de alambre (solo se ve abajo, a los lados de la barba).
PECHO = [(84, 480), (96, 440), (130, 404), (180, 386), (240, 382), (300, 386), (350, 404), (384, 440), (396, 480)]
pecho = mechones(PECHO, lambda x, y: 11, semilla=11, cerrar=False) + "Z"

# Oreja corta, doblada hacia adelante, que cae junto al ojo (izquierda; la derecha es el espejo).
OREJA = [(186, 130), (150, 122), (112, 136), (94, 162), (98, 192), (110, 224), (124, 256), (140, 276), (154, 264), (160, 228), (168, 186), (184, 152)]
OREJA_SOMBRA = [(146, 136), (118, 152), (112, 178), (122, 212), (134, 244), (146, 254), (150, 222), (156, 180), (156, 150)]

# Bigote: trazos de pelo que caen desde los lados de la nariz.
BIGOTE = [
    "M224 334c-12 10-22 26-26 46", "M230 340c-6 12-10 28-10 44", "M216 328c-16 6-30 20-38 40",
    "M256 334c12 10 22 26 26 46", "M250 340c6 12 10 28 10 44", "M264 328c16 6 30 20 38 40",
]


def ojo(cx, cy, lado):
    """Ojo almendrado y algo caído: párpado de pelo que tapa la parte de arriba."""
    return f"""
  <ellipse cx="{cx}" cy="{cy}" rx="15" ry="14" fill="#231711"/>
  <circle cx="{cx - 5 * lado}" cy="{cy - 1}" r="4.5" fill="#FFFFFF"/>
  <circle cx="{cx + 5 * lado}" cy="{cy + 6}" r="1.8" fill="#FFFFFF"/>
  <path d="M{cx - 20} {cy - 8}Q{cx} {cy - 15} {cx + 20} {cy - 8}L{cx + 22} {cy - 24}Q{cx} {cy - 32} {cx - 22} {cy - 24}Z" fill="{PELO}"/>
  <path d="M{cx - 17} {cy - 7}Q{cx} {cy - 15} {cx + 17} {cy - 7}" fill="none" stroke="{TINTA}" stroke-width="4.5" stroke-linecap="round"/>"""


def ceja(cx, cy, lado):
    """Mechón de ceja despeinado que sube hacia afuera."""
    pts = [(cx + lado * 22, cy + 6), (cx + lado * 8, cy + 4), (cx - lado * 6, cy + 4), (cx - lado * 18, cy + 7)]
    d = mechones(pts, lambda x, y: 8, semilla=int(cx), cerrar=False, inclinacion=0.2)
    return d + f"Q{cx:.0f} {cy + 13:.0f} {cx + lado * 22:.0f} {cy + 6:.0f}Z"


# --------------------------------------------------------------------------- dibujo

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" role="img" aria-labelledby="t">
  <title id="t">Melloco, perrito blanco de pelo despeinado, con collar rojo y corbatita de moño</title>
  <rect width="480" height="480" fill="#F2E5D3"/>

  <!-- Pecho y collar -->
  <path d="{pecho}" fill="{PELO}" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>
  <path d="M146 420C196 444 284 444 334 420L338 438C286 464 194 464 142 438Z" fill="{ROJO}" stroke="{TINTA}" stroke-width="6" stroke-linejoin="round"/>

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

  <!-- Ojos pequeños y tranquilos -->
  {ojo(198, 236, 1)}
  {ojo(282, 236, -1)}

  <!-- Cejas -->
  <g fill="{PELO}" stroke="{TINTA}" stroke-width="5" stroke-linejoin="round">
    <path d="{ceja(194, 200, -1)}"/><path d="{ceja(286, 200, 1)}"/>
  </g>

  <!-- Nariz grande rosada-café -->
  <path d="M208 304C208 284 272 284 272 304C272 324 258 338 240 338C222 338 208 324 208 304Z" fill="#A06C66" stroke="{TINTA}" stroke-width="6" stroke-linejoin="round"/>
  <ellipse cx="230" cy="296" rx="11" ry="5" fill="#CF9F98"/>
  <path d="M224 318c4-3 9-2 10 2M256 318c-4-3-9-2-10 2" fill="none" stroke="#5A3533" stroke-width="5" stroke-linecap="round"/>

  <!-- Bigote que cae a los lados -->
  <g fill="none" stroke="{TRAZO_SOMBRA}" stroke-width="4.5" stroke-linecap="round">
    {"".join(f'<path d="{b}"/>' for b in BIGOTE)}
  </g>
  <path d="M240 338v10M226 352c8 5 20 5 28 0" fill="none" stroke="{TINTA}" stroke-width="4.5" stroke-linecap="round"/>

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
