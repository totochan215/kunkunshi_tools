# -*- coding: utf-8 -*-
"""Tests de l'alias ::song -> ::section (nom de chanson en medley mega).

Implémenté le 2026-11-21 : `::song <nom>` est accepté comme alias de
`::section <nom>` (info stderr, comme les autres alias), pour que les medleys
nommés en `::song` (ex. samples/kkml/medley-samples.kkml) rendent bien les
titres de chanson au-dessus des colonnes en layout mega.

Usage :
    python3 tests/test_song_section.py
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
import kkml_cleaner as c

# 1. Parsing : ::song -> section avec label
err = io.StringIO()
with contextlib.redirect_stderr(err):
    song = k.parse_kkml("::song 南島節\n::tab\n合 工\n::\n")
assert [(b.kind, b.label) for b in song.blocks] == [("section", "南島節"), ("tab", None)]
assert "::song" in err.getvalue() and "::section" in err.getvalue()  # info de renommage
print("OK parse ::song -> kind=section (info stderr de renommage)")

# 2. Rendu mega : le nom de la chanson est imprimé (en-tête 11 pt #555)
kkml = ("@title medley\n@layout mega\n::song 南島節\n::tab\n合 工 工 工\n::\n"
        "::song 仲順流り\n::tab\n合 工\n::\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(kkml), layout="mega"))
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert "南島節" in svg and "仲順流り" in svg, "titres de chansons absents du SVG"
assert 'font-size="11" fill="#555"' in svg
print("OK rendu mega : titres ::song rendus en en-tête de chanson")

# 3. Le sample medley du dépôt rend aussi ses titres de chanson
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(
        open(ROOT / "samples/kkml/medley-samples.kkml", encoding="utf-8").read()),
        layout="mega"))
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert "てぃんさぐ" in svg
print("OK sample medley-samples.kkml : titres de chansons rendus en mega")

# 4. Cleaner : ::song émis en ::section (forme canonique)
out = c.clean("::song 南島節\n::tab\n合 工\n::\n")
assert "::section 南島節" in out, out
print("OK cleaner : ::song réémis en ::section")

print("\nTous les tests ::song/::section passent.")
