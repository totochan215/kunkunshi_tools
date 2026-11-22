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

# --- 5. alignement des bornes sur l'élément rattaché (slot), point masqué compris ---
import re as _re
# cell 0 : "(.あ" -> koedashi ○ sur le POINT (élément 0) ; cell 1 : "あ.)" -> koekiri □ sur le POINT (élément 1)
src_al = ("@format KKML\n::tab\n" + chr(0x5408) + " " + chr(0x5408) + "\n::\n::vocal\n(."
          + chr(0x3042) + " " + chr(0x3042) + ".)\n::\n")


def koe_and_syl(svg):
    koe = [(float(m[0]), float(m[1]), m[3]) for m in
           _re.findall(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="(\d+)"[^>]*>([\u25cb\u25a1])</text>', svg)]
    syl = [(float(m[0]), float(m[1]), m[2]) for m in
           _re.findall(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*fill="#333">(.)</text>', svg)
           if m[2] != chr(0x30FB)]
    dot = [(float(m[0]), float(m[1])) for m in
           _re.findall(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*fill="#333">' + chr(0x30FB) + r'</text>', svg)]
    return koe, syl, dot


# vertical : ○/□ en hauteur (y) en face de l'élément rattaché
v_on = render("@show_dots on\n" + src_al, "vertical")
v_off = render(src_al, "vertical")
koe, syl, dot = koe_and_syl(v_on)
assert len(koe) == 2 and len(syl) == 2 and len(dot) == 2, (koe, syl, dot)
o_cell0 = next(k for k in koe if k[2] == KOE_O)     # ○ de la case 0 (slot 0 = point)
s_cell1 = next(k for k in koe if k[2] == KOE_S)     # □ de la case 1 (slot 1 = point)
a0 = syl[0][1]                                     # syllabe あ de la case 0 (slot 1)
d0, d1 = dot[0][1], dot[1][1]                      # points des cases 0 et 1
assert o_cell0[1] < a0, (o_cell0, a0)              # ○ au-dessus de あ : slot 0 < slot 1
assert abs(o_cell0[1] - d0) < 6, (o_cell0, d0)     # ○ en face du point de la case 0
assert abs(s_cell1[1] - d1) < 6, (s_cell1, d1)     # □ en face du point de la case 1
# @show_dots off : les points disparaissent MAIS l'alignement des bornes ne change pas
koe_off, syl_off, dot_off = koe_and_syl(v_off)
assert dot_off == [] and koe_off == koe, (koe_off, koe)   # mêmes positions de ○/□
print("OK vertical : ○/□ alignés sur le slot de l'élément rattaché (point masqué compris)")

# horizontal : ○/□ alignés en x sur l'élément rattaché
h_on = render("@show_dots on\n" + src_al, "horizontal")
koe_h, syl_h, dot_h = koe_and_syl(h_on)
o_h = next(k for k in koe_h if k[2] == KOE_O)
a_h = syl_h[0]
d_h = dot_h[0]
assert o_h[0] < a_h[0], (o_h, a_h)                 # ○ à gauche de あ (slot 0 < slot 1)
assert abs(o_h[0] - d_h[0]) < 6, (o_h, d_h)        # ○ en face du point (même x)
print("OK horizontal : ○/□ alignés en x sur l'élément rattaché")
# --- 6. petit kana tassé à droite du grand en vertical (vertical/chindami/mega), même taille de police ---
src_sk = "@format KKML\n::tab\n" + chr(0x5408) + " " + chr(0x5408) + "\n::\n::vocal\n" + chr(0x3061) + chr(0x3085) + " -\n::\n"


def chi_yu(svg):
    return [(float(m[0]), float(m[1]), int(m[2]), m[3]) for m in
            _re.findall(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="(\d+)"[^>]*fill="#333">(.)</text>', svg)
            if m[3] in (chr(0x3061), chr(0x3085))]


for layout in ("vertical", "mega", "chindami"):
    pair = chi_yu(render(src_sk, layout))
    assert len(pair) == 2, (layout, pair)
    (x0, y0, f0, c0), (x1, y1, f1, c1) = pair
    assert c0 == chr(0x3061) and c1 == chr(0x3085), pair
    assert x1 > x0 and y1 > y0, pair                      # décalé à droite et rapproché
    assert f1 == f0, pair                                  # MÊME taille de police (le glyphe petit kana est nativement plus petit : グヮ vs グワ)
    assert abs((x1 - x0) - 0.25 * f0) < 1 and abs((y1 - y0) - 0.55 * f0) < 1, pair
print("OK vertical/mega/chindami : petit kana tassé à droite du grand, même taille de police")

pair_h = chi_yu(render(src_sk, "horizontal"))
assert pair_h and pair_h[0][1] == pair_h[1][1], pair_h   # horizontal : côte à côte, même y
print("OK horizontal : inchangé (côte à côte)")
print("Tous les tests de test_vocal_choonpu_koe.py passent.")
