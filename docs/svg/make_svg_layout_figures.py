#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère les schémas SVG cotés (style figures JLREQ) des mises en page de
`kkml2svg.py` : `docs/svg-layout-<layout>.svg` pour vertical, horizontal,
nomura, chindami, tuto, mega.

Convention graphique : éléments de la page en GRIS FONCÉ (#333), cotes,
flèches et noms de constantes en BLEU (#1a56db). Les constantes de page
les instances LayoutSpec (NOMURA, CHINDAMI, MEGA, TUTO, CM, PX) sont importées de `kkml2svg`
(source de vérité) ; les autres sont les valeurs par défaut du code.

Usage :
    python3 docs/svg/make_svg_layout_figures.py  # réécrit les 6 SVG dans docs/svg/
"""
import os
import sys
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
DOCS = os.path.dirname(os.path.abspath(__file__))   # docs/svg/

import kkml2svg as k   # specs de mise en page (k.NOMURA.page_w, k.CHINDAMI.cell_h, k.MEGA.block_gap...)

GRAY, BLUE, PAGE_FILL = "#333333", "#1a56db", "#fdfdfd"
CM = k.CM


class Fig:
    """Canvas SVG avec helpers de dessin + cotes. Toutes les coordonnées
    passées aux helpers sont en unités RÉELLES de la mise en page ; la classe
    applique l'origine (ox, oy) et l'échelle sc. Les tailles de police des
    ÉTIQUETTES restent en px canvas (lisibilité), celles des glyphes simulés
    sont mises à l'échelle."""

    def __init__(self, name, W, H, sc=1.0, ox=0, oy=0, title=""):
        self.name, self.W, self.H, self.sc = name, W, H, sc
        self.ox, self.oy = ox, oy
        self.out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">',
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker></defs>',
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
        ]
        if title:
            self.text(ox, 22, title, fs=13, anchor="start", mono=False, bold=True)
            self.text(ox, 38, "gris foncé = éléments · bleu = cotes (flèches) et constantes"
                      + (f" · échelle {sc:g}" if sc != 1 else ""),
                      fs=9.5, anchor="start", mono=False)

    def X(self, x):
        return self.ox + x * self.sc

    def Y(self, y):
        return self.oy + y * self.sc

    def S(self, v):
        return v * self.sc

    @staticmethod
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def rect(self, x, y, w, h, fill="none", stroke=GRAY, sw=1.0):
        self.out.append(f'<rect x="{self.X(x):g}" y="{self.Y(y):g}" '
                        f'width="{self.S(w):g}" height="{self.S(h):g}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{self.S(sw):g}"/>')

    def line(self, x1, y1, x2, y2, stroke=GRAY, sw=1.0, marker=None):
        m = (f' marker-start="url(#{marker})" marker-end="url(#{marker})"'
             if marker else "")
        self.out.append(f'<line x1="{self.X(x1):g}" y1="{self.Y(y1):g}" '
                        f'x2="{self.X(x2):g}" y2="{self.Y(y2):g}" stroke="{stroke}" '
                        f'stroke-width="{self.S(sw):g}"{m}/>')

    def text(self, x, y, s, fill=GRAY, fs=10, anchor="middle", mono=True,
             rotate=None, bold=False, scaled=False):
        fam = "monospace" if mono else "sans-serif"
        w = ' font-weight="bold"' if bold else ""
        r = f' transform="rotate({rotate} {self.X(x):g} {self.Y(y):g})"' if rotate else ""
        f = self.S(fs) if scaled else fs
        self.out.append(f'<text x="{self.X(x):g}" y="{self.Y(y):g}" '
                        f'text-anchor="{anchor}" font-family="{fam}" '
                        f'font-size="{f:g}" fill="{fill}"{w}{r}>{self.esc(s)}</text>')

    def dim_h(self, x1, x2, y, label, ext_y, fs=10):
        """Cote horizontale (unités réelles) à la hauteur y ; traits de rappel
        depuis ext_y (bord de l'élément) jusqu'à la cote."""
        for x in (x1, x2):
            self.line(x, ext_y, x, y + 3 / self.sc, stroke=BLUE, sw=0.5)
        self.line(x1, y, x2, y, stroke=BLUE, sw=1.0, marker="arr")
        self.text((x1 + x2) / 2, y - 4 / self.sc, label, fill=BLUE, fs=fs)

    def dim_v(self, y1, y2, x, label, side="left", ext_x=None, fs=10):
        """Cote verticale (unités réelles) à l'abscisse x ; étiquette tournée."""
        if ext_x is None:
            ext_x = 0 if side == "left" else 10 ** 9  # sera remplacé par l'appelant
        for y in (y1, y2):
            self.line(ext_x, y, x + (-3 / self.sc if side == "left" else 3 / self.sc),
                      y, stroke=BLUE, sw=0.5)
        self.line(x, y1, x, y2, stroke=BLUE, sw=1.0, marker="arr")
        rot = -90 if side == "left" else 90
        self.text(x + (-5 / self.sc if side == "left" else 5 / self.sc),
                  (y1 + y2) / 2, label, fill=BLUE, fs=fs, rotate=rot)

    def save(self):
        self.out.append("</svg>")
        svg = "\n".join(self.out) + "\n"
        path = os.path.join(DOCS, f"svg-layout-{self.name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        dom = xml.dom.minidom.parseString(svg)
        vb = [float(v) for v in dom.documentElement.getAttribute("viewBox").split()]
        for el in dom.getElementsByTagName("*"):
            for attr in ("x", "x1", "x2"):
                if el.hasAttribute(attr):
                    v = float(el.getAttribute(attr))
                    assert vb[0] - 1 <= v <= vb[0] + vb[2] + 1, (self.name, el.tagName, attr, v)
            for attr in ("y", "y1", "y2"):
                if el.hasAttribute(attr):
                    v = float(el.getAttribute(attr))
                    assert vb[1] - 1 <= v <= vb[1] + vb[3] + 1, (self.name, el.tagName, attr, v)
        return path, len(svg)


# --------------------------------------------------------------------------- #
# vertical (valeurs par défaut render_svg : cell_w=52, cell_h=58, fs=22)
# --------------------------------------------------------------------------- #
def fig_vertical():
    CELL_W, CELL_H, FS = 52, 58, 22
    ML = MR = MT = 16
    HEADER_H, GAP_HEADER = 10, 30          # header_h vertical AVEC titre (70 sinon)
    MARKER_W = CELL_W // 2                 # 26
    GROUP_W = CELL_W + MARKER_W            # 78
    ROWS_DRAWN, ROWS_DEFAULT, BREAK_H = 4, 12, 20
    TITLE_W, TITLE_GAP = 36, 10
    TITLE_OFFSET = TITLE_W + TITLE_GAP
    TITLE_SPACING, TUNING_SPACING = 30, 22
    TITLE_FS, META_FS = 26, 15
    LYRICS_FS = int(FS * 0.75)             # medium
    LYRICS_SP = int(LYRICS_FS * 1.2)
    LYRICS_COL_W = int(LYRICS_FS * 1.33)
    LYRICS_VERSE_GAP = int(LYRICS_COL_W * 0.8)
    LYR_GAP = 12
    SYLLABLE_FS = min(int(CELL_H * 0.26), int(MARKER_W * 0.8))
    N_DANS, N_VERSES = 2, 2
    LYRICS_TOTAL_W = N_VERSES * LYRICS_COL_W + (N_VERSES - 1) * LYRICS_VERSE_GAP
    LYRICS_OFFSET = LYRICS_TOTAL_W + LYR_GAP
    TOTAL_W = N_DANS * GROUP_W + ML + MR + TITLE_OFFSET + LYRICS_OFFSET
    GRID_H = ROWS_DRAWN * CELL_H + BREAK_H
    PAGE_H = MT + HEADER_H + GAP_HEADER + GRID_H + MT

    f = Fig("vertical", 580, 610, sc=1.0, ox=170, oy=190,
            title="Mise en page verticale — constantes (kkml2svg.py, layout « vertical », px)")
    f.rect(0, 0, TOTAL_W, PAGE_H, fill=PAGE_FILL, stroke=GRAY, sw=1.5)
    f.text(5, PAGE_H - 5, f"page : total_w × total_h = {TOTAL_W} × {PAGE_H} (exemple)",
           fs=9, anchor="start", mono=False)
    f.rect(0, MT, TOTAL_W, HEADER_H, fill="#ececec", stroke=GRAY, sw=0.75)
    Y0 = MT + HEADER_H + GAP_HEADER

    dan_x = []
    for ci in range(N_DANS):
        x = TOTAL_W - MR - TITLE_OFFSET - (ci + 1) * GROUP_W
        dan_x.append(x)
        for r in range(ROWS_DRAWN):
            f.rect(x, Y0 + r * CELL_H, CELL_W, CELL_H, stroke=GRAY, sw=0.75)
        f.rect(x + CELL_W, Y0, MARKER_W, ROWS_DRAWN * CELL_H, fill="#f3f3f3",
               stroke=GRAY, sw=0.75)
        yb = Y0 + ROWS_DRAWN * CELL_H
        f.line(x + 4, yb + BREAK_H, x + CELL_W - 4, yb + 2, stroke=GRAY, sw=0.75)
        f.line(x + CELL_W + 3, yb + BREAK_H, x + GROUP_W - 3, yb + 2, stroke=GRAY, sw=0.75)
    f.text(dan_x[0] + CELL_W / 2, Y0 + CELL_H / 2 + 7, "工", fs=FS, bold=True, scaled=True)
    f.text(dan_x[0] + CELL_W + MARKER_W / 2, Y0 + CELL_H / 2 + 5, "あ",
           fs=SYLLABLE_FS, scaled=True)
    f.text(dan_x[0] + CELL_W / 2 + 16, Y0 + CELL_H / 2 + 4, f"note fs = {FS}",
           fs=9, anchor="start", mono=False)
    f.text(dan_x[0] + CELL_W + MARKER_W / 2, Y0 - 5, "marker", fs=8.5)
    f.text(dan_x[1] + GROUP_W / 2, Y0 - 5, "grille ::tab (dans)", fs=9)

    TX = TOTAL_W - MR - TITLE_W
    for i, ch in enumerate("音楽"):
        f.text(TX + TITLE_W / 2, Y0 + TITLE_FS - 4 + i * TITLE_SPACING, ch,
               fs=TITLE_FS, bold=True, scaled=True)
    for i, ch in enumerate("本調子"):
        f.text(TX + TITLE_W / 2, Y0 + TITLE_FS + 24 + i * TUNING_SPACING, ch,
               fs=META_FS, fill="#555", scaled=True)
    f.text(TX + TITLE_W / 2, Y0 - 5, "titre", fs=9)

    for vi in range(N_VERSES):
        vx = ML + LYRICS_TOTAL_W - vi * (LYRICS_COL_W + LYRICS_VERSE_GAP) - LYRICS_COL_W / 2
        f.rect(vx - LYRICS_COL_W / 2, Y0, LYRICS_COL_W, 3 * LYRICS_SP, fill="#f6f6f6",
               stroke=GRAY, sw=0.75)
        for kk, ch in enumerate("あいう"):
            f.text(vx, Y0 + LYRICS_FS + kk * LYRICS_SP, ch, fs=LYRICS_FS, scaled=True)
    f.text(ML + LYRICS_TOTAL_W / 2, Y0 - 5, "paroles ::lyrics", fs=9)

    y = -132                              # cotes empilées au-dessus (coords négatives = au-dessus de la page)
    for x1, x2, label in [
        (0, ML, f"margin_l = {ML}"),
        (ML, ML + LYRICS_TOTAL_W, f"{N_VERSES}×LYRICS_COL_W={LYRICS_COL_W} + LYRICS_VERSE_GAP={LYRICS_VERSE_GAP}"),
        (ML + LYRICS_TOTAL_W, ML + LYRICS_OFFSET, f"gap paroles = {LYR_GAP}"),
        (dan_x[1], dan_x[1] + N_DANS * GROUP_W, f"{N_DANS}×group_w = cell_w+marker_w = {GROUP_W}"),
        (dan_x[0] + GROUP_W, dan_x[0] + GROUP_W + TITLE_GAP, f"title_gap = {TITLE_GAP}"),
        (TX, TX + TITLE_W, f"title_w = {TITLE_W}"),
        (TOTAL_W - MR, TOTAL_W, f"margin_r = {MR}"),
    ]:
        f.dim_h(x1, x2, y, label, ext_y=-2)
        y += 16
    f.dim_h(0, TOTAL_W, y, f"total_w = max_cols·group_w + ml + mr + title_offset + lyrics_offset = {TOTAL_W} (ex. {N_DANS} dans)", ext_y=-2)

    f.dim_v(0, MT, -18, f"margin_t = {MT}", ext_x=-2)
    f.dim_v(MT, MT + HEADER_H, -34, f"header_h = {HEADER_H} (70 sans titre)", ext_x=-2)
    f.dim_v(MT + HEADER_H, Y0, -18, f"gap_header = {GAP_HEADER}", ext_x=-2)
    f.dim_v(Y0, Y0 + CELL_H, -34, f"cell_h = {CELL_H}", ext_x=-2)
    f.dim_v(Y0, Y0 + GRID_H, -50,
            f"cells_per_dan·cell_h = {ROWS_DEFAULT}·{CELL_H} = {ROWS_DEFAULT * CELL_H} px "
            f"({ROWS_DRAWN} cases + rupture dessinées, -c)", ext_x=-2)
    f.dim_v(PAGE_H - MT, PAGE_H, -18, f"margin_t = {MT}", ext_x=-2)
    f.dim_v(0, PAGE_H, TOTAL_W + 18, f"total_h = {PAGE_H} (exemple)", side="right",
            ext_x=TOTAL_W + 2)

    yb = PAGE_H + 18
    for x in (dan_x[1], dan_x[1] + CELL_W, dan_x[1] + GROUP_W):
        f.line(x, PAGE_H + 2, x, yb + 3, stroke=BLUE, sw=0.5)
    f.line(dan_x[1], yb, dan_x[1] + CELL_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(dan_x[1] + CELL_W / 2, yb + 13, f"cell_w = {CELL_W}", fill=BLUE, fs=10)
    f.line(dan_x[1] + CELL_W, yb, dan_x[1] + GROUP_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(dan_x[1] + CELL_W + MARKER_W / 2, yb + 13, f"marker_w = {MARKER_W}",
           fill=BLUE, fs=10)

    ly = PAGE_H + 40
    f.text(0, ly, "espacements/tailles : "
           f"title_spacing = {TITLE_SPACING} · tuning_spacing = {TUNING_SPACING} · "
           f"LYRICS_SP = {LYRICS_SP} · LYRICS_FS = {LYRICS_FS} (medium) · "
           f"SYLLABLE_FS = {SYLLABLE_FS} · SYLLABLE_SP = {int(SYLLABLE_FS * 0.9)} · fs notes = {FS}",
           fill=BLUE, fs=9.5, anchor="start")
    f.text(0, ly + 14, f"title_offset = title_w + title_gap = {TITLE_OFFSET} · "
           f"lyrics_offset = lyrics_total_w + {LYR_GAP} = {LYRICS_OFFSET} · "
           f"group_w = {GROUP_W} · marker_w = cell_w//2 si @marker on, sinon 0",
           fill=BLUE, fs=9.5, anchor="start")
    return f


# --------------------------------------------------------------------------- #
# horizontal (page à taille variable, règle alignée ; cell_w=52, cell_h=58, fs=22)
# --------------------------------------------------------------------------- #
def fig_horizontal():
    CELL_W, CELL_H, FS = 52, 58, 22
    ML = MT = 16
    MR = max(16, CELL_W // 2)              # 26 : demi-case min à droite
    TITLE_INK_DESCENT, H_TITLE_AIR = 6, 10 + (36 - 26) // 2   # 15
    HEADER_H = 26 + TITLE_INK_DESCENT + H_TITLE_AIR           # 47 avec titre
    GAP_HEADER = 0
    MARKER_H = CELL_H // 2                 # 29, ligne marker sous chaque rangée
    COLS_DEFAULT = 12
    COLS_DRAWN, BREAK_W = 8, 24
    H_LYRICS_FS = int(FS * 0.75)           # 16 (medium)
    H_LYRICS_SP = int(H_LYRICS_FS * 1.2)    # 19
    H_LYRICS_COL_W = int(H_LYRICS_FS * 1.33)
    GAP_TAB_LYRICS = 12 + H_LYRICS_COL_W + int(H_LYRICS_FS * 0.88) - 6   # 41
    H_SYL_FS = min(int(CELL_W * 0.26), int(MARKER_H * 0.8))              # 13
    ROWS_DRAWN = 2
    GRID_W = COLS_DRAWN * CELL_W + BREAK_W
    TOTAL_W = ML + GRID_W + MR
    GRID_H = ROWS_DRAWN * (CELL_H + MARKER_H)
    PAGE_H = MT + HEADER_H + GAP_HEADER + GRID_H + GAP_TAB_LYRICS + 2 * H_LYRICS_SP + 10

    f = Fig("horizontal", 690, 580, sc=1.0, ox=150, oy=170,
            title="Mise en page horizontale — constantes (layout « horizontal », px, page à taille variable)")
    f.rect(0, 0, TOTAL_W, PAGE_H, fill=PAGE_FILL, stroke=GRAY, sw=1.5)
    f.text(ML, 20, "音楽", fs=26, anchor="start", bold=True, scaled=True)
    f.text(ML + 90, 20, "@author @composer … (flux, sans repli)", fs=12, anchor="start",
           fill="#777", mono=False)
    Y0 = MT + HEADER_H + GAP_HEADER
    for r in range(ROWS_DRAWN):
        y = Y0 + r * (CELL_H + MARKER_H)
        for c in range(COLS_DRAWN):
            f.rect(ML + c * CELL_W, y, CELL_W, CELL_H, stroke=GRAY, sw=0.75)
        f.rect(ML + COLS_DRAWN * CELL_W, y, BREAK_W, CELL_H, fill="none", stroke=GRAY,
               sw=0.5)
        f.line(ML + COLS_DRAWN * CELL_W + 4, y + CELL_H, ML + COLS_DRAWN * CELL_W + BREAK_W - 4,
               y + 2, stroke=GRAY, sw=0.5)
        f.rect(ML, y + CELL_H, GRID_W, MARKER_H, fill="#f3f3f3", stroke=GRAY, sw=0.75)
    f.text(ML + 20, Y0 + CELL_H / 2 + 7, "工", fs=FS, bold=True, scaled=True)
    f.text(ML + 20, Y0 + CELL_H + MARKER_H / 2 + 4, "あ", fs=H_SYL_FS, scaled=True)
    f.text(ML + GRID_W / 2, Y0 - 5, f"grille ::tab ({COLS_DEFAULT} cases/dan défaut, -c)", fs=9)
    f.text(ML + GRID_W / 2, Y0 + CELL_H + MARKER_H / 2 + 12, "ligne marker", fs=8.5)
    YL = Y0 + GRID_H + GAP_TAB_LYRICS
    f.text(ML, YL, "あいうえおかきくけこ", fs=H_LYRICS_FS, anchor="start", scaled=True)
    f.text(ML, YL + H_LYRICS_SP, "さしすせそたちつてと", fs=H_LYRICS_FS, anchor="start", scaled=True)
    f.text(ML + GRID_W / 2, YL - 8, "paroles ::lyrics (1 colonne verticale = 1 ligne, pas de repli)",
           fs=9)

    y = -100
    for x1, x2, label in [
        (0, ML, f"ml = {ML}"),
        (ML, ML + GRID_W, f"cols·cell_w (cols = {COLS_DEFAULT} défaut)"),
        (ML + GRID_W, TOTAL_W, f"mr = max(16, cell_w//2) = {MR}"),
    ]:
        f.dim_h(x1, x2, y, label, ext_y=-2)
        y += 16
    f.dim_h(0, TOTAL_W, y, f"total_w = contenu (règle alignée, pas de largeur imposée)", ext_y=-2)

    f.dim_v(0, MT, -18, f"mt = {MT}", ext_x=-2)
    f.dim_v(MT, MT + HEADER_H, -34, f"header_h = 26+6+15 = {HEADER_H} (titre fs 26 ; 26 sans titre)", ext_x=-2)
    f.dim_v(Y0, Y0 + CELL_H, -18, f"cell_h = {CELL_H}", ext_x=-2)
    f.dim_v(Y0 + CELL_H, Y0 + CELL_H + MARKER_H, -34, f"marker_h = cell_h//2 = {MARKER_H}", ext_x=-2)
    f.dim_v(Y0 + GRID_H, YL, -18, f"GAP_TAB_LYRICS = 12+{H_LYRICS_COL_W}+…−6 = {GAP_TAB_LYRICS}", ext_x=-2)
    f.dim_v(YL, YL + H_LYRICS_SP, -34, f"h_lyrics_sp = {H_LYRICS_SP}", ext_x=-2)
    f.dim_v(0, PAGE_H, TOTAL_W + 18, f"total_h = {PAGE_H} (exemple, contenu)", side="right", ext_x=TOTAL_W + 2)

    yb = PAGE_H + 18
    f.line(ML, PAGE_H + 2, ML, yb + 3, stroke=BLUE, sw=0.5)
    f.line(ML + CELL_W, PAGE_H + 2, ML + CELL_W, yb + 3, stroke=BLUE, sw=0.5)
    f.line(ML, yb, ML + CELL_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(ML + CELL_W / 2, yb + 13, f"cell_w = {CELL_W}", fill=BLUE, fs=10)
    f.text(0, PAGE_H + 40, "gap_header = 0 · h_lyrics_fs = 16 (medium) · H_LYRICS_COL_W = 21 · "
           f"h_syl_fs = {H_SYL_FS} · syllabes en ligne marker sous la rangée",
           fill=BLUE, fs=9.5, anchor="start")
    return f


# --------------------------------------------------------------------------- #
# nomura (A4 portrait, pt) — spec k.NOMURA (champs page_w, marges, pad_*, dan_gap...)
# --------------------------------------------------------------------------- #
def fig_nomura():
    PW, PH = k.NOMURA.page_w, k.NOMURA.page_h               # 595.28 x 841.89 pt
    FMX, FM, FX1, FY1 = k.NOMURA.frame_rect()               # cadre = marges depuis le bord
    FW, FH = FX1 - FMX, FY1 - FM                          # ~559.3 x ~745.9
    GAP = k.NOMURA.dan_gap                                  # 14.5 (= pad_* : padding du cadre)
    ROWS = k.NOMURA.cells_per_dan                                    # 12
    MAX_DANS = k.NOMURA.dans_per_block                     # 7 dans/bloc (1 bloc/page : cap deriv 7)
    CELL_W, CELL_H = ((FW - 8 * GAP) / 14.0), ((FH - 2 * GAP) / ROWS)       # ~31.7 x ~60.7
    MARKER_W = CELL_W                                       # marker = pleine case
    GROUP_W = CELL_W + MARKER_W
    FS = 26.0
    LYR_COL_W = GROUP_W / 3.0                               # 3 colonnes de couplets = 1 dan
    LYR_FS = LYR_COL_W * 0.7
    DRAWN = 4
    sc = 0.62
    ox, oy = 120, 90
    W = int(ox + PW * sc + 90)
    H = int(oy + PH * sc + 70)
    f = Fig("nomura", W, H, sc=sc, ox=ox, oy=oy,
            title="Mise en page Nomura-ryu — constantes (layout « nomura », pt, A4 portrait 21×29,7 cm)")
    f.rect(0, 0, PW, PH, fill=PAGE_FILL, stroke=GRAY, sw=1.5)
    f.rect(FMX, FM, FW, FH, fill="none", stroke=GRAY, sw=1.0)
    grid_y0 = FM + GAP
    grid_h = ROWS * CELL_H
    # dans de droite à gauche : bord droit du cadre − M, puis −group_w − M…
    dan_x = [FMX + FW - GAP - (ci + 1) * GROUP_W - ci * GAP for ci in range(DRAWN)]
    for x in dan_x:
        for r in range(3):
            f.rect(x, grid_y0 + r * CELL_H, CELL_W, CELL_H, stroke=GRAY, sw=0.6)
        f.rect(x + CELL_W, grid_y0, MARKER_W, 3 * CELL_H, fill="#f3f3f3", stroke=GRAY, sw=0.6)
        yb = grid_y0 + 3 * CELL_H
        f.line(x + 3, yb + 14, x + GROUP_W - 3, yb + 2, stroke=GRAY, sw=0.6)
    f.text(dan_x[0] + CELL_W / 2, grid_y0 + CELL_H / 2 + 9, "工", fs=FS, bold=True, scaled=True)
    f.text(dan_x[0] + GROUP_W / 2, grid_y0 + CELL_H / 2 + 6, "あ", fs=int(FS * 0.6), scaled=True)
    f.text(dan_x[-1] + GROUP_W / 2, grid_y0 - 8, f"dans (max {MAX_DANS}/bloc, {ROWS} cases)", fs=9)
    # colonne titre page 1 (droite) + paroles (gauche, 3 colonnes = 1 dan virtuel)
    f.rect(FMX + FW - GAP - GROUP_W - 60, grid_y0, 30, 3 * CELL_H, fill="#f6f6f6", stroke=GRAY, sw=0.6)
    f.text(FMX + FW - GAP - GROUP_W - 45, grid_y0 - 8, "titre p.1", fs=9)
    f.rect(FMX + GAP, grid_y0, GROUP_W, 3 * CELL_H, fill="#f6f6f6", stroke=GRAY, sw=0.6)
    f.text(FMX + GAP + GROUP_W / 2, grid_y0 - 8, "paroles (dernière page)", fs=9)

    y = -70
    for x1, x2, label in [
        (FMX, FMX + GAP, f"dan_gap = {GAP:g}"),
        (dan_x[-1], dan_x[-1] + GROUP_W, f"group_w = cell_w + marker_w = {GROUP_W:.1f}"),
        (dan_x[-1] + GROUP_W, dan_x[-1] + GROUP_W + GAP, f"dan_gap = {GAP:g}"),
    ]:
        f.dim_h(x1, x2, y, label, ext_y=-2)
        y += 22
    f.dim_h(0, PW, y, f"page = {PW:.1f} × {PH:.1f} pt = 21 × 29,7 cm (A4)", ext_y=-2)
    f.dim_h(FMX, FMX + FW, y - 22, f"cadre = {FW:.1f} × {FH:.1f} pt (frame_rect), marges {FMX:.1f} / {FM:.1f} pt", ext_y=-2)

    f.dim_v(0, FM, -16, f"margin_t = {FM:.1f}", ext_x=-2)
    f.dim_v(FM, grid_y0, -32, f"pad_t = dan_gap = {GAP:g}", ext_x=-2)
    f.dim_v(grid_y0, grid_y0 + CELL_H, -16, f"cell_h = {CELL_H:.1f}", ext_x=-2)
    f.dim_v(grid_y0, grid_y0 + ROWS * CELL_H, -48,
            f"rows = {ROWS} × cell_h = {ROWS * CELL_H:.0f} pt", ext_x=-2)
    f.dim_v(0, PH, PW + 16, f"page {PH:.1f} pt", side="right", ext_x=PW + 2)
    yb = PH + 16
    f.line(dan_x[-1], PH + 2, dan_x[-1], yb + 3, stroke=BLUE, sw=0.5)
    f.line(dan_x[-1] + CELL_W, PH + 2, dan_x[-1] + CELL_W, yb + 3, stroke=BLUE, sw=0.5)
    f.line(dan_x[-1], yb, dan_x[-1] + CELL_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(dan_x[-1] + CELL_W / 2, yb + 12, f"cell_w = {CELL_W:.1f}", fill=BLUE, fs=9)
    f.line(dan_x[-1] + CELL_W, yb, dan_x[-1] + GROUP_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(dan_x[-1] + GROUP_W / 2, yb + 12, f"marker_w = cell_w", fill=BLUE, fs=9)
    f.text(0, PH + 34, f"fs notes = {FS:g} pt · LYRICS_COL_W = group_w/3 = {LYR_COL_W:.1f} · "
           f"LYRICS_FS = 0,7·LYRICS_COL_W = {LYR_FS:.1f} · {MAX_DANS} dans max/bloc · "
           f"titre + paroles = 1 dan chacun", fill=BLUE, fs=9, anchor="start")
    return f


# --------------------------------------------------------------------------- #
# chindami (23 x 15 cm paysage, pt) — spec k.CHINDAMI
# --------------------------------------------------------------------------- #
def fig_chindami():
    PW, PH = k.CHINDAMI.page_w, k.CHINDAMI.page_h     # 651.96 x 425.16 pt
    FMX, GT, FX1, GB = k.CHINDAMI.frame_rect()         # cadre virtuel = hanmen (pad 0, non tracé)
    CELL_H = k.CHINDAMI.cell_h                        # ~29.8
    CELL_W, MARKER_W, PILE_W = k.CHINDAMI.cell_w, k.CHINDAMI.marker_w, k.CHINDAMI.pile_w
    ROWS = k.CHINDAMI.cells_per_dan                            # 12
    TITLE_W, TITLE_GAP = k.CHINDAMI.title_w, k.CHINDAMI.title_gap
    FS = k.CHINDAMI.fs                                # 12
    LYR_FS = int(k.CHINDAMI.lyr_fs)                    # 10 (10,8 -> int)
    LYR_COL_W = int(LYR_FS * 1.33)
    LYR_SP = int(LYR_FS * 1.2)
    LYR_SEP = k.CHINDAMI.lyr_gap                      # 12
    MAX_DANS = k.CHINDAMI.dans_per_block              # 16 (plafond absolu : page non extensible)
    DRAWN = 6
    sc = 1.0
    ox, oy = 110, 120
    W, H = 830, 600
    f = Fig("chindami", W, H, sc=sc, ox=ox, oy=oy,
            title="Mise en page Chindami-Kunkunshi — constantes (layout « chindami », pt, 23×15 cm paysage)")
    f.rect(0, 0, PW, PH, fill=PAGE_FILL, stroke=GRAY, sw=1.5)
    f.rect(FMX, GT, FX1 - FMX, GB - GT, fill="none", stroke=GRAY, sw=0.75)   # hanmen (= cadre, pad 0)
    title_offset = TITLE_W + TITLE_GAP
    pile_x = []
    for ci in range(DRAWN):
        x = PW - FMX - title_offset - (ci + 1) * PILE_W
        pile_x.append(x)
        for r in range(4):
            f.rect(x, GT + r * CELL_H, CELL_W, CELL_H, stroke=GRAY, sw=0.6)
        f.rect(x + CELL_W, GT, MARKER_W, 4 * CELL_H, fill="#f3f3f3", stroke=GRAY, sw=0.6)
        yb = GT + 4 * CELL_H
        f.line(x + 3, yb + 12, x + PILE_W - 3, yb + 2, stroke=GRAY, sw=0.6)
    f.text(pile_x[0] + CELL_W / 2, GT + CELL_H / 2 + 4, "工", fs=FS, bold=True, scaled=True)
    f.text(pile_x[0] + CELL_W + MARKER_W / 2, GT + CELL_H / 2 + 3, "あ", fs=int(FS * 0.9), scaled=True)
    f.text(pile_x[-1] + PILE_W / 2, GT - 7, f"piles (max {MAX_DANS}/bloc, {ROWS} cases)", fs=9)
    tx = PW - FMX - TITLE_W
    f.rect(tx, GT, TITLE_W, 4 * CELL_H, fill="#f6f6f6", stroke=GRAY, sw=0.6)
    f.text(tx + TITLE_W / 2, GT - 7, "titre p.1", fs=9)
    f.rect(FMX, GT, LYR_COL_W * 2, 4 * CELL_H, fill="#f6f6f6", stroke=GRAY, sw=0.6)
    f.text(FMX + LYR_COL_W, GT - 7, "paroles", fs=9)

    y = -64
    for x1, x2, label in [
        (FMX, FMX + LYR_SEP, f"lyr_gap = {LYR_SEP:g}"),
        (pile_x[-1], pile_x[-1] + PILE_W, f"pile_w = cell_w + marker_w = {PILE_W:.1f}"),
        (pile_x[0] + PILE_W, pile_x[0] + PILE_W + TITLE_GAP, f"title_gap = {TITLE_GAP:g}"),
        (tx, tx + TITLE_W, f"title_w = {TITLE_W:.1f}"),
        (PW - FMX, PW, f"marge = {FMX:.1f}"),
    ]:
        f.dim_h(x1, x2, y, label, ext_y=-2)
        y += 16
    f.dim_h(0, PW, y, f"page = {PW:.1f} × {PH:.1f} pt = 23 × 15 cm", ext_y=-2)

    f.dim_v(0, GT, -16, f"margin_t = {GT:.1f}", ext_x=-2)
    f.dim_v(GT, GT + CELL_H, -32, f"cell_h = {CELL_H:.1f}", ext_x=-2)
    f.dim_v(GT, GB, -48, f"{ROWS} × cell_h = {GB - GT:.0f} pt (hanmen haut→bas)", ext_x=-2)
    f.dim_v(0, PH, PW + 16, f"page {PH:.1f} pt", side="right", ext_x=PW + 2)
    yb = PH + 16
    for x in (pile_x[-1], pile_x[-1] + CELL_W, pile_x[-1] + PILE_W):
        f.line(x, PH + 2, x, yb + 3, stroke=BLUE, sw=0.5)
    f.line(pile_x[-1], yb, pile_x[-1] + CELL_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(pile_x[-1] + CELL_W / 2, yb + 12, f"cell_w = {CELL_W:.1f}", fill=BLUE, fs=9)
    f.line(pile_x[-1] + CELL_W, yb, pile_x[-1] + PILE_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(pile_x[-1] + PILE_W / 2, yb + 12, f"marker_w = {MARKER_W:.1f}", fill=BLUE, fs=9)
    f.text(0, PH + 32, f"spec.fs = {FS:g} · lyr_fs = {LYR_FS} (spec.lyr_fs = {k.CHINDAMI.lyr_fs:g} pt) · "
           f"lyr_sp = {LYR_SP} · lyr_col_w = {LYR_COL_W} · max_lyr_u = hauteur grille en unités · "
           f"repli des paroles avec kinsoku (@kinsoku)", fill=BLUE, fs=9, anchor="start")
    return f


# --------------------------------------------------------------------------- #
# tuto (bloc WxH fixe en px, @tuto_block 1280x720 défaut)
# --------------------------------------------------------------------------- #
def fig_tuto():
    W0, H0 = (int(k.TUTO.page_w / k.PX), int(k.TUTO.page_h / k.PX))          # 1280 x 720
    COLS = k.TUTO.cells_per_dan             # 8
    DANS = k.TUTO.dans_per_block             # 7
    ML = MT = MB = 16
    CELL_W = (W0 - ML - 16) / (COLS + 0.25)
    MR = 16 + CELL_W / 4
    CELL_H = (H0 - MT - MB) / DANS
    FS = max(8, int(CELL_H * 0.38))
    SYL_FS = int(FS * 0.6)
    sc = 0.34
    ox, oy = 110, 130
    W, H = 640, 420
    f = Fig("tuto", W, H, sc=sc, ox=ox, oy=oy,
            title="Mise en page tutoriel vidéo — constantes (layout « tuto », px, bloc @tuto_block)")
    f.rect(0, 0, W0, H0, fill=PAGE_FILL, stroke=GRAY, sw=2)
    f.text(W0 - 16, 14, "titre de section", fs=12, anchor="end", fill="#999", mono=False)
    ROWS_DRAWN, COLS_DRAWN = 2, 8
    for r in range(ROWS_DRAWN):
        y = MT + (10 if r == 0 else 0) + r * CELL_H
        for c in range(COLS_DRAWN):
            f.rect(ML + c * CELL_W, y, CELL_W, CELL_H, stroke=GRAY, sw=0.75)
    y0 = MT + 10
    f.text(ML + CELL_W / 2, y0 + CELL_H / 2 + FS * 0.35, "工", fs=FS, bold=True, scaled=True)
    f.text(ML + CELL_W / 2, y0 + CELL_H - 6, "あ", fs=SYL_FS, scaled=True)
    f.text(ML + 4 * CELL_W, y0 - 6, f"{COLS} cases/dan · {DANS} dans/bloc (défaut)", fs=10)
    yb = MT + 10 + ROWS_DRAWN * CELL_H
    f.line(ML, yb + 16, ML + COLS * CELL_W, yb + 2, stroke=GRAY, sw=0.75)
    f.text(ML + COLS * CELL_W / 2, yb + 24, "⋮", fs=12, scaled=True)

    y = -70
    for x1, x2, label in [
        (0, ML, f"ml = {ML}"),
        (ML, ML + COLS * CELL_W, f"cols·cell_w (cols = {COLS})"),
        (ML + COLS * CELL_W, W0, f"mr = 16 + cell_w/4 = {MR:.1f}"),
    ]:
        f.dim_h(x1, x2, y, label, ext_y=-2)
        y += 18
    f.dim_h(0, W0, y, f"@tuto_block = {W0} × {H0} px (défaut 1280×720)", ext_y=-2)

    f.dim_v(0, MT, -16, f"mt = {MT}", ext_x=-2)
    f.dim_v(MT, MT + CELL_H, -32, f"cell_h = {CELL_H:.1f}", ext_x=-2)
    f.dim_v(MT, H0 - MB, -48, f"{DANS} dans × cell_h (mb = {MB})", ext_x=-2)
    f.dim_v(0, H0, W0 + 16, f"H = {H0} px", side="right", ext_x=W0 + 2)
    yb2 = H0 + 16
    f.line(ML, H0 + 2, ML, yb2 + 3, stroke=BLUE, sw=0.5)
    f.line(ML + CELL_W, H0 + 2, ML + CELL_W, yb2 + 3, stroke=BLUE, sw=0.5)
    f.line(ML, yb2, ML + CELL_W, yb2, stroke=BLUE, sw=1.0, marker="arr")
    f.text(ML + CELL_W / 2, yb2 + 12, f"cell_w = {CELL_W:.1f}", fill=BLUE, fs=9)
    f.text(0, H0 + 34, f"cell_w = (W−ml−16)/(cols+0,25) = {CELL_W:.1f} · cell_h = (H−mt−mb)/dans = {CELL_H:.1f} · "
           f"fs = max(8, 0,38·cell_h) = {FS} · syl_fs = 0,6·fs = {SYL_FS} (syllabes en bas de case, PAS de bande marker)",
           fill=BLUE, fs=9, anchor="start")
    return f


# --------------------------------------------------------------------------- #
# mega (A3 paysage 42 x 29,7 cm, pt) — spec k.MEGA
# --------------------------------------------------------------------------- #
def fig_mega():
    PW, PH = k.MEGA.page_w, k.MEGA.page_h      # 1190.55 x 841.89
    MARGIN, BLOCKS, BLOCK_GAP = k.MEGA.margin_l, k.MEGA.blocks, k.MEGA.block_gap
    ROWS = k.MEGA.cells_per_dan                          # 12
    DANS_PER_BLOCK = k.MEGA.dans_per_block      # 32
    CELL_H = (PH - 2 * MARGIN - (BLOCKS - 1) * BLOCK_GAP) / (BLOCKS * ROWS)
    FS = max(8, int(CELL_H * 0.38))
    TITLE_W, TITLE_GAP = 36, 10
    TITLE_OFFSET = TITLE_W + TITLE_GAP
    LYRICS_OFFSET = 0                           # page 1 pleine largeur (paroles en pages dédiées)
    AVAIL_W = PW - 2 * MARGIN - TITLE_OFFSET - LYRICS_OFFSET
    CELL_W = AVAIL_W / (DANS_PER_BLOCK * 1.5)
    MARKER_W = CELL_W / 2
    GROUP_W = CELL_W + MARKER_W
    DRAWN = 5
    sc = 0.30
    ox, oy = 100, 120
    W, H = 620, 440
    f = Fig("mega", W, H, sc=sc, ox=ox, oy=oy,
            title="Mise en page mega — constantes (layout « mega », pt, A3 paysage 42×29,7 cm)")
    f.rect(0, 0, PW, PH, fill=PAGE_FILL, stroke=GRAY, sw=2)
    blk_h = ROWS * CELL_H
    for b in range(BLOCKS):
        by = MARGIN + b * (blk_h + BLOCK_GAP)
        for ci in range(DRAWN):
            x = PW - MARGIN - TITLE_OFFSET - (ci + 1) * GROUP_W
            for r in range(3):
                f.rect(x, by + r * CELL_H, CELL_W, CELL_H, stroke=GRAY, sw=0.6)
            f.rect(x + CELL_W, by, MARKER_W, 3 * CELL_H, fill="#f3f3f3", stroke=GRAY, sw=0.6)
            yb = by + 3 * CELL_H
            f.line(x + 2, yb + 10, x + GROUP_W - 2, yb + 2, stroke=GRAY, sw=0.6)
        f.text(PW - MARGIN - TITLE_OFFSET - DRAWN * GROUP_W / 2, by - 7,
               f"bloc {b + 1}/{BLOCKS} : jusqu'à {DANS_PER_BLOCK} dans × {ROWS} cases", fs=10)
    f.text(PW - MARGIN - CELL_W / 2, MARGIN + CELL_H / 2 + 4, "工", fs=FS, bold=True, scaled=True)
    tx = PW - MARGIN - TITLE_W
    f.rect(tx, MARGIN, TITLE_W, 3 * CELL_H, fill="#f6f6f6", stroke=GRAY, sw=0.6)
    f.text(tx + TITLE_W / 2, MARGIN - 7, "titre vertical (chaque page)", fs=10)

    y = -64
    for x1, x2, label in [
        (0, MARGIN, f"margin_l = {MARGIN:g}"),
        (PW - MARGIN - TITLE_OFFSET - DRAWN * GROUP_W, PW - MARGIN - TITLE_OFFSET,
         f"{DRAWN}×group_w = 1,5·cell_w = {GROUP_W:.1f}"),
        (PW - MARGIN - TITLE_OFFSET, PW - MARGIN - TITLE_GAP, f"title_gap = {TITLE_GAP:g}"),
        (tx, tx + TITLE_W, f"title_w = {TITLE_W:g}"),
    ]:
        f.dim_h(x1, x2, y, label, ext_y=-2)
        y += 18
    f.dim_h(0, PW, y, f"page A3 = {PW:.1f} × {PH:.1f} pt = 42 × 29,7 cm", ext_y=-2)

    f.dim_v(0, MARGIN, -16, f"margin_l = {MARGIN:g}", ext_x=-2)
    f.dim_v(MARGIN, MARGIN + CELL_H, -32, f"cell_h = {CELL_H:.1f}", ext_x=-2)
    f.dim_v(MARGIN, MARGIN + blk_h, -48, f"bloc = {ROWS}×cell_h = {blk_h:.0f} pt", ext_x=-2)
    f.dim_v(MARGIN + blk_h, MARGIN + blk_h + BLOCK_GAP, -16,
            f"block_gap = {BLOCK_GAP:g}", ext_x=-2)
    f.dim_v(0, PH, PW + 16, f"page {PH:.1f} pt", side="right", ext_x=PW + 2)
    yb = PH + 16
    x0 = PW - MARGIN - TITLE_OFFSET - GROUP_W
    for x in (x0, x0 + CELL_W, x0 + GROUP_W):
        f.line(x, PH + 2, x, yb + 3, stroke=BLUE, sw=0.5)
    f.line(x0, yb, x0 + CELL_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(x0 + CELL_W / 2, yb + 12, f"cell_w = {CELL_W:.1f}", fill=BLUE, fs=9)
    f.line(x0 + CELL_W, yb, x0 + GROUP_W, yb, stroke=BLUE, sw=1.0, marker="arr")
    f.text(x0 + GROUP_W / 2, yb + 12, f"marker_w = cell_w/2 = {MARKER_W:.1f}", fill=BLUE, fs=9)
    f.text(0, PH + 32, f"blocks = {BLOCKS} · dans_per_block = {DANS_PER_BLOCK} → "
           f"{BLOCKS * DANS_PER_BLOCK} dans/page (blocs x dans_per_block) · fs = {FS} · paroles en pages A3 dédiées "
           f"(inline si ≤ {k.MEGA.lyr_inline_max_ratio:.0%} de la largeur utile) · cell_w = "
           f"(page−2·marge−title_offset)/({DANS_PER_BLOCK}×1,5)", fill=BLUE, fs=9, anchor="start")
    return f


FIGS = [fig_vertical, fig_horizontal, fig_nomura, fig_chindami, fig_tuto, fig_mega]

if __name__ == "__main__":
    for fn in FIGS:
        f = fn()
        path, size = f.save()
        print(f"OK: {os.path.relpath(path, ROOT)}  ({size} octets, viewBox {f.W}x{f.H}, XML valide)")
