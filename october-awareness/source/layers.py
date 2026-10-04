"""Split the flat poster into animatable layers (all at source resolution 1122x1402).

Outputs (layers/):
  clean.png      poster with text, logo and hands removed (ribbon intact)
  plate.png      clean poster with the ribbon (and its shadow) removed too
  arc.npy        per-pixel arc-length along the ribbon path (inf outside the ribbon zone)
  hands.png      RGBA hands
  t_*.png        RGBA text / logo elements, exact poster pixels un-mixed from the background
"""
import json, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

os.makedirs('layers', exist_ok=True)
src = np.asarray(Image.open('src.png').convert('RGB')).astype(np.float32)
H, W = src.shape[:2]

def pullpush(img, hole):
    """Smooth multiscale fill of `hole` (bool) from the surrounding pixels."""
    levels = []
    im, w = img * (~hole)[..., None], (~hole).astype(np.float32)
    while min(im.shape[:2]) > 4:
        levels.append((im, w))
        h2, w2 = (im.shape[0] + 1) // 2, (im.shape[1] + 1) // 2
        im = cv2.resize(im * w[..., None], (w2, h2), interpolation=cv2.INTER_AREA)
        w = cv2.resize(w, (w2, h2), interpolation=cv2.INTER_AREA)
        im = np.where(w[..., None] > 1e-4, im / np.maximum(w[..., None], 1e-4), 0)
        w = np.minimum(w * 4, 1)
    fill = im
    for im, w in reversed(levels):
        up = cv2.resize(fill, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_LINEAR)
        up = cv2.GaussianBlur(up, (0, 0), 1.0)
        fill = im * w[..., None] + up * (1 - w[..., None])
    return np.where(hole[..., None], fill, img)

G = src[..., 1]
# ---------- white elements (logo, headline, rule, descriptors) ----------
bg0 = pullpush(src, G > 185)
bgG = bg0[..., 1]
boxes = {  # x0, y0, x1, y1 in poster pixels
    'logo':     (40, 55, 380, 160),
    'october':  (500, 712, 760, 775),
    'awareness':(500, 775, 880, 840),
    'month':    (500, 840, 740, 905),
    'rule':     (500, 920, 840, 942),
    'care':     (505, 955, 670, 1000),
    'health':   (505, 1003, 710, 1048),
    'tomorrow': (505, 1050, 785, 1095),
}
white = np.zeros((H, W), bool)
for x0, y0, x1, y1 in boxes.values():
    sub = (G[y0:y1, x0:x1] - bgG[y0:y1, x0:x1]) > 14
    white[y0:y1, x0:x1] |= sub
white_hole = ndimage.binary_dilation(white, iterations=4)

# ---------- hands ----------
R, B = src[..., 0], src[..., 2]
ratio = B / np.maximum(R, 1)
hb = np.zeros((H, W), bool); hb[880:, 830:] = True
core = (ratio < 0.56) & hb
core = ndimage.binary_closing(core, iterations=6)
core = ndimage.binary_fill_holes(core)
lab, n = ndimage.label(core); sizes = ndimage.sum(core, lab, range(1, n + 1))
core = lab == (np.argmax(sizes) + 1)
soft = np.clip((0.64 - ratio) / 0.10, 0, 1) * hb           # continuous edge alpha
bgh = pullpush(src, ndimage.binary_dilation(core, iterations=14))
diff = np.abs(src - bgh).max(2)
core2 = core | (hb & (diff > 22) & ndimage.binary_dilation(core, iterations=14) & ~white_hole)
core2 = ndimage.binary_fill_holes(ndimage.binary_closing(core2, iterations=3))
lab, n = ndimage.label(core2); sizes = ndimage.sum(core2, lab, range(1, n + 1)); core = lab == (np.argmax(sizes) + 1)
soft = np.clip((diff - 8) / 22, 0, 1) * hb
hand_a = np.where(ndimage.binary_erosion(core, iterations=2), 1.0,
                  np.where(ndimage.binary_dilation(core, iterations=3), soft, 0.0))
hand_a = hand_a * np.clip((diff - 8) / 16, 0, 1)
hand_a = cv2.GaussianBlur(hand_a.astype(np.float32), (0, 0), 0.6)
hand_hole = ndimage.binary_dilation(core, iterations=10)

clean = pullpush(src, white_hole | hand_hole)

# ---------- ribbon path (traced on the poster grid), drawn left-exit → loop → tail ----------
PATH = [(-110, 702, 165), (0, 665, 160), (200, 625, 170), (400, 555, 155), (600, 485, 145), (720, 425, 150),
        (800, 350, 200), (850, 260, 215), (860, 180, 190), (830, 110, 150), (760, 60, 130), (660, 35, 120),
        (560, 40, 120), (480, 80, 120), (430, 130, 115), (395, 200, 115), (360, 280, 115), (330, 350, 115),
        (300, 430, 120), (270, 520, 125), (250, 610, 130), (235, 700, 140), (225, 800, 145), (225, 900, 140),
        (235, 1000, 130), (255, 1100, 120), (275, 1200, 110), (310, 1300, 115), (345, 1440, 120)]
P = np.array(PATH, np.float64)
# dense resample with Catmull-Rom
def catmull(P, step=2.0):
    pts = []
    Q = np.vstack([P[0], P, P[-1]])
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        seg = np.linalg.norm(p2[:2] - p1[:2]); n = max(2, int(seg / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    pts.append(P[-1]); return np.array(pts)
D = catmull(P)
arcs = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(D[:, :2], axis=0), axis=1))])
tree = cKDTree(D[:, :2])
yy, xx = np.mgrid[:H, :W]
pix = np.stack([xx.ravel(), yy.ravel()], 1).astype(np.float64)
# nearest few samples; pick the earliest arc among samples that cover the pixel (so the top strand wins at the crossing)
# chunk the path so every strand is tested (the crossing has two strands on top of each other)
cand_arc, cand_mar = [], []
CH = 150
for c0 in range(0, len(D), CH):
    sub = D[c0:c0 + CH + 1]; tr = cKDTree(sub[:, :2])
    dd, ii = tr.query(pix, k=1, distance_upper_bound=float(sub[:, 2].max()) + 1)
    ok = np.isfinite(dd); iic = np.where(ok, ii, 0)
    cov = ok & (dd <= sub[iic, 2])
    cand_arc.append(np.where(cov, arcs[c0 + iic], np.inf).astype(np.float32))
    cand_mar.append(np.where(cov, sub[iic, 2] - dd, -np.inf).astype(np.float32))
cand_arc = np.stack(cand_arc); cand_mar = np.stack(cand_mar)
mmax = cand_mar.max(0)
# a strand owns the pixel if it is well inside it; among strong owners the earliest wins (top strand at the crossing)
strong = cand_mar >= 0.65 * mmax[None]
arc_best = np.where(strong, cand_arc, np.inf).min(0)
edge_best = mmax
del cand_arc, cand_mar
arc = arc_best.reshape(H, W)
edge = edge_best.reshape(H, W)
zone = np.isfinite(arc)
POLYS = [
  [(420,150),(520,120),(650,125),(760,170),(830,250),(840,340),(770,430),(560,475),(420,460),(390,300)],      # loop interior
  [(790,90),(940,170),(1040,310),(1060,490),(990,600),(800,620),(690,580),(760,430)],             # cast shadow right of loop
  [(260,690),(520,610),(760,520),(860,540),(820,640),(560,700),(300,770),(120,820)],              # shadow under the band
  [(330,700),(420,720),(430,900),(400,1150),(420,1402),(330,1402),(330,1000)],                     # shadow right of tail
]
extra = np.zeros((H, W), np.uint8)
for poly in POLYS: cv2.fillPoly(extra, [np.array(poly, np.int32)], 1)
extra = (extra > 0) & ~zone
ep = pix[extra.ravel()]
d1, i1 = tree.query(ep, k=1)
dk, ik = tree.query(ep, k=48, distance_upper_bound=600)
okk = np.isfinite(dk); ikc = np.where(okk, ik, 0)
cov2 = okk & (dk <= D[ikc, 2] + 140)  # dk/ik over 48 samples is enough here (no overlapping strands in the shadow polygons)
early = np.where(cov2, arcs[ikc], np.inf).min(1)
arc[extra] = np.where(np.isfinite(early), early, arcs[i1]) + 40
edge[extra] = 0
zone = np.isfinite(arc)
print('path length', arcs[-1], 'zone px', zone.mean())

plate = pullpush(clean, ndimage.binary_dilation(zone, iterations=2))
plate = cv2.GaussianBlur(plate, (0, 0), 0.8) * zone[..., None] + plate * (~zone)[..., None]

# ---------- un-mix white elements against the clean background ----------
meta = {}
for name, (x0, y0, x1, y1) in boxes.items():
    c = src[y0:y1, x0:x1]; b = clean[y0:y1, x0:x1]
    a = np.clip((c[..., 1] - b[..., 1]) / np.maximum(255 - b[..., 1], 1), 0, 1)
    a[a < 0.02] = 0
    f = np.where(a[..., None] > 0.05, b + (c - b) / np.maximum(a[..., None], 0.05), 255)
    f = np.clip(f, 0, 255)
    rgba = np.dstack([f, a * 255]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(f'layers/t_{name}.png')
    meta[name] = [x0, y0, x1, y1]

hands = np.dstack([src, hand_a * 255]).astype(np.uint8)
ys, xs = np.nonzero(hand_a > 0); hb_box = [int(xs.min()), int(ys.min()), W, H]
Image.fromarray(hands[hb_box[1]:, hb_box[0]:], 'RGBA').save('layers/hands.png')
meta['hands'] = hb_box
meta['path_len'] = float(arcs[-1])
json.dump(meta, open('layers/meta.json', 'w'))
np.save('layers/arc.npy', arc.astype(np.float32)); np.save('layers/path.npy', np.column_stack([D, arcs]).astype(np.float32)); np.save('layers/edge.npy', edge.astype(np.float32))
Image.fromarray(np.clip(clean, 0, 255).astype(np.uint8)).save('layers/clean.png')
Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).save('layers/plate.png')
# debug: path overlay
dbg = src.copy(); dbg[zone] = dbg[zone] * 0.6 + np.array([0, 255, 0]) * 0.4
for x, y, _ in D[::10]:
    if 0 <= x < W and 0 <= y < H: cv2.circle(dbg, (int(x), int(y)), 3, (255, 255, 0), -1)
Image.fromarray(dbg.astype(np.uint8)).save('dbg_path.png')
