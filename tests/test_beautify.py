# -*- coding: utf-8 -*-
"""Tests de kkml_beautify.py : alignement des débuts de cellules dans
::tab et ::vocal (chasse fixe : CJK pleine chasse = 2, combinant = 0),
après normalisation des tokens (comme kkml_cleaner). Espaces simples
uniquement, pas d'espace en fin de ligne, reste du fichier inchangé,
idempotent, rendu SVG inchangé.

Usage :
    python3 tests/test_beautify.py
"""
import os
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
import sys
sys.path.insert(0, str(ROOT))

import kkml2svg as k
import kkml_beautify as b


def w(s):
    return sum(0 if unicodedata.combining(c)
               else (2 if unicodedata.east_asian_width(c) in ("W", "F") else 1)
               for c in s)


def col_starts(line):
    """Colonnes d'affichage des débuts de tokens d'une ligne (scan brut)."""
    starts, col, in_tok = [], 0, False
    for ch in line:
        cw = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if ch == " ":
            in_tok = False
        elif not in_tok:
            starts.append(col)
            in_tok = True
        col += cw
    return starts


# 1. ::tab : débuts de cellules alignés en colonnes (largeur max par colonne)
src = "@format KKML\n@title t\n::tab\n合/工 尺 中\n中 合\n|:中 合/工 尺:| 四\n::\n"
out = b.beautify(src)
tab_lines = out.splitlines()[3:6]
assert tab_lines[0] == "合/工 尺    中", repr(tab_lines[0])   # col1 à 6
assert tab_lines[1] == "中    合", repr(tab_lines[1])          # col1 à 6
assert tab_lines[2].startswith("|:中  合/工"), repr(tab_lines[2])
cs = [col_starts(ln) for ln in tab_lines]
assert cs[0][1] == cs[1][1] == cs[2][1] == 6, cs
assert all(not ln.endswith(" ") for ln in out.splitlines())
print("OK ::tab : colonnes alignées en chasse fixe, pas d'espace final")

# 2. ::vocal : idem + normalisation (－ pleine chasse -> -)
src = "::vocal\n－ てぃ し-\n. あ い\n::\n"
out = b.beautify(src)
v = out.splitlines()[1:3]
assert v[0] == "- てぃ し-", repr(v[0])
assert v[1] == ". あ   い", repr(v[1])       # てぃ = 4, あ = 2 -> col2 à 7
assert col_starts(v[0])[2] == col_starts(v[1])[2]
assert "－" not in out
print("OK ::vocal : aligné + normalisé")

# 3. Le reste du fichier est inchangé octet par octet (lyrics avec ruby et
#    espaces idéographiques U+3000, métadonnées, commentaires)
src = ("@format KKML\n# commentaire\n::tab\n合 工\n::\n"
       "::lyrics\n一、x 《y》　z\n::\n")
out = b.beautify(src)
assert "::lyrics\n一、x 《y》　z\n::" in out, repr(out)
assert out.splitlines()[0] == "@format KKML" and "# commentaire" in out
print("OK reste du fichier inchangé (lyrics/métas/commentaires)")

# 4. L'en-tête de la section SUIVANTE n'est pas avalé dans le corps
src = "::tab\n合 工\n::\n::lyrics\n一、a\n::\n"
out = b.beautify(src)
assert out == "::tab\n合 工\n::\n::lyrics\n一、a\n::\n", repr(out)
print("OK fermeture '::' + section suivante préservées")

# 5. Idempotent
for f in sorted(os.listdir("samples/kkml")):
    if not f.endswith(".kkml"):
        continue
    x = open(f"samples/kkml/{f}", encoding="utf-8").read()
    assert b.beautify(b.beautify(x)) == b.beautify(x), f
print("OK idempotent sur tous les samples")

# 6. Rendu SVG inchangé : parse(beautify(x)) rend pareil que parse(x)
for f in ("samples/kkml/medley-samples.kkml", "samples/kkml/十九の春.kkml"):
    x = open(f, encoding="utf-8").read()
    for layout in ("vertical", "mega"):
        a = "".join(k.render_svg(k.parse_kkml(x), layout=layout))
        c = "".join(k.render_svg(k.parse_kkml(b.beautify(x)), layout=layout))
        assert a == c, (f, layout)
print("OK rendu SVG identique raw vs beautifié (vertical + mega)")


# 7. Straddle de tête '/B' (1er token de la 1re ligne de ::tab) : sorti de la
#    grille d'alignement — émis tel quel + 1 espace, colonnes calculées sur la
#    note suivante (et non sur le '/B')
src = "::tab\n/六 合/尺 工\n中 合\n::\n"
out = b.beautify(src)
ls = out.splitlines()
assert ls[1] == "/六 合/尺 工", repr(ls[1])     # col0 = max(合/尺=5, 中=2) = 5 -> 合/尺 + 1 espace
assert ls[2] == "中    合", repr(ls[2])          # 中 + 4 espaces -> 合 à la colonne 6
assert b.beautify(out) == out
print("OK straddle de tête /B : hors grille, alignement sur la note suivante")


# 8. alias tolérés ::tabs/::vocals : corps aligné, en-tête émis tel quel
src = "::tabs\n合/工 尺\n中 合\n::\n::vocals\n- てぃ\n. あ\n::\n"
out = b.beautify(src)
ls = out.splitlines()
assert ls[0] == "::tabs" and ls[2] == "中    合", ls
assert ls[4] == "::vocals" and ls[6] == ". あ", ls
assert b.beautify(out) == out
print("OK alias ::tabs/::vocals : corps alignés, en-têtes conservés")

print("Tous les tests de test_beautify.py passent.")
