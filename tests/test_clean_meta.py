# -*- coding: utf-8 -*-
"""Tests de l'ordre des métadonnées produites par kkml_clean.

Règle (2026-11-21) : toutes les métadonnées sont regroupées en haut du fichier ;
`@format` `@version` `@title` toujours en premier (si présents), puis les
autres métadonnées présentes dans leur ordre d'apparition dans le fichier
(l'ancien ordre canonique est supprimé). Dédoublonnage : première occurrence.

Usage :
    python3 tests/test_clean_meta.py
"""
import contextlib
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml_clean as c


def meta_lines(out):
    return [ln for ln in out.splitlines() if ln.startswith("@")]


# 1. format/version/title en premier (si présents), puis ordre du fichier
src = "@tuning 本調子\n@title t\n@source S\n@version 0.1\n@format KKML\n::tab\n合 工\n::\n"
out = c.clean(src)
assert meta_lines(out) == ["@format KKML", "@version 0.1", "@title t",
                           "@choshi 本調子", "@source S"], meta_lines(out)
print("OK @format/@version/@title en premier, puis ordre du fichier")

# 2. métadonnées éparpillées (y compris après les sections) -> toutes en haut
src = "::tab\n合 工\n::\n@tuning 本調子\n@title t\n::lyrics\n一、x\n::\n"
out = c.clean(src)
ml = meta_lines(out)
assert ml == ["@format KKML", "@title t", "@choshi 本調子"], ml
assert all(out.index(ln) < out.index("::tab") for ln in ml), out
print("OK métadonnées regroupées en haut, @title en tête, puis ordre du fichier")

# 3. sans format/version/title -> ordre du fichier pur
src = "@source S\n@tuning 本調子\n@author A\n::tab\n合\n::\n"
out = c.clean(src)
assert meta_lines(out) == ["@format KKML", "@source S", "@choshi 本調子", "@author A"], meta_lines(out)
print("OK sans @format/@version/@title : ordre du fichier conservé")

# 4. @layout/@cells_per_dan/@dans_per_page conservés à leur place (ordre fichier)
src = "@cells_per_dan 2\n@layout tuto\n@title t\n@dans_per_page 3\n::tab\n合 工 工 工\n::\n"
out = c.clean(src)
assert meta_lines(out) == ["@format KKML", "@title t", "@cells_per_dan 2", "@layout tuto",
                           "@dans_per_page 3"], meta_lines(out)
assert "合 工\n工 工" in out  # repli à 2 cellules/ligne appliqué
print("OK @layout/@cells_per_dan/@dans_per_page préservés, ordre du fichier")

# 5. dédup : une seule ligne par clé, position de la première occurrence
src = "@tuning A\n@title t\n@tuning B\n::tab\n合\n::\n"
out = c.clean(src)
ml = meta_lines(out)
assert ml[0] == "@format KKML" and ml[1] == "@title t" and sum(ln.startswith("@choshi") for ln in ml) == 1, ml
print("OK dédup des métadonnées (une seule ligne par clé)")

# 6. @cols renommé en @cells_per_dan
out = c.clean("@cols 2\n::tab\n合 工 工 工\n::\n")
assert meta_lines(out) == ["@format KKML", "@cells_per_dan 2"], meta_lines(out)
print("OK @cols renommé en @cells_per_dan")

# 7. idempotence
for src in ("@tuning 本調子\n@title t\n@source S\n@version 0.1\n@format KKML\n::tab\n合 工\n::\n",
            "@cells_per_dan 2\n@layout tuto\n@title t\n::tab\n合 工 工 工\n::\n",
            "@source S\n@tuning 本調子\n::tab\n合\n::\n"):
    o1 = c.clean(src)
    assert c.clean(o1) == o1, f"non idempotent:\n{o1}\n---\n{c.clean(o1)}"
print("OK idempotence cleaner(cleaner(x)) == cleaner(x)")

# 8. séparateurs : une et une seule ligne vide entre le bloc métadonnées et la
# première section, et entre chaque section ; aucune en tête si pas de
# métadonnées, aucune en fin de fichier
src = "@title t\n::tab\n合 工\n::\n::lyrics\n一、x\n\n二、y\n::\n"
out = c.clean(src)
assert out.startswith("@format KKML\n@title t\n\n::tab\n"), repr(out)
assert "\n\n\n" not in out, repr(out)          # jamais deux lignes vides de suite
assert "::\n\n::" in out, repr(out)             # une ligne vide entre chaque section
assert not out.endswith("\n\n"), repr(out)
out2 = c.clean("::tab\n合 工\n::\n::lyrics\nx\n::\n")
# @format KKML est ajouté d'office : jamais de ligne vide en tête de fichier
assert out2.startswith("@format KKML\n\n::tab\n"), repr(out2)
assert not out2.startswith("\n")
assert "\n\n\n" not in out2 and not out2.endswith("\n\n"), repr(out2)
assert c.clean(out) == out and c.clean(out2) == out2
print("OK séparateurs : une seule ligne vide entre bloc méta/sections, aucune en tête/fin")

# 9. @format KKML ajouté s'il est absent (et épinglé en première ligne)
out = c.clean("@title t\n::tab\n合 工\n::\n")
assert meta_lines(out)[0] == "@format KKML", meta_lines(out)
assert meta_lines(out)[1] == "@title t", meta_lines(out)
out = c.clean("@format KKML\n@title t\n::tab\n合 工\n::\n")
assert meta_lines(out)[:2] == ["@format KKML", "@title t"], meta_lines(out)
assert c.clean(c.clean("@title t\n::tab\n合 工\n::\n")) == c.clean("@title t\n::tab\n合 工\n::\n")
print("OK @format KKML ajouté si absent, en première ligne, idempotent")

# 10. alias @tuning -> @choshi rectifié par le cleaner (info stderr), y compris collé
err = io.StringIO()
with contextlib.redirect_stderr(err):
    out = c.clean("@tuning 本調子\n::tab\n合\n::\n")
assert meta_lines(out) == ["@format KKML", "@choshi 本調子"], meta_lines(out)
assert "renommé en @choshi" in err.getvalue(), err.getvalue()
out = c.clean("@tuning二揚げ\n::tab\n合\n::\n")
assert "@choshi 二揚げ" in meta_lines(out), meta_lines(out)
assert c.clean(out) == out
print("OK alias @tuning rectifié en @choshi (info stderr), forme collée comprise, idempotent")

print("\nTous les tests d'ordre des métadonnées passent.")
