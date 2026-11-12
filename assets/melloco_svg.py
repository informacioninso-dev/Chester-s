"""Genera el dibujo de Melloco (pedidos/static/pedidos/img/melloco.svg) en el estilo de Chester.

Referencia: assets/melloco-original.png. Uso:
    python assets/melloco_svg.py pedidos/static/pedidos/img/melloco.svg
"""
import math, sys

INK = "#1E1B18"

def peludo(cx, cy, rx_top, rx_bot, ry_top, ry_bot, puntas, amp, semilla=1, amp_abajo=None, desde=0.0, hasta=2 * math.pi):
    """Contorno ovalado con mechones en punta. amp_abajo da mechones más largos en la mitad de abajo."""
    pts = []
    n = puntas * 2
    for i in range(n + 1):
        t = desde + (hasta - desde) * i / n
        s, c = math.sin(t), math.cos(t)
        rx = rx_bot if s > 0 else rx_top
        ry = ry_bot if s > 0 else ry_top
        x, y = cx + rx * c, cy + ry * s
        if i % 2:  # punta del mechón
            a = (amp_abajo if (amp_abajo and s > 0.2) else amp)
            a *= 0.75 + 0.5 * ((i * 37 + semilla * 11) % 7) / 6  # variación irregular
            nx, ny = c / rx, s / ry
            norma = math.hypot(nx, ny)
            x, y = x + a * nx / norma, y + a * ny / norma
        pts.append((x, y))
    return pts

def ruta(pts, cerrar=True):
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}" + "".join(f"L{x:.1f} {y:.1f}" for x, y in pts[1:])
    return d + ("Z" if cerrar else "")

def ruta_suave(pts, cerrar=True):
    """Puntos alternos base/punta -> mechones redondeados (curva cuadrática por la punta)."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1, 2):
        (cx, cy), (x, y) = pts[i], pts[i + 1]
        d += f"Q{cx:.1f} {cy:.1f} {x:.1f} {y:.1f}"
    return d + ("Z" if cerrar else "")

cabeza = ruta_suave(peludo(240, 238, 128, 122, 130, 146, 24, 22, amp_abajo=44, semilla=3))
hocico = ruta_suave(peludo(240, 314, 72, 64, 44, 58, 12, 14, amp_abajo=30, semilla=5))
pecho = ruta_suave(peludo(240, 480, 150, 150, 110, 60, 8, 18, semilla=2, desde=math.pi, hasta=2 * math.pi), cerrar=False) + "L390 480L90 480Z"

def ceja(cx, cy, lado):
    """Mechón de ceja como el de Chester: más alto hacia afuera, con puntas suaves."""
    arriba = []
    for i in range(7):
        t = i / 6
        x = cx + lado * (-30 + 64 * t)
        y = cy - 8 - 4 * t - (12 if i % 2 else 0)
        arriba.append((x, y))
    d = ruta_suave(arriba, cerrar=False)
    ex, ey = arriba[-1]
    d += f"Q{cx + lado * 30:.1f} {cy + 2:.1f} {cx - lado * 30:.1f} {cy + 4:.1f}Z"
    return d

def oreja(lado):
    # lado = -1 izquierda, 1 derecha. Cuelga desde arriba de la cabeza, con flecos abajo.
    x0 = 240 + lado * 70
    puntos = [(x0, 120)]
    puntos += [(240 + lado * 140, 112), (240 + lado * 182, 156), (240 + lado * 192, 236)]
    # flecos de la punta
    base = [(240 + lado * 188, 290), (240 + lado * 172, 324), (240 + lado * 150, 334), (240 + lado * 130, 316)]
    flecos = []
    for i, (x, y) in enumerate(base):
        flecos.append((x, y))
        if i < len(base) - 1:
            nx, ny = base[i + 1]
            flecos.append(((x + nx) / 2 + lado * 6, (y + ny) / 2 + 16))
    puntos += flecos
    puntos += [(240 + lado * 120, 270), (240 + lado * 116, 200), (x0, 150)]
    return ruta(puntos)

def oreja_sombra(lado):
    return ruta([(240 + lado * 140, 136), (240 + lado * 172, 176), (240 + lado * 178, 250), (240 + lado * 166, 300),
                 (240 + lado * 148, 306), (240 + lado * 136, 262), (240 + lado * 134, 190)])

hueso = """
  <g fill="{c}">
    <circle cx="222" cy="452" r="{r}"/><circle cx="222" cy="466" r="{r}"/>
    <circle cx="258" cy="452" r="{r}"/><circle cx="258" cy="466" r="{r}"/>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>
  </g>"""

pompones = [(206, 104, "#EF6FA0"), (226, 98, "#9B7AD8"), (246, 93, "#E53935"), (266, 89, "#8BC34A"), (286, 86, "#64B5F6")]

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" role="img" aria-labelledby="t">
  <title id="t">Melloco, perrito blanco despeinado con gorro de cumpleaños y collar rojo</title>
  <!-- Ilustración en el estilo de la de Chester (contorno grueso, colores planos, fondo crema).
       Generada con assets/melloco_svg.py: editar el script y regenerar, no el SVG a mano. -->
  <rect width="480" height="480" fill="#F2E5D3"/>

  <!-- Pecho y collar -->
  <path d="{pecho}" fill="#FFFDF9" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
  <path d="M138 404C190 432 290 432 342 404L348 430C292 462 188 462 132 430Z" fill="#E2342D" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
  <path d="M240 436V448" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
  {hueso.format(c=INK, r=11, x=218, y=446, w=44, h=26)}
  {hueso.format(c="#E2342D", r=7, x=221, y=450, w=38, h=18)}

  <!-- Orejas (detrás de la cabeza) -->
  <g stroke="{INK}" stroke-width="7" stroke-linejoin="round">
    <path d="{oreja(-1)}" fill="#F0DAB6"/>
    <path d="{oreja(1)}" fill="#F0DAB6"/>
  </g>
  <path d="{oreja_sombra(-1)}" fill="#E3C493"/>
  <path d="{oreja_sombra(1)}" fill="#E3C493"/>

  <!-- Cabeza despeinada -->
  <path d="{cabeza}" fill="#FFFDF9" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>

  <!-- Sombras grises del pelo, como la barba de Chester -->
  <path d="{hocico}" fill="#EEE8DF"/>
  <g fill="none" stroke="#D2C9BD" stroke-width="4" stroke-linecap="round">
    <path d="M150 240c6 12 8 26 4 40"/><path d="M330 240c-6 12-8 26-4 40"/>
    <path d="M186 356l-4 18"/><path d="M212 366l-2 18"/><path d="M240 370v18"/><path d="M268 366l2 18"/><path d="M294 356l4 18"/>
    <path d="M204 148c10-6 22-8 34-6"/><path d="M262 140c8 0 16 2 22 6"/>
  </g>

  <!-- Ojos -->
  <g fill="#211611" stroke="{INK}" stroke-width="3">
    <circle cx="196" cy="252" r="21"/><circle cx="284" cy="252" r="21"/>
  </g>
  <g fill="#FFFFFF">
    <circle cx="189" cy="244" r="7"/><circle cx="203" cy="260" r="3"/>
    <circle cx="277" cy="244" r="7"/><circle cx="291" cy="260" r="3"/>
  </g>

  <!-- Cejas de pelo -->
  <g fill="#FFFDF9" stroke="{INK}" stroke-width="5" stroke-linejoin="round">
    <path d="{ceja(196, 222, -1)}"/><path d="{ceja(284, 222, 1)}"/>
  </g>

  <!-- Nariz y boca -->
  <path d="M208 300C208 280 272 280 272 300C272 320 256 332 240 332C224 332 208 320 208 300Z" fill="#3C2522" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
  <ellipse cx="228" cy="292" rx="11" ry="5.5" fill="#8E6D65"/>
  <path d="M240 332v10M220 342c10 9 30 9 40 0" fill="none" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>

  <!-- Gorro de cumpleaños, pequeño y ladeado -->
  <path d="M202 106L262 14L292 86Z" fill="#5AA9E6" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
  <path d="M262 14L292 86L270 90Z" fill="#3E8FD1"/>
  <path d="M202 106L262 14L292 86Z" fill="none" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
  <g fill="{INK}">
    <circle cx="263" cy="16" r="15"/>
    {"".join(f'<circle cx="{x}" cy="{y}" r="13"/>' for x, y, _ in pompones)}
  </g>
  <circle cx="263" cy="16" r="10" fill="#FFFFFF"/>
  {"".join(f'<circle cx="{x}" cy="{y}" r="8.5" fill="{c}"/>' for x, y, c in pompones)}
</svg>
"""
open(sys.argv[1], "w", encoding="utf-8", newline="\n").write(svg)
print(len(svg), "bytes")
