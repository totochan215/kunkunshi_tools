# -*- coding: utf-8 -*-
"""Tests de l'alignement bas du @choshi en mega et nomura (chindami le fait déjà).

Règle (2026-11-22) : comme en chindami (fy1 − 4 − len·16), le @choshi est rendu en
bas de la colonne titre, première baseline à grid_bottom − 4 − len(choshi)·espacement :
- mega : grid_bottom = bas du 2e bloc, répété sur chaque page (tablature et paroles) ;
- nomura : grid_bottom = grid_y0 + grid_h (page 1, colonne titre).

Usage :
    python3 tests/test_choshi_align.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

TXT = re.compile(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*fill="#555"[^>]*>([^<]+)</text>')


def tuning_chars(svg, chars):
    return [(float(x), float(y), c) for x, y, c in TXT.findall(svg)
            if len(c) == 1 and c in chars]


GO = "合"
SRC = "@title t\n@choshi 本調子\n::tab\n" + " ".join([GO] * 12) + "\n::\n"

# 1. mega : @choshi en bas de colonne, bas ancré sur le bas de la grille, sur chaque page
spec = k.MEGA
cell_h = ((spec.page_h - 2 * spec.margin_t - (spec.blocks - 1) * spec.block_gap)
          / (spec.blocks * spec.cells_per_dan))
grid_bottom = (spec.margin_t + spec.blocks * spec.cells_per_dan * cell_h
               + (spec.blocks - 1) * spec.block_gap)
sp = spec.u(spec.tuning_spacing)
svgs = k.render_svg(k.parse_kkml(SRC), layout="mega")
for s in svgs:
    tc = tuning_chars(s, set("本調子"))
    assert len(tc) == 3, tc
    assert abs(max(y for _, y, _ in tc) - (grid_bottom - 4 - sp)) < 0.01
print("OK mega : @choshi en bas de la colonne titre, ancré sur le bas de la grille, chaque page")

# 2. nomura : page 1, colonne titre, ancré sur le bas de la grille
spec = k.NOMURA
fx0, fy0, fx1, fy1 = spec.frame_rect()
hx0, hy0, hx1, hy1 = spec.hanmen_rect()
cell_h = (fy1 - fy0 - 2 * spec.dan_gap) / spec.cells_per_dan
grid_bottom = hy0 + spec.cells_per_dan * cell_h
tab8 = "::tab\n" + "\n".join([" ".join([GO] * 12)] * 8) + "\n::\n"
svgs = k.render_svg(k.parse_kkml("@title t\n@choshi 本調子\n" + tab8), layout="nomura")
assert len(svgs) == 2
tc = tuning_chars(svgs[0], set("本調子"))
assert len(tc) == 3, tc
assert abs(max(y for _, y, _ in tc) - (grid_bottom - 4 - 20.0)) < 0.01
assert not tuning_chars(svgs[1], set("本調子"))   # colonne titre = page 1 seule
print("OK nomura : @choshi en bas de la colonne titre (page 1), ancré sur le bas de la grille")

# 3. chindami : @choshi en bas, même fs que le titre (17,5), dernière baseline à 2,3 cm du bord bas page
#     (ancrage page, recueil Chindami Kunkunshi Hyoukashuu 2026-11-24)
spec = k.CHINDAMI
svgs = k.render_svg(k.parse_kkml(SRC), layout="chindami")
m = re.search(r'<text\b[^>]*\sy="([^"]+)"[^>]*font-size="([\d.]+)"[^>]*>本調子</text>', svgs[0])
assert m, svgs[0][:400]
last_y = float(m.group(1).split()[-1])
assert m.group(2) == "17.5", m.group(2)   # fs @choshi = fs titre
assert abs(last_y - (spec.page_h - 2.3 * k.CM)) < 0.01, (last_y, spec.page_h)
print("OK chindami : @choshi en bas, baseline à 2,3 cm du bord bas page, fs = fs titre (17,5)")

# 4. vertical/horizontal : le @choshi reste sous le titre (en haut), inchangés
for layout in ("vertical", "horizontal"):
    svgs = k.render_svg(k.parse_kkml(SRC), layout=layout)
    assert "本調子" in svgs[0], layout
print("OK vertical/horizontal : @choshi inchangé (sous le titre)")

print("\nTous les tests d'alignement bas du @choshi passent.")
