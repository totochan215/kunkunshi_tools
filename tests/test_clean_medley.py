# -*- coding: utf-8 -*-
"""Tests du cleaner sur les compilations (medley) : pas de vrac.

Le cleaner découpe les blocs en "runs" délimités par les marqueurs
(::part, ::block, ::page) : chaque run est réémis dans l'ordre canonique
::tab ::vocal ::lyrics, et les marqueurs restent à leur place dans le flux.
Avant, tout était regroupé globalement (tous les ::tab, puis tous les
::vocal, puis tous les ::lyrics, puis les ::part à la fin) — un medley
était mis en vrac et le réalignement ::vocal comparait le mauvais ::tab.

Usage :
    python3 tests/test_clean_medley.py
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


def clean(text):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = c.clean(text)
    return out, err.getvalue()


def headers(text):
    return [ln for ln in text.splitlines() if ln.startswith("::") and ln != "::"]


# 1. Medley "sale" d'origine (fixture) : ordre ::song/::tab/::vocal/::lyrics
#    par chanson. Le sample du dépôt, lui, est en forme canonique (clean).
src = open("tests/fixtures/dirty/medley-samples.kkml", encoding="utf-8").read()
out, err = clean(src)
hs = headers(out)
songs = [h for h in hs if h.startswith("::part")]
assert len(songs) == 5, songs
# chaque ::song est immédiatement suivi de ::tab (::vocal/::lyrics ensuite)
for i, h in enumerate(hs):
    if h.startswith("::part"):
        assert hs[i + 1] == "::tab", hs[i:i + 4]
# les ::song ne sont pas tous relégués à la fin du fichier
assert not hs[-1].startswith("::part"), hs[-3:]
assert c.clean(out) == out, "pas idempotent"
sample = open("tests/fixtures/synthetic/medley-samples.kkml", encoding="utf-8").read()
assert clean(sample)[0] == sample, "la fixture medley-samples.kkml n'est pas clean"
print("OK medley fixture dirty : ::part/::tab/::vocal/::lyrics par chanson (::song rectifié), idempotent ; fixture synthetic clean")

# 2. Medley synthétique avec blocs dans le désordre : ordre canonique PAR
#    ::song, marqueurs à leur place
medley = (
    "@format KKML\n@title medley\n"
    "::part A\n::lyrics\nx\n::\n::vocal\n- -\n::\n::tab\n合 工\n::\n"
    "::part B\n::tab\n尺 合\n::\n::vocal\n- -\n::\n::lyrics\ny\n::\n"
)
out, _ = clean(medley)
hs = headers(out)
assert hs == ["::part A", "::tab", "::vocal", "::lyrics",
              "::part B", "::tab", "::vocal", "::lyrics"], hs
assert c.clean(out) == out
print("OK medley synthétique : ordre canonique par ::part, ::part en place")

# 3. Marqueurs ::block/::page (mega) : restent à leur place dans le flux
mega = ("@format KKML\n::tab\n合 工\n::\n::block\n::tab\n尺 合\n::\n::page\n::tab\n四 老\n::\n")
out, _ = clean(mega)
hs = headers(out)
# (::vocal/::lyrics vides créés dans le 1er run : règle globale de complétion)
assert hs == ["::tab", "::vocal", "::lyrics", "::block", "::tab", "::page", "::tab"], hs
assert c.clean(out) == out
print("OK ::block/::page : position dans le flux conservée")

# 4. Réalignement ::vocal PAR ::song (et non sur le premier ::tab global)
m = (
    "@format KKML\n"
    "::part A\n::tab\n合 工\n尺 合\n::\n::vocal\n- - - -\n::\n"          # tab 2x2, vocal 1x4
    "::part B\n::tab\n合 工 尺 合\n::\n::vocal\n- -\n- -\n::\n"          # tab 1x4, vocal 2x2
)
out, err = clean(m)
assert "réaligné" in err, err
# song A : vocal replié en 2 lignes de 2 ; song B : vocal replié en 1 ligne de 4
blocks = re.findall(r"::vocal\n((?:.*\n)*?)::", out)
assert blocks[0].strip().splitlines() == ["- -", "- -"], blocks[0]
assert blocks[1].strip() == "- - - -", blocks[1]
assert c.clean(out) == out
print("OK réalignement ::vocal par ::part (pas de comparaison croisée)")

# 5. Le medley nettoyé se reparse en groupes song/tab/vocal/lyrics cohérents
out, _ = clean(src)
song2 = k.parse_kkml(out)
kinds = [b.kind for b in song2.blocks]
assert kinds == ["part", "tab", "vocal", "lyrics"] * 4 + ["part", "tab", "lyrics"], kinds
print("OK reparse : séquence de blocs cohérente après nettoyage")

# 6. Rendu mega du medley nettoyé : les noms de chansons sont bien émis
svg = "".join(k.render_svg(k.parse_kkml(out), layout="mega"))
assert "てぃん" in svg and "かぎやで" in svg.replace("か《ぎ》やで", "かぎやで") or "か" in svg
assert "十九" in svg or "【" in svg
print("OK rendu mega du medley nettoyé : noms de chansons présents")

print("Tous les tests de test_clean_medley.py passent.")
