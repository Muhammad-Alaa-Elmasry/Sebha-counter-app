# OsLoop brand ident (7.6 s)

`osloop_ident_1080p60.mp4` is 1920×1080, 60 fps, 7.6 s, H.264 + AAC 48 kHz.
`preview_540p.mp4` is the low-res review render.

The logo isn't revealed; it's built from its own geometry. Every moving part is a vector path
taken straight from the approved PDF (`source/approved_logo.pdf` → `source/logo_parts.json`).
No letterforms are redrawn, typed, scaled or bent. Each part is drawn by a mask that comes
from its own shape, and moves only by a short straight translation.

## Timeline (60 fps)
| Time | Frames | Event |
|---|---|---|
| 0.00–0.45 | 0–26 | Black; low tension starts from silence |
| 0.45–0.67 | 27–40 | Hard cut to paper. The orange triangle registers at the centre: 92 % → 100 %, 3° → 0°, no overshoot. Click at 0.52 |
| 1.20–1.54 | 72–92 | The triangle moves to its exact place in the wordmark |
| 1.36–3.02 | 82–181 | Construction: و loop (circle, angular sweep) → upright blade → ب bowl → س cup → ب dot (circle) → س cup → alef blade → hamza → و tail blade. Three micro-registration ticks |
| 3.04–3.12 | 182–187 | Wordmark lock: 5-frame compression of about 1.4 px, the two contact shadows set in, soft low impact |
| 3.62–3.87 | 217–232 | ميديا برودكشن: right-to-left mask plus 5 px rise (approved vector glyphs) |
| 3.9–7.6 | — | Hero hold. Nothing moves except a light drift of under 1 %. Silence from about 4.5 s. Ends on the brand, no fade |

## Integrity check
At t = 99 the final frame was rendered 1:1 on white and compared with the original artwork in the
same renderer. Geometry matches (best sub-pixel alignment 0.05 logo units; ink coverage within 0.01 %).
The only differences are anti-aliasing at the edges.

## Formats
All motion is written in logo units. A frame format is just an entry in `FORMATS` in
`ident_template.html`: `h` = 1920×1080, `v` = 1080×1920.
```
cd source
python3 build.py                                 # → ident.html
python3 sound.py                                 # → sound.wav
node render.js h 0.5 60 preview_540p.mp4 20      # low-res review
node render.js h 1 60 osloop_ident_1080p60.mp4 14
node render.js v 1 60 osloop_ident_9x16.mp4 14   # 9:16, same animation
```
Requires Node + Playwright (Chromium), ffmpeg, Python 3 with numpy / scipy / pillow.
