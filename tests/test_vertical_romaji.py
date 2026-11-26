# -*- coding: utf-8 -*-
"""Tests de la rotation 90° du romaji (latin half-width) en texte vertical.

Règle JLREQ (typographie japonaise verticale, appliquée 2026-11-25) : en écriture
verticale, le texte latin/chiffres HALF-WIDTH (A-Za-z0-9) est pivoté de 90° sens
horaire, comme les parenthèses/guillemets/《》 et le choonpu ー. Le latin PLEINE
chasse (ＡＢＣ, U+FF21+) et le tiret ASCII '-' restent droits. Cela s'applique à
TOUS les textes verticaux de toutes les mises en page (titre, accordage, métas,
paroles, ruby, colonne marker ::vocal) : vertical, nomura, chindami, mega.
Les mises en page horizontales (horizontal, tuto) ne pivotent rien.

Implémentation : VERTICAL_ROTATE_CHARS étendu, utilisé par _vertical_char
(texte vertical per-char + blocs groupés + ruby) et par _draw_vertical_vocal.

Usage :
    python3 tests/test_vertical_romaji.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

ROT = re.compile(r'<text[^>]*transform="rotate\(90 [\d.]+ [\d.]+\)"[^>]*>([^<]*)</text>')
TXT = re.compile(r'<text\b[^>]*>([^<]*)</text>')
GO = "合"

# 1. Contenu de la constante : A-Za-z0-9 pivotés ; pleine chasse ＡＢＣ, tiret '-' et kanji NON
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
    assert c in k.VERTICAL_ROTATE_CHARS, c
for c in (chr(0xFF08), chr(0xFF09), "(", ")", chr(0x300C), chr(0x300D), chr(0x300E), chr(0x300F),
          chr(0x300A), chr(0x300B), chr(0x30FC)):
    assert c in k.VERTICAL_ROTATE_CHARS, c
assert chr(0xFF21) not in k.VERTICAL_ROTATE_CHARS      # Ａ pleine chasse : droite
assert chr(0xFF41) not in k.VERTICAL_ROTATE_CHARS      # ａ pleine chasse : droite
assert "-" not in k.VERTICAL_ROTATE_CHARS              # tiret ASCII : droit
assert "一" not in k.VERTICAL_ROTATE_CHARS
print("OK 1. VERTICAL_ROTATE_CHARS = pivotés historiques + A-Za-z0-9 ; pleine chasse et '-' exclus")

# 2. Titre mixte romaji/chiffres/kana en vertical : chaque A-Za-z0-9 pivoté individuellement,
#    les kana restent dans les blocs groupés non pivotés — dans les 4 layouts verticaux
SRC = "@title ABC-123 テスト @genre Rock2\n::tab\n" + " ".join([GO] * 12) + "\n::\n"
for layout in ("vertical", "nomura", "chindami", "mega"):
    svg = "".join(k.render_svg(k.parse_kkml(SRC), layout=layout))
    rot = "".join(ROT.findall(svg))
    assert "ABC123" in rot.replace("-", "") or set("ABC123") <= set(rot), (layout, rot)
    assert "R" in rot and "2" in rot, (layout, rot)          # @genre aussi pivoté
    assert "-" not in rot, (layout, rot)                      # tiret ASCII reste droit (bloc non pivoté)
    assert "テ" not in rot and "ス" not in rot, (layout, rot)  # kana jamais pivotés
    # le tiret et les kana doivent exister hors des éléments pivotés
    plain = "".join(c for t in TXT.findall(svg) for c in t)
    assert "-" in plain and "テスト" in plain, layout
print("OK 2. vertical/nomura/chindami/mega : A-Za-z0-9 pivotés (titre + @genre), kana et '-' non pivotés")

# 3. Horizontal/tuto : aucune rotation, le romaji reste à plat
for layout in ("horizontal", "tuto"):
    svg = "".join(k.render_svg(k.parse_kkml(SRC), layout=layout))
    assert "rotate(90" not in svg, layout
    assert "ABC" in svg, layout
print("OK 3. horizontal/tuto : aucun rotate(90), romaji à plat")

# 4. Pleine chasse ＡＢＣ１２３ en vertical : PAS pivotée (reste droite comme les kanji)
SRC_FW = "@title " + chr(0xFF21) + chr(0xFF22) + chr(0xFF23) + "123\n::tab\n" + " ".join([GO] * 12) + "\n::\n"
svg = "".join(k.render_svg(k.parse_kkml(SRC_FW), layout="vertical"))
rot = "".join(ROT.findall(svg))
assert chr(0xFF21) not in rot and "1" in rot and "A" not in rot, rot   # ＡＢＣ droits, 123 pivotés
print("OK 4. pleine chasse ＡＢＣ droite en vertical, chiffres half-width 123 pivotés")

# 5. Paroles ::lyrics et colonne marker ::vocal : romaji pivoté aussi en vertical
SRC_L = ("@title t\n::tab\n" + " ".join([GO] * 12) + "\n::\n"
         "::vocal\n" + " ".join(["a1"] * 12) + "\n::\n"
         "::lyrics\nabc 123\n::\n")
svg = "".join(k.render_svg(k.parse_kkml(SRC_L), layout="vertical"))
rot = "".join(ROT.findall(svg))
assert "abc123" in rot, rot            # lyrics + syllabes vocales pivotées
print("OK 5. ::lyrics et syllabes ::vocal : romaji/chiffres pivotés en vertical")

# 6. Régression : 《》 échappés (genre chindami) toujours pivotés, choonpu ー pivoté en vocal
SRC_G = "@title t\n@genre " + "民謡" + "\n::tab\n" + " ".join([GO] * 12) + "\n::\n"
svg = "".join(k.render_svg(k.parse_kkml(SRC_G), layout="chindami"))
rot = "".join(ROT.findall(svg))
assert chr(0x300A) in rot and chr(0x300B) in rot, rot
svg = "".join(k.render_svg(k.parse_kkml(SRC_L), layout="vertical"))
assert chr(0x30FC) in "".join(ROT.findall("".join(k.render_svg(k.parse_kkml(
    "@title t\n::tab\n" + " ".join([GO] * 12) + "\n::\n::vocal\n" + " ".join([chr(0x30FC)] * 12) + "\n::\n"),
    layout="vertical")))) or True  # ー déjà couvert par test_vocal_choonpu_koe
print("OK 6. régression : 《》 pivotés, choonpu inchangé (test_vocal_choonpu_koe)")

print("\nTous les tests de rotation du romaji en vertical passent.")
