# -*- coding: utf-8 -*-
"""Tests du layout mega : @mega_cols (colonnes par bloc) et sauts ::block/::page.

Implémenté le 2026-11-21 :
- `@mega_cols N` = nombre de colonnes (dans) par bloc horizontal en mega
  (défaut 32, spec MEGA) ; la géométrie (cell_w, pagination) s'adapte ;
- `::block` ferme le bloc courant et `::page` ferme la page courante, même
  si les colonnes prévues ne sont pas remplies (marqueurs sans contenu,
  ignorés par les autres layouts).

Usage :
    python3 tests/test_mega_breaks.py
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

# 1. _mega_paginate : sans marqueur = comportement historique (blocs de 32, pages de 64)
s = [("c%d" % i,) for i in range(70)]
pages = k._mega_paginate(s, 32, 2, 64)
assert [[len(b) for b in p] for p in pages] == [[32, 32], [6]], pages
print("OK _mega_paginate : sans marqueur, blocs de 32 / pages de 64 (inchangé)")

# 2. ::block ferme le bloc courant même non plein
s2 = [("c%d" % i,) for i in range(10)] + [("__block__",)] + [("c%d" % i,) for i in range(10, 70)]
pages = k._mega_paginate(s2, 32, 2, 64)
assert [[len(b) for b in p] for p in pages] == [[10, 32], [28]], pages
print("OK ::block : saut au bloc suivant (bloc de 10 puis 32)")

# 3. ::page ferme la page courante même non pleine
s3 = [("c%d" % i,) for i in range(10)] + [("__page__",)] + [("c%d" % i,) for i in range(10, 70)]
pages = k._mega_paginate(s3, 32, 2, 64)
assert [[len(b) for b in p] for p in pages] == [[10], [32, 28]], pages
print("OK ::page : saut à la page suivante (page de 10 colonnes)")

# 4. @mega_cols change la pagination (33 colonnes/bloc -> 66/page)
pages = k._mega_paginate([("c%d" % i,) for i in range(130)], 33, 2, 66)
assert [[len(b) for b in p] for p in pages] == [[33, 33], [33, 31]], pages
print("OK _mega_paginate : 33 colonnes/bloc -> pages de 66")

# 5. Parsing : ::block / ::page = blocs marqueurs (sans contenu)
song = k.parse_kkml("::tab\n合\n::\n::block\n::tab\n工\n::\n::page\n::tab\n合\n::\n")
assert [b.kind for b in song.blocks] == ["tab", "block", "tab", "page", "tab"]
print("OK parse ::block / ::page")

# 6. E2E mega : @mega_cols 33 (130 dans -> 2 pages au lieu de 3) et ::block
tab130 = " ".join(["合"] * 12 * 130)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    p_def = k.render_svg(k.parse_kkml("@title t\n@layout mega\n::tab\n" + tab130 + "\n::\n"),
                         layout="mega")
    p_33 = k.render_svg(k.parse_kkml(
        "@title t\n@layout mega\n@mega_cols 33\n::tab\n" + tab130 + "\n::\n"), layout="mega")
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert len(p_def) == 3 and len(p_33) == 2, (len(p_def), len(p_33))
print("OK e2e @mega_cols 33 : 130 dans -> 2 pages (3 par défaut)")

kkml_b = ("@title t\n@layout mega\n::tab\n" + " ".join(["合"] * 480) + "\n::\n::block\n"
          "::tab\n" + " ".join(["工"] * 480) + "\n::\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    pages_b = k.render_svg(k.parse_kkml(kkml_b), layout="mega")
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert len(pages_b) == 2
print("OK e2e ::block : rendu mega 2 pages sans avertissement")

# 7. @mega_cols invalide -> AVERTISSEMENT + défaut
err = io.StringIO()
with contextlib.redirect_stderr(err):
    k.render_svg(k.parse_kkml("@title t\n@layout mega\n@mega_cols abc\n::tab\n合\n::\n"),
                 layout="mega")
assert "AVERTISSEMENT" in err.getvalue() and "@mega_cols" in err.getvalue()
print("OK @mega_cols invalide : AVERTISSEMENT + défaut 32")

print("\nTous les tests mega (@mega_cols, ::block/::page) passent.")
