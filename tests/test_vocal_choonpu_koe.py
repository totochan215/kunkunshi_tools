# -*- coding: utf-8 -*-
"""Tests : choonpu littéral échappé \\ー dans ::vocal, et rendu koedashi/koekiri
○/□ DANS la case (rattachés à la case ::tab alignée) sur tous les layouts
sauf tuto (render_koe off).

- `ー` (ou ｰ －) ISOLÉ dans ::vocal = case vide (comportement historique).
- `\\ー` = choonpu LITTÉRAL seul dans la case (voyelle longue isolée, ex.
  唐船ドーイ) : jamais pris pour une case vide ; rendu ー (tourné à 90° en
  vertical, à plat en horizontal). Le cleaner conserve l'échappement.

Usage :
    python3 tests/test_vocal_choonpu_koe.py
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

CH = chr(0x30FC)          # ー choonpu
BS = chr(92)              # antislash
KOE_O = chr(0x25CB)       # ○ koedashi
KOE_S = chr(0x25A1)       # □ koekiri


def render(kkml, layout):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svgs = k.render_svg(k.parse_kkml(kkml), layout=layout)
    assert "AVERTISSEMENT" not in err.getvalue(), (layout, err.getvalue())
    return "".join(svgs)


# --- 1. choonpu échappé : rendu ー, case non vide ---
src = ("@format KKML\n::tab\n" + chr(0x5408) + " " + chr(0x5c3a) + "\n::\n::vocal\n"
       + BS + CH + " " + chr(0x3042) + "\n::\n")
song = k.parse_kkml(src)
assert song.blocks[1].lines == [[BS + CH, chr(0x3042)]], song.blocks[1].lines  # échappement conservé au parse
v = render(src, "vertical")
assert CH in v and "rotate(90" in v, "ー non rendu (tourné) en vertical"   # ー pivoté en écriture verticale
h = render(src, "horizontal")
assert CH in h and "rotate(90" not in h, "ー devrait être à plat en horizontal"
m = render(src, "mega")
assert CH in m, "ー non rendu en mega"
print("OK \\ー : choonpu littéral rendu (vertical pivoté, horizontal à plat, mega), case non vide")

# variantes ｰ － échappées -> forme canonique \ー
for var in (chr(0xFF70), chr(0xFF0D)):
    s2 = src.replace(BS + CH, BS + var)
    assert k.parse_kkml(s2).blocks[1].lines[0][0] == BS + CH
print("OK variantes \\ｰ \\－ -> \\ー canonique au parsing")

# --- 2. ー isolé NON échappé = case vide (inchangé) ---
src_bare = src.replace(BS + CH, CH)
assert k.parse_kkml(src_bare).blocks[1].lines[0][0] == "-"
vb = render(src_bare, "vertical")
assert CH not in vb, "ー isolé devrait rester case vide"
print("OK ー isolé non échappé = case vide (comportement historique)")

# --- 3. cleaner : \ー conservé (idempotent), ー isolé -> - ---
out = c.clean(src)
assert BS + CH in out, out
assert c.clean(out) == out, "cleaner non idempotent sur \\ー"
out_bare = c.clean(src_bare)
assert BS + CH not in out_bare and "\n- " in out_bare, out_bare
print("OK cleaner : \\ー conservé tel quel (idempotent), ー isolé -> case vide '-'")

# --- 4. koedashi/koekiri : ○/□ dans la case sur tous les layouts sauf tuto ---
src_koe = ("@format KKML\n::tab\n" + chr(0x5408) + " " + chr(0x5c3a) + " " + chr(0x4e2d) + "\n::\n"
           "::vocal\n(" + chr(0x3042) + " " + chr(0x3044) + " " + chr(0x3046) + ")\n::\n")
for layout in ("vertical", "horizontal", "mega", "nomura", "chindami"):
    s = render(src_koe, layout)
    assert KOE_O in s and KOE_S in s, (layout, "○/□ absents de la case")
print("OK koedashi/koekiri : ○ et □ rendus dans la case (vertical/horizontal/mega/nomura/chindami)")
t = render(src_koe, "tuto")
assert KOE_O not in t and KOE_S not in t, "tuto ne doit pas rendre ○/□ (render_koe off)"
print("OK tuto : ○/□ non rendus (render_koe off), interprétation conservée")

# le cleaner ne déplace pas les parenthèses : elles restent dans ::vocal
out_koe = c.clean(src_koe)
assert "(" + chr(0x3042) in out_koe and chr(0x3046) + ")" in out_koe, out_koe
print("OK cleaner : parenthèses koedashi/koekiri restent dans ::vocal")

print("Tous les tests de test_vocal_choonpu_koe.py passent.")
