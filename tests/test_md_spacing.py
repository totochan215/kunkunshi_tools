# -*- coding: utf-8 -*-
"""Tests de la constante md_spacing (espacement homogène titre -> métadonnées).

Règle (2026-11-22) : chaque layout a une constante `md_spacing` (LayoutSpec, en pt,
convertie via spec.u()) qui fixe l'avance entre le titre et la 1re métadonnée ET
entre chaque bloc de métadonnées — homogène partout. Exception : @choshi quand il
est ancré en bas de la colonne titre (chindami/nomura/mega), qui garde son ancrage.
Valeurs : vertical 15 px, horizontal 20 px, nomura 8 pt, chindami 6 pt,
tuto 43,2 px (H*0,06 à H=720), mega 15 pt.

Usage :
    python3 tests/test_md_spacing.py
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

SRC = ("@title t\n@author A\n@speed 120\n@choshi \u672c\u8abf\u5b50\n"
       "::tab\n\u5408 \u5408\n::\n")
PX = k.PX


def render(layout, spec=None):
    orig = k.LAYOUTS[layout]
    if spec is not None:
        k.LAYOUTS[layout] = spec
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            return k.render_svg(k.parse_kkml(SRC), layout=layout)
    finally:
        k.LAYOUTS[layout] = orig


def els(svg):
    return re.findall(r'<text\b([^>]*)>([^<]*)</text>', svg)


def xy(attrs):
    x = [float(v) for v in re.search(r'x="([^"]+)"', attrs).group(1).split()]
    y = [float(v) for v in re.search(r'y="([^"]+)"', attrs).group(1).split()]
    fs = float(re.search(r'font-size="([\d.]+)"', attrs).group(1))
    return x, y, fs


def find(svg, pred):
    return [(attrs, txt) for attrs, txt in els(svg) if pred(txt, attrs)]


# 1. les 6 modèles ont une constante md_spacing définie
for name, spec in k.LAYOUTS.items():
    assert spec.md_spacing > 0, name
    print("OK %-10s md_spacing = %g pt -> %g %s" % (name, spec.md_spacing, spec.u(spec.md_spacing), spec.unit))

# 2. horizontal : gaps titre->méta et méta->méta == md_spacing (20 px), homogène
svgs = render("horizontal")
md = k.HORIZONTAL.u(k.HORIZONTAL.md_spacing)
prev_end = prev_name = None
gaps = []
for attrs, txt in els(svgs[0]):
    x, y, fs = xy(attrs)
    if fs == 26 and txt == "t":
        prev_end, prev_name = x[0] + k._h_text_w("t", 26), "title"
    elif txt == "A" or "♩" in txt or "本調子" in txt:
        if prev_end is not None:
            gaps.append((prev_name, txt, x[0] - prev_end))
        prev_end = x[0] + k._h_text_w(k._link_free(txt), fs)
        prev_name = txt
assert len(gaps) == 3, gaps
for a, b, g in gaps:
    assert abs(g - md) < 0.01, (a, b, g, md)
print("OK horizontal : 3 gaps = %.1f px (homogène)" % md)

# 2b. horizontal avec md_spacing surchargé : les gaps suivent exactement
spec2 = dataclasses.replace(k.HORIZONTAL, md_spacing=40 * PX)
svgs2 = render("horizontal", spec2)
prev_end = prev_name = None
for attrs, txt in els(svgs2[0]):
    x, y, fs = xy(attrs)
    if fs == 26 and txt == "t":
        prev_end, prev_name = x[0] + k._h_text_w("t", 26), "title"
    elif txt == "A" or "♩" in txt or "本調子" in txt:
        if prev_end is not None:
            assert abs((x[0] - prev_end) - 40) < 0.01, (prev_name, txt, x[0] - prev_end)
        prev_end = x[0] + k._h_text_w(k._link_free(txt), fs)
        prev_name = txt
print("OK horizontal : md_spacing=40*PX -> gaps = 40 px exactement")

# 3. vertical : lead de chaque bloc méta = md_spacing (delta test : +10 px décale
#    chaque 1re baseline de méta de +10, le titre ne bouge pas)
def vert_ys(svg):
    out = {}
    for attrs, txt in els(svg):
        x, y, fs = xy(attrs)
        if fs == 26 and txt == "t":
            out["title"] = y[0]
        elif txt == "A":
            out["author"] = y[0]
        elif "♩" in txt:
            out["speed"] = y[0]
        elif "本調子" in txt:
            out["choshi"] = y[0]
    return out

v1 = vert_ys(render("vertical")[0])
v2 = vert_ys(render("vertical", dataclasses.replace(k.VERTICAL, md_spacing=25 * PX))[0])
assert v1["title"] == v2["title"], (v1, v2)
# chaque bloc méta a son propre lead = md_spacing : le delta est cumulatif
# (author +10, tempo +20, choshi +30), le titre ne bouge pas (son lead propre = 20)
for i, key in enumerate(("author", "speed", "choshi"), 1):
    assert abs((v2[key] - v1[key]) - 10 * i) < 0.01, (key, v1[key], v2[key])
print("OK vertical : md_spacing 15->25 px, leads cumulatifs +10/+20/+30, titre fixe")

# 4. tuto : tous les gaps de la page de titre = md_spacing (43,2 px)
mdt = k.TUTO.u(k.TUTO.md_spacing)
prev = None
for attrs, txt in els(render("tuto")[0]):
    x, y, fs = xy(attrs)
    if txt == "t" or "♩" in txt or "本調子" in txt or txt == "A":
        if prev is not None:
            assert abs((y[0] - prev[1]) - mdt) < 0.01, (prev[0], txt, y[0] - prev[1], mdt)
        prev = (txt, y[0])
print("OK tuto : gaps page de titre = %.1f px (homogène)" % mdt)

# 5. mega / chindami / nomura : le gap titre -> tempo suit md_spacing (delta)
def speed_y(svg):
    (attrs, txt), = find(svg, lambda t, a: "♩" in t)
    return xy(attrs)[1][0]

for name in ("mega", "chindami", "nomura"):
    spec = k.LAYOUTS[name]
    base = k.LAYOUTS[name]
    y1 = speed_y(render(name)[0])
    y2 = speed_y(render(name, dataclasses.replace(base, md_spacing=base.md_spacing + 10))[0])
    assert abs((y2 - y1) - spec.u(10)) < 0.01, (name, y1, y2)
    print("OK %-8s : +10 pt sur md_spacing décale ♩= de +%g" % (name, spec.u(10)))

print("OK tests md_spacing (homogène titre<->métas, 6 layouts)")
