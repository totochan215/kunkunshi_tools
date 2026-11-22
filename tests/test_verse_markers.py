# -*- coding: utf-8 -*-
"""Tests des marqueurs de couplet ①-⑳ (U+2460-U+2473) en début de ligne de ::lyrics.

Implémenté le 2026-11-21 : ① ② ③ … ⑳ en début de ligne sont reconnus comme
numéros de couplet (comme 一、二、…), virgule 、 facultative après.

Usage :
    python3 tests/test_verse_markers.py
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

# 1. Reconnaissance (et non-régression des autres marqueurs)
assert k._verse_indent_len("①x") == 1
assert k._verse_indent_len("②、x") == 2       # 、 facultatif consommé
assert k._verse_indent_len("⑳abc") == 1
assert k._verse_indent_len("x") == 0
assert k._verse_indent_len("一、x") == 2        # inchangé
assert k._verse_indent_len("女、x") == 2        # inchangé
assert k._verse_indent_target(["①x", "②y"]) == 3
print("OK _verse_indent_len/_verse_indent_target : ①-⑳ reconnus, autres marqueurs inchangés")

# 2. Découpage en couplets (y compris mélangé avec 一、)
assert k._split_verses(["①a", "b", "②c"]) == [["①a", "b"], ["②c"]]
assert k._split_verses(["一、a", "①b"]) == [["一、a"], ["①b"]]
print("OK _split_verses : ① ouvre un nouveau couplet")

# 3. Marqueur inline paddé à 3 caractères pleine chasse (règle des en-têtes)
assert k._pad_inline_marker("①ab") == "①　　ab"
assert k._pad_inline_marker("②、ab") == "②、　ab"
print("OK _pad_inline_marker : ①/②、 complétés à 3 caractères pleine chasse")

# 4. Layout vertical : deux couplets ①/② -> deux couplets, chacun en colonne indent 0
verses = k._split_verses(["①あいう", "②かきく"])
assert len(verses) == 2, verses
for v in verses:
    cols = k._lyrics_columns_layout(v, 3)
    assert len(cols) == 1 and cols[0][1] == 0, cols  # colonne marqueur alignée en haut
print("OK layout : ① et ② ouvrent chacun un couplet en colonne indent 0")

# 5. E2E render (vertical/horizontal/chindami) : pas d'avertissement, glyphes rendus
kkml = "@title t\n::tab\n合 工\n::\n::lyrics\n①あいう\n②かきく\n::\n"
for layout in ("vertical", "horizontal", "chindami"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(kkml), layout=layout))
    assert "WARNING" not in err.getvalue(), (layout, err.getvalue())
    assert "①" in svg and "②" in svg, layout
print("OK e2e render (vertical/horizontal/chindami) : ①② rendus sans avertissement")

print("\nTous les tests de marqueurs ①-⑳ passent.")
