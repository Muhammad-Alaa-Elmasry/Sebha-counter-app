import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 15.0
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(5)

def t_arr(d): return np.arange(int(d * SR)) / SR

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[i:i+n] += sig[:n] * gain * l * 1.414
    R[i:i+n] += sig[:n] * gain * r * 1.414

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)

def env(n, a, d, curve=4):
    e = np.ones(n); ia = int(a * SR)
    if ia: e[:ia] = np.linspace(0, 1, ia)
    rest = n - ia
    e[ia:] = np.exp(-curve * np.linspace(0, 1, rest)) if d else 1
    return e

def sweep_noise(d, f0, f1, q=0.5):
    """noise through a band-pass whose centre glides f0->f1 (block-wise)"""
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n); B = 1024
    for s in range(0, n, B):
        p = s / n; fc = f0 * (f1 / f0) ** p
        lo = max(30, fc * (1 - q)); hi = min(SR / 2 - 100, fc * (1 + q))
        seg = x[max(0, s - 2048):s + B]
        y = bp(seg, lo, hi); out[s:s + B] = y[-len(out[s:s + B]):]
    return out

def whoosh(d, f0, f1, peak=0.6):
    n = int(d * SR); x = sweep_noise(d, f0, f1)
    ph = np.linspace(0, 1, n); e = np.where(ph < peak, (ph / peak) ** 2, ((1 - ph) / (1 - peak)) ** 1.5)
    return x * e / (np.abs(x).max() + 1e-9)

def boom(d=2.2, f0=90, f1=32):
    t = t_arr(d); f = f1 + (f0 - f1) * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    s += 0.5 * np.tanh(3 * s)
    click = lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 40) * 0.6
    return s + click

def pluck(f, d=0.6, bright=4.0):
    t = t_arr(d); s = np.zeros_like(t)
    for h in range(1, 6): s += np.sin(2 * np.pi * f * h * t) / h ** 1.3 * np.exp(-t * bright * h)
    return s * env(len(t), 0.003, 1, 1)

def bell(f, d=2.5):
    t = t_arr(d); s = np.zeros_like(t)
    for ratio, amp, dec in [(1, 1, 1.6), (2.76, .45, 3.0), (5.4, .25, 5.0), (8.93, .12, 8.0)]:
        s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * dec)
    return s * env(len(t), 0.002, 1, 0)

def pad(freqs, d, a=1.5, rel=2.0):
    t = t_arr(d); s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * t + rng.random() * 6) + 0.3 * np.sin(4 * np.pi * ff * t)
    s = lp(s, 2200)
    e = np.minimum(1, t / a) * np.minimum(1, (d - t) / rel)
    return s * e / len(freqs)

def riser(d, f0, f1):
    t = t_arr(d); f = f0 * (f1 / f0) ** (t / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return s * (t / d) ** 2

# --- Scene A: dark intro ---
add(pad([73.42, 110.0, 146.83, 220.0], 3.9, a=0.8, rel=0.25), 0.0, 0.16)                 # D drone
add(bell(587.33, 3.0), 0.25, 0.10, 0.0)                                                   # triangle appears
add(whoosh(1.2, 300, 2500, 0.8), 0.15, 0.25, 0.0)
for i, tt in enumerate([0.5, 0.92, 1.34, 1.76, 2.18, 2.6]):                               # sonar rings
    add(bell([880, 1174.7, 1318.5, 1760][i % 4], 1.6) * 0.5, tt, 0.05, (-1) ** i * 0.4)
add(whoosh(2.0, 120, 900, 0.7), 1.0, 0.12, -0.3)                                          # flare
add(riser(1.6, 110, 880), 2.1, 0.12)                                                      # riser
add(sweep_noise(1.6, 400, 9000) * np.linspace(0, 1, int(1.6 * SR)) ** 3 * 0.12, 2.1, 1.0)
add(whoosh(0.5, 200, 6000, 0.9), 3.25, 0.5)                                               # zoom into camera

# --- Transition impact ---
add(boom(), 3.70, 0.9)
add(whoosh(0.9, 6000, 300, 0.05), 3.70, 0.30)
for i in range(6):                                                                        # band swishes
    add(whoosh(0.32, 900, 4500, 0.5), 3.58 + i * 0.06, 0.16, 0.8 - i * 0.32)

# --- Scene B music bed ---
add(pad([87.31, 130.81, 174.61, 220.0, 261.63], 11.4, a=1.2, rel=2.5), 3.6, 0.13)         # F maj9-ish
beat = 60 / 120
for k in range(int((15 - 4.3) / beat)):                                                   # soft pulse kick
    tt = 4.3 + k * beat
    if tt > 14.2: break
    add(boom(0.5, 120, 45) * 0.5, tt, 0.18 * (1 if tt < 12 else (14.2 - tt) / 2.2))
for k in range(int((14 - 7.3) / (beat / 2))):                                             # shimmering arp
    tt = 7.3 + k * beat / 2
    f = [523.25, 659.25, 783.99, 1046.5, 783.99, 659.25][k % 6]
    add(pluck(f, 0.5, 6), tt, 0.05 * min(1, (14 - tt) / 1.5), 0.5 * np.sin(k))

# --- Logo build hits (RTL) ---
add(whoosh(0.4, 400, 3000, 0.8), 4.25, 0.22, 0.7)    # alef
add(pluck(392, 0.4), 4.82, 0.18, 0.7)
add(pluck(784, 0.25), 4.9, 0.10, 0.7)                # hamza bounces
add(pluck(784, 0.2), 5.12, 0.06, 0.7)
add(whoosh(0.5, 2500, 500, 0.6), 4.75, 0.18, 0.4)    # seen wipe
add(whoosh(0.42, 800, 7000, 0.92), 5.1, 0.35, 0.0)   # stroke slice
add(boom(0.9, 160, 50), 5.52, 0.45)                  # stroke impact
add(lp(rng.standard_normal(int(0.08 * SR)), 6000) * np.exp(-np.arange(int(0.08 * SR)) / SR * 50), 5.52, 0.3)
add(whoosh(0.6, 300, 2200, 0.7), 5.35, 0.18, -0.2)   # waw swirl
add(whoosh(0.55, 1800, 400, 0.6), 5.65, 0.18, -0.6)  # baa
for i, (tt, g) in enumerate([(6.27, .22), (6.52, .12), (6.66, .06)]):                    # dot bounces
    add(pluck(196 * (1 + i * .05), 0.35, 8), tt, g, -0.5); add(boom(0.25, 140, 60), tt, g * 0.4, -0.5)
add(whoosh(0.8, 5000, 600, 0.85), 6.45, 0.25, -0.2)  # triangle returning
add(boom(1.6, 110, 40), 7.25, 0.6)                   # triangle lock
for i, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
    add(bell(f, 2.2), 7.25 + i * 0.05, 0.07, (-0.3 + i * 0.2))
for n in range(12):                                                                       # subtitle ticks
    add(pluck(2093 + n * 40, 0.12, 30), 7.42 + n * 0.085, 0.035, 0.6 - n * 0.1)

# --- Shine shimmers ---
for st in (9.0, 13.0):
    add(sweep_noise(1.0, 3000, 12000) * np.sin(np.linspace(0, np.pi, SR)) * 0.08, st, 1.0, 0)
    for i, f in enumerate([1568, 2093, 2637, 3136]):
        add(bell(f, 1.5) * 0.4, st + 0.15 + i * 0.12, 0.05, -0.6 + i * 0.4)

add(bell(523.25, 3.5) + bell(784, 3.5) * 0.6, 12.0, 0.06)                                 # final resolve

# --- reverb + master ---
def reverb(x, d=2.2):
    n = int(d * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2); ir = lp(ir, 5000); ir /= np.abs(ir).sum() ** 0.5 * 12
    return fftconvolve(x, ir)[:len(x)]
L2 = L + reverb(L) * 0.9; R2 = R + reverb(R[::-1])[::-1] * 0 + reverb(R) * 0.9
mix = np.stack([L2, R2], 1)
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
fade = np.ones(N); fn = int(0.6 * SR); fade[-fn:] = np.linspace(1, 0, fn) ** 2
mix *= fade[:, None]
mix *= 0.89 / np.abs(mix).max()
wavfile.write('audio.wav', SR, (mix * 32767).astype(np.int16))
print('ok', np.abs(mix).max())
