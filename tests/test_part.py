# -*- coding: utf-8 -*-
"""Tests de ::part (nom de chanson en compilation/medley mega) et des anciens alias ::song/::section.

Décision du 2026-11-23 : `::part <nom>` est la forme canonique pour délimiter
les chansons d'une compilation (`::song` était l'ancien nom, renommé en `::part` ;
`::section`, encore plus ancien, était trop générique, `::tab` étant déjà
une section). `::song` et `::section` restent acceptés comme alias au parsing
(info stderr, comme les autres alias) et rectifiés en `::part` par le cleaner,
pour que les medleys nommés en `::song` (ex. fixtures dirty) continuent de
rendre les titres de chanson au-dessus des colonnes en layout mega.

Usage :
    python3 tests/test_part.py
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

# 1. Parsing : ::part -> kind=part avec label, SANS info (forme canonique)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    song = k.parse_kkml("::part 南島節\n::tab\n合 工\n::\n")
assert [(b.kind, b.label) for b in song.blocks] == [("part", "南島節"), ("tab", None)]
assert "normalis" not in err.getvalue(), err.getvalue()
print("OK parse ::part -> kind=part (canonique, pas de renommage)")

# 2. Parsing : ::song et ::section -> alias de ::part (info stderr de renommage)
for alias in ("::song", "::section", "::songs"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        song = k.parse_kkml(f"{alias} 南島節\n::tab\n合 工\n::\n")
    assert [(b.kind, b.label) for b in song.blocks] == [("part", "南島節"), ("tab", None)], alias
    assert alias in err.getvalue() and "::part" in err.getvalue(), (alias, err.getvalue())
print("OK parse ::song/::section/::songs -> kind=part (alias, info stderr de renommage)")

# 3. Rendu mega : le nom de la chanson est imprimé (en-tête 11 pt #555)
kkml = ("@title medley\n@layout mega\n::part 南島節\n::tab\n合 工 工 工\n::\n"
        "::part 仲順流り\n::tab\n合 工\n::\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(kkml), layout="mega"))
assert "WARNING" not in err.getvalue(), err.getvalue()
assert "南島節" in svg and "仲順流り" in svg, "titres de chansons absents du SVG"
assert 'font-size="11" fill="#555"' in svg
print("OK rendu mega : titres ::part rendus en en-tête de chanson")

# 3b. Compat ascendante : un medley écrit en ::song rend pareil (mêmes titres, pas d'info bloquante)
kkml_old = kkml.replace("::part", "::song")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg_old = "".join(k.render_svg(k.parse_kkml(kkml_old), layout="mega"))
assert "WARNING" not in err.getvalue(), err.getvalue()
assert svg_old == svg, "rendu ::song != rendu ::part"
print("OK compat : ::song rend exactement comme ::part (mega)")

# 4. La fixture medley rend aussi ses titres de chanson
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(
        open(ROOT / "tests/fixtures/synthetic/medley-samples.kkml", encoding="utf-8").read()),
        layout="mega"))
assert "WARNING" not in err.getvalue(), err.getvalue()
assert "てぃんさぐ" in svg
print("OK fixture medley-samples.kkml : titres de chansons rendus en mega")

# 5. Cleaner : ::song/::section réémis en ::part (forme canonique) ; ::part conservé (idempotent)
out = c.clean("::song 南島節\n::tab\n合 工\n::\n")
assert "::part 南島節" in out and "::song" not in out, out
out_sec = c.clean("::section 南島節\n::tab\n合 工\n::\n")
assert out_sec == out, (out, out_sec)
out2 = c.clean("::part 南島節\n::tab\n合 工\n::\n")
assert "::part 南島節" in out2 and out2 == out
print("OK cleaner : ::song/::section réémis en ::part ; ::part conservé (idempotent)")

print("\nTous les tests ::part passent.")
