# -*- coding: utf-8 -*-
"""Tests des blocs de paroles multiples (@lyr_blocks), consommés en chindami.

Règles (2026-11-27) :
- le nombre de blocs de paroles par page est piloté par la méta chanson
  `@lyr_blocks` (unique à l'échelle d'une chanson ; peut varier d'une chanson
  à l'autre d'une compilation) ; défaut = spec.lyr_blocks (1 pour tous les
  layouts), plafonné à spec.lyr_blocks_max (chindami : 3 ; autres layouts : 1,
  pas de multi-blocs) ; valeur non entière ou hors bornes -> WARNING + défaut
  (ou valeur ramenée dans [1, max]) ;
- spanning vertical comme en mega : blocs chaînés haut -> bas, hauteurs égales,
  couvrant tout le kihon hanmen, gap spec.lyr_block_gap entre blocs (chindami :
  0,7 cm) — méthode LayoutSpec.lyr_block_spans() ;
- la longueur de ligne des paroles = hauteur d'un bloc (repli en sous-lignes
  via _cap_lyr_column) ;
- sans @lyr_blocks (défaut 1), le rendu est byte-identique au rendu historique.

Usage :
    python3 tests/test_chindami_lyr_blocks.py
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

CM = k.CM
SPEC = k.CHINDAMI


def count(kkml, spec):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        n = k._lyr_blocks_count(k.parse_kkml(kkml), spec)
    return n, err.getvalue()


# 1. @lyr_blocks : défaut, bornes, invalid, autres layouts plafonnés à 1
assert count("@title t\n::tab\n\u5408\n::\n", SPEC)[0] == 1
assert count("@title t\n@lyr_blocks 1\n::tab\n\u5408\n::\n", SPEC)[0] == 1
assert count("@title t\n@lyr_blocks 2\n::tab\n\u5408\n::\n", SPEC)[0] == 2
assert count("@title t\n@lyr_blocks 3\n::tab\n\u5408\n::\n", SPEC)[0] == 3
n, err = count("@title t\n@lyr_blocks 9\n::tab\n\u5408\n::\n", SPEC)
assert n == 3 and "WARNING" in err and "@lyr_blocks" in err, (n, err)
n, err = count("@title t\n@lyr_blocks abc\n::tab\n\u5408\n::\n", SPEC)
assert n == 1 and "WARNING" in err and "@lyr_blocks" in err, (n, err)
n, err = count("@title t\n@lyr_blocks 2\n::tab\n\u5408\n::\n", k.VERTICAL)   # layout max = 1
assert n == 1 and "WARNING" in err, (n, err)
print("OK 1. @lyr_blocks : défaut 1, chindami accepte 1-3, clamp/WARNING hors bornes, autres layouts plafonnés à 1")

# 2. spans : hauteurs égales, chaînés haut->bas, gap 0,7 cm, couvrent le kihon hanmen
hy0, hy1 = SPEC.hanmen_rect()[1], SPEC.hanmen_rect()[3]
gap = 0.7 * CM
for n in (1, 2, 3):
    spans = SPEC.lyr_block_spans(hy0, hy1, n)
    assert len(spans) == n
    assert abs(spans[0][0] - hy0) < 1e-9 and abs(spans[-1][1] - hy1) < 1e-9
    hs = [b - a for a, b in spans]
    assert all(abs(h - hs[0]) < 1e-9 for h in hs)          # hauteurs égales
    for a, b in zip(spans, spans[1:]):
        assert abs(b[0] - a[1] - (gap if n > 1 else 0)) < 1e-9   # gap entre blocs
assert SPEC.lyr_block_spans(hy0, hy1, 1) == [(hy0, hy1)]    # n=1 : hanmen entier, pas de gap
print("OK 2. lyr_block_spans : n=1..3, hauteurs égales, chaînés haut->bas, gap 0,7 cm, couvrent tout le hanmen")

# 3. rendu chindami : défaut byte-identique à @lyr_blocks 1 ; @lyr_blocks 2 remplit les 2 strips
SRC = open("samples/kkml/PSC-eisa-medley.kkml", encoding="utf-8").read()


def render(kkml):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        return k.render_svg(k.parse_kkml(kkml), layout="chindami"), err.getvalue()


base, _ = render(SRC)
one, _ = render(SRC.replace("@mega_dans 33", "@mega_dans 33\n@lyr_blocks 1"))
two, _ = render(SRC.replace("@mega_dans 33", "@mega_dans 33\n@lyr_blocks 2"))
three, _ = render(SRC.replace("@mega_dans 33", "@mega_dans 33\n@lyr_blocks 3"))
assert base == one                      # défaut = 1 bloc : byte-identique
assert two != base and three != base    # multi-blocs : rendu différent

TXT = re.compile(r'<text x="([\d.]+(?: [\d.]+)*)" y="([\d.]+(?: [\d.]+)*)"[^>]*font-size="([\d.]+)"[^>]*fill="([^"]*)"[^>]*>([^<]*)</text>')


def lyr_ys(svgs):
    ys = []
    for svg in svgs:
        for _xs, ysv, f, _fill, chars in TXT.findall(svg):
            if float(f) == 10 and "\u2013" not in chars:   # fs 10 = paroles (hors n° de page)
                ys.extend(float(v) for v in ysv.split())
    return ys


spans2 = SPEC.lyr_block_spans(hy0, hy1, 2)
lyr_sp = int(int(SPEC.lyr_fs) * 1.2)
ys2 = lyr_ys(two)
in0 = [y for y in ys2 if spans2[0][0] <= y <= spans2[0][1]]
in1 = [y for y in ys2 if spans2[1][0] <= y <= spans2[1][1]]
assert in0 and in1, (len(in0), len(in1))    # les 2 strips sont utilisés
# rien ne traverse le gap au-delà de l'allongement kinsoku (追い出し = +1 unité,
# déjà présent dans l'ancien rendu pleine hauteur) : le gap 0,7 cm > 1 pas l'absorbe
assert all(y <= spans2[0][1] + lyr_sp or y >= spans2[1][0] for y in ys2), \
    [y for y in ys2 if spans2[0][1] + lyr_sp < y < spans2[1][0]]
assert all(y <= hy1 + lyr_sp for y in ys2)   # pas de débordement hors hanmen (+kinsoku)
ys1 = lyr_ys(base)
assert all(hy0 <= y <= hy1 + lyr_sp for y in ys1)   # défaut : tout dans le hanmen unique
print("OK 3. rendu : défaut == @lyr_blocks 1 (byte-identique) ; @lyr_blocks 2 -> 2 strips remplis, rien dans le gap")

# 4. kkml_clean préserve @lyr_blocks (méta reconnue, non dépréciée)
out = c.clean("@title t\n@lyr_blocks 2\n::tab\n\u5408\n::\n")
assert "@lyr_blocks 2" in out.splitlines(), out
print("OK 4. kkml_clean conserve @lyr_blocks")

print("\nTous les tests de blocs de paroles (@lyr_blocks, chindami) passent.")
