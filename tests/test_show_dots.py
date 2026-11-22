# -*- coding: utf-8 -*-
"""Tests : métadonnée @show_dots on|off (défaut off) — affiche ou masque les
points ・ (U+30FB) de positionnement des syllabes ::vocal dans la colonne/ligne
marker des sorties SVG (kkml2pdf hérite via render_svg).

Le point occupe toujours sa sous-partie de case dans le calcul de position :
masquer les points ne déplace JAMAIS les syllabes (test : les <text> non-・
sont identiques avec on et off).

Usage :
    python3 tests/test_show_dots.py
"""
import contextlib
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k
import kkml_clean as c

DOT = chr(0x30FB)

BASE = ("@format KKML\n@title Test dots\n::tab\n"
        + chr(0x5408) + " " + chr(0x5c3a) + "\n" + chr(0x4e2d) + " " + chr(0x5408) + "\n::\n"
        "::vocal\n. " + chr(0x3042) + chr(0x3044) + "\n- ." + chr(0x3046) + "\n::\n")

LAYOUTS = ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega")


def render(kkml, layout):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svgs = k.render_svg(k.parse_kkml(kkml), layout=layout)
    assert "WARNING" not in err.getvalue(), (layout, err.getvalue())
    return svgs


def text_lines(svgs):
    out = []
    for svg in svgs:
        out.extend(ln for ln in svg.splitlines() if ln.lstrip().startswith("<text"))
    return out


for layout in LAYOUTS:
    off = render(BASE, layout)                       # défaut : off
    on = render("@show_dots on\n" + BASE, layout)
    expoff = render("@show_dots off\n" + BASE, layout)
    joined_off = "".join(off)
    joined_on = "".join(on)
    assert DOT not in joined_off, layout            # défaut : points masqués
    assert DOT not in "".join(expoff), layout
    assert DOT in joined_on, layout                 # @show_dots on : points rendus
    # les syllabes ne bougent pas : mêmes <text> hors points ・
    assert [l for l in text_lines(off) if DOT not in l] == \
           [l for l in text_lines(on) if DOT not in l], layout
    # au moins un point ・ rendu en 'on' (le token ". あい" en contient 1)
    assert sum(l.count(">" + DOT + "<") for l in text_lines(on)) >= 1, layout
    print("OK layout %-10s : défaut off (masqué), on (rendu), syllabes immobiles" % layout)

# parsing : la méta est lue telle quelle
s = k.parse_kkml("@show_dots on\n" + BASE)
assert s.meta.get("show_dots") == "on"
s = k.parse_kkml(BASE)
assert "show_dots" not in s.meta
print("OK parsing : @show_dots stockée dans song.meta")

# cleaner : la méta est conservée telle quelle
out = c.clean("@format KKML\n@show_dots on\n::tab\n" + chr(0x5408) + "\n::\n")
assert "@show_dots on" in out, out
print("OK cleaner : @show_dots conservée")

print("Tous les tests de test_show_dots.py passent.")
