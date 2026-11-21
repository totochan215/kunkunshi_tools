# -*- coding: utf-8 -*-
r"""Tests de la métadonnée @source et des liens hypertexte [label](url).

Implémenté le 2026-11-21 : @source = texte libre sourçant la version du morceau
(chindami, nomura, site web, production perso…), ruby supporté, placée entre
@origin et @tuning dans META_ORDER. Liens style Markdown `[label](url)` dans
les métadonnées uniquement, rendus en <a xlink:href> dans le SVG (label seul
affiché) ; `\[` `\]` = crochet littéral. Pas de liens dans ::lyrics/::tab/::vocal.

Usage :
    python3 tests/test_source.py
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

# 1. Parsing : clé reconnue, texte libre, tolérance @sourceValeur collé
song = k.parse_kkml("@source chindami p.78\n@title t\n::tab\n合 工\n::\n")
assert song.meta.get("source") == "chindami p.78", song.meta
song2 = k.parse_kkml("@sourcehttps://exemple.jp\n::tab\n合 工\n::\n")
assert song2.meta.get("source") == "https://exemple.jp", song2.meta
print("OK parsing @source (valeur libre + @sourceValeur collé)")

# 2. META_ORDER / _meta_blocks : source entre origin et tuning
assert k.META_ORDER == ("author", "composer", "lyricist", "genre", "origin", "source", "tuning")
blocks = k._meta_blocks(k.parse_kkml("@origin O\n@source S\n@tuning 本調子\n::tab\n合\n::\n"))
assert [b[0] for b in blocks] == ["O", "S", "本調子"], blocks
print("OK META_ORDER / _meta_blocks : @source entre @origin et @tuning")

# 3. _split_links / _link_free
assert k._split_links("a[b](http://x) c") == [
    ("text", "a"), ("link", "b", "http://x"), ("text", " c")]
assert k._split_links("a\\[b](c)") == [("text", "a[b](c)")]   # crochet littéral
assert k._split_links("pas de lien [ici] (espacement)") == [("text", "pas de lien [ici] (espacement)")]
assert k._split_links("x\\《y》[t](u)") == [("text", "x\\《y》"), ("link", "t", "u")]
assert k._link_free("a[b](http://x)c") == "abc"
print("OK _split_links/_link_free (lien, \\[ littéral, paire ruby échappée conservée)")

# 4. Rendu @source (texte + ruby) en vertical / horizontal / tuto
kkml = "@title t\n@source ma source ｛沖縄｝《おきなわ》\n::tab\n合 工\n::\n"
for layout in ("vertical", "horizontal", "tuto"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(kkml), layout=layout))
    assert "AVERTISSEMENT" not in err.getvalue(), (layout, err.getvalue())
    # en vertical, le bloc groupé joint les glyphes (l'espace est sauté)
    assert "source" in svg and "沖縄" in svg and "おきなわ" in svg, layout
print("OK rendu @source avec ruby en vertical/horizontal/tuto")

# 5. Lien [label](url) rendu en <a xlink:href> (url échappée XML, non affichée)
kkml_link = "@title t\n@source [Portama](https://exemple.jp/x?a=1&b=2)\n::tab\n合 工\n::\n"
for layout in ("vertical", "horizontal", "tuto"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(kkml_link), layout=layout))
    assert "AVERTISSEMENT" not in err.getvalue(), (layout, err.getvalue())
    assert '<a xmlns:xlink="http://www.w3.org/1999/xlink" ' \
           'xlink:href="https://exemple.jp/x?a=1&amp;b=2">' in svg, layout
    assert "Portama" in svg, layout
    assert svg.count("https://exemple.jp") == 1, layout  # uniquement dans le href
print("OK lien [Portama](url) en <a xlink:href> (vertical/horizontal/tuto, url non affichée)")

# 6. Lien dans le titre, avec ruby dans le label
kkml2 = "@title ｛安｝《あ》[site](https://x.jp)\n::tab\n合 工\n::\n"
svg = "".join(k.render_svg(k.parse_kkml(kkml2), layout="vertical"))
assert 'xlink:href="https://x.jp"' in svg and "安" in svg and "あ" in svg and "site" in svg
svg_h = "".join(k.render_svg(k.parse_kkml(kkml2), layout="horizontal"))
assert 'xlink:href="https://x.jp"' in svg_h and "site" in svg_h
print("OK lien dans @title avec ruby dans le label (vertical + horizontal)")

# 7. Crochet littéral \[ : pas de lien
svg = "".join(k.render_svg(
    k.parse_kkml("@title t\n@source a\\[b](c)\n::tab\n合 工\n::\n"), layout="horizontal"))
assert "<a " not in svg and "a[b](c)" in svg
print("OK \\[ = crochet littéral (pas de lien)")

# 8. Pas de lien dans les paroles : [a](url) rendu littéralement
import re
svg = "".join(k.render_svg(
    k.parse_kkml("@title t\n::tab\n合 工\n::\n::lyrics\n[a](http://x)\n::\n"), layout="vertical"))
texts = "".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg))
assert "<a " not in svg and "[a](http://x)" in texts
print("OK pas de lien dans ::lyrics (texte littéral)")

# 9. Cleaner : @source conservé, ordre canonique (après @origin)
out = c.clean("@title t\n@source S\n@origin O\n::tab\n合 工\n::\n")
assert "@origin O" in out and "@source S" in out
assert out.index("@origin O") < out.index("@source S"), out
print("OK cleaner : @source conservé, ordre canonique après @origin")

print("\nTous les tests @source/liens passent.")
