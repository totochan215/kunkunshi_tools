#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère `docs/svg-layout-vertical.svg` : schéma coté (style figures JLREQ)
des constantes de la mise en page VERTICALE de `kkml2svg.py` (layout
« vertical », valeurs par défaut, en px).

Convention graphique : éléments de la page en GRIS FONCÉ (#333), cotes,
flèches et noms de constantes en BLEU (#1a56db). Les cotes horizontales sont
empilées au-dessus de la page (une ligne par segment, avec traits de rappel),
les cotes verticales en colonnes à gauche/droite de la page.

Usage :
    python3 docs/make_svg_layout_figure.py     # réécrit docs/svg-layout-vertical.svg
"""
import os
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "svg-layout-vertical.svg")

# --- Constantes de la mise en page verticale (kkml2svg.py, valeurs par défaut)
CELL_W, CELL_H, FS = 52, 58, 22          # render_svg(cell_w=52, cell_h=58, font_size=22)
ML = MR = MT = 16                        # MARGIN_L/R/T
HEADER_H = 10                            # header_h en vertical AVEC titre (70 sinon)
GAP_HEADER = 30
MARKER_W = CELL_W // 2                   # 26, si @marker on
GROUP_W = CELL_W + MARKER_W              # 78
ROWS_DRAWN = 4                           # cases dessinées (sur rows_per_col, défaut 12)
ROWS_DEFAULT = 12                        # rows_per_col = cols, défaut 12 (-c)
BREAK_H = 20                             # hauteur de la rupture (⋮) dans la grille
TITLE_W, TITLE_GAP = 36, 10
TITLE_OFFSET = TITLE_W + TITLE_GAP       # 46
TITLE_SPACING, TUNING_SPACING = 30, 22
TITLE_FS, META_FS = 26, 15
LYRICS_FS = int(FS * 0.75)               # @lyrics_size medium = 75% -> 16
LYRICS_SP = int(LYRICS_FS * 1.2)         # 19
LYRICS_COL_W = int(LYRICS_FS * 1.33)     # 21
LYRICS_VERSE_GAP = int(LYRICS_COL_W * 0.8)   # 16
LYR_GAP = 12                             # lyrics_offset = lyrics_total_w + 12
SYLLABLE_FS = min(int(CELL_H * 0.26), int(MARKER_W * 0.8))  # 15
SYLLABLE_SP = int(SYLLABLE_FS * 0.9)     # 13

N_DANS, N_VERSES = 2, 2                   # exemple dessiné : 2 dans, 2 couplets
LYRICS_TOTAL_W = N_VERSES * LYRICS_COL_W + (N_VERSES - 1) * LYRICS_VERSE_GAP  # 58
LYRICS_OFFSET = LYRICS_TOTAL_W + LYR_GAP                                     # 70
TOTAL_W = N_DANS * GROUP_W + ML + MR + TITLE_OFFSET + LYRICS_OFFSET         # 304
GRID_H = ROWS_DRAWN * CELL_H + BREAK_H
PAGE_H = MT + HEADER_H + GAP_HEADER + GRID_H + MT                            # 324

GRAY, BLUE, PAGE_FILL = "#333333", "#1a56db", "#fdfdfd"
OX, OY = 170, 190                        # origine de la page dans le canvas
W, H = 580, 610

out = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rect(x, y, w, h, fill="none", stroke=GRAY, sw=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
               f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def line(x1, y1, x2, y2, stroke=GRAY, sw=1.0, marker=None, dash=None):
    m = f' marker-start="url(#{marker})" marker-end="url(#{marker})"' if marker else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
               f'stroke="{stroke}" stroke-width="{sw}"{m}{d}/>')


def text(x, y, s, fill=GRAY, fs=10, anchor="middle", mono=True, rotate=None, bold=False):
    fam = "monospace" if mono else "sans-serif"
    w = ' font-weight="bold"' if bold else ""
    r = f' transform="rotate({rotate} {x:g} {y:g})"' if rotate else ""
    out.append(f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" '
               f'font-family="{fam}" font-size="{fs}" fill="{fill}"{w}{r}>{esc(s)}</text>')


def dim_h(x1, x2, y, label):
    """Cote horizontale à la hauteur y, étiquette au-dessus, traits de rappel
    depuis le haut de la page (OY) jusqu'à la cote."""
    for x in (x1, x2):
        line(x, OY - 2, x, y + 3, stroke=BLUE, sw=0.5)
    line(x1, y, x2, y, stroke=BLUE, sw=1.0, marker="arr")
    text((x1 + x2) / 2, y - 4, label, fill=BLUE, fs=10)


def dim_v(y1, y2, x, label, side="left"):
    """Cote verticale à l'abscisse x, étiquette verticale (rotated -90)."""
    for y in (y1, y2):
        line(OX - 2 if side == "left" else OX + TOTAL_W + 2, y, x - 3 if side == "left" else x + 3, y,
             stroke=BLUE, sw=0.5)
    line(x, y1, x, y2, stroke=BLUE, sw=1.0, marker="arr")
    text(x - 5 if side == "left" else x + 5, (y1 + y2) / 2, label, fill=BLUE, fs=10,
         rotate=-90 if side == "left" else 90)


# --- En-tête du SVG ---
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}">')
out.append('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
           'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker></defs>')
rect(0, 0, W, H, fill="#ffffff", stroke="none")
text(OX, 22, "Mise en page verticale — constantes (kkml2svg.py, layout « vertical », px)",
     fs=13, anchor="start", mono=False, bold=True)
text(OX, 38, "gris foncé = éléments de la page · bleu = cotes (flèches) et constantes",
     fs=9.5, anchor="start", mono=False)

# --- La page ---
rect(OX, OY, TOTAL_W, PAGE_H, fill=PAGE_FILL, stroke=GRAY, sw=1.5)
text(OX + 5, OY + PAGE_H - 5, f"page : total_w × total_h = {TOTAL_W} × {PAGE_H} (exemple)",
     fs=9, anchor="start", mono=False)

# En-tête (header_h) puis GAP_HEADER
rect(OX, OY + MT, TOTAL_W, HEADER_H, fill="#ececec", stroke=GRAY, sw=0.75)
Y0 = OY + MT + HEADER_H + GAP_HEADER          # haut de la grille

# --- Grille ::tab : N_DANS dans, chacune = cases (cell_w) + marker (marker_w) ---
dan_x = []
for ci in range(N_DANS):
    x = OX + TOTAL_W - MR - TITLE_OFFSET - (ci + 1) * GROUP_W
    dan_x.append(x)
    for r in range(ROWS_DRAWN):
        rect(x, Y0 + r * CELL_H, CELL_W, CELL_H, fill="none", stroke=GRAY, sw=0.75)
    rect(x + CELL_W, Y0, MARKER_W, ROWS_DRAWN * CELL_H, fill="#f3f3f3", stroke=GRAY, sw=0.75)
    # rupture (⋮) en bas de chaque dan
    yb = Y0 + ROWS_DRAWN * CELL_H
    line(x + 4, yb + BREAK_H, x + CELL_W - 4, yb + 2, stroke=GRAY, sw=0.75)
    line(x + CELL_W + 3, yb + BREAK_H, x + GROUP_W - 3, yb + 2, stroke=GRAY, sw=0.75)
# glyphe de note (fs) dans la 1re case du 1er dan, syllabe dans son marker
nx, ny = dan_x[0] + CELL_W / 2, Y0 + CELL_H / 2
text(nx, ny + 7, "工", fs=FS, bold=True)
text(dan_x[0] + CELL_W + MARKER_W / 2, ny + 5, "あ", fs=SYLLABLE_FS)
text(nx + 16, ny + 4, f"note fs = {FS}", fs=9, anchor="start", mono=False)
text(dan_x[0] + CELL_W + MARKER_W / 2, Y0 - 5, "marker", fs=8.5)
text((dan_x[1] + dan_x[1] + GROUP_W) / 2, Y0 - 5, "grille ::tab (dans)", fs=9)

# --- Colonne titre (droite) ---
TX = OX + TOTAL_W - MR - TITLE_W
for i, ch in enumerate("音楽"):
    text(TX + TITLE_W / 2, Y0 + TITLE_FS - 4 + i * TITLE_SPACING, ch, fs=TITLE_FS, bold=True)
for i, ch in enumerate("本調子"):
    text(TX + TITLE_W / 2, Y0 + TITLE_FS + 24 + i * TUNING_SPACING, ch, fs=META_FS, fill="#555")
text(TX + TITLE_W / 2, Y0 - 5, "titre", fs=9)

# --- Paroles ::lyrics (gauche) : N_VERSES colonnes de LYRICS_COL_W ---
for vi in range(N_VERSES):
    vx = OX + ML + LYRICS_TOTAL_W - vi * (LYRICS_COL_W + LYRICS_VERSE_GAP) - LYRICS_COL_W / 2
    rect(vx - LYRICS_COL_W / 2, Y0, LYRICS_COL_W, 3 * LYRICS_SP, fill="#f6f6f6",
         stroke=GRAY, sw=0.75)
    for k, ch in enumerate("あいう"):
        text(vx, Y0 + LYRICS_FS + k * LYRICS_SP, ch, fs=LYRICS_FS)
text(OX + ML + LYRICS_TOTAL_W / 2, Y0 - 5, "paroles ::lyrics", fs=9)

# --- Cotes horizontales empilées au-dessus de la page ---
y = 58
step = 16
segs = [
    (OX, OX + ML, f"MARGIN_L = {ML}"),
    (OX + ML, OX + ML + LYRICS_TOTAL_W, f"{N_VERSES} × LYRICS_COL_W = {LYRICS_COL_W} + LYRICS_VERSE_GAP = {LYRICS_VERSE_GAP}"),
    (OX + ML + LYRICS_TOTAL_W, OX + ML + LYRICS_OFFSET, f"gap paroles = {LYR_GAP}"),
    (dan_x[1], dan_x[1] + N_DANS * GROUP_W, f"{N_DANS} × group_w = cell_w + marker_w = {GROUP_W}"),
    (dan_x[0] + GROUP_W, dan_x[0] + GROUP_W + TITLE_GAP, f"TITLE_GAP = {TITLE_GAP}"),
    (TX, TX + TITLE_W, f"TITLE_W = {TITLE_W}"),
    (OX + TOTAL_W - MR, OX + TOTAL_W, f"MARGIN_R = {MR}"),
]
for x1, x2, label in segs:
    dim_h(x1, x2, y, label)
    y += step
dim_h(OX, OX + TOTAL_W, y, f"total_w = max_cols·group_w + ml + mr + title_offset + lyrics_offset = {TOTAL_W} (ex. {N_DANS} dans)")

# --- Cotes verticales à gauche de la page (colonnes empilées) ---
x = OX - 18
dim_v(OY, OY + MT, x, f"MARGIN_T = {MT}")
dim_v(OY + MT, OY + MT + HEADER_H, x - 16, f"header_h = {HEADER_H} (70 sans titre)")
dim_v(OY + MT + HEADER_H, Y0, x, f"GAP_HEADER = {GAP_HEADER}")
dim_v(Y0, Y0 + CELL_H, x - 16, f"cell_h = {CELL_H}")
dim_v(Y0, Y0 + GRID_H, x - 32,
      f"rows_per_col · cell_h = {ROWS_DEFAULT} · {CELL_H} = {ROWS_DEFAULT * CELL_H} px "
      f"({ROWS_DRAWN} cases + rupture dessinées, -c)")
dim_v(OY + PAGE_H - MT, OY + PAGE_H, x, f"MARGIN_T = {MT}")

# --- Cotes à droite (total_h) et en bas (cell_w, marker_w) ---
dim_v(OY, OY + PAGE_H, OX + TOTAL_W + 18, f"total_h = {PAGE_H} (exemple)", side="right")
yb = OY + PAGE_H + 18
for x in (dan_x[1], dan_x[1] + CELL_W, dan_x[1] + GROUP_W):
    line(x, OY + PAGE_H + 2, x, yb + 3, stroke=BLUE, sw=0.5)
line(dan_x[1], yb, dan_x[1] + CELL_W, yb, stroke=BLUE, sw=1.0, marker="arr")
text(dan_x[1] + CELL_W / 2, yb + 13, f"cell_w = {CELL_W}", fill=BLUE, fs=10)
line(dan_x[1] + CELL_W, yb, dan_x[1] + GROUP_W, yb, stroke=BLUE, sw=1.0, marker="arr")
text(dan_x[1] + CELL_W + MARKER_W / 2, yb + 13, f"marker_w = {MARKER_W}", fill=BLUE, fs=10)

# --- Légende des constantes d'espacement / tailles ---
ly = OY + PAGE_H + 40
text(OX, ly, "espacements / tailles : "
     f"TITLE_SPACING = {TITLE_SPACING} · TUNING_SPACING = {TUNING_SPACING} · "
     f"LYRICS_SP = {LYRICS_SP} · LYRICS_FS = {LYRICS_FS} (medium) · "
     f"SYLLABLE_FS = {SYLLABLE_FS} · SYLLABLE_SP = {SYLLABLE_SP} · fs notes = {FS}",
     fill=BLUE, fs=9.5, anchor="start")
text(OX, ly + 14, "title_offset = TITLE_W + TITLE_GAP = "
     f"{TITLE_OFFSET} · lyrics_offset = lyrics_total_w + {LYR_GAP} = {LYRICS_OFFSET} · "
     f"group_w = {GROUP_W} · marker_w = cell_w // 2 si @marker on, sinon 0",
     fill=BLUE, fs=9.5, anchor="start")

out.append("</svg>")
svg = "\n".join(out) + "\n"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

# --- Auto-contrôle : XML valide + coordonnées dans le viewBox ---
dom = xml.dom.minidom.parseString(svg)
vb = [float(v) for v in dom.documentElement.getAttribute("viewBox").split()]
for el in dom.getElementsByTagName("*"):
    for attr in ("x", "y", "x1", "y1", "x2", "y2"):
        if el.hasAttribute(attr):
            v = float(el.getAttribute(attr))
            assert vb[0] - 1 <= v <= vb[0] + vb[2] + 1, (el.tagName, attr, v)
    for attr in ("width", "height"):
        if el.hasAttribute(attr):
            v = float(el.getAttribute(attr))
            assert 0 <= v <= max(vb[2], vb[3]), (el.tagName, attr, v)
print(f"OK: {OUT}  ({len(svg)} octets, viewBox {W}x{H}, XML valide, coordonnées bornées)")
