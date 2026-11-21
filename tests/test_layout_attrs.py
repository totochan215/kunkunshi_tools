# -*- coding: utf-8 -*-
"""Tests des attributs de design par mise en page, surchargeables par
métadonnées KKML : @text_color @frame_color @frame_width @cell_color
@cell_width @arrow_color @arrow_width @arrow_fill on|off.

Les défauts viennent du LayoutSpec de chaque mise en page (champs
text_color/frame_color/frame_width/cell_color/cell_width/arrow_color/
arrow_width/arrow_fill) ; la métadonnée surcharge. Couleurs au format HTML
(#rgb, #rrggbb ou nom CSS), épaisseurs en pt > 0 ; valeur invalide ->
AVERTISSEMENT + défaut du layout. Sans métadonnée, le rendu est identique
octet par octet au rendu historique.

Usage :
    python3 tests/test_layout_attrs.py
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

TAB = "::tab\n|: 合 工 尺 :| 合\n::\n"


def render(kkml, layout):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(kkml), layout=layout))
    return svg, err.getvalue()


# 1. Défauts du design de chaque mise en page (champs LayoutSpec)
assert k.VERTICAL.cell_color == "#bbbbbb" and k.VERTICAL.cell_width == 0.75
assert k.VERTICAL.arrow_color == "#bbbbbb" and k.VERTICAL.arrow_width == 0.75
assert k.HORIZONTAL.cell_color == "#999999" and k.HORIZONTAL.arrow_color == "#999999"
assert k.NOMURA.cell_color == "#333333" and k.NOMURA.cell_width == 0.6
assert k.NOMURA.frame_color == "#333333" and k.NOMURA.frame_width == 1.5
assert k.NOMURA.arrow_color == "#333333" and k.NOMURA.arrow_width == 0.6
assert k.CHINDAMI.cell_color == "#bbbbbb" and k.CHINDAMI.cell_width == 0.6
assert k.TUTO.cell_color == "#999999" and k.TUTO.cell_width == 0.75
assert k.MEGA.cell_color == "#bbbbbb" and k.MEGA.cell_width == 0.75
assert all(not s.arrow_fill and s.text_color == "#000000" for s in k.LAYOUTS.values())
print("OK LayoutSpec : défauts de design des 6 mises en page")

# 2. Sans métadonnée : rendu historique (couleurs/épaisseurs littérales du layout)
svg, err = render("@title t\n" + TAB, "vertical")
assert 'stroke="#bbbbbb" stroke-width="0.75"' in svg          # grille
assert 'fill="none" stroke="#bbbbbb" stroke-width="0.75"' in svg  # tête de flèche creuse
assert 'fill="black"' in svg and '<svg fill=' not in svg     # texte noir, pas de fill racine
svg_h, _ = render("@title t\n" + TAB, "horizontal")
assert 'stroke="#999999" stroke-width="0.75"' in svg_h
svg_n, _ = render("@title t\n" + TAB, "nomura")
assert 'stroke="#333333" stroke-width="1.5"' in svg_n           # cadre
assert 'stroke="#333333" stroke-width="0.6"' in svg_n           # grille
print("OK sans métadonnée : défauts du layout rendus tels quels")

# 3. Les 8 métadonnées surchargent le layout (vertical)
kkml = ("@title t\n@text_color #a00000\n@cell_color red\n@cell_width 2\n"
        "@arrow_color blue\n@arrow_width 1.5\n@arrow_fill on\n" + TAB)
svg, err = render(kkml, "vertical")
assert "AVERTISSEMENT" not in err
assert '<svg fill="#a00000"' in svg and 'fill="black"' not in svg
assert 'stroke="red" stroke-width="2"' in svg                       # grille
assert 'fill="blue" stroke="blue" stroke-width="1.5"' in svg        # tête remplie
assert 'stroke="blue" stroke-width="1.5"' in svg                     # trait de la flèche
print("OK métadonnées : @text_color (racine SVG), @cell_*, @arrow_* + @arrow_fill on")

# 4. @arrow_fill off (défaut) = têtes creuses ; couleur nommée acceptée
svg, _ = render("@title t\n@arrow_color blue\n@arrow_fill off\n" + TAB, "vertical")
assert 'fill="none" stroke="blue"' in svg and 'fill="blue"' not in svg
svg, _ = render("@title t\n@text_color red\n" + TAB, "vertical")
assert '<svg fill="red"' in svg
print("OK @arrow_fill off = creux ; nom CSS de couleur accepté")

# 5. @frame_color/@frame_width sur le cadre nomura ; @cell_* sur sa grille
svg, _ = render("@title t\n@frame_color green\n@frame_width 3\n@cell_color red\n@cell_width 2\n" + TAB,
                "nomura")
assert 'stroke="green" stroke-width="3"' in svg
assert 'stroke="red" stroke-width="2"' in svg
print("OK nomura : @frame_* sur le filet de cadre, @cell_* sur la grille")

# 6. @arrow_width ne touche que les flèches, pas la grille (et inversement)
svg, _ = render("@title t\n@arrow_width 2\n" + TAB, "vertical")
assert 'stroke="#bbbbbb" stroke-width="0.75"' in svg
assert 'stroke="#bbbbbb" stroke-width="2"' in svg
svg, _ = render("@title t\n@cell_width 2\n" + TAB, "vertical")
assert 'stroke="#bbbbbb" stroke-width="2"' in svg
assert 'stroke="#bbbbbb" stroke-width="0.75"' in svg   # flèches gardent leur épaisseur
print("OK @cell_width et @arrow_width indépendants")

# 7. Valeurs invalides : AVERTISSEMENT + défaut du layout conservé
svg, err = render("@title t\n@text_color pas-une-couleur!\n@cell_width abc\n"
                  "@arrow_width -2\n@arrow_fill maybe\n" + TAB, "vertical")
assert err.count("AVERTISSEMENT") == 4, err
assert 'fill="black"' in svg and '<svg fill=' not in svg
assert 'stroke="#bbbbbb" stroke-width="0.75"' in svg
assert 'fill="none" stroke="#bbbbbb" stroke-width="0.75"' in svg
print("OK valeurs invalides : 4 AVERTISSEMENT, défauts du layout appliqués")

# 8. Horizontal : défauts #999999, surcharge par @cell_color (les flèches gardent
#    @arrow_color, donc #999999 tant que @arrow_color n'est pas renseigné)
svg, _ = render("@title t\n@cell_color teal\n" + TAB, "horizontal")
assert 'fill="none" stroke="teal" stroke-width="0.75"' in svg   # grille
assert 'fill="none" stroke="#999999" stroke-width="0.75"' in svg   # flèches inchangées
print("OK horizontal : surcharge @cell_color, flèches sur @arrow_color")

# 9. Cleaner : les 8 métadonnées sont reconnues et conservées (idempotent)
src = ("@format KKML\n@title t\n@text_color #a00000\n@frame_color green\n@frame_width 3\n"
       "@cell_color red\n@cell_width 2\n@arrow_color blue\n@arrow_width 1.5\n@arrow_fill on\n"
       + TAB)
out = c.clean(src)
for key in ("@text_color #a00000", "@frame_color green", "@frame_width 3",
            "@cell_color red", "@cell_width 2", "@arrow_color blue",
            "@arrow_width 1.5", "@arrow_fill on"):
    assert key in out, (key, out)
assert c.clean(out) == out
print("OK cleaner : métadonnées d'attributs conservées, idempotent")

print("Tous les tests de test_layout_attrs.py passent.")
