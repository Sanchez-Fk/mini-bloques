# Caja rectificada -> foto de catálogo 900x900 sobre fondo de estudio (como las existentes)
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
S, B = 900, 740
def background():
    bg = Image.new('RGB', (S, S)); d = ImageDraw.Draw(bg)
    top, bot = (247, 246, 242), (221, 218, 211)
    for y in range(S):
        t = (y / S) ** 1.6
        d.line([(0, y), (S, y)], fill=tuple(round(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return bg
def upscale(im, size):
    # Escalado progresivo (x1.5 por paso) para evitar halos, con enfoque suave al final
    w = im.width
    while w * 1.5 < size:
        w = round(w * 1.5); im = im.resize((w, w), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 35, 2))
    im = im.resize((size, size), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(1.6, 55 if w < size else 30, 2))
os.makedirs('final', exist_ok=True)
BG = background()
for f in sorted(os.listdir('rect')):
    n = f[:-4]
    if len(sys.argv) > 1 and n not in sys.argv[1:]: continue
    im = Image.open('rect/' + f).convert('RGB')
    im = ImageOps.autocontrast(im, cutoff=0.4, preserve_tone=True)
    im = ImageEnhance.Color(im).enhance(1.08)
    im = upscale(im, B)
    out = BG.copy(); x = y = (S - B) // 2; y -= 12
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).rectangle([x + 10, y + 24, x + B - 10, y + B + 14], fill=95)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    out.paste(Image.new('RGB', (S, S), (60, 50, 70)), (0, 0), sh)
    out.paste(im, (x, y))
    out.save(f'final/{n}.jpg', quality=90, optimize=True, progressive=True, subsampling=0)
print(len(os.listdir('final')))
