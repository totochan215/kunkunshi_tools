# -*- coding: utf-8 -*-
"""Tests des attributs de design par mise en page, surchargeables par
métadonnées KKML : @text_color @frame_color @frame_width @cell_color
@cell_width @arrow_color @arrow_width @rep_fill @vrep_fill on|off (alias @arrow_fill = @rep_fill).

Les défauts viennent du LayoutSpec de chaque mise en page (champs
text_color/frame_color/frame_width/cell_color/cell_width/arrow_color/
arrow_width/rep_fill/vrep_fill) ; la métadonnée surcharge. Couleurs au format HTML
(#rgb, #rrggbb ou nom CSS), épaisseurs en pt > 0 ; valeur invalide ->
WARNING + défaut du layout. Sans métadonnée, le rendu est identique
octet par octet au rendu historique.

Usage :
    python3 tests/test_layout_attrs.py
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

TAB = "::tab\n|: 合 工 尺 :| 合\n::\n"
TAB_V = "::tab\n|: 合 (:尺 尺:) :|\n::\n"   # boucle instrumentale |: :| + boucle vocale (: :)


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
assert all(not s.vrep_fill for s in k.LAYOUTS.values())
assert all(s.text_color == "#000000" for s in k.LAYOUTS.values())
assert k.CHINDAMI.rep_fill is True   # recueil chindami : flèches instrumentales pleines
assert all(not s.rep_fill for n, s in k.LAYOUTS.items() if n != "chindami")
assert k.CHINDAMI.circle_width == 0.5   # cercles de 尺 : 0,5 pt en chindami (recueil)
assert all(s.circle_width == 1.0 for n, s in k.LAYOUTS.items() if n != "chindami")
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
        "@arrow_color blue\n@arrow_width 1.5\n@rep_fill on\n" + TAB)
svg, err = render(kkml, "vertical")
assert "WARNING" not in err
assert '<svg fill="#a00000"' in svg and 'fill="black"' not in svg
assert 'stroke="red" stroke-width="2"' in svg                       # grille
assert 'fill="blue" stroke="blue" stroke-width="1.5"' in svg        # tête remplie
assert 'stroke="blue" stroke-width="1.5"' in svg                     # trait de la flèche
print("OK métadonnées : @text_color (racine SVG), @cell_*, @arrow_* + @rep_fill on")

# 4. @arrow_fill off (défaut) = têtes creuses ; couleur nommée acceptée
svg, _ = render("@title t\n@arrow_color blue\n@rep_fill off\n" + TAB, "vertical")
assert 'fill="none" stroke="blue"' in svg and 'fill="blue"' not in svg
svg, _ = render("@title t\n@text_color red\n" + TAB, "vertical")
assert '<svg fill="red"' in svg
print("OK @rep_fill off = creux ; nom CSS de couleur accepté")

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

# 7. Valeurs invalides : WARNING + défaut du layout conservé
svg, err = render("@title t\n@text_color pas-une-couleur!\n@cell_width abc\n"
                  "@arrow_width -2\n@arrow_fill maybe\n@circle_width abc\n" + TAB, "vertical")
assert err.count("WARNING") == 5, err
assert 'fill="black"' in svg and '<svg fill=' not in svg
assert 'stroke="#bbbbbb" stroke-width="0.75"' in svg
assert 'fill="none" stroke="#bbbbbb" stroke-width="0.75"' in svg
print("OK valeurs invalides : 5 WARNING, défauts du layout appliqués")

# 8. Horizontal : défauts #999999, surcharge par @cell_color (les flèches gardent
#    @arrow_color, donc #999999 tant que @arrow_color n'est pas renseigné)
svg, _ = render("@title t\n@cell_color teal\n" + TAB, "horizontal")
assert 'fill="none" stroke="teal" stroke-width="0.75"' in svg   # grille
assert 'fill="none" stroke="#999999" stroke-width="0.75"' in svg   # flèches inchangées
print("OK horizontal : surcharge @cell_color, flèches sur @arrow_color")

# 9. Cleaner : les 8 métadonnées sont reconnues et conservées (idempotent)
src = ("@format KKML\n@title t\n@text_color #a00000\n@frame_color green\n@frame_width 3\n"
       "@cell_color red\n@cell_width 2\n@arrow_color blue\n@arrow_width 1.5\n@rep_fill on\n@circle_width 2\n"
       + TAB)
out = c.clean(src)
for key in ("@text_color #a00000", "@frame_color green", "@frame_width 3",
            "@cell_color red", "@cell_width 2", "@arrow_color blue",
            "@arrow_width 1.5", "@rep_fill on", "@circle_width 2"):
    assert key in out, (key, out)
assert c.clean(out) == out
out_alias = c.clean("@format KKML\n@title t\n@arrow_fill on\n" + TAB)
assert "@rep_fill on" in out_alias and "@arrow_fill" not in out_alias  # alias rectifié
print("OK cleaner : métadonnées d'attributs conservées, idempotent")

# 10. Modèle cadre/hanmen générique : cadre = marges depuis le bord de feuille,
#     hanmen = cadre - padding ; frame_width = 0 -> cadre non tracé
fx0, fy0, fx1, fy1 = k.NOMURA.frame_rect()
hx0, hy0, hx1, hy1 = k.NOMURA.hanmen_rect()
assert abs(hx0 - fx0 - k.NOMURA.pad_l) < 1e-9 and abs(fy1 - hy1 - k.NOMURA.pad_b) < 1e-9
assert k.NOMURA.frame_width == 1.5                      # seul layout avec filet tracé
assert all(s.frame_width == 0 for n, s in k.LAYOUTS.items() if n != "nomura")
assert k.CHINDAMI.frame_rect()[0] == k.CHINDAMI.margin_l  # chindami : cadre virtuel = hanmen
print("OK LayoutSpec : frame_rect()/hanmen_rect(), pad_*, frame_width par défaut")

# 11. nomura : cadre tracé par défaut (#333333 x 1.5) ; @frame_width 0 -> plus de filet
svg, _ = render("@title t\n" + TAB, "nomura")
assert 'stroke="#333333" stroke-width="1.5"' in svg
svg, err = render("@title t\n@frame_width 0\n" + TAB, "nomura")
assert "WARNING" not in err
assert 'stroke="#333333" stroke-width="1.5"' not in svg   # filet parti
assert 'stroke="#333333" stroke-width="0.6"' in svg       # grille intacte
print("OK nomura : cadre tracé par défaut, @frame_width 0 = non tracé")

# 12. chindami/mega/tuto : pas de cadre par défaut ; tracé si @frame_width > 0
svg, _ = render("@title t\n" + TAB, "chindami")
assert not re.search(r'<rect [^>]*stroke="#333333" stroke-width="1\.5"', svg)
svg, _ = render("@title t\n@frame_width 2\n@frame_color red\n" + TAB, "chindami")
assert re.search(r'<rect x="49\.55[^>]*stroke="red" stroke-width="2"/>', svg)
svg, _ = render("@title t\n@frame_width 2\n" + TAB, "mega")
assert re.search(r'<rect [^>]*stroke="#333333" stroke-width="2"/>', svg)
svg, _ = render("@title t\n@frame_width 1.5\n" + TAB, "tuto")   # 1,5 pt = 2 px en tuto
assert re.search(r'<rect x="16" y="16"[^>]*stroke="#333333" stroke-width="2"/>', svg)
print("OK chindami/mega/tuto : cadre virtuel par défaut, tracé si @frame_width > 0")

# 13. page libre (vertical/horizontal) : pas de cadre tracé, @frame_width sans effet
assert render("@title t\n@frame_width 2\n" + TAB, "vertical")[0] == render("@title t\n" + TAB, "vertical")[0]
print("OK vertical (page libre) : cadre non tracé, @frame_width ignoré")

# 14. @frame_width invalide (négatif ou non numérique) : WARNING + défaut
svg, err = render("@title t\n@frame_width -1\n" + TAB, "nomura")
assert err.count("WARNING") == 1 and 'stroke="#333333" stroke-width="1.5"' in svg
svg, err = render("@title t\n@frame_width abc\n" + TAB, "nomura")
assert err.count("WARNING") == 1 and 'stroke="#333333" stroke-width="1.5"' in svg
print("OK @frame_width invalide : WARNING + défaut du layout")

print("Tous les tests de test_layout_attrs.py passent.")

# 10. Split rep_fill / vrep_fill : flèches instrumentales vs disques vocaux
svg, _ = render("@title t\n" + TAB_V, "vertical")
assert 'class="repeat-arrow" fill="none"' in svg and 'class="vocal-rep" fill="none"' in svg
svg, _ = render("@title t\n@rep_fill on\n" + TAB_V, "vertical")
assert 'class="repeat-arrow" fill="#bbbbbb"' in svg and 'class="vocal-rep" fill="none"' in svg
svg, _ = render("@title t\n@vrep_fill on\n" + TAB_V, "vertical")
assert 'class="repeat-arrow" fill="none"' in svg and 'class="vocal-rep" fill="#bbbbbb"' in svg
svg, _ = render("@title t\n@rep_fill on\n@vrep_fill on\n" + TAB_V, "vertical")
assert 'class="repeat-arrow" fill="#bbbbbb"' in svg and 'class="vocal-rep" fill="#bbbbbb"' in svg
svg, _ = render("@title t\n@vrep_fill on\n" + TAB_V, "horizontal")
assert 'class="vocal-rep" fill="#999999"' in svg and 'class="repeat-arrow" fill="none"' in svg
svg, _ = render("@title t\n" + TAB_V, "chindami")
assert 'class="repeat-arrow" fill="#bbbbbb"' in svg and 'class="vocal-rep" fill="none"' in svg  # défaut chindami : flèches pleines, disques creux
print("OK split rep_fill/vrep_fill : flèches instrumentales vs disques vocaux, tous layouts ; chindami flèches pleines par défaut")

print("Tous les tests passent.")

# 11. circle_width : épaisseur du cercle de 尺 (@shaku_circled on)
SHAKU = "@shaku_circled on\n::tab\n尺\n::\n"
svg, _ = render("@title t\n" + SHAKU, "vertical")
assert "<circle" in svg and 'stroke-width="1"' in svg          # défaut layout = 1
svg, _ = render("@title t\n" + SHAKU, "chindami")
assert 'stroke-width="0.5"' in svg                             # chindami : 0,5 pt (recueil)
svg, _ = render("@title t\n@circle_width 2\n" + SHAKU, "vertical")
assert 'stroke-width="2"' in svg                               # surcharge méta
print("OK circle_width : cercle de 尺, défaut 1 / chindami 0,5 pt / @circle_width surcharge")

print("Tous les tests passent.")
