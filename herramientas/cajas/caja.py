"""Recrea la caja (estilo ZINZ Special Edition) con el personaje redibujado en bloques nítidos."""
import sys, os, json, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

FT = '/usr/share/fonts/TTF/'
B = 740                      # lado de la caja dentro de la foto 900x900
SS = 2                       # supermuestreo para bordes limpios
def F(name, size): return ImageFont.truetype(FT + name, int(size))
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def mix(c, t, a): return tuple(max(0, min(255, round(c[i] + (t[i]-c[i])*a))) for i in range(3))

def rod(t):
    return -0.30 * (abs(t - .5) * 2) ** 2.2 + 0.40 * math.exp(-((t - .33) / .09) ** 2)

def ladrillos(pal, rows, C):
    """Figura de nanobloques: C px por bloque. Devuelve RGBA y desplazamiento del bloque (0,0)."""
    w = max(map(len, rows)); rows = [r.ljust(w, '.') for r in rows]; h = len(rows)
    ok = lambda r, c: 0 <= r < h and 0 <= c < w and rows[r][c] != '.'
    D = round(C * .28); pad = C
    img = Image.new('RGBA', (w*C + D + 2*pad, h*C + D + 2*pad), (0, 0, 0, 0)); g = ImageDraw.Draw(img)
    ox, oy = pad, pad + D
    prof = [rod((x + .5) / (C / 2)) for x in range(C // 2)]
    for r in range(h - 1, -1, -1):
        for c in range(w):
            if not ok(r, c): continue
            base = hx(pal[rows[r][c]]); x, y = ox + c*C, oy + r*C
            if not ok(r, c+1):
                g.polygon([(x+C, y), (x+C+D, y-D), (x+C+D, y+C-D), (x+C, y+C)], fill=mix(base, (0,0,0), .4))
            if not ok(r-1, c):
                g.polygon([(x, y), (x+D, y-D), (x+C+D, y-D), (x+C, y)], fill=mix(base, (255,255,255), .2))
                for k in range(2):
                    cx, cy = x + C/2*(k+.5) + D/2, y - D/2; rx, ry, sh = C*.17, D*.26, C*.1
                    g.rectangle([cx-rx, cy-sh, cx+rx, cy], fill=mix(base, (0,0,0), .15))
                    g.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=mix(base, (0,0,0), .15))
                    g.ellipse([cx-rx, cy-sh-ry, cx+rx, cy-sh+ry], fill=mix(base, (255,255,255), .3))
            for k in range(2):
                x0 = x + k*C//2
                for i, p in enumerate(prof):
                    g.line([(x0+i, y), (x0+i, y+C-1)], fill=mix(base, (255,255,255), p) if p > 0 else mix(base, (0,0,0), -p))
            g.line([(x, y+C-1), (x+C, y+C-1)], fill=mix(base, (0,0,0), .42), width=max(1, C//14))
            g.line([(x, y+1), (x+C, y+1)], fill=mix(base, (255,255,255), .2), width=max(1, C//16))
    return img, (ox, oy)

def fondo(n, mask_cells, g):
    src = cv2.cvtColor(np.asarray(Image.open(f'rect/{n}.png').convert('RGB')), cv2.COLOR_RGB2BGR)
    src = cv2.resize(src, (B, B), interpolation=cv2.INTER_CUBIC)
    # quitar figura, título y logos originales antes de suavizar
    m = np.zeros((B, B), np.uint8); p = B / g['n']
    for (r, c) in mask_cells: cv2.rectangle(m, (int(c*p)-6, int(r*p)-6), (int((c+1)*p)+6, int((r+1)*p)+6), 255, -1)
    for x0, y0, x1, y1 in ((.06, .02, .94, .22), (.02, .66, .3, .99), (.66, .6, .99, .97)):
        cv2.rectangle(m, (int(x0*B), int(y0*B)), (int(x1*B), int(y1*B)), 255, -1)
    small = cv2.resize(src, (B//4, B//4), interpolation=cv2.INTER_AREA)
    sm = cv2.resize(m, (B//4, B//4), interpolation=cv2.INTER_NEAREST)
    small = cv2.inpaint(small, sm, 9, cv2.INPAINT_TELEA)
    bg = cv2.GaussianBlur(cv2.resize(small, (B, B), interpolation=cv2.INTER_CUBIC), (0, 0), 14)
    bg = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB))
    bg = ImageEnhance.Color(bg).enhance(1.25); bg = ImageEnhance.Contrast(bg).enhance(1.08)
    # destellos y estrellas como en las cajas originales
    rnd = random.Random(n); glow = Image.new('RGBA', (B, B), (0, 0, 0, 0)); d = ImageDraw.Draw(glow)
    for _ in range(26):
        x, y, s = rnd.uniform(0, B), rnd.uniform(0, B), rnd.uniform(6, 22)
        d.ellipse([x-s, y-s, x+s, y+s], fill=(255, 255, 255, rnd.randint(25, 60)))
    glow = glow.filter(ImageFilter.GaussianBlur(5)); d = ImageDraw.Draw(glow)
    for _ in range(140):
        x, y, s = rnd.uniform(0, B), rnd.uniform(0, B), rnd.choice((.8, 1, 1.2, 1.6, 2.2))
        d.ellipse([x-s, y-s, x+s, y+s], fill=(255, 255, 255, rnd.randint(120, 230)))
    bg = Image.alpha_composite(bg.convert('RGBA'), glow)
    return bg, np.asarray(bg.convert('RGB')).reshape(-1, 3).mean(0)

def acento(avg):
    hsv = cv2.cvtColor(np.uint8([[avg]]), cv2.COLOR_RGB2HSV)[0, 0].astype(float)
    hsv[1] = max(hsv[1], 170); hsv[2] = 175
    return tuple(int(v) for v in cv2.cvtColor(np.uint8([[hsv]]), cv2.COLOR_HSV2RGB)[0, 0])

def texto(d, xy, s, font, fill, anchor='mm', spacing=0, shadow=None, stroke=0, stroke_fill=None):
    if spacing:
        widths = [font.getlength(ch) for ch in s]; total = sum(widths) + spacing * (len(s) - 1)
        x = xy[0] - total / 2
        for ch, w in zip(s, widths):
            if shadow: d.text((x+shadow[0], xy[1]+shadow[1]), ch, font=font, fill=shadow[2], anchor='lm')
            d.text((x, xy[1]), ch, font=font, fill=fill, anchor='lm'); x += w + spacing
        return
    if shadow: d.text((xy[0]+shadow[0], xy[1]+shadow[1]), s, font=font, fill=shadow[2], anchor=anchor, stroke_width=stroke, stroke_fill=shadow[2])
    d.text(xy, s, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)

def caja(n, titulo, pz, g):
    rows, pal = g['rows'], g['pal']
    cells = [(g['r0']+r, g['c0']+c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != '.']
    bg, avg = fondo(n, cells, g)
    S = B * SS; can = bg.resize((S, S), Image.BICUBIC)
    # personaje: centrado horizontalmente, apoyado abajo, sin tapar el título
    h, w = len(rows), max(map(len, rows))
    C = int(min(S * .62 / h, S * .44 / w))
    fig, (ox, oy) = ladrillos(pal, rows, C)
    fx = (S - w*C) // 2 - ox; fy = int(S * .93) - h*C - oy
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).ellipse([S/2 - w*C*.55, S*.915, S/2 + w*C*.55, S*.955], fill=110)
    can.paste((25, 15, 40), (0, 0), sh.filter(ImageFilter.GaussianBlur(S * .012)))
    halo = Image.new('RGBA', fig.size, (0, 0, 0, 0)); halo.paste((20, 10, 30, 120), (0, 0), fig.split()[3])
    can.alpha_composite(halo.filter(ImageFilter.GaussianBlur(C * .4)), (fx + C//6, fy + C//4))
    can.alpha_composite(fig, (fx, fy))
    d = ImageDraw.Draw(can)
    # título
    size = S * .135; f = F('FiraSansCompressed-Heavy.ttf', size)
    while f.getlength(titulo.upper()) > S * .86: size *= .95; f = F('FiraSansCompressed-Heavy.ttf', size)
    texto(d, (S/2, S*.105), titulo.upper(), f, (255, 255, 255), shadow=(0, S*.006, (20, 15, 40, 140)), stroke=int(S*.002), stroke_fill=(255, 255, 255))
    fs = F('OpenSans-Regular.ttf', S * .043)
    texto(d, (S/2, S*.185), 'SPECIAL EDITION', fs, (255, 255, 255), spacing=S*.012, shadow=(0, S*.003, (20, 15, 40, 120)))
    # logos abajo a la izquierda
    x0, y0, bw, bh = S*.05, S*.70, S*.2, S*.075
    d.rounded_rectangle([x0, y0, x0+bw, y0+bh], S*.012, fill=(150, 18, 32), outline=(60, 10, 18), width=int(S*.005))
    d.rounded_rectangle([x0+S*.008, y0+S*.008, x0+bw-S*.008, y0+bh-S*.008], S*.008, outline=(255, 255, 255), width=int(S*.002))
    texto(d, (x0+bw/2, y0+bh/2), 'ZINZ', F('FiraSansCompressed-Heavy.ttf', S*.06), (255, 255, 255), stroke=int(S*.003), stroke_fill=(30, 20, 30))
    y1 = y0 + bh + S*.022; acc = acento(avg)
    d.rounded_rectangle([x0, y1, x0+bw, y1+S*.06], S*.014, fill=mix(acc, (0,0,0), .05), outline=(255, 255, 255), width=int(S*.004))
    cx, cy = x0 + bw*.3, y1 + S*.03
    d.ellipse([cx-S*.009, cy-S*.02, cx+S*.009, cy-S*.002], fill=(255, 255, 255))
    d.pieslice([cx-S*.016, cy-S*.002, cx+S*.016, cy+S*.03], 180, 360, fill=(255, 255, 255))
    texto(d, (x0+bw*.62, cy), '6+', F('OpenSans-Bold.ttf', S*.042), (255, 255, 255))
    y2 = y1 + S*.08
    d.rounded_rectangle([x0, y2, x0+bw, y2+S*.06], S*.014, fill=mix(acc, (0,0,0), .3) + (150,), outline=(255, 255, 255), width=int(S*.003))
    texto(d, (x0+bw*.6, y2+S*.021), 'BLOQUES', F('OpenSans-SemiBold.ttf', S*.019), (255, 255, 255))
    texto(d, (x0+bw*.6, y2+S*.041), 'INTELIGENTES', F('OpenSans-SemiBold.ttf', S*.015), (255, 255, 255))
    bx = x0 + bw*.18; by = y2 + S*.03; q = S*.016
    d.polygon([(bx, by-q), (bx+q, by-q*.4), (bx, by+q*.2), (bx-q, by-q*.4)], outline=(255, 255, 255), width=int(S*.0025))
    d.line([(bx-q, by-q*.4), (bx-q, by+q*.6), (bx, by+q*1.2), (bx+q, by+q*.6), (bx+q, by-q*.4)], fill=(255, 255, 255), width=int(S*.0025))
    # piezas abajo a la derecha
    if pz:
        texto(d, (S*.835, S*.735), 'LUCI-2027', F('OpenSans-Regular.ttf', S*.038), (255, 255, 255), shadow=(0, S*.003, (20, 15, 40, 120)))
        L, T, R, Bt = S*.7, S*.775, S*.97, S*.93; tip = S*.03
        shield = [(L, T), (R, T), (R, Bt), ((L+R)/2, Bt+tip), (L, Bt)]
        d.polygon([(x+S*.004, y+S*.008) for x, y in shield], fill=(20, 15, 40, 90))
        d.polygon(shield, fill=acc, outline=(255, 255, 255), width=int(S*.006))
        texto(d, ((L+R)/2, T+S*.065), str(pz), F('FiraSansCompressed-Heavy.ttf', S*.095), (255, 255, 255), stroke=int(S*.003), stroke_fill=mix(acc, (0,0,0), .45))
        texto(d, ((L+R)/2, T+S*.13), 'PIEZAS', F('OpenSans-Bold.ttf', S*.033), (255, 255, 255))
    return can.resize((B, B), Image.LANCZOS).convert('RGB')

def foto(box):
    S = 900; bg = Image.new('RGB', (S, S)); d = ImageDraw.Draw(bg)
    top, bot = (247, 246, 242), (221, 218, 211)
    for y in range(S):
        t = (y / S) ** 1.6; d.line([(0, y), (S, y)], fill=tuple(round(top[i] + (bot[i]-top[i]) * t) for i in range(3)))
    x = (S - B) // 2; y = x - 12
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).rectangle([x+10, y+24, x+B-10, y+B+14], fill=95)
    bg.paste((60, 50, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    bg.paste(box, (x, y)); return bg

if __name__ == '__main__':
    info = json.load(open('info.json'))
    os.makedirs('nuevas', exist_ok=True)
    for n in sys.argv[1:]:
        g = json.load(open(f'grillas/{n}.json'))
        foto(caja(n, info[n]['t'], info[n]['pz'], g)).save(f'nuevas/{n}.jpg', quality=90, optimize=True, progressive=True, subsampling=0)
        print('ok', n)
