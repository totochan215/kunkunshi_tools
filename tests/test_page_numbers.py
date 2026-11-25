# -*- coding: utf-8 -*-
"""Tests des numéros de page auto-incrémentés –n– (nomura/chindami/mega) avec @page_base.

Règles (2026-11-22) :
- nomura/chindami/mega : chaque page porte –n–, n = @page_base (défaut 1) + index de page ;
- nomura : hors du cadre, juste au-dessus (baseline fy0 - 4) ; n pair -> aligné à gauche
  du cadre (x=fx0, start), n impair -> aligné à droite (x=fx1, end) ;
- chindami : centré (x = page_w/2), à mi-hauteur entre le bas de la grille et le bas de la page ;
- mega : centré, à mi-distance entre le bas du 2e bloc de tablature et le bord bas de la
  feuille ; même hauteur sur une page ne contenant que des paroles ;
- vertical/horizontal/tuto : pas de numéro de page ;
- @page_base invalide (< 1 ou non entier) -> WARNING + défaut 1 ; forme collée @page_baseN
  reconnue ; le cleaner conserve @page_base (idempotent).

Usage :
    python3 tests/test_page_numbers.py
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
import kkml_clean as c

PNO_RE = re.compile(
    r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="(\w+)"[^>]*font-size="([\d.]+)" fill="[^"]*">–(\d+)–</text>')


def page_nos(svg):
    return PNO_RE.findall(svg)


def render(src, layout):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svgs = k.render_svg(k.parse_kkml(src), layout=layout)
    return svgs, err.getvalue()


GO = "合"
MEDLEY = open("tests/fixtures/synthetic/medley-samples.kkml", encoding="utf-8").read()

# 1. mega : 2 pages, –1– –2–, centrés, même y (mi-distance bas du 2e bloc / bord bas feuille)
svgs, err = render(MEDLEY, "mega")
assert len(svgs) == 2 and "WARNING" not in err, (len(svgs), err)
p1, p2 = page_nos(svgs[0])[0], page_nos(svgs[1])[0]
assert p1[4] == "1" and p2[4] == "2", (p1, p2)
assert p1[2] == "middle" and abs(float(p1[0]) - k.MEGA.page_w / 2) < 0.01
assert p1[1] == p2[1], (p1, p2)
spec = k.MEGA
cell_h = ((spec.page_h - 2 * spec.margin_t - (spec.blocks - 1) * spec.block_gap)
          / (spec.blocks * spec.cells_per_dan))
grid_bottom = (spec.margin_t + spec.blocks * spec.cells_per_dan * cell_h
               + (spec.blocks - 1) * spec.block_gap)
assert abs(float(p1[1]) - ((grid_bottom + spec.page_h) / 2 + spec.page_no_fs * 0.35)) < 0.01
print("OK mega : –n– centré, mi-distance bas du 2e bloc / bord bas feuille, n auto-incrémenté")

# 2. @page_base 5 -> –5– –6– ; forme collée @page_base7 -> 7, 8
svgs, _ = render("@page_base 5\n" + MEDLEY, "mega")
assert [page_nos(s)[0][4] for s in svgs] == ["5", "6"]
svgs, _ = render("@page_base7\n" + MEDLEY, "mega")
assert [page_nos(s)[0][4] for s in svgs] == ["7", "8"]
print("OK @page_base (et forme collée) : la 1re page porte @page_base")

# 3. @page_base invalide -> WARNING + défaut 1
for bad in ("0", "-3", "abc"):
    svgs, err = render(f"@page_base {bad}\n::tab\n{GO}\n::\n", "mega")
    assert "WARNING" in err and "@page_base" in err, (bad, err)
    assert page_nos(svgs[0])[0][4] == "1", (bad,)
print("OK @page_base < 1 ou non entier : WARNING + défaut 1")

# 4. mega page paroles seules : même hauteur de numéro que les pages de tablature
lyr = "\n\n".join("一、" + "あいうえおかきくけこさしすせそ" * 3 for _ in range(12))
src = "@title t\n::tab\n" + " ".join([GO] * 12) + "\n::\n::lyrics\n" + lyr + "\n::\n"
svgs, _ = render(src, "mega")
assert len(svgs) == 2, len(svgs)
ys = {page_nos(s)[0][1] for s in svgs}
assert len(ys) == 1, ys
assert [page_nos(s)[0][4] for s in svgs] == ["1", "2"]
print("OK mega : même hauteur de numéro sur une page paroles seules")

# 5. nomura : hors cadre en haut, alterné gauche/droite selon la parité de n
tab8 = "::tab\n" + "\n".join([" ".join([GO] * 12)] * 8) + "\n::\n"
spec = k.NOMURA
fx0, fy0, fx1, fy1 = spec.frame_rect()
svgs, _ = render(tab8, "nomura")
assert len(svgs) == 2, len(svgs)
n1, n2 = page_nos(svgs[0])[0], page_nos(svgs[1])[0]
assert n1[4] == "1" and n2[4] == "2"
assert n1[2] == "end" and abs(float(n1[0]) - fx1) < 0.01
assert n2[2] == "start" and abs(float(n2[0]) - fx0) < 0.01
assert abs(float(n1[1]) - (fy0 - 8)) < 0.01 and float(n1[1]) < fy0
assert n1[3] == "13", n1   # nomura : fs 13 = taille des métadonnées (champ page_no_fs indépendant)
svgs, _ = render("@page_base 2\n" + tab8, "nomura")
n1, n2 = page_nos(svgs[0])[0], page_nos(svgs[1])[0]
assert n1[4] == "2" and n1[2] == "start" and n2[4] == "3" and n2[2] == "end", (n1, n2)
print("OK nomura : –n– au-dessus du cadre, n pair -> gauche, impair -> droite, @page_base")

# 6. chindami : centré en x, baseline à 0,7 cm du bord bas (recueil 2026-11-24), fs 10, auto-incrémenté
svgs, err = render(MEDLEY, "chindami")
assert len(svgs) > 1 and "WARNING" not in err, (len(svgs), err)
spec = k.CHINDAMI
fx0, fy0, fx1, fy1 = spec.frame_rect()
grid_bottom = fy0 + spec.cells_per_dan * spec.cell_h
p0 = page_nos(svgs[0])[0]
assert p0[4] == "1" and p0[2] == "middle" and abs(float(p0[0]) - spec.page_w / 2) < 0.01
assert p0[3] == "10" and abs(float(p0[1]) - (spec.page_h - 0.7 * k.CM)) < 0.01, p0   # fs 10, baseline à 0,7 cm du bord bas
assert [page_nos(s)[0][4] for s in svgs] == [str(i + 1) for i in range(len(svgs))]
print("OK chindami : –n– centré en x, baseline à 0,7 cm du bord bas, fs 10, auto-incrémenté")

# 7. layouts libres : pas de numéro de page
for layout in ("vertical", "horizontal", "tuto"):
    svgs, _ = render(MEDLEY, layout)
    assert all(not page_nos(s) for s in svgs), layout
print("OK vertical/horizontal/tuto : aucun numéro de page")

# 8. cleaner : @page_base conservé (forme collée comprise), idempotent
out = c.clean("@page_base 12\n@title t\n::tab\n" + GO + "\n::\n")
assert "@page_base 12" in out, out
out2 = c.clean("@page_base12\n::tab\n" + GO + "\n::\n")
assert "@page_base 12" in out2, out2
assert c.clean(out) == out and c.clean(out2) == out2
print("OK cleaner : @page_base conservé (forme collée comprise), idempotent")

print("\nTous les tests de numéros de page passent.")
