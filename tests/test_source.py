# -*- coding: utf-8 -*-
r"""Tests de la métadonnée @source (information KKML, non affichée) et des
liens hypertexte [label](url) dans les métadonnées affichées.

Implémenté le 2026-11-21 : @source = texte libre sourçant la version du morceau
(chindami, nomura, site web, production perso…) — reconnue par le parser et
conservée par le cleaner, mais NON affichée dans les mises en page SVG (comme
@comment). Liens style Markdown `[label](url)` dans les métadonnées affichées
uniquement (@title, @author, …), rendus en <a xlink:href> dans le SVG (label
seul affiché) ; `\[` `\]` = crochet littéral. Pas de liens dans ::lyrics/::tab/::vocal.

Usage :
    python3 tests/test_source.py
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

# 1. Parsing : clé reconnue, texte libre (éventuellement avec lien en clair), @sourceValeur collé
song = k.parse_kkml("@source chindami p.78\n@title t\n::tab\n合 工\n::\n")
assert song.meta.get("source") == "chindami p.78", song.meta
song_l = k.parse_kkml("@source [Portama](https://exemple.jp)\n::tab\n合 工\n::\n")
assert song_l.meta.get("source") == "[Portama](https://exemple.jp)", song_l.meta
song2 = k.parse_kkml("@sourcehttps://exemple.jp\n::tab\n合 工\n::\n")
assert song2.meta.get("source") == "https://exemple.jp", song2.meta
print("OK parsing @source (valeur libre conservée telle quelle + @sourceValeur collé)")
# 1b. alias @tuning -> @choshi : info stderr, clé canonique, rendu identique
err = io.StringIO()
with contextlib.redirect_stderr(err):
    s_t = k.parse_kkml("@tuning 本調子\n::tab\n合\n::\n")
assert s_t.meta.get("choshi") == "本調子" and "tuning" not in s_t.meta, s_t.meta
assert "'@tuning'" in err.getvalue(), err.getvalue()
s_g = k.parse_kkml("@tuning二揚げ\n::tab\n合\n::\n")   # forme collée
assert s_g.meta.get("choshi") == "二揚げ", s_g.meta
s_c = k.parse_kkml("@choshi 二揚げ\n::tab\n合\n::\n")
assert s_c.meta.get("choshi") == "二揚げ", s_c.meta
base = "@title t\n::tab\n合 工\n::\n"
svg_t = "".join(k.render_svg(k.parse_kkml("@tuning 二揚げ\n" + base), layout="vertical"))
svg_c = "".join(k.render_svg(k.parse_kkml("@choshi 二揚げ\n" + base), layout="vertical"))
assert svg_t == svg_c and "二揚げ" in svg_t
print("OK alias @tuning -> @choshi (info stderr, meta['choshi'], rendu @tuning == @choshi)")


# 2. @source NON affichée : hors META_ORDER / _meta_blocks
assert k.META_ORDER == ("author", "composer", "lyricist", "genre", "origin", "choshi")
blocks = k._meta_blocks(k.parse_kkml("@origin O\n@source S\n@tuning 本調子\n::tab\n合\n::\n"))
assert [b[0] for b in blocks] == ["O", "本調子"], blocks
print("OK @source hors META_ORDER/_meta_blocks (non affichée)")

# 3. @source absente du SVG dans tous les layouts
kkml = "@title t\n@source chindami p.78 ｛沖縄｝《おきなわ》\n::tab\n合 工\n::\n"
for layout in ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(kkml), layout=layout))
    assert "WARNING" not in err.getvalue(), (layout, err.getvalue())
    texts = "".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg))
    assert "chindami" not in texts and "沖縄" not in texts, layout
print("OK @source non rendue dans les SVG (vertical/horizontal/nomura/chindami/tuto/mega)")

# 4. _split_links / _link_free
assert k._split_links("a[b](http://x) c") == [
    ("text", "a"), ("link", "b", "http://x"), ("text", " c")]
assert k._split_links("a\\[b](c)") == [("text", "a[b](c)")]   # crochet littéral
assert k._split_links("pas de lien [ici] (espacement)") == [("text", "pas de lien [ici] (espacement)")]
assert k._split_links("x\\《y》[t](u)") == [("text", "x\\《y》"), ("link", "t", "u")]
assert k._link_free("a[b](http://x)c") == "abc"
print("OK _split_links/_link_free (lien, \\[ littéral, paire ruby échappée conservée)")

# 5. Lien [label](url) rendu en <a xlink:href> dans les métadonnées AFFICHÉES (@author)
kkml_link = "@title t\n@author [Portama](https://exemple.jp/x?a=1&b=2)\n::tab\n合 工\n::\n"
for layout in ("vertical", "horizontal", "tuto"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(kkml_link), layout=layout))
    assert "WARNING" not in err.getvalue(), (layout, err.getvalue())
    assert '<a xmlns:xlink="http://www.w3.org/1999/xlink" ' \
           'xlink:href="https://exemple.jp/x?a=1&amp;b=2">' in svg, layout
    if layout == "vertical":
        # romaji du label pivoté lettre à lettre (JLREQ, 2026-11-25)
        rot = "".join(re.findall(r'transform="rotate\(90 [^"]*"[^>]*>([^<]*)</text>', svg))
        assert "Portama" in rot, (layout, rot)
    else:
        assert "Portama" in svg, layout
    assert svg.count("https://exemple.jp") == 1, layout  # uniquement dans le href
print("OK lien [Portama](url) en <a xlink:href> via @author (vertical/horizontal/tuto, url non affichée)")

# 6. Lien dans le titre, avec ruby dans le label
kkml2 = "@title ｛安｝《あ》[site](https://x.jp)\n::tab\n合 工\n::\n"
svg = "".join(k.render_svg(k.parse_kkml(kkml2), layout="vertical"))
assert 'xlink:href="https://x.jp"' in svg and "安" in svg and "あ" in svg
rot_t = "".join(re.findall(r'transform="rotate\(90 [^"]*"[^>]*>([^<]*)</text>', svg))
assert "site" in rot_t  # label romaji du lien pivoté en vertical (JLREQ, 2026-11-25)
svg_h = "".join(k.render_svg(k.parse_kkml(kkml2), layout="horizontal"))
assert 'xlink:href="https://x.jp"' in svg_h and "site" in svg_h
print("OK lien dans @title avec ruby dans le label (vertical + horizontal)")

# 7. Crochet littéral \[ : pas de lien
svg = "".join(k.render_svg(
    k.parse_kkml("@title t\n@author a\\[b](c)\n::tab\n合 工\n::\n"), layout="horizontal"))
assert "<a " not in svg and "a[b](c)" in svg
print("OK \\[ = crochet littéral (pas de lien)")

# 8. Pas de lien dans les paroles : [a](url) rendu littéralement
svg = "".join(k.render_svg(
    k.parse_kkml("@title t\n::tab\n合 工\n::\n::lyrics\n[a](http://x)\n::\n"), layout="vertical"))
texts = "".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg))
assert "<a " not in svg and "[a](http://x)" in texts
print("OK pas de lien dans ::lyrics (texte littéral)")

# 9. Cleaner : @source conservé ; @title en premier, puis ordre du fichier
out = c.clean("@title t\n@source S\n@origin O\n::tab\n合 工\n::\n")
assert "@origin O" in out and "@source S" in out
assert out.index("@title t") < out.index("@source S") < out.index("@origin O"), out
print("OK cleaner : @source conservé, @title en tête puis ordre d'apparition dans le fichier")

print("\nTous les tests @source/liens passent.")
