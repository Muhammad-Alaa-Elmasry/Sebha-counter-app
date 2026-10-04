# October Awareness Month: 10 s animated poster

`october_awareness_1080x1350.mp4` is 1080×1350 (4:5, made for Instagram/Facebook feed), 60 fps, 10 s, H.264 + AAC.

Everything comes from the original poster pixels (`source/src.png`). The ribbon, hands, logo and text
are separated from the flat image, so the last frame is the poster itself.

## Motion
| Time | Beat |
|---|---|
| 0.0–3.0 s | The ribbon ties itself: a reveal runs along the ribbon's path (enters from the left, round the loop, down the tail) with a light catching its leading edge. The camera pulls back from a close shot |
| 2.25–3.4 s | The two hands rise from the bottom and meet |
| 2.85–3.6 s | OSLOOP logo wipes in |
| 3.25–4.1 s | "October" focus-pulls in; "Awareness" and "Month" rise into their lines |
| 4.1–4.8 s | The dot pops and the rule draws across |
| 4.45–5.4 s | "for care / for health / for tomorrow" slide in one after another |
| 5.4–10 s | Hold: slow push-in, soft floating motes, light travels through the satin twice (5.6 s and 8.1 s) |

Music is a hopeful piano and strings piece (Am → F → C → G/B → C), generated in `music.py`, with hits matched to the picture.

## Re-render
```
cd source
python3 layers.py     # → layers/ (plate, clean, ribbon path map, hands, text mattes)
python3 music.py      # → music.wav
python3 render.py --preview --out preview.mp4
python3 render.py --out october_awareness_1080x1350.mp4
```
Needs Python 3 with numpy, scipy, pillow, opencv-python-headless, and ffmpeg.
