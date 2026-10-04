"""OsLoop ident — minimal sound bed. Cue times are locked to the timeline in ident.html."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 7.6
N = int(SR * DUR)
out = np.zeros((N, 2))
rng = np.random.default_rng(11)

CUES = dict(tri_lock=0.52, reg1=1.70, reg2=2.34, reg3=2.50, lock=3.04, desc=3.66)

def T(d): return np.arange(int(d * SR)) / SR
def filt(x, kind, f, o=2): return sosfilt(butter(o, f, kind, fs=SR, output='sos'), x)

def place(sig, at, gain, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
    out[i:i + n, 0] += sig[:n] * gain * l
    out[i:i + n, 1] += sig[:n] * gain * r

def click(f1=2100, f2=3900, body=150, d=0.25):
    t = T(d)
    trans = filt(rng.standard_normal(len(t)), 'high', 2500) * np.exp(-t * 900)
    res = 0.5 * np.sin(2 * np.pi * f1 * t) * np.exp(-t * 160) + 0.25 * np.sin(2 * np.pi * f2 * t) * np.exp(-t * 260)
    thump = np.sin(2 * np.pi * np.cumsum(body * (0.65 + 0.35 * np.exp(-t * 40))) / SR) * np.exp(-t * 45)
    s = 0.7 * trans + res + 0.9 * thump
    return s / np.abs(s).max()

def impact(d=2.6):
    t = T(d)
    f = 46 + 26 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - np.exp(-t * 400)) * np.exp(-t * 2.4)
    knock = filt(rng.standard_normal(len(t)), 'low', 260) * np.exp(-t * 28)
    knock /= np.abs(knock).max()
    tick = click(1600, 3000, 110, d)[:len(t)] * 0.18
    s = sub + 0.35 * knock + tick
    return s / np.abs(s).max()

# low-frequency tension: starts from silence, sits under the build, dissolves into the lock
t = T(DUR)
ten = 0.7 * np.sin(2 * np.pi * 41 * t) + 0.3 * np.sin(2 * np.pi * 61.5 * t + 1.0)
ten *= 1 + 0.08 * np.sin(2 * np.pi * 0.9 * t)
air = filt(rng.standard_normal(N), 'band', [180, 900]) * 0.05
env = np.clip(t / 1.4, 0, 1) ** 1.6 * np.clip((3.6 - t) / 0.9, 0, 1) ** 2   # gone shortly after lock
bed = (ten + air) * env
place(bed, 0, 0.10)

place(click(), CUES['tri_lock'], 0.42)                              # triangle registration
place(click(2600, 4700, 190, 0.2), CUES['reg1'], 0.13, -0.15)       # micro registrations
place(click(2350, 4300, 170, 0.2), CUES['reg2'], 0.11, 0.25)
place(click(2900, 5200, 210, 0.2), CUES['reg3'], 0.09, 0.4)
place(impact(), CUES['lock'], 0.62)                                 # wordmark lock
d = T(0.3)
brush = filt(rng.standard_normal(len(d)), 'band', [1800, 7000]) * np.sin(np.pi * np.clip(d / 0.22, 0, 1)) ** 2
place(brush / np.abs(brush).max() * 0.6 + click(3200, 5600, 0, 0.3)[:len(d)] * 0.4, CUES['desc'], 0.05, 0.2)

# small, dark room: keeps it physical without a cinematic tail
n = int(0.7 * SR); ti = np.arange(n) / SR
ir = filt(rng.standard_normal(n), 'low', 4000) * np.exp(-ti * 9)
ir /= np.sqrt((ir ** 2).sum()) * 6
wet = np.stack([fftconvolve(out[:, c], ir)[:N] for c in (0, 1)], 1)
mix = out + wet * 0.8
mix = filt(mix.T, 'high', 25).T                                     # remove sub-rumble DC
mix *= 0.80 / np.abs(mix).max()                                     # ≈ -2 dBFS peak, no limiting
wavfile.write('sound.wav', SR, (mix * 32767).astype(np.int16))
print('peak', np.abs(mix).max(), 'last 3s rms', np.sqrt((mix[-3 * SR:] ** 2).mean()))
