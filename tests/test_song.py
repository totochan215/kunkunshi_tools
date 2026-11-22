# -*- coding: utf-8 -*-
"""Tests de ::song (nom de chanson en compilation/medley mega) et de l'ancien alias ::section.

Décision du 2026-11-21 : `::song <nom>` est la forme canonique pour délimiter
les chansons d'une compilation (`::section` était trop générique, `::tab` étant
déjà une section) ; `::section <nom>` reste accepté comme alias (info stderr,
comme les autres alias), pour que les medleys nommés en `::song`
(ex. samples/kkml/medley-samples.kkml) rendent bien les titres de chanson
au-dessus des colonnes en layout mega.

Usage :
    python3 tests/test_song.py
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

# 1. Parsing : ::song -> kind=song avec label, SANS info (forme canonique)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    song = k.parse_kkml("::song 南島節\n::tab\n合 工\n::\n")
assert [(b.kind, b.label) for b in song.blocks] == [("song", "南島節"), ("tab", None)]
assert "normalis" not in err.getvalue(), err.getvalue()
print("OK parse ::song -> kind=song (canonique, pas de renommage)")

# 2. Parsing : ::section -> alias de ::song (info stderr de renommage)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    song = k.parse_kkml("::section 南島節\n::tab\n合 工\n::\n")
assert [(b.kind, b.label) for b in song.blocks] == [("song", "南島節"), ("tab", None)]
assert "::section" in err.getvalue() and "::song" in err.getvalue()  # info de renommage
print("OK parse ::section -> kind=song (alias, info stderr de renommage)")

# 3. Rendu mega : le nom de la chanson est imprimé (en-tête 11 pt #555)
kkml = ("@title medley\n@layout mega\n::song 南島節\n::tab\n合 工 工 工\n::\n"
        "::song 仲順流り\n::tab\n合 工\n::\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(kkml), layout="mega"))
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert "南島節" in svg and "仲順流り" in svg, "titres de chansons absents du SVG"
assert 'font-size="11" fill="#555"' in svg
print("OK rendu mega : titres ::song rendus en en-tête de chanson")

# 4. Le sample medley du dépôt rend aussi ses titres de chanson
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(
        open(ROOT / "samples/kkml/medley-samples.kkml", encoding="utf-8").read()),
        layout="mega"))
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert "てぃんさぐ" in svg
print("OK sample medley-samples.kkml : titres de chansons rendus en mega")

# 5. Cleaner : ::section réémis en ::song (forme canonique) ; ::song conservé
out = c.clean("::section 南島節\n::tab\n合 工\n::\n")
assert "::song 南島節" in out and "::section" not in out, out
out2 = c.clean("::song 南島節\n::tab\n合 工\n::\n")
assert "::song 南島節" in out2 and out2 == out
print("OK cleaner : ::section réémis en ::song ; ::song conservé (idempotent)")

print("\nTous les tests ::song passent.")
