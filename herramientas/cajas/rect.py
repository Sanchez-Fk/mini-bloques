import os, sys, math
from PIL import Image
from crops import C
D="/home/sanchez/Documentos/tienda/WhatsApp Unknown 2026-11-26 at 3.42.45 PM"; fs=sorted(os.listdir(D))
os.makedirs('rect',exist_ok=True)
L=lambda a,b: math.dist(a,b)
for n,(i,tl,tr,br,bl) in C.items():
    if len(sys.argv)>1 and n not in sys.argv[1:]: continue
    im=Image.open(os.path.join(D,fs[i])).convert('RGB')
    w=round((L(tl,tr)+L(bl,br))/2); h=round((L(tl,bl)+L(tr,br))/2)
    out=im.transform((w,h),Image.QUAD,(*tl,*bl,*br,*tr),Image.BICUBIC)
    out.save(f'rect/{n}.png'); print(n,w,h)
