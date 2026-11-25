"""Renderiza una cuadrícula de piezas (paleta + filas) como nanobloques de plástico realistas."""
import sys, os, json, math
from PIL import Image, ImageDraw, ImageFilter

def hx(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def mix(c, t, a): return tuple(max(0, min(255, round(c[i] + (t[i] - c[i]) * a))) for i in range(3))
def lighten(c, a): return mix(c, (255, 255, 255), a)
def darken(c, a): return mix(c, (0, 0, 0), a)

def load(path):
    lines = open(path).read().split('\n')
    pal = json.loads(lines[0]); rows = [l for l in lines[1:] if l.strip()]
    return pal, rows

# perfil de una varilla cilíndrica: sombra en bordes, brillo cerca del 35 %
def rod_profile(t):
    shade = -0.28 * (abs(t - 0.5) * 2) ** 2.2
    spec = 0.42 * math.exp(-((t - 0.33) / 0.09) ** 2)
    return shade + spec

def render(pal, rows, out_png, size=800, rods=2):
    w = max(len(r) for r in rows); rows = [r.ljust(w, '.') for r in rows]; h = len(rows)
    filled = lambda r, c: 0 <= r < h and 0 <= c < w and rows[r][c] != '.'
    SS = 2; C = 34 * SS; D = round(C * 0.30); pad = C * 2
    Wd = w * C + D + pad * 2; Ht = h * C + D + pad * 2
    img = Image.new('RGBA', (Wd, Ht), (0, 0, 0, 0)); g = ImageDraw.Draw(img)
    ox, oy = pad, pad + D
    rw = C / rods
    prof = [rod_profile((x + .5) / rw) for x in range(int(rw))]
    for r in range(h - 1, -1, -1):
        for c in range(w):
            ch = rows[r][c]
            if ch == '.': continue
            base = hx(pal[ch]); x, y = ox + c * C, oy + r * C
            if not filled(r, c + 1):
                g.polygon([(x + C, y), (x + C + D, y - D), (x + C + D, y + C - D), (x + C, y + C)], fill=darken(base, .38))
            if not filled(r - 1, c):
                g.polygon([(x, y), (x + D, y - D), (x + C + D, y - D), (x + C, y)], fill=lighten(base, .18))
                for k in range(rods):
                    cx, cy = x + rw * (k + .5) + D / 2, y - D / 2
                    rx, ry, sh = rw * .36, D * .26, C * .10
                    g.rectangle([cx - rx, cy - sh, cx + rx, cy], fill=darken(base, .15))
                    g.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=darken(base, .15))
                    g.ellipse([cx - rx, cy - sh - ry, cx + rx, cy - sh + ry], fill=lighten(base, .30))
            # varillas frontales
            for k in range(rods):
                x0 = x + round(k * rw)
                for i, p in enumerate(prof):
                    col = lighten(base, p) if p > 0 else darken(base, -p)
                    g.line([(x0 + i, y), (x0 + i, y + C - 1)], fill=col)
            # juntas entre capas
            g.line([(x, y + C - 1), (x + C, y + C - 1)], fill=darken(base, .40), width=SS)
            g.line([(x, y + SS), (x + C, y + SS)], fill=lighten(base, .22), width=SS)
            # oclusión bajo una pieza saliente
            if filled(r - 1, c) and not filled(r - 1, c + 1) and filled(r, c + 1):
                pass
    # sombra en el piso
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    by = oy + h * C
    sd.ellipse([ox - C * .3, by - C * .5, ox + w * C + D + C * .3, by + C * .7], fill=(30, 15, 50, 80))
    sh = sh.filter(ImageFilter.GaussianBlur(C * .5)); sh.alpha_composite(img); img = sh.crop(sh.getbbox())
    side = max(img.size); m = round(side * .05); side += 2 * m
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(img, ((side - img.width) // 2, (side - img.height) // 2))
    sq.resize((size, size), Image.LANCZOS).save(out_png)

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    names = sys.argv[3:] or [f[:-4] for f in sorted(os.listdir(src)) if f.endswith('.txt')]
    for n in names:
        pal, rows = load(os.path.join(src, n + '.txt'))
        render(pal, rows, os.path.join(out, n + '.png'))
        print('ok', n)
