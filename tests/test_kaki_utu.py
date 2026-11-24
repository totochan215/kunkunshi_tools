# -*- coding: utf-8 -*-
"""Tests de kaki-utu (^) — symbole ⌝ U+231D — et de l'homogénéité note_fs des techniques.

Règles (2026-11-22, ancrage coin 2026-11-23) :
- Taille ET position des caractères de technique (souhou) sont entièrement relatives
  à `note_fs` (taille réelle de la note porteuse) : tech_fs = int(note_fs·1,1·scale),
  facteur propre à chaque ornement et INDÉPENDANT de la condensation du composite.
- uchi/nuchi/kaki-utu : ancrage 'corner': 'top-right' sur le rectangle englobant de la
  note rendue : tx = cx + box_w/2 + note_fs·dx, ty = box_top + note_fs·dy
  (box_w = largeur rendue : note_fs, textLength du composite, ou max du groupe d'accord ;
  box_top = base_y − note_fs, ou sommet du membre le plus haut pour un accord).
  dx/dy sont mesurés depuis le coin (dx = ex-dx − 0,5 ; dy depuis le sommet em).
- Calibrage kaki-utu (correction manuelle Inkscape, Hiragino Mincho ProN, nomura
  十九の春) : ⌝ décalé de −3/+3 pt sur note à cheval (ss = 18) -> offset coin = 0.63 − 3/18 = 0.4633
  (dx = 0.4633 − 0,5 = −0,0367) ; dy depuis le sommet em = 1 − 0,44 = 0,56.

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
assert tech["symbol"] == C and tech["pos"] == "top-right" and tech["corner"] == "top-right"
assert abs(tech["dx"] - (-0.0367)) < 1e-4, tech
assert abs(tech["dy"] - 0.56) < 1e-4, tech
print("OK entrée ^ : dx=%.4f dy=%.4f depuis le coin haut-droit (offset effectif note seule = %.4f)" % (tech["dx"], tech["dy"], 0.5 + tech["dx"]))

# 2. _tech_char_pos, ancrage coin : tx = cx + box_w/2 + note_fs*dx, ty = box_top + note_fs*dy
#    (box_w défaut = note_fs, box_top défaut = base_y - note_fs : positions note seule préservées)
base_y, fs, note_fs = 100.0, 26.0, 18.0
tx, ty, _ = k._tech_char_pos(tech, 50.0, base_y, fs, note_fs)
assert abs(tx - (50.0 + note_fs / 2 + note_fs * tech["dx"])) < 1e-9
assert abs(ty - (base_y - note_fs + note_fs * tech["dy"])) < 1e-9
# box explicite (accord) : box_w/box_top pris en compte
tx2, ty2, _ = k._tech_char_pos(tech, 50.0, base_y, fs, note_fs, box_w=30.0, box_top=base_y - 40)
assert abs(tx2 - (50.0 + 15.0 + note_fs * tech["dx"])) < 1e-9
assert abs(ty2 - (base_y - 40 + note_fs * tech["dy"])) < 1e-9
print("OK _tech_char_pos coin : tx = cx + box_w/2 + note_fs*dx, ty = box_top + note_fs*dy")

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
        assert abs((cx_el - sx) - (ss / 2 + ss * tech["dx"])) < 0.06, (layout, cx_el - sx, ss / 2 + ss * tech["dx"])
        assert abs((cy_el - sy) - (-ss + ss * tech["dy"])) < 0.06, (layout, cy_el - sy, -ss + ss * tech["dy"])
        assert abs(tfs - int(ss * 1.1 * tech["scale"])) < 0.01, (layout, tfs)
        found = True
    assert found, "⌝/straddle non trouvés en " + layout
    print("OK %-10s : offset ⌝ = (ss·dx, ss·dy), tech_fs = int(ss·1,1·scale), ss=%d" % (layout, ss))

# 5. Accords : l'ornement s'ancre sur le coin haut-droit du GROUPE (box_w = largeur max
#    des membres, box_top = sommet em du membre le plus haut) ; taille tjrs int(note_fs*1,1*scale)
_cx, _cy, _fs = 42, 29, 22
for tok, exp_boxw in ((GO + "-" + chr(0x4E59) + "+" + chr(0x8001) + "^", None),
                      (chr(0x30A4) + GO + "-" + chr(0x4E59) + "'", None)):
    out = []
    k.render_cell(out, tok, _cx, _cy, _fs, cell_w=52, cell_h=58, opts={})
    svg5 = "".join(out)
    small = int(_fs * k.CHORD_RATIO)
    members = re.findall(r'font-size="' + str(small) + r'"[^>]*textLength="([\d.]+)"', svg5)
    box_w = max([small] + [float(t) for t in members])   # membres simples = small, composites = textLength
    step = _fs * 0.82
    n = len(re.findall(r'font-size="' + str(small) + r'"', svg5))
    box_top = (_cy - (n - 1) * step / 2) + small / 3 - small
    tech5 = k.TECHNIQUE_SUFFIXES["^" if tok.endswith("^") else "'"]
    m = re.search(r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*font-size="(\d+)"[^>]*>' + re.escape(tech5["symbol"]) + r'</text>', svg5)
    assert abs(float(m.group(1)) - (_cx + box_w / 2 + _fs * tech5["dx"])) < 1e-9, (tok, m.group(1))
    assert abs(float(m.group(2)) - (box_top + _fs * tech5["dy"])) < 1e-9, (tok, m.group(2))
    # règle (a) : taille de l'ornement = int(note_fs*1,1*scale), indépendante de la condensation
    assert int(m.group(3)) == int(_fs * 1.1 * tech5["scale"]), (tok, m.group(3))
    print("OK accord %r : coin groupe box_w=%.1f, tech_fs=%d" % (tok, box_w, int(m.group(3))))
# taille identique sur composite condensé et note seule (pas de réponse à la condensation)
for tok in (GO + "'", chr(0x30A4) + GO + "'"):
    out = []
    k.render_cell(out, tok, _cx, _cy, _fs, cell_w=52, cell_h=58, opts={})
    fss = [int(f) for f in re.findall(r'font-size="(\d+)"[^>]*>｀<', "".join(out))]
    assert fss == [int(_fs * 1.1 * k.TECHNIQUE_SUFFIXES["'"]["scale"])], (tok, fss)
print("OK taille ornement = int(note_fs*1,1*scale) quelle que soit la condensation du composite")

print("OK tests kaki-utu ⌝ + homogénéité note_fs des techniques (6 layouts)")
