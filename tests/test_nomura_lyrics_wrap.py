# -*- coding: utf-8 -*-
"""Tests du repli des paroles (::lyrics) en nomura : une colonne plus haute que le
hanmen est repliée en sous-colonnes (comme en chindami, `_cap_lyr_column`), jamais
de débordement du cadre.

Règle (2026-11-22) : en nomura la page est imposée (A4) — `max_lyr_u =
int((grid_h − LYRICS_FS) // LYRICS_SP) + 1` unités par colonne de paroles ; les
sous-colonnes issues du repli comptent dans la pagination (dans virtuels).

Usage :
    python3 tests/test_nomura_lyrics_wrap.py
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

GO = chr(0x5408)
# colonne de paroles très longue (une seule colonne, pas de |) -> doit être repliée
LONG = "\u3042" * 25 + "\u3044" * 25 + "\u3046" * 25   # 75 glyphes > max_lyr_u (~40)
SRC = ("@title t\n@layout nomura\n"
       "::tab\n" + " ".join([GO] * 12) + "\n::\n"
       "::lyrics\n" + LONG + "\n::\n")


def render():
    with contextlib.redirect_stderr(io.StringIO()):
        return k.render_svg(k.parse_kkml(SRC), layout="nomura")


# 1. aucune colonne ne dépasse le bas du cadre, sur toutes les pages
svgs = render()
assert len(svgs) >= 1
frame_re = re.compile(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="none" stroke="#333333" stroke-width="1.5"')
text_re = re.compile(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="([\d.]+)"[^>]*>([^<]*)</text>')
all_glyphs = 0
for svg in svgs:
    fr = frame_re.search(svg)
    fy1 = float(fr.group(2)) + float(fr.group(4))
    for m in text_re.finditer(svg):
        y = float(m.group(2))
        assert y <= fy1 + 0.5, ("débordement du cadre", y, fy1, m.group(4))
        all_glyphs += len(m.group(4))
print("OK nomura : aucune parole ne dépasse le bas du cadre (fy1=%.1f)" % fy1)

# 2. la longue colonne a bien été repliée en plusieurs sous-colonnes (x distincts)
last = svgs[-1]
xs = sorted(set(float(m.group(1)) for m in text_re.finditer(last)
                if m.group(4) and m.group(4)[0] in "\u3042\u3044\u3046"))
assert len(xs) >= 2, xs
print("OK repli : %d sous-colonnes de paroles (x distincts)" % len(xs))

# 3. aucun glyphe perdu au repli
assert all_glyphs >= len(LONG), (all_glyphs, len(LONG))
print("OK aucun glyphe perdu (%d glyphes de paroles rendus)" % all_glyphs)

# 4. colonne courte : pas de repli (1 seule sous-colonne), inchangé
SRC2 = SRC.replace(LONG, "\u3042" * 10)
with contextlib.redirect_stderr(io.StringIO()):
    svgs2 = k.render_svg(k.parse_kkml(SRC2), layout="nomura")
xs2 = sorted(set(float(m.group(1)) for m in text_re.finditer(svgs2[-1])
                 if m.group(4) and m.group(4)[0] == "\u3042"))
assert len(xs2) == 1, xs2
print("OK colonne courte : pas de repli (1 colonne)")

print("OK tests repli des paroles en nomura")
