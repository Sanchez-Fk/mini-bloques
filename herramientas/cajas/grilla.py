"""Extrae la cuadrícula de bloques del personaje a partir de la caja rectificada (rect/<id>.png)."""
import sys, os, json
import numpy as np, cv2
from PIL import Image, ImageEnhance
from sklearn.cluster import KMeans

U = 512
K = (30, 28, 36); W = (247, 246, 242)
# Área de búsqueda (x0, y0, x1, y1) para cajas donde el fondo se confunde con la figura
RECT = {
    'mester-popo': (0.31, 0.19, 0.71, 0.97),
    'tao-pai-pai': (0.34, 0.20, 0.75, 0.92),
    'chilindrina': (0.27, 0.22, 0.70, 0.97),
    'joker': (0.33, 0.20, 0.80, 0.97),
    'mario': (0.28, 0.20, 0.80, 0.97),
    'minion': (0.26, 0.20, 0.71, 0.97),
}

def mask_figura(img, rect=(0.17, 0.19, 0.83, 0.97)):
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    r = (int(rect[0]*w), int(rect[1]*h), int((rect[2]-rect[0])*w), int((rect[3]-rect[1])*h))
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, m, r, bg, fg, 8, cv2.GC_INIT_WITH_RECT)
    m = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        big = st[1:, cv2.CC_STAT_AREA].max()
        keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > big * 0.08]
        m = np.isin(lab, keep).astype(np.uint8) * 255
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

def lab(c): return cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_RGB2LAB)[0, 0].astype(float)

def extraer(n, ncells=56, rect=None, k=None):
    src = Image.open(f'rect/{n}.png').convert('RGB').resize((U, U), Image.LANCZOS)
    m = mask_figura(cv2.cvtColor(np.asarray(src), cv2.COLOR_RGB2BGR), rect or RECT.get(n, (0.17, 0.19, 0.83, 0.97)))
    a = np.asarray(ImageEnhance.Color(src).enhance(1.25))
    p = U / ncells
    cells = {}
    for r in range(ncells):
        for c in range(ncells):
            y0, y1, x0, x1 = int(r*p), int((r+1)*p), int(c*p), int((c+1)*p)
            if m[y0:y1, x0:x1].mean() / 255 < 0.5: continue
            q = int(p * 0.25)
            blk = a[y0+q:y1-q, x0+q:x1-q].reshape(-1, 3)
            cells[(r, c)] = np.median(blk, 0)
    keys = list(cells); X = np.array([cells[k_] for k_ in keys], np.uint8)
    L = cv2.cvtColor(X[None], cv2.COLOR_RGB2LAB)[0].astype(float)
    kk = k or min(9, max(3, len(keys) // 25))
    km = KMeans(kk, n_init=6, random_state=0).fit(L)
    cent = km.cluster_centers_; lbl = km.labels_
    # fusionar centros casi iguales
    alias = list(range(kk))
    for i in range(kk):
        for j in range(i):
            if np.linalg.norm(cent[i] - cent[j]) < 13 and alias[j] == j: alias[i] = j; break
    lbl = np.array([alias[l] for l in lbl])
    cols = {}
    for i in set(lbl):
        rgb = np.median(X[lbl == i], 0)
        hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0, 0].astype(float)
        hsv[1] = min(255, hsv[1] * 1.15); hsv[2] = min(255, hsv[2] * 1.06)
        rgb = cv2.cvtColor(np.uint8([[hsv]]), cv2.COLOR_HSV2RGB)[0, 0]
        if hsv[2] < 70: rgb = K
        elif hsv[1] < 30 and hsv[2] > 185: rgb = W
        cols[i] = '#%02X%02X%02X' % tuple(int(v) for v in rgb)
    grid = {keys[t]: lbl[t] for t in range(len(keys))}
    # limpiar bloques sueltos: sin vecino del mismo color y con mayoría clara alrededor
    for (r, c), v in list(grid.items()):
        nb = [grid.get((r+dr, c+dc)) for dr, dc in ((1,0),(-1,0),(0,1),(0,-1))]
        if v in nb: continue
        ring = [grid.get((r+dr, c+dc)) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc)]
        ring = [x for x in ring if x is not None]
        if ring:
            mode = max(set(ring), key=ring.count)
            if ring.count(mode) >= 4: grid[(r, c)] = mode
    rs = [r for r, _ in grid]; cs = [c for _, c in grid]
    r0, c0 = min(rs), min(cs)
    letters = 'abcdefghijklmnopqrstuvwxyz'
    used = sorted(set(grid.values()))
    key = {v: letters[i] for i, v in enumerate(used)}
    rows = []
    for r in range(r0, max(rs) + 1):
        rows.append(''.join(key[grid[(r, c)]] if (r, c) in grid else '.' for c in range(c0, max(cs) + 1)).rstrip('.'))
    pal = {key[v]: cols[v] for v in used}
    return {'pal': pal, 'rows': rows, 'r0': r0, 'c0': c0, 'n': ncells}

if __name__ == '__main__':
    os.makedirs('grillas', exist_ok=True)
    for n in sys.argv[1:]:
        g = extraer(n)
        json.dump(g, open(f'grillas/{n}.json', 'w'))
        print(n, len(g['rows']), max(map(len, g['rows'])), len(g['pal']))
