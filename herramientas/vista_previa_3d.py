# Vista previa del armado 3D (mismo algoritmo que el visor) con proyección y pintor
import json, math, sys
from PIL import Image, ImageDraw
src=open('/home/sanchez/Documentos/tienda/js/modelos.js').read()
M=json.loads(src[src.index('=')+1:].rstrip().rstrip(';'))
def hx(h): h=h.lstrip('#'); return [int(h[i:i+2],16) for i in (0,2,4)]
def build(id):
    pal,rows=M[id]['pal'],M[id]['rows']; H=len(rows); W=max(map(len,rows))
    at=lambda r,c: rows[r][c] if 0<=r<H and 0<=c<len(rows[r]) and rows[r][c]!='.' else None
    INF=10**9; d=[[INF if at(r,c) else 0 for c in range(W)] for r in range(H)]; q=[]
    N=[(1,0),(-1,0),(0,1),(0,-1)]
    for r in range(H):
        for c in range(W):
            if at(r,c) and any(not at(r+a,c+b) for a,b in N): d[r][c]=1; q.append((r,c))
    i=0
    while i<len(q):
        r,c=q[i]; i+=1
        for a,b in N:
            if at(r+a,c+b) and d[r+a][c+b]>d[r][c]+1: d[r+a][c+b]=d[r][c]+1; q.append((r+a,c+b))
    mx=max(2,round(W*.19)); half=lambda r,c: min(mx,math.ceil(d[r][c]*.85)) if at(r,c) else -1
    def mode(r,c):
        n={}
        for a in range(-2,3):
            for b in range(-2,3):
                k=at(r+a,c+b)
                if k: n[k]=n.get(k,0)+1
        return max(n,key=n.get)
    def back(r,c):
        n={}
        for a in range(-8,2):
            for b in range(-3,4):
                k=at(r+a,c+b)
                if k: n[k]=n.get(k,0)+1+2*(a<-1)
        return max(n,key=n.get)
    vox={}
    for r in range(H):
        for c in range(W):
            if not at(r,c): continue
            h=half(r,c); s=mode(r,c); bk=back(r,c)
            for z in range(-h,h+1): vox[(c,-r,z)]=pal[at(r,c) if z==h else (s if z>=0 else bk)]
    return vox
def render(id,yaw,out):
    vox=build(id); cy,sy=math.cos(yaw),math.sin(yaw); S=9
    faces=[]
    dirs={(0,0,1):.95,(1,0,0):.7,(-1,0,0):.7,(0,1,0):1.12,(0,0,-1):.6}
    for (x,y,z),col in vox.items():
        for (dx,dy,dz),sh in dirs.items():
            if (x+dx,y+dy,z+dz) in vox: continue
            # cuadrado de la cara
            if dz: pts=[(x-.5,y-.5,z+dz*.5),(x+.5,y-.5,z+dz*.5),(x+.5,y+.5,z+dz*.5),(x-.5,y+.5,z+dz*.5)]
            elif dx: pts=[(x+dx*.5,y-.5,z-.5),(x+dx*.5,y-.5,z+.5),(x+dx*.5,y+.5,z+.5),(x+dx*.5,y+.5,z-.5)]
            else: pts=[(x-.5,y+.5,z-.5),(x+.5,y+.5,z-.5),(x+.5,y+.5,z+.5),(x-.5,y+.5,z+.5)]
            P=[];dep=0
            for X,Y,Z in pts:
                rx=X*cy+Z*sy; rz=-X*sy+Z*cy
                ry=Y*math.cos(.25)-rz*math.sin(.25); rz2=Y*math.sin(.25)+rz*math.cos(.25)
                P.append((300+rx*S,300-ry*S-100)); dep+=rz2
            faces.append((dep,P,[min(255,int(v*sh)) for v in hx(col)]))
    faces.sort(key=lambda f:f[0])
    im=Image.new('RGB',(600,600),(255,232,204)); g=ImageDraw.Draw(im)
    for _,P,col in faces: g.polygon(P,fill=tuple(col),outline=tuple(int(v*.8) for v in col))
    bb=im.getbbox(); im.save(out)
for id in sys.argv[1:]:
    for k,yaw in enumerate((0.6,1.4,3.14)): render(id,yaw,f'vox_{id}_{k}.png')
