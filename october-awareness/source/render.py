"""October Awareness — 10 s animated poster. Renders frames from the layers made by layers.py.

python3 render.py [--preview] [--fps 60] [--out file.mp4] [--still t1,t2,...]
"""
import argparse, json, subprocess
import numpy as np, cv2
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--fps', type=int, default=60)
ap.add_argument('--out', default='october_awareness.mp4')
ap.add_argument('--preview', action='store_true')
ap.add_argument('--still', default='')
ap.add_argument('--audio', default='music.wav')
A = ap.parse_args()

DUR = 10.0
OW, OH = (540, 676) if A.preview else (1080, 1350)
L = 'layers/'
f32 = lambda p: np.asarray(Image.open(p)).astype(np.float32) / 255
clean, plate = f32(L + 'clean.png'), f32(L + 'plate.png')
arc = np.load(L + 'arc.npy'); M = json.load(open(L + 'meta.json'))
H, W = clean.shape[:2]
PATH_LEN = M['path_len']

# ribbon matte (for the light that travels through the satin): where the ribbon makes the image
# more saturated / brighter than the empty plate
def sat(x): mx, mn = x.max(2), x.min(2); return (mx - mn) / (mx + 1e-4)
# the supplied clean ribbon cut-out, registered to the poster (scale 1.0, offset 0,12 — found by template match)
RIB = np.zeros((H, W, 4), np.float32)
_rc = f32('ribbon_cut.png'); RX, RY = 0, 12
RIB[RY:RY + _rc.shape[0], RX:RX + _rc.shape[1]] = _rc[:H - RY, :W - RX]
ribA = RIB[..., 3]
_rp = cv2.GaussianBlur(cv2.dilate((ribA > 0.02).astype(np.float32), np.ones((15, 15), np.uint8)), (0, 0), 4)
rib = ribA
from scipy import ndimage
# feather the filled plate back into the real background near the fill boundary (no visible seams)
_zone = np.isfinite(arc)
_w = np.clip(ndimage.distance_transform_edt(_zone) / 60.0, 0, 1).astype(np.float32)
_w = _w * _w * (3 - 2 * _w)
_w = np.maximum(_w, _rp)
plate = clean - (clean - plate) * _w[..., None]
_inf = ~np.isfinite(arc)
_, (iy, ix) = ndimage.distance_transform_edt(_inf, return_indices=True)
arc_f = np.where(_inf, arc[iy, ix], arc).astype(np.float32)          # every ribbon pixel gets a reveal time
arc_f = np.where(np.isfinite(arc_f), arc_f, 1e9).astype(np.float32)

# ribbon reveal timing from strand ownership: the front band (traced outline) owns its pixels; everything
# else on the ribbon follows the loop / under-strand / tail part of the path. Keeps the crossing clean.
from scipy.spatial import cKDTree
PD = np.load(L + 'path.npy'); PXY, PARC = PD[:, :2], PD[:, 3]
BAND = np.array([(-8, 562), (200, 502), (400, 422), (600, 347), (800, 282), (875, 252), (866, 330), (824, 422),
                 (762, 498), (700, 539), (600, 594), (400, 659), (300, 699), (200, 724), (100, 754), (0, 779), (-8, 779)], np.int32)
band = np.zeros((H, W), np.uint8); cv2.fillPoly(band, [BAND], 1); band = band.astype(bool)
iA1 = int(np.argmin(np.hypot(PXY[:, 0] - 800, PXY[:, 1] - 350)))
yy, xx = np.nonzero(ribA > 0)
pts = np.column_stack([xx, yy]).astype(np.float32)
inb = band[yy, xx]
arc_r = np.full((H, W), 1e9, np.float32)
_, i1 = cKDTree(PXY[:iA1 + 1]).query(pts[inb]); arc_r[yy[inb], xx[inb]] = PARC[i1]
_, i2 = cKDTree(PXY[iA1:]).query(pts[~inb]); arc_r[yy[~inb], xx[~inb]] = PARC[iA1 + i2]
arc_r = cv2.GaussianBlur(arc_r * (ribA > 0) + arc_f * (ribA <= 0), (0, 0), 3.0)   # soften Voronoi seams
# shadow timing: follow the ribbon's own timing where possible, then blur hard so cast shadows bloom smoothly
_ar = np.where(ribA > 0.5, arc_r, 0).astype(np.float32)
_near = ndimage.grey_dilation(_ar, size=(61, 61))                       # latest ribbon time nearby
_sh = np.minimum(np.where(ribA > 0.5, arc_r, np.maximum(arc_f, _near)), PATH_LEN + 400).astype(np.float32)
arc_s = cv2.GaussianBlur(_sh, (0, 0), 40.0)

hands = f32(L + 'hands.png'); HX, HY = M['hands'][:2]
TXT = {k: f32(L + f't_{k}.png') for k in ['logo', 'october', 'awareness', 'month', 'rule', 'care', 'health', 'tomorrow']}

# ---------------- easing ----------------
clamp = lambda x, a=0.0, b=1.0: min(b, max(a, x))
P = lambda t, a, d: clamp((t - a) / d)
lerp = lambda a, b, p: a + (b - a) * p
eOut3 = lambda p: 1 - (1 - p) ** 3
eOut5 = lambda p: 1 - (1 - p) ** 5
eIO3 = lambda p: 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def eOutExpo(p): return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)
def eBack(p, s=1.25): c = s + 1; return 1 + c * (p - 1) ** 3 + s * (p - 1) ** 2

def over(dst, src_rgba, x, y, opacity=1.0, mask=None):
    """alpha-composite src (h,w,4 float) onto dst at integer-ish offset (sub-pixel via warp)."""
    if mask is not None: src_rgba = src_rgba.copy(); src_rgba[..., 3] *= mask; mask = None
    h, w = src_rgba.shape[:2]
    ix, iy = int(np.floor(x)), int(np.floor(y)); fx, fy = x - ix, y - iy
    if fx or fy:
        Mt = np.float32([[1, 0, fx], [0, 1, fy]])
        src_rgba = cv2.warpAffine(src_rgba, Mt, (w + 1, h + 1), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        h, w = h + 1, w + 1
    x0, y0, x1, y1 = max(ix, 0), max(iy, 0), min(ix + w, W), min(iy + h, H)
    if x1 <= x0 or y1 <= y0: return
    s = src_rgba[y0 - iy:y1 - iy, x0 - ix:x1 - ix]
    a = s[..., 3:4] * opacity
    if mask is not None: a = a * mask[y0 - iy:y1 - iy, x0 - ix:x1 - ix, None]
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a

def blur(img, sig):
    return cv2.GaussianBlur(img, (0, 0), sig) if sig > 0.25 else img

def hwipe(shape, x_reveal, soft=18.0, rtl=False):
    """horizontal wipe mask: pixels with column < x_reveal are visible (soft edge)."""
    xs = np.arange(shape[1], dtype=np.float32)
    m = np.clip((x_reveal - xs) / soft + 0.5, 0, 1)
    return np.broadcast_to(m[None, :], shape[:2])

# soft bokeh motes that drift upward (seeded)
rng = np.random.default_rng(4)
MOTES = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), r=rng.uniform(5, 22), sp=rng.uniform(8, 26),
              ph=rng.uniform(0, 6.28), a=rng.uniform(0.05, 0.16)) for _ in range(16)]
def mote_sprite(r):
    s = int(r * 3) | 1; yy, xx = np.mgrid[:s, :s] - s // 2
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    a = np.clip(1.15 - d, 0, 1) ** 1.6
    return np.dstack([np.ones((s, s, 3), np.float32), a.astype(np.float32)])
for m in MOTES: m['spr'] = mote_sprite(m['r'])

def frame(t):
    # ---- ribbon ties itself: reveal travels along the traced path ----
    head = lerp(-150, PATH_LEN + 260, eIO3(P(t, 0.15, 2.75)) * 0.25 + eOut3(P(t, 0.15, 2.75)) * 0.75)
    ms = np.clip((head - arc_s) / 220.0, 0, 1); ms = ms * ms * (3 - 2 * ms)      # shadows: soft
    mr = np.clip((head - arc_r) / 45.0, 0, 1); mr = mr * mr * (3 - 2 * mr)        # ribbon: crisp leading edge
    img = plate + (clean - plate) * (ms * (1 - ribA))[..., None]                     # cast shadows only
    a = (ribA * mr)[..., None]
    img = img * (1 - a) + RIB[..., :3] * a
    # bright leading edge — the satin catches light as it lands
    if 0.15 < t < 3.2:
        edge = np.exp(-((head - 90 - arc_f) / 110.0) ** 2) * rib * 0.30 * (1 - P(t, 2.6, 0.6))
        img = 1 - (1 - img) * (1 - edge[..., None])
    # light travelling through the ribbon during the hold
    for t0, amp in ((5.6, 0.22), (8.1, 0.16)):
        if t0 < t < t0 + 1.9:
            s = lerp(-300, PATH_LEN + 300, eIO3(P(t, t0, 1.9)))
            g = np.exp(-((arc_f - s) / 170.0) ** 2) * rib * amp
            img = 1 - (1 - img) * (1 - g[..., None])

    # ---- motes ----
    vis = P(t, 1.0, 1.5)
    for mo in MOTES:
        x = mo['x'] + np.sin(t * 0.6 + mo['ph']) * 18
        y = (mo['y'] - t * mo['sp']) % (H + 80) - 40
        over(img, mo['spr'], x - mo['spr'].shape[1] / 2, y - mo['spr'].shape[0] / 2, mo['a'] * vis * (0.7 + 0.3 * np.sin(t * 1.3 + mo['ph'])))

    # ---- hands rise and meet ----
    ph = P(t, 2.25, 1.15)
    if ph > 0:
        dy = lerp(560, 0, eBack(ph, 1.05)) + np.sin(max(0, t - 3.4) * 1.4) * 2.0 * P(t, 3.4, 1.0)
        over(img, hands, HX, HY + dy)

    # ---- logo: soft wipe left→right with a short slide ----
    pl = P(t, 2.85, 0.75)
    if pl > 0:
        lg = TXT['logo']; e = eOut5(pl)
        over(img, lg, M['logo'][0] - 24 * (1 - e), M['logo'][1], 1.0, hwipe(lg.shape, e * (lg.shape[1] + 40), 30))

    # ---- headline ----
    po = P(t, 3.25, 0.7)
    if po > 0:
        e = eOut3(po); o = TXT['october']
        o2 = o.copy(); o2[..., 3] = blur(o[..., 3], (1 - e) * 7)
        over(img, o2, M['october'][0], M['october'][1] + 26 * (1 - e), e)
    for key, t0 in (('awareness', 3.45), ('month', 3.62)):
        p = P(t, t0, 0.65)
        if p > 0:
            e = eOutExpo(p); el = TXT[key]; x0, y0, x1, y1 = M[key]
            # masked rise: the word slides up into its own line
            clip = np.zeros(el.shape[:2], np.float32); hh = el.shape[0]
            shift = (1 - e) * hh * 1.05
            yy = np.arange(hh, dtype=np.float32)[:, None] + shift
            clip[:] = (yy < hh).astype(np.float32)
            over(img, el, x0, y0 + shift, 1.0, clip)

    # ---- rule: dot pops, line draws ----
    pr = P(t, 4.1, 0.6)
    if pr > 0:
        r = TXT['rule']; x0, y0 = M['rule'][:2]
        dot_w = 26
        dot = r[:, :dot_w]; s = eBack(P(t, 4.1, 0.28), 2.0)
        if s > 0.01:
            dd = cv2.resize(dot, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR) if abs(s - 1) > 1e-3 else dot
            cx, cy = x0 + 16, y0 + 11
            over(img, dd, cx - 16 * s, cy - 11 * s)
        line = r[:, dot_w:]
        e = eOut5(P(t, 4.22, 0.55))
        over(img, line, x0 + dot_w, y0, 1.0, hwipe(line.shape, e * (line.shape[1] + 20), 14))

    # ---- descriptors ----
    for i, key in enumerate(('care', 'health', 'tomorrow')):
        p = P(t, 4.45 + i * 0.17, 0.6)
        if p > 0:
            e = eOut5(p); el = TXT[key]
            el2 = el.copy(); el2[..., 3] = blur(el[..., 3], (1 - e) * 5)
            over(img, el2, M[key][0] - 36 * (1 - e), M[key][1], e)

    # ---- camera: pull back while the ribbon ties, then a slow push ----
    k1 = eOut3(P(t, 0.0, 3.7)); k2 = eIO3(P(t, 3.7, 6.3))
    sc = lerp(1.22, 1.0, k1) * lerp(1.0, 1.035, k2)
    cx = lerp(600, W / 2, k1); cy = lerp(470, H / 2, k1)
    base = OW / W
    Mc = np.float32([[sc * base, 0, OW / 2 - cx * sc * base], [0, sc * base, OH / 2 - cy * sc * base]])
    out = cv2.warpAffine(np.clip(img, 0, 1), Mc, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

if A.still:
    for ts in A.still.split(','):
        Image.fromarray(frame(float(ts))).save(f'still_{ts}.png')
else:
    N = int(DUR * A.fps)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(A.fps), '-i', '-',
           '-i', A.audio, '-c:v', 'libx264', '-preset', 'slow', '-crf', '22' if A.preview else '15', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '256k', '-t', str(DUR), '-movflags', '+faststart', A.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        ff.stdin.write(frame(i / A.fps).tobytes())
        if i % 120 == 0: print('frame', i, flush=True)
    ff.stdin.close(); ff.wait(); print('done', A.out)
