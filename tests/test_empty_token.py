# -*- coding: utf-8 -*-
"""Tests du token vide `-` (EMPTY_TOKEN) : JAMAIS rendu comme texte, dans toutes
les mises en page — y compris en première partie de token (`-/合^` = case vide +
note à cheval), en straddle de tête, ou token `-` seul.

Règle (2026-11-25) : le `-` en première partie d'un token indique un vide.
Implémentation : guard `render_cell` (token seul), branche `/` de render_cell
(note principale `-` sautée), `_note_svg` renvoie "" pour EMPTY_TOKEN,
`_draw_lead_straddle` guard.

Usage :
    python3 tests/test_empty_token.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

GO = "合"
Tiret = re.compile(r'<text\b[^>]*>-</text>')

# 1. _note_svg : token vide -> chaîne vide (filet de sécurité)
assert k._note_svg(k.EMPTY_TOKEN, 12) == ""
assert k._note_svg("", 12) == ""
assert k._note_svg(GO, 12) == GO
print("OK 1. _note_svg(EMPTY_TOKEN) == \"\"")

# 2. Toutes les mises en page : `-` seul, `-/合^`, `合/-` -> aucun glyphe "-" rendu,
#    mais la note à cheval / la note réelle bien présente
SRC = "@title t\n::tab\n-/" + GO + "^ " + GO + " - " + GO + "/-\n::\n"
for layout in ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega"):
    svg = "".join(k.render_svg(k.parse_kkml(SRC), layout=layout))
    assert not Tiret.search(svg), (layout, Tiret.findall(svg)[:3])
    assert GO in svg, layout   # la note 合 (principale et/ou à cheval) est bien rendue
print("OK 2. 6 layouts : aucun <text>-</text> pour `-`, `-/合^`, `合/-` ; la note 合 est rendue")

# 3. La case vide reste vide (pas de cercle de repos non plus) : `-` seul ne rend rien dans la case
svg = "".join(k.render_svg(k.parse_kkml("@title t\n::tab\n-\n::\n"), layout="vertical"))
assert not Tiret.search(svg)
assert chr(0x25EF) not in svg and chr(0x30FB) not in svg   # pas de ● ni de ・ non plus
print("OK 3. `-` seul : case vide, aucun symbole")

print("\nTous les tests du token vide passent.")
