# -*- coding: utf-8 -*-
"""Tests du straddle de tête '/B' (rang -1) en tête de bloc ::tab.

Implémenté le 2026-11-21 : un token '/B' en tout premier token d'un bloc
::tab = note à cheval sur le bord PRÉCÉDENT de la première case (rang -1 ;
haut en vertical, gauche en horizontal). Le token ne consomme pas de case.
Ailleurs : WARNING + ignoré. Rendu : vertical, horizontal, mega.

Usage :
    python3 tests/test_lead_straddle.py
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

# 1. Parsing : '/六' en premier token du bloc ::tab -> Block.leading_straddle,
#    le token est retiré des cases (ne consomme pas de case)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    song = k.parse_kkml("::tab\n/六 合 工\n::\n")
assert song.blocks[0].leading_straddle == "六"
assert song.blocks[0].lines == [["合", "工"]], song.blocks[0].lines
assert "WARNING" not in err.getvalue(), err.getvalue()
print("OK parse /六 -> leading_straddle, token retiré des cases")

# 2. Token '/X' ailleurs dans le bloc : WARNING + ignoré
err = io.StringIO()
with contextlib.redirect_stderr(err):
    song = k.parse_kkml("::tab\n合 /工\n::\n")
assert song.blocks[0].leading_straddle is None
assert song.blocks[0].lines == [["合"]]
assert "WARNING" in err.getvalue()
print("OK '/X' hors tête de bloc : WARNING + ignoré")

# 3. Rendu vertical : le 六 est rendu en petit AU-DESSUS de la 1re case (grille)
kkml = ("@title t\n::tab\n/六 " + " ".join(["合", "工/尺", "合/上", "合/老", "四/老", "上/尺",
                                             "工/五", "尺/上", "四/六", "工/上", "尺/老", "工/老"])
        + "\n::\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg = "".join(k.render_svg(k.parse_kkml(kkml), layout="vertical"))
assert "WARNING" not in err.getvalue(), err.getvalue()
ms = re.findall(r'<text x="([0-9.]+)" y="([0-9.]+)"[^>]*font-size="(\d+)"[^>]*>六</text>', svg)
assert ms, "straddle de tête 六 absent du SVG vertical"
m = min(ms, key=lambda t: float(t[1]))  # le plus haut = le straddle de tête
grid_top = float(re.search(r'<rect x="[0-9.]+" y="([0-9.]+)"[^>]*stroke="#bbbbbb"', svg).group(1))
# le glyphe (centre = baseline - 0,35*fs) doit être CENTRÉ sur le bord de case
center = float(m[1]) - 0.35 * float(m[2])
assert abs(center - grid_top) < 1.0, (center, grid_top, m)
print("OK vertical : /六 pile à cheval sur le bord de la 1re case (centre=%s, bord=%s), fs=%s"
      % (round(center, 2), grid_top, m[2]))

# 4. Rendu horizontal : Six sur le bord GAUCHE de la 1re case de la 1re rangée
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svgh = "".join(k.render_svg(k.parse_kkml(kkml), layout="horizontal"))
assert "WARNING" not in err.getvalue(), err.getvalue()
mhs = re.findall(r'<text x="([0-9.]+)" y="([0-9.]+)"[^>]*font-size="(\d+)"[^>]*>六</text>', svgh)
assert mhs, "straddle de tête 六 absent du SVG horizontal"
mh = min(mhs, key=lambda t: float(t[0]))  # le plus à gauche = le straddle de tête
first_cell_x = float(re.search(r'<rect x="([0-9.]+)" y="[0-9.]+"[^>]*stroke="#999999"', svgh).group(1))
assert float(mh[0]) <= first_cell_x + 0.01, (mh[0], first_cell_x)
print("OK horizontal : /六 sur le bord gauche de la 1re case (x=%s, case x=%s)"
      % (mh[0], first_cell_x))

# 5. Mega (medley) : /六 en tête de la ::tab d'une ::part
kkml2 = ("@title medley\n@layout mega\n::part A\n::tab\n/六 " + " ".join(["合"] * 12) + "\n::\n"
         "::part B\n::tab\n" + " ".join(["工"] * 12) + "\n::\n")
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svgm = "".join(k.render_svg(k.parse_kkml(kkml2), layout="mega"))
assert "WARNING" not in err.getvalue(), err.getvalue()
assert re.search(r'font-size="\d+"[^>]*>六</text>', svgm)
print("OK mega : /六 rendu en tête de chanson dans le medley")

# 6. Layout non supporté (nomura) : WARNING, pas de crash
err = io.StringIO()
with contextlib.redirect_stderr(err):
    k.render_svg(k.parse_kkml(kkml), layout="nomura")
assert "non support" in err.getvalue()
print("OK nomura : WARNING 'non supporté', rendu sans crash")

# 7. Cleaner : réémet '/六' en tête de bloc, idempotent
out = c.clean("::tab\n/六 合 工\n::\n")
assert "/六 合 工" in out, out
assert c.clean(out) == out
print("OK cleaner : /六 réémis en tête de bloc, idempotent")

print("\nTous les tests du straddle de tête '/B' passent.")
