"""Hopeful piano + strings bed for the October Awareness animation, hits locked to the picture."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000; DUR = 10.0; N = int(SR * DUR)
out = np.zeros((N, 2)); rng = np.random.default_rng(8)
T = lambda d: np.arange(int(d * SR)) / SR
filt = lambda x, k, f, o=2: sosfilt(butter(o, f, k, fs=SR, output='sos'), x)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def put(sig, at, g, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    out[i:i + n, 0] += sig[:n] * g * np.cos((pan + 1) * np.pi / 4) * 1.414
    out[i:i + n, 1] += sig[:n] * g * np.sin((pan + 1) * np.pi / 4) * 1.414

def piano(m, d=3.5, vel=1.0):
    f = hz(m); t = T(d); s = np.zeros_like(t)
    for h in range(1, 9):
        fh = f * h * np.sqrt(1 + 0.0004 * h * h)
        s += np.sin(2 * np.pi * fh * t + rng.random()) * (vel ** (0.4 * h)) / h ** 1.1 * np.exp(-t * (0.9 + 0.55 * h) * (1 + f / 1500))
    hammer = filt(rng.standard_normal(len(t)), 'band', [800, 5000]) * np.exp(-t * 120) * 0.08
    return (s + hammer) * (1 - np.exp(-t * 900))

def strings(ms, d, a=1.2, r=1.5):
    t = T(d); s = np.zeros_like(t)
    for m in ms:
        for det in (-0.08, 0.0, 0.07):
            f = hz(m) * 2 ** (det / 12); vib = 1 + 0.003 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6)
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            s += np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    s = filt(s, 'low', 2600)
    env = np.minimum(1, t / a) * np.clip((d - t) / r, 0, 1)
    return s * env / (len(ms) * 3)

def swell(d, f0, f1):
    n = int(d * SR); x = rng.standard_normal(n); y = np.zeros(n); B = 2048
    for i in range(0, n, B):
        p = i / n; fc = f0 * (f1 / f0) ** p
        seg = filt(x[max(0, i - 4096):i + B], 'band', [fc * 0.6, min(fc * 1.6, 20000)])
        y[i:i + B] = seg[-len(y[i:i + B]):]
    ph = np.linspace(0, 1, n)
    return y * np.sin(np.pi * ph) ** 2

# chords (C major, hopeful): Am → F → C → G/B → C
CH = [(0.0, [57, 60, 64], 45), (2.4, [53, 57, 60], 41), (4.8, [48, 55, 60, 64], 36), (7.2, [55, 59, 62], 47)]
for t0, ch, bass in CH:
    put(strings(ch + [c + 12 for c in ch[:2]], 2.9 if t0 < 7 else 2.8 + 0.2), t0, 0.16)
    put(piano(bass, 4.0, 0.9), t0, 0.20)
# piano arpeggio (eighths at 75 bpm = 0.4 s)
ARP = {0.0: [69, 72, 76, 79], 2.4: [65, 69, 72, 77], 4.8: [67, 72, 76, 79], 7.2: [67, 71, 74, 79]}
for t0, notes in ARP.items():
    seq = notes + notes[::-1][1:3]
    for i, m in enumerate(seq):
        put(piano(m, 2.5, 0.8), t0 + i * 0.4, 0.10 if t0 < 7 else 0.09, -0.3 + 0.12 * i)
# final resolve: C chord, let ring
for m, g in ((48, .18), (60, .12), (64, .10), (67, .10), (72, .09)):
    put(piano(m, 3.0, 1.0), 8.8, g)
put(strings([60, 64, 67, 72], 1.6, 0.4, 1.0), 8.6, 0.10)

# picture hits
put(swell(2.9, 300, 6000), 0.05, 0.05, -0.2)                         # ribbon ties itself
d = T(1.0); put(np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-d * 8)) / SR) * np.exp(-d * 5), 3.25, 0.22)  # hands meet
for i, t0 in enumerate([3.0, 3.35, 3.55, 4.12, 4.5, 4.67, 4.84]):    # type: soft glass ticks
    d = T(0.6); f = [2093, 1760, 1975.5, 2637, 2349, 2637, 3136][i]
    put(np.sin(2 * np.pi * f * d) * np.exp(-d * 9) * (1 - np.exp(-d * 2000)), t0, 0.035, 0.5)
for t0 in (5.6, 8.1):                                                 # light through the ribbon
    put(swell(1.9, 2500, 9000), t0, 0.025, 0.3)

# room
n = int(1.8 * SR); ti = np.arange(n) / SR
ir = filt(rng.standard_normal(n), 'low', 6000) * np.exp(-ti * 3.5); ir /= np.sqrt((ir ** 2).sum()) * 5
wet = np.stack([fftconvolve(out[:, c], ir)[:N] for c in (0, 1)], 1)
mix = out + wet * 0.7
fade = np.ones(N); fn = int(0.5 * SR); fade[-fn:] = np.linspace(1, 0, fn) ** 1.5
mix = filt(mix.T, 'high', 30).T * fade[:, None]
mix *= 0.85 / np.abs(mix).max()
wavfile.write('music.wav', SR, (mix * 32767).astype(np.int16))
print('ok')
