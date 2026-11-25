"""Tests des constantes de layout meta_order / render_sections / render_koe / render_yubii.

Règle (2026-11-24) : ce que chaque layout affiche (métadonnées) et rend
(sections, symboles) est déclaré dans son LayoutSpec, en surcharge des
constantes globales META_ORDER et SECTION_KINDS :
- meta_order = clés de META_ORDER affichées, dans cet ordre (@title et @speed
  restent toujours affichés ; @source/@comment jamais) ;
- render_sections = types de sections rendus (défaut SECTION_KINDS = toutes ;
  tuto = ("tab", "vocal") : ::lyrics exclu). La ::vocal rattachée à un ::tab
  voyage dans le 4-uplet du tab : elle n'est rendue avec lui que si le layout
  déclare aussi "vocal" (sinon : tab sans vocal) ; l'inverse (vocal sans tab)
  n'a pas de rendu : une ::vocal sans ::tab n'est jamais dessinée (alignement
  sur la tablature) ;
- render_koe / render_yubii = symboles koedashi/koekiri et doigtés rendus
  dans les cases (tuto : off).
Les rendus par défaut sont inchangés octet par octet (175 rendus vérifiés
avant/après sur fixtures + samples x 6 layouts).

Usage :
    python3 tests/test_layout_constants.py
"""
import contextlib
import dataclasses
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

SRC = ("@format KKML\n"
       "@title ZZTitre\n"
       "@author ZZAuteur\n@composer ZZComp\n@lyricist ZZParol\n"
       "@genre ZZGenre\n@origin ZZOrig\n@choshi ZZChoshi\n"
       "@speed 120\n"
       "::tab\n合" + chr(0x3280) + " 尺\n::\n"
       "::vocal\n(う た\n::\n"
       "::lyrics\nZZparoles\n::\n")

TEMPO = chr(0x2669) + "=120"   # ♩=120
KOEDASHI = chr(0x25CB)        # ◯
YUBII1 = chr(0x3280)          # ①


def render(layout, spec=None):
    orig = k.LAYOUTS[layout]
    if spec is not None:
        k.LAYOUTS[layout] = spec
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            return k.render_svg(k.parse_kkml(SRC), layout=layout)
    finally:
        k.LAYOUTS[layout] = orig


def text_of(layout, spec=None):
    """Texte brut de tous les SVG du layout (balises et espaces retirés :
    les rendus verticaux émettent un <text> par caractère)."""
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", "\n".join(render(layout, spec))))


# 1. Constantes globales
assert k.META_ORDER == ("author", "composer", "lyricist", "genre", "origin", "choshi")
assert k.SECTION_KINDS == ("part", "tab", "vocal", "lyrics", "block", "page")
print("OK 1 : constantes globales META_ORDER / SECTION_KINDS")

# 2. Constantes déclarées par layout
for name in ("vertical", "horizontal"):
    assert k.LAYOUTS[name].meta_order == k.META_ORDER, name
    assert k.LAYOUTS[name].render_sections == k.SECTION_KINDS, name
    assert k.LAYOUTS[name].render_koe is True and k.LAYOUTS[name].render_yubii is True
t = k.LAYOUTS["tuto"]
assert t.render_sections == ("tab", "vocal")
assert t.render_koe is False and t.render_yubii is False
assert t.meta_order == ("genre", "author", "composer", "lyricist", "origin", "choshi")
assert k.LAYOUTS["nomura"].meta_order == ("choshi",)
assert k.LAYOUTS["chindami"].meta_order == ("choshi",)
assert k.LAYOUTS["mega"].meta_order == ("genre", "author", "choshi")
for name in ("nomura", "chindami", "mega"):
    assert k.LAYOUTS[name].render_sections == k.SECTION_KINDS, name
    assert k.LAYOUTS[name].render_koe is True and k.LAYOUTS[name].render_yubii is True
print("OK 2 : constantes déclarées dans chaque LayoutSpec")

# 3. Comportement par défaut : quelles méta / quelles sections, par layout
v = text_of("vertical")
for m in ("ZZTitre", "ZZAuteur", "ZZComp", "ZZParol", "ZZGenre", "ZZOrig", "ZZChoshi", TEMPO):
    assert m in v, m
assert "ZZparoles" in v
h = text_of("horizontal")
for m in ("ZZAuteur", "ZZComp", "ZZParol", "ZZGenre", "ZZOrig", "ZZChoshi", TEMPO):
    assert m in h, m
assert "ZZparoles" in h
tu = text_of("tuto")
for m in ("ZZGenre", "ZZAuteur", "ZZComp", "ZZParol", "ZZOrig", "ZZChoshi", TEMPO):
    assert m in tu, m
assert "ZZparoles" not in tu          # ::lyrics exclu de tuto
assert "う" in tu                     # ::vocal rattaché au ::tab, rendu en cellule
nm = text_of("nomura")
assert "ZZChoshi" in nm and "ZZAuteur" not in nm and "ZZComp" not in nm and "ZZGenre" not in nm
cd = text_of("chindami")
assert "ZZChoshi" in cd and "ZZAuteur" not in cd and "ZZComp" not in cd
mg = text_of("mega")
assert "ZZGenre" in mg and "ZZAuteur" in mg and "ZZChoshi" in mg
assert "ZZComp" not in mg and "ZZParol" not in mg and "ZZOrig" not in mg
assert "ZZparoles" in mg              # paroles rendues en mega
print("OK 3 : méta affichées et sections rendues par défaut, par layout")

# 4. Surcharge de meta_order par le layout
spec = dataclasses.replace(k.LAYOUTS["vertical"], meta_order=("choshi",))
v2 = text_of("vertical", spec)
assert "ZZChoshi" in v2 and "ZZAuteur" not in v2 and "ZZGenre" not in v2 and "ZZOrig" not in v2
assert TEMPO in v2                    # @speed toujours affiché
spec = dataclasses.replace(k.LAYOUTS["horizontal"], meta_order=("genre", "author"))
h2 = text_of("horizontal", spec)
assert "ZZGenre" in h2 and "ZZAuteur" in h2
assert "ZZComp" not in h2 and "ZZChoshi" not in h2 and TEMPO in h2
print("OK 4 : meta_order surchargeable par layout (vertical, horizontal)")

# 5. Surcharge de render_sections par le layout : tab et vocal filtrables séparément
spec = dataclasses.replace(k.LAYOUTS["horizontal"], render_sections=("tab",))
h3 = text_of("horizontal", spec)
assert "ZZparoles" not in h3          # ::lyrics exclu
assert "合" in h3                     # ::tab rendu
assert "う" not in h3                 # ::vocal rattaché écarté aussi (tab sans vocal)
spec = dataclasses.replace(k.LAYOUTS["horizontal"], render_sections=("tab", "vocal"))
h4 = text_of("horizontal", spec)
assert "ZZparoles" not in h4 and "合" in h4 and "う" in h4  # vocal rattaché conservé (ligne marker)
print("OK 5 : render_sections surchargeable par layout (tab sans vocal ; vocal avec tab si déclaré)")

# 6. render_koe / render_yubii en constantes de layout
assert KOEDASHI in text_of("vertical") and YUBII1 in text_of("vertical")
spec = dataclasses.replace(k.LAYOUTS["vertical"], render_koe=False, render_yubii=False)
v_off = text_of("vertical", spec)
assert KOEDASHI not in v_off and YUBII1 not in v_off
assert "う" in v_off                  # la syllabe reste rendue
tu_off = text_of("tuto")
assert KOEDASHI not in tu_off and YUBII1 not in tu_off
print("OK 6 : render_koe / render_yubii (défaut on, off en tuto, surchargeable)")

# 7. _meta_blocks(order=...) : ordre surchargeable, tempo avant choshi ou en fin
song = k.parse_kkml(SRC)
assert [b[0] for b in k._meta_blocks(song)] == \
    ["ZZAuteur", "ZZComp", "ZZParol", "ZZGenre", "ZZOrig", "ZZChoshi"]
assert [b[0] for b in k._meta_blocks(song, speed_h=True)] == \
    ["ZZAuteur", "ZZComp", "ZZParol", "ZZGenre", "ZZOrig", TEMPO, "ZZChoshi"]
assert [b[0] for b in k._meta_blocks(song, order=("genre", "author"))] == ["ZZGenre", "ZZAuteur"]
assert [b[0] for b in k._meta_blocks(song, speed_h=True, order=("author",))] == ["ZZAuteur", TEMPO]
print("OK 7 : _meta_blocks(order=...)")

print("Tous les tests passent.")
