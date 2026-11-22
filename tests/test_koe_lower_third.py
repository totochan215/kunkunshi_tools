# -*- coding: utf-8 -*-
"""Tests de l'alignement vertical des bornes de chant (koedashi/koekiri ◯/□) en horizontal.

Règle (2026-11-22) : en layout `horizontal`, les symboles ◯/□ rendus DANS la case
(dans la case, bord droit, via `_draw_marker_line_vocal`) sont alignés en y sur la
centerline du TIERS INFÉRIEUR de la case : yk = y_top − cell_h/6 + ss·0,318
(y_top = bas de la rangée de cases). Les autres layouts ne changent pas (en vertical,
alignement sur la sous-partie de case de l'élément vocal rattaché).

Usage :
    python3 tests/test_koe_lower_third.py
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

SRC = ("@title t\n"
       "::tab\n\u5408 \u5408 \u5408\n::\n"
       "::vocal\n(\u3042 \u3044) \u3046\n::\n")

KOE_RE = re.compile(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="(\d+)"[^>]*>([\u25cb\u25a1])</text>')
RECT_RE = re.compile(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"')
NOTE_RE = re.compile(r'<text x="[\d.]+" y="([\d.]+)"[^>]*font-size="(\d+)" fill="black">\u5408</text>')


def render(layout):
    with contextlib.redirect_stderr(io.StringIO()):
        song = k.parse_kkml(SRC)
        return k.render_svg(song, layout=layout)[0]


def koe_els(svg):
    return [(float(x), float(y), int(fs), g) for x, y, fs, g in KOE_RE.findall(svg)]


# 1. horizontal : ◯ et □ présents, alignés sur la centerline du tiers inférieur de la case
sh = render("horizontal")
koe = koe_els(sh)
assert sorted(k[3] for k in koe) == ["\u25a1", "\u25cb"], koe
rect = RECT_RE.findall(sh)[0]           # 1re case de la rangée
ry, rh = float(rect[1]), float(rect[3])
y_top, cell_h = ry + rh, rh
note = NOTE_RE.search(sh)
fs = int(note.group(2))
ss = int(fs * 0.42)
y_expected = y_top - cell_h / 6 + ss * 0.318
for x, y, kfs, g in koe:
    assert kfs == ss, (kfs, ss)
    assert abs(y - y_expected) < 0.01, (g, y, y_expected)
# alignement en x sur l'élément rattaché : ( → élément après (case 1, cx=42), ) → élément avant (case 2, cx=94)
xs = {g: x for x, _y, _fs, g in koe}
assert xs["\u25cb"] == 42 and xs["\u25a1"] == 94, xs
print("OK horizontal : ◯/□ à y=%.3f = y_top − cell_h/6 + ss·0,318 (case [%g..%g], tiers inférieur)"
      % (y_expected, ry, y_top))

# 2. vertical : inchangé — alignement sur la centerline de la case (slot), pas le tiers inférieur
sv = render("vertical")
koe_v = koe_els(sv)
assert len(koe_v) == 2, koe_v
rect_v = RECT_RE.findall(sv)[0]
ry_v, rh_v = float(rect_v[1]), float(rect_v[3])
note_v = NOTE_RE.search(sv)
fs_v = int(note_v.group(2))
ss_v = int(fs_v * 0.42)
# ◯ du token "(あ" (slot 0, n=1) : case top + cell_h/2 + 0 + ss·0,318 = centerline de la case
y_center = ry_v + rh_v / 2 + ss_v * 0.318
y_lower_third = ry_v + rh_v + (-rh_v / 6) + ss_v * 0.318
for x, y, kfs, g in koe_v:
    assert abs(y - y_center) < 0.01 or abs(y - (ry_v + rh_v / 2 + rh_v * 1 + ss_v * 0.318)) < 0.01, (g, y)
assert all(abs(y - y_lower_third) > 0.5 for _x, y, _fs, _g in koe_v), "vertical a changé !"
print("OK vertical : inchangé (◯/□ sur la sous-partie de case, pas le tiers inférieur)")

# 3. tuto : render_koe off, aucun symbole
st = render("tuto")
assert not koe_els(st), "◯/□ rendu en tuto !"
print("OK tuto : pas de ◯/□ (render_koe off)")

print("OK tests koedashi/koekiri : tiers inférieur de la case en horizontal")
