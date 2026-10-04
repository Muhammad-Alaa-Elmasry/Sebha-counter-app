# Osloop Media Production — 15s logo reveal

`osloop_logo_reveal.mp4` — 1920×1080, 60 fps, 15 s, H.264 + AAC with a soundtrack generated in code.

## Timeline
| Time | Beat |
|---|---|
| 0.0–2.7s | Dark cinematic space: the orange play-triangle spins in, with sonar rings, light rays and an anamorphic flare |
| 2.7–3.7s | Wind-up, then the triangle zooms into the camera (orange fills the frame) and hits with a boom |
| 3.6–4.4s | Brand-palette stripes sweep right→left and reveal a white scene |
| 4.3–7.3s | Logo builds right→left (Arabic reading order): alef rises, hamza bounces, س wipes in, the slanted stroke slices down, و spins in, ب slides, its dot drops, and the triangle flies back and locks in with sparks |
| 7.4–8.8s | "ميديا برودكشن" reveals glyph by glyph |
| 9.0–15s | Hero hold: 3D settle, slow push-in, light shine sweeps at 9s and 13s |

## Re-render
Requires Node with Playwright/Chromium, ffmpeg, and Python with numpy/scipy.
```
cd source
python3 make.py            # builds anim.html from template.html + logo.json
node render.js             # -> video_silent.mp4
python3 audio.py           # -> audio.wav
ffmpeg -i video_silent.mp4 -i audio.wav -c:v copy -c:a aac -b:a 256k -shortest osloop_logo_reveal.mp4
```
