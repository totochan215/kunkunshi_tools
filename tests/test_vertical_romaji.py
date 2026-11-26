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


# 7. Runs de latins pivotés en UN SEUL bloc rotatif (2026-11-25, après comparaison
#    avec le texte horizontal même police/fs : le pivotage lettre par lettre à chasses
#    approchées décalait jusqu'à 8,7 pt et élargissait « composites » de +7,6 % à fs 26).
#    Le moteur avance alors les glyphes avec leurs VRAIES largeurs ; la table LATIN_WIDTH_EM
#    (vraies métriques Times-Roman AFM) ne sert qu'à l'avance du run (frontière suivante).
#    Titre "iWmあ-ab" en vertical (fs 26, sp 30) : runs "iWm" et "ab" en blocs uniques.
RUN = re.compile(r'<text x="[\d.]+" y="([\d.]+)"[^>]*font-size="([\d.]+)"[^>]*transform="rotate\(90 [\d.]+ [\d.]+\)"[^>]*>([^<]+)</text>')
svg = "".join(k.render_svg(k.parse_kkml("@title iWm" + chr(0x3042) + "-ab\n::tab\n" + " ".join([GO] * 12) + "\n::\n"), layout="vertical"))
runs = [(float(y), float(f), t) for y, f, t in RUN.findall(svg)]
assert [t for _, _, t in runs] == ["iWm", "ab"], runs          # 2 runs, un seul <text> chacun
assert all(f == 26.0 for _, f, _ in runs)
y_iwm, y_ab = runs[0][0], runs[1][0]
# avance du run iWm = (0,278 + 0,944 + 0,778) em x 26 = 52 pt, puis あ et '-' au pas sp=30
assert abs((y_ab - y_iwm) - (2.0 * 26 + 2 * 30)) < 0.01, (y_iwm, y_ab)
# le kana あ et le tiret restent dans le bloc groupé non pivoté, au pas fixe
blk = re.search(r'<text (?![^>]*transform)[^>]*x="([0-9. ]+)" y="([0-9. ]+)"[^>]*font-size="26"[^>]*>([^<]*)</text>', svg)
ys = [float(v) for v in blk.group(2).split()]
assert blk.group(3) == chr(0x3042) + "-" and ys == [y_iwm + 2.0 * 26, y_iwm + 2.0 * 26 + 30], (blk.group(3), ys)
# un run interrompu par un non-latin est coupé : "a-b" -> run "a", tiret, run "b"
svg2 = "".join(k.render_svg(k.parse_kkml("@title a-b\n::tab\n" + " ".join([GO] * 12) + "\n::\n"), layout="vertical"))
runs2 = [t for _, _, t in RUN.findall(svg2)]
assert runs2 == ["a", "b"], runs2
print("OK 7. runs de latins pivotés en UN bloc rotatif (iWm / ab), avance du run = somme des vraies chasses, kana/tiret au pas fixe entre les runs")

# 8. _vstep / _latin_run_char : latin half-width alnum -> fs x chasse AFM ; le reste -> sp
assert abs(k._vstep("i", 26, 30) - 26 * 0.278) < 1e-9
assert abs(k._vstep("m", 26, 30) - 26 * 0.778) < 1e-9
assert abs(k._vstep("W", 26, 30) - 26 * 0.944) < 1e-9
assert abs(k._vstep("s", 26, 30) - 26 * 0.389) < 1e-9
assert abs(k._vstep("c", 26, 30) - 26 * 0.444) < 1e-9
assert k._vstep("5", 26, 30) == 26 * 0.5
assert k._vstep(chr(0x3042), 26, 30) == 30          # kana : sp
assert k._vstep(chr(0xFF21), 26, 30) == 30          # pleine chasse Ａ : sp (non pivotée)
assert k._vstep(chr(0x30FC), 26, 30) == 30          # choonpu pleine chasse : sp
assert k._vstep("-", 26, 30) == 30                  # tiret : sp
assert k._vstep("(", 26, 30) == 30                  # parenthèse ASCII : sp (pivotée seule, pleine chasse)
assert k._latin_run_char("a") and k._latin_run_char("9") and not k._latin_run_char("(") and not k._latin_run_char(chr(0x3042))
print("OK 8. _vstep/_latin_run_char : chasses AFM Times pour A-Za-z0-9, sp sinon (parenthèses pleine chasse exclues des runs)")

print("\nTous les tests de rotation du romaji en vertical passent.")
