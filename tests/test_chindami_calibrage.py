# -*- coding: utf-8 -*-
"""Tests du calibrage chindami (recueil Chindami Kunkunshi Hyoukashuu, 2026-11-24).

Vérifie les constantes de la spec CHINDAMI et les ancres de rendu :
- marges mesurées au bloc de tablature : haut ≈ 1 cm, bas ≈ 1,3 cm, droite/gauche ≈ 1,5 cm ;
- 16 dans max constatés, 12 cases/dan, pas de gap entre piles (dan_gap = 0) ;
- case 65x83 px, pile 97 px, marker 32 px (px ÷ 2,785) ;
- colonne titre dans la marge droite (bord droit à 0,75 cm du bord page), fs 17,5,
  1re baseline à 2,1 cm du haut de page (ancrage page = hanmen = cadre ici) ;
- @musicno : fs = 6 mm (largeur « 99 » = 6 mm), centré sur la colonne titre, ligne médiane ~1 mm au-dessus de celle de la 1re cellule (ancrage page), écart 0,4 cm avec le haut du titre ;
- @choshi : même fs que le titre, dernière baseline à 2,3 cm du bord bas ;
- @genre : colonne entre bloc de tab et titre, centerline à 0,4 cm du bord droit du
  bloc de tab, fs 50 % titre, yamakakko pivotés à 90° ;
- n° de page : baseline à 0,7 cm du bord bas, centré en x, fs 10 (≈ 2,5 mm) ;
- une seule couleur #000, filets 0,5 pt, flèches de boucle pleines (rep_fill),
  cercles de 尺 à 0,5 pt (circle_width) ;
- marker cosubstantiel (forcé même avec @marker off), syllabes à 80 % du marker.

Usage :
    python3 tests/test_chindami_calibrage.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

CM = k.CM
spec = k.CHINDAMI
TXT = re.compile(r'<text x="([\d.]+(?: [\d.]+)*)" y="([\d.]+(?: [\d.]+)*)"[^>]*font-size="([\d.]+)"[^>]*fill="([^"]*)"[^>]*>([^<]*)</text>')
ROT = re.compile(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="([\d.]+)"[^>]*transform="rotate\(90 [\d.]+ [\d.]+\)"[^>]*>([^<]*)</text>')

TITRE = "てぃんさぐぬ花"
CHOSHI = "本調子"
GO = "合"


def render(src):
    return k.render_svg(k.parse_kkml(src), layout="chindami")


def base_src(**meta):
    lines = ["@title " + TITRE, "@choshi " + CHOSHI]
    for key, val in meta.items():
        lines.append("@" + key + " " + val)
    lines.append("::tab")
    lines.append(" ".join([GO] * 12))
    lines.append("::")
    return "\n".join(lines) + "\n"


def blocks(svg, fs=None):
    """Blocs <text> groupés (texte vertical) : liste (xs, ys, fs, fill, chars)."""
    out = []
    for xs, ys, f, fill, chars in TXT.findall(svg):
        if fs is not None and float(f) != fs:
            continue
        out.append(([float(v) for v in xs.split()],
                    [float(v) for v in ys.split()], float(f), fill, chars))
    return out


# 1. Constantes de la spec (mesures recueil 2026-11-24)
assert abs(spec.margin_t - 1 * CM) < 1e-9
assert abs(spec.margin_b - 1.3 * CM) < 1e-9
assert abs(spec.margin_l - 1.5 * CM) < 1e-9
assert abs(spec.margin_r - 1.5 * CM) < 1e-9
assert spec.dans_per_block == 16 and spec.page_dans_cap == 16 and spec.cells_per_dan == 12
# 16 = plafond absolu par bloc (page non extensible ; atteint seulement sans titre/méta sur la page)
assert spec.dan_gap == 0
assert abs(spec.cell_w - 65 / 2.785) < 1e-9 and abs(spec.cell_h - 83 / 2.785) < 1e-9
assert abs(spec.pile_w - 97 / 2.785) < 1e-9 and abs(spec.marker_w - 32 / 2.785) < 1e-9
assert spec.title_fs == 17.5 and spec.title_spacing == 17.5   # fs choshi = fs titre
assert abs(spec.title_w - 0.6 * CM) < 1e-9            # pitch colonne titre = 6 mm hors ruby (1,5+6,0+7,5 = 15 mm au total, recueil 2026-11-25)
assert abs(spec.title_gap - 0.15 * CM) < 1e-9         # gap bloc tab -> colonne titre = 1,5 mm
assert abs(spec.genre_w - 0.4 * CM) < 1e-9 and abs(spec.genre_gap - 0.1 * CM) < 1e-9  # genre : pitch 4 mm, gaps 1 mm
assert spec.page_no_fs == 10                                   # n° ≈ 2,5 mm de haut
assert spec.cell_color == "#000000" and spec.arrow_color == "#000000"
assert spec.cell_width == 0.4 and spec.arrow_width == 0.4      # filets fins (0,4 pt, essai 2026-11-25)
assert spec.rep_fill is True and spec.vrep_fill is False       # flèches pleines, disques creux
assert spec.circle_width == 0.5                                # cercles de 尺 0,5 pt
assert spec.meta_order == ("genre", "choshi")
fx0, fy0, fx1, fy1 = spec.frame_rect()
assert abs(fx0 - 1.5 * CM) < 1e-9 and abs(fy0 - 1 * CM) < 1e-9
assert abs(fx1 - (spec.page_w - 1.5 * CM)) < 1e-9 and abs(fy1 - (spec.page_h - 1.3 * CM)) < 1e-9
print("OK 1. constantes de la spec CHINDAMI (marges, grille, fs, couleurs, meta_order)")

# 2. Ancres de base : titre, @choshi, n° de page (sans @musicno ni @genre)
svgs = render(base_src())
assert len(svgs) == 1
svg = svgs[0]
tx0 = spec.page_w - 0.75 * CM - spec.title_w / 2          # bord droit du titre à 0,75 cm du bord page
tb = blocks(svg, fs=17.5)
titre = [b for b in tb if b[4] == TITRE]
assert len(titre) == 1, [b[4] for b in tb]
xs, ys, _f, fill, _c = titre[0]
assert all(abs(x - tx0) < 0.01 for x in xs), xs             # colonne titre dans la marge droite
assert abs(ys[0] - 2.1 * CM) < 0.01, ys[0]                  # 1re baseline à 2,1 cm du haut de page
assert fill == "#000"
choshi = [b for b in tb if b[4] == CHOSHI]
assert len(choshi) == 1
cxs, cys, _f, _fill, _c = choshi[0]
assert all(abs(x - tx0) < 0.01 for x in cxs)                # aligné sur la 1re colonne du titre
assert abs(cys[-1] - (spec.page_h - 2.3 * CM)) < 0.01, cys[-1]   # dernière baseline à 2,3 cm du bord bas
title_col_left = tx0 - spec.title_w / 2
tab_right = min(fx1, title_col_left - spec.title_gap)          # = fx1 exactement : 1,5 + 6,0 + 7,5 = 15 mm au total
assert abs(tab_right - fx1) < 1e-6, (tab_right, fx1)
mrect = [r for r in re.findall(r'<rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)"[^>]*/>', svg)
         if abs(float(r[1]) - spec.marker_w) < 1e-6]
assert mrect and all(abs(float(r[0]) + float(r[1]) - tab_right) < 0.01 for r in mrect), (mrect, tab_right)
assert abs((title_col_left - tab_right) - spec.title_gap) < 0.01
m = re.search(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="([\d.]+)"[^>]*fill="([^"]*)">–1–</text>', svg)
assert m, "n° de page introuvable"
assert abs(float(m.group(1)) - spec.page_w / 2) < 0.01      # centré en x sur la page
assert abs(float(m.group(2)) - (spec.page_h - 0.7 * CM)) < 0.01   # baseline à 0,7 cm du bord bas
assert m.group(3) == "10" and m.group(4) == "#000"
print("OK 2. titre (baseline 2,1 cm, marge droite 0,75 cm), @choshi (bas 2,3 cm, fs 17,5), n° page (bas 0,7 cm, centré, fs 10)")

# 3. @musicno + @genre : n° à 1,4 cm (fs 11, haut ≈ 4 mm), titre poussé de 0,4 cm,
#    genre en colonne à 0,4 cm du bord droit du bloc de tab, yamakakko pivotés, fs 50 %
svgs = render(base_src(musicno="12", genre="民謡"))
svg = svgs[0]
m = re.search(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="([\d.]+)"[^>]*fill="([^"]*)">12</text>', svg)
assert m, "@musicno introuvable"
mno_x, mno_y, mno_fs = float(m.group(1)), float(m.group(2)), m.group(3)
MNO_FS = 6 * CM / 10
assert mno_fs == f"{MNO_FS:g}" and m.group(4) == "#000"     # fs = 6 mm -> largeur "99" = 6 mm
y_mno_attendu = spec.margin_t + spec.cell_h / 2 - 0.1 * CM + MNO_FS * 0.35
assert abs(mno_y - y_mno_attendu) < 0.01, mno_y
# ligne médiane du n° = baseline - 0,35 fs, à 1 mm au-dessus de la ligne médiane de la 1re cellule
assert abs((mno_y - 0.35 * MNO_FS) - (spec.margin_t + spec.cell_h / 2 - 0.1 * CM)) < 0.01
tx0b = spec.page_w - 0.75 * CM - spec.title_w / 2            # colonne titre ancrée à 0,75 cm du bord droit, ne bouge PAS
assert abs(mno_x - tx0b) < 0.01, (mno_x, tx0b)
tcl = tx0b - spec.title_w / 2
gx = tcl - spec.genre_gap - spec.genre_w / 2                  # centerline genre : 1 mm avant le titre, pitch 4 mm
tb = blocks(svg, fs=17.5)
titre = [b for b in tb if b[4] == TITRE][0]
assert all(abs(x - tx0b) < 0.01 for x in titre[0])           # le titre ne bouge pas quand @genre est présent
tab_right_g = min(fx1, tcl - 2 * spec.genre_gap - spec.genre_w)   # bloc tab reculé de 2*1 mm + 4 mm = 6 mm
mrect = [r for r in re.findall(r'<rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)"[^>]*/>', svg)
         if abs(float(r[1]) - spec.marker_w) < 1e-6]
assert mrect and all(abs(float(r[0]) + float(r[1]) - tab_right_g) < 0.01 for r in mrect), (mrect, tab_right_g)
assert abs(titre[1][0] - (y_mno_attendu + MNO_FS * 0.12 + 0.4 * CM + 17.5 * 0.88)) < 0.01, titre[1][0]   # écart 0,4 cm bas d'encre n° -> haut du titre
rot = [(float(x), float(y), float(f), c) for x, y, f, c in ROT.findall(svg)]
yama = [r for r in rot if r[3] in ("《", "》")]
assert len(yama) == 2, rot                                 # yamakakko pivotés à 90°
assert all(abs(r[0] - gx) < 0.01 and r[2] == 8.75 for r in yama), yama   # fs = 50 % fs titre
assert any(b[4] == "民謡" and abs(b[0][0] - gx) < 0.01 and b[2] == 8.75 for b in blocks(svg, fs=8.75))
print("OK 3. @musicno (fs 6 mm, centré sur le titre, médiane à 1 mm au-dessus de la 1re cellule, écart 0,4 cm avec le titre), titre ancré 0,75 cm du bord droit (ne bouge pas avec @genre), genre intercalé (1 mm + 4 mm + 1 mm, bloc tab reculé de 6 mm, fs 8,75, 《》 pivotés)")

# 4. Marker cosubstantiel : présent même avec @marker off ; syllabes à 80 % du marker
src_off = "@marker off\n" + base_src()
svgs = render(src_off)
mw = spec.marker_w
assert any(f'width="{mw}"' in r for r in re.findall(r'<rect[^>]*/>', svgs[0])), "marker absent malgré @marker off"
src_v = base_src() + "::vocal\n" + " ".join(["あ"] * 12) + "\n::\n"
svgs = render(src_v)
sfs = int(mw * 0.8)
voc = [b for b in blocks(svgs[0]) if "あ" in b[4]]
assert len(voc) == 12 and all(b[2] == sfs for b in voc), [(b[2], b[4]) for b in voc]
print("OK 4. marker forcé (@marker off ignoré), fs syllabes = int(0,8 x marker_w) =", sfs)

# 5. Noir partout, filets 0,5 pt ; pagination à 16 dans (17 dans -> 2 pages)
svg = render(base_src())[0]
rects = re.findall(r'<rect [^>]*fill="none"[^>]*/>', svg)
assert rects, "cases introuvables"
for r in rects:
    assert 'stroke="#000000"' in r and 'stroke-width="0.4"' in r, r
src17 = ("@title " + TITRE + "\n@choshi " + CHOSHI + "\n::tab\n"
         + "\n".join(" ".join([GO] * 12) for _ in range(17)) + "\n::\n")
svgs = render(src17)   # 17 colonnes de 12 cases -> 2 pages (plafond 16 dans/bloc, page non extensible)
assert len(svgs) == 2, len(svgs)
print("OK 5. cases/marker en #000 filet 0,4 pt ; 17 dans -> 2 pages (dans_per_block = 16)")

# 6. Titre long : saut de colonne (2 colonnes de titre, bloc de tab repoussé à gauche)
long_title = "あ" * 25
src = "@title " + long_title + "\n@choshi " + CHOSHI + "\n::tab\n" + " ".join([GO] * 12) + "\n::\n"
svg = render(src)[0]
tb = sorted((b for b in blocks(svg, fs=17.5) if set(b[4]) == {"あ"}),
            key=lambda b: -b[0][0])
assert len(tb) == 2, [b[4] for b in blocks(svg, fs=17.5)]     # 2 colonnes de titre (20 car./colonne)
assert abs(tb[1][0][0] - tb[0][0][0] + spec.title_w) < 0.01  # colonne suivante à gauche d'une title_w
first_pile_x = min(float(r.split('x="')[1].split('"')[0]) for r in re.findall(r'<rect [^>]*fill="none"[^>]*/>', svg) if 'height="29.8' in r)
tcl6 = (spec.page_w - 0.75 * CM - spec.title_w / 2) - spec.title_w / 2
x_right6 = min(fx1, tcl6 - spec.title_gap) - spec.title_w   # gap 1,5 mm + colonne titre suppl. (titre long)
assert abs(first_pile_x - (x_right6 - spec.pile_w)) < 0.01, (first_pile_x, x_right6)
print("OK 6. titre long : 2 colonnes verticales, bloc de tab repoussé à gauche d'autant")


# 7. Flèche pleine (rep_fill chindami) : seule la TÊTE est remplie — la queue (path
#    en L) porte fill="none" explicite, sinon le path ouvert serait fermé implicitement
#    au remplissage et créerait un triangle rectangle rempli au coude (8 sites : 4 fonctions
#    x start/end, vertical + horizontal).
TAB_V = "::tab\n|: " + GO + " (:" + chr(0x5C3A) + " " + chr(0x5C3A) + ":) :|\n::\n"
for layout in ("chindami", "vertical", "horizontal"):
    src = "@title t\n" + ("@rep_fill on\n@vrep_fill on\n" if layout != "chindami" else "") + TAB_V
    svg = "".join(k.render_svg(k.parse_kkml(src), layout=layout))
    groups = re.findall(r'<g class="(?:repeat-arrow|vocal-rep)"([^>]*)>(.*?)</g>', svg, re.S)
    assert len(groups) == 4, (layout, len(groups))
    for attrs, body in groups:
        gfill = re.search(r'fill="([^"]*)"', attrs).group(1)
        path = re.search(r'<path[^>]*/>', body).group(0)
        head = re.search(r'<(?:polygon|circle)[^>]*/>', body).group(0)
        assert 'fill="none"' in path, (layout, path)          # queue JAMAIS remplie
        assert "fill=" not in head, (layout, head)            # tête hérite du fill du <g>
        if gfill != "none":                                   # flèche/disque plein
            assert "fill=" not in path or 'fill="none"' in path
print("OK 7. rep_fill/vrep_fill : seule la tête (polygon/cercle) est remplie, queue fill=\"none\" (4 fonctions x 2, vertical+horizontal+chindami)")

print("\nTous les tests de calibrage chindami passent.")
