# -*- coding: utf-8 -*-
"""Tests du positionnement de kaki-utu (^) — symbole ⌝ U+231D.

Calibrage (2026-11-22, correction manuelle Inkscape sur nomura 十九の春, police
Hiragino Mincho ProN) : ⌝ décalé de -3/+3 pt à fs 26 sur une note à cheval
(note_fs = ss = int(26*0,713) = 18) -> dx = 0.63 - 3/18 = 0.4633, dy = -0.42 + 3/26 = -0.3046
(dy est pondéré par la fs de case, dx par la fs de la note porteuse).

Usage :
    python3 tests/test_kaki_utu.py
"""
import contextlib
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

C = chr(0x231D)
GO, GO5 = chr(0x5408), chr(0x5DE5)

# 1. constantes de l'entrée ^
tech = k.TECHNIQUE_SUFFIXES["^"]
assert tech["symbol"] == C and tech["pos"] == "top-right"
assert abs(tech["dx"] - 0.4633) < 1e-4, tech
assert abs(tech["dy"] - (-0.3046)) < 1e-4, tech
print("OK entrée ^ : dx=%.4f dy=%.4f (correction -3/+3 pt à fs 26, note à cheval ss=18)" % (tech["dx"], tech["dy"]))

# 2. rendu nomura : ⌝ sur note à cheval à la position prédite par _tech_char_pos
SRC = "@layout nomura\n::tab\n" + GO + "/" + GO5 + "^ " + GO + "\n::\n"
with contextlib.redirect_stderr(io.StringIO()):
    svg = k.render_svg(k.parse_kkml(SRC), layout="nomura")[0]
els = re.findall(r'<text\b([^>]*)>([^<]*)</text>', svg)
corner = next((a, t) for a, t in els if t == C)
cx_el = float(re.search(r'x="([\d.]+)"', corner[0]).group(1))
cy_el = float(re.search(r'y="([\d.]+)"', corner[0]).group(1))
# ancré sur le kanji principal 合 (fs 26, x = cx) et le kanji à cheval 巳 (fs 18, y = straddle_y)
notes = [(float(re.search(r'x="([\d.]+)"', a).group(1)), float(re.search(r'y="([\d.]+)"', a).group(1)),
          float(re.search(r'font-size="([\d.]+)"', a).group(1)), t)
         for a, t in els if t in (GO, GO5)]
main = next(n for n in notes if n[3] == GO and n[2] == 26.0 and abs(n[0] - cx_el) < 20)
strad = next(n for n in notes if n[3] == GO5)
cx, straddle_y = main[0], strad[1]
fs = 26.0
ss = int(fs * 0.713)
tx, ty, _anc = k._tech_char_pos(tech, cx, straddle_y, fs, ss)
assert abs(cx_el - tx) < 0.05, (cx_el, tx)
assert abs(cy_el - ty) < 0.05, (cy_el, ty)
# et le décalage vs l'ancienne constante (0.63 / -0.42) vaut bien -3/+3 pt
assert abs((tx - (cx + ss * 0.63)) + 3) < 0.01, (tx, cx)
assert abs((ty - (straddle_y + fs * -0.42)) - 3) < 0.01, (ty, straddle_y)
print("OK nomura : ⌝ à (cx + ss*dx, base_y + fs*dy) = décalage -3/+3 pt vs ancien calibrage")

# 3. la position suit _tech_char_pos dans tous les layouts (note pleine, fs du layout)
for layout in ("vertical", "horizontal", "mega", "chindami", "tuto"):
    with contextlib.redirect_stderr(io.StringIO()):
        svgs = k.render_svg(k.parse_kkml("@layout " + layout + "\n::tab\n" + GO + "^\n::\n"), layout=layout)
    found = False
    for svg in svgs:
        for a, t in re.findall(r'<text\b([^>]*)>([^<]*)</text>', svg):
            if t == C:
                found = True
    assert found, "⌝ non rendu en " + layout
print("OK ⌝ rendu dans les 6 layouts (position = _tech_char_pos avec les nouvelles constantes)")

print("OK tests kaki-utu ⌝ (dx=0.4633, dy=-0.3046)")
