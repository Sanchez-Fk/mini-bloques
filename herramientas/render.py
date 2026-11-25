import sys, os, importlib.util
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('sprites', os.path.join(HERE, 'sprites.py'))
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)

def hx(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def mix(c, t, a):
    return tuple(round(c[i] + (t[i] - c[i]) * a) for i in range(3))
def lighten(c, a): return mix(c, (255, 255, 255), a)
def darken(c, a): return mix(c, (0, 0, 0), a)

def render(name, out_dir, size=1000, preview=False):
    pal, rows = sp.SPRITES[name]
    w = max(len(r) for r in rows)
    bad = [i for i, r in enumerate(rows) if len(r) != w]
    if bad: print(f'  ! {name}: rows {bad} width != {w}')
    rows = [r.ljust(w, '.') for r in rows]
    h = len(rows)
    filled = lambda r, c: 0 <= r < h and 0 <= c < w and rows[r][c] != '.'
    SS = 3
    C = 30 * SS
    D = round(C * 0.32)
    pad = C
    W = w * C + D + pad * 2; H = h * C + D + pad * 2 + C
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(img)
    ox, oy = pad, pad + D
    for r in range(h - 1, -1, -1):
        for c in range(w):
            ch = rows[r][c]
            if ch == '.': continue
            if ch not in pal: print(f'  ! {name}: unknown {ch!r} at {r},{c}'); continue
            base = hx(pal[ch])
            x, y = ox + c * C, oy + r * C
            if not filled(r, c + 1):
                g.polygon([(x + C, y), (x + C + D, y - D), (x + C + D, y + C - D), (x + C, y + C)], fill=darken(base, .30))
                g.line([(x + C, y + C), (x + C + D, y + C - D)], fill=darken(base, .42), width=SS)
            if not filled(r - 1, c):
                g.polygon([(x, y), (x + D, y - D), (x + C + D, y - D), (x + C, y)], fill=lighten(base, .22))
                # stud on top
                cx, cy = x + C / 2 + D / 2, y - D / 2
                rx, ry, sh = C * .27, D * .36, C * .13
                g.rectangle([cx - rx, cy - sh, cx + rx, cy], fill=darken(base, .12))
                g.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=darken(base, .12))
                g.ellipse([cx - rx, cy - sh - ry, cx + rx, cy - sh + ry], fill=lighten(base, .38))
                g.ellipse([cx - rx * .55, cy - sh - ry * .7, cx - rx * .05, cy - sh - ry * .1], fill=lighten(base, .6))
            # front face with bevel
            g.rectangle([x, y, x + C - 1, y + C - 1], fill=darken(base, .16))
            b = SS * 2
            g.rectangle([x + b, y + b, x + C - 1 - b, y + C - 1 - b], fill=base)
            g.rectangle([x + b, y + b, x + C - 1 - b, y + b + SS * 2], fill=lighten(base, .18))
            g.rectangle([x + b, y + b, x + b + SS * 2, y + C - 1 - b], fill=lighten(base, .10))
    # ground shadow
    bbox = img.getbbox()
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    bx0, bx1 = ox - C * .2, ox + w * C + D + C * .2
    by = oy + h * C
    sd.ellipse([bx0, by - C * .35, bx1, by + C * .55], fill=(40, 20, 60, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(C * .35))
    sh.alpha_composite(img)
    img = sh.crop(sh.getbbox())
    # square canvas
    side = max(img.size); m = round(side * 0.06); side += m * 2
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(img, ((side - img.width) // 2, (side - img.height) // 2))
    sq = sq.resize((size, size), Image.LANCZOS)
    sq.save(os.path.join(out_dir, name + '.png'), optimize=True)
    if preview:
        bg = Image.new('RGBA', sq.size, (255, 236, 200, 255)); bg.alpha_composite(sq)
        bg.convert('RGB').resize((320, 320), Image.LANCZOS).save(os.path.join(HERE, 'prev', name + '.png'))

if __name__ == '__main__':
    out = sys.argv[1]
    names = sys.argv[2:] or list(sp.SPRITES)
    os.makedirs(os.path.join(HERE, 'prev'), exist_ok=True)
    for n in names:
        render(n, out, preview=True); print('ok', n)
