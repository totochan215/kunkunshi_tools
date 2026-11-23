# -*- coding: utf-8 -*-
"""Tests de kaki-utu (^) — symbole ⌝ U+231D — et de l'homogénéité note_fs des techniques.

Règles (2026-11-22) :
- Taille ET position des caractères de technique (souhou) sont entièrement relatives
  à `note_fs` (taille réelle de la note porteuse) : tech_fs = int(note_fs·1,1·scale),
  tx = cx ± note_fs·dx, ty = baseline + note_fs·dy (idem drop, retrait 0,34) —
  homogène entre toutes les mises en page (mêmes constantes globales TECHNIQUE_SUFFIXES,
  chaque glyphe garde ses propres offsets selon sa forme).
- Calibrage kaki-utu (correction manuelle Inkscape, Hiragino Mincho ProN, nomura
  十九の春) : ⌝ décalé de −3/+3 pt sur note à cheval (ss = 18) -> dx = 0.63 − 3/18 = 0.4633 ;
  l'ancien dy était × fs de case (26) : dy = (26·(−0,42)+3)/18 = −0,44 (maintenant × note_fs).

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


def render(layout, src):
    with contextlib.redirect_stderr(io.StringIO()):
        return k.render_svg(k.parse_kkml(src), layout=layout)


def els(svg):
    return re.findall(r'<text\b([^>]*)>([^<]*)</text>', svg)


def num(attrs, name):
    return float(re.search(name + r'="([\d.]+)"', attrs).group(1))


# 1. constantes de l'entrée ^
tech = k.TECHNIQUE_SUFFIXES["^"]
assert tech["symbol"] == C and tech["pos"] == "top-right"
assert abs(tech["dx"] - 0.4633) < 1e-4, tech
assert abs(tech["dy"] - (-0.44)) < 1e-4, tech
print("OK entrée ^ : dx=%.4f dy=%.4f (relatifs à note_fs ; correction −3/+3 pt à ss=18)" % (tech["dx"], tech["dy"]))

# 2. _tech_char_pos : ty = base_y + note_fs*dy (plus fs*dy)
base_y, fs, note_fs = 100.0, 26.0, 18.0
tx, ty, _ = k._tech_char_pos(tech, 50.0, base_y, fs, note_fs)
assert abs(tx - (50.0 + note_fs * tech["dx"])) < 1e-9
assert abs(ty - (base_y + note_fs * tech["dy"])) < 1e-9
print("OK _tech_char_pos : tx/ty en fractions de note_fs (fs ignoré pour les offsets)")

# 3. nomura : ⌝ sur note à cheval = correction utilisateur exacte (−3/+3 pt vs main)
SRC = "@layout nomura\n::tab\n" + GO + "/" + GO5 + "^ " + GO + "\n::\n"
svg = render("nomura", SRC)[0]
corner = next(a for a, t in els(svg) if t == C)
cx_el, cy_el = num(corner, "x"), num(corner, "y")
notes = [(num(a, "x"), num(a, "y"), num(a, "font-size"), t) for a, t in els(svg) if t in (GO, GO5)]
main = next(n for n in notes if n[3] == GO and n[2] == 26.0 and abs(n[0] - cx_el) < 20)
strad = next(n for n in notes if n[3] == GO5)
cx, straddle_y, ss = main[0], strad[1], int(strad[2])
tx, ty, _ = k._tech_char_pos(tech, cx, straddle_y, 26.0, ss)
assert abs(cx_el - tx) < 0.05 and abs(cy_el - ty) < 0.05, (cx_el, cy_el, tx, ty)
# décalage vs l'ancien calibrage (main : dx x ss, dy x fs=26) = exactement -3/+3 pt
assert abs((tx - (cx + ss * 0.63)) + 3) < 0.01, (tx, cx)
assert abs((ty - (straddle_y + 26.0 * -0.42)) - 3) < 0.01, (ty, straddle_y)
print("OK nomura : ⌝ décalé de −3/+3 pt exactement (ss=%d)" % ss)

# 4. homogénéité entre les 6 layouts : offset ⌝/note-à-cheval == (ss·dx, ss·dy),
#    taille du glyphe == int(ss·1,1·scale) — mêmes valeurs relatives partout
for layout in ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega"):
    src = "@layout " + layout + "\n::tab\n" + GO + "/" + GO5 + "^ " + GO + "\n::\n"
    found = False
    for svg in render(layout, src):
        ee = els(svg)
        cs = [a for a, t in ee if t == C]
        if not cs:
            continue
        corner = cs[0]
        cx_el, cy_el = num(corner, "x"), num(corner, "y")
        tfs = num(corner, "font-size")
        strads = [(num(a, "x"), num(a, "y"), num(a, "font-size")) for a, t in ee if t == GO5]
        if not strads:
            continue
        sx, sy, ssfs = strads[0]
        ss = int(ssfs)
        assert abs((cx_el - sx) - ss * tech["dx"]) < 0.06, (layout, cx_el - sx, ss * tech["dx"])
        assert abs((cy_el - sy) - ss * tech["dy"]) < 0.06, (layout, cy_el - sy, ss * tech["dy"])
        assert abs(tfs - int(ss * 1.1 * tech["scale"])) < 0.01, (layout, tfs)
        found = True
    assert found, "⌝/straddle non trouvés en " + layout
    print("OK %-10s : offset ⌝ = (ss·dx, ss·dy), tech_fs = int(ss·1,1·scale), ss=%d" % (layout, ss))

print("OK tests kaki-utu ⌝ + homogénéité note_fs des techniques (6 layouts)")
