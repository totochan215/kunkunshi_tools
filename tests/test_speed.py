# -*- coding: utf-8 -*-
"""Tests du rendu de @speed en \u2669=120 (horizontal, fs 12, sans espace), tous layouts.

R\u00e8gle (2026-11-22) : @speed est rendu \u2669=valeur, texte horizontal NON pivot\u00e9,
fs 12, sans espace apr\u00e8s \u2669 :
- layouts horizontaux sauf tuto : dans le flux des m\u00e9tadonn\u00e9es, \u00e0 droite du titre,
  avant @choshi ;
- layouts verticaux (vertical, chindami, nomura, mega) : sous le titre, centr\u00e9 sur
  la colonne titre, au-dessus de @choshi (mega : r\u00e9p\u00e9t\u00e9 sur chaque page) ;
- tuto : page de titre, sous le titre, centr\u00e9, au-dessus de @choshi, m\u00eame fs
  (px) que la ligne @choshi (max(10, int(H*0.035)) = 25 px \u00e0 H=720).

Usage :
    python3 tests/test_speed.py
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

GO = "\u5408"          # 合
CHOSHI = "\u672c\u8abf\u5b50"  # 本調子
SRC = ("@title \u30c6\u30b9\u30c8\n@choshi " + CHOSHI + "\n@speed 120\n"
       "::tab\n" + " ".join([GO] * 12) + "\n::\n")
LAYOUTS = ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega")

TEXT_RE = re.compile(r'<text\b[^>]*>([^<]*)</text>')


def render(layout, src=SRC):
    with contextlib.redirect_stderr(io.StringIO()):
        song = k.parse_kkml(src)
        return k.render_svg(song, layout=layout)


def speed_els(svg):
    """El\u00e9ments <text> contenant \u2669=... : [(attrs, texte, y, x)] — y/x lus sur
    l'attribut (x peut \u00eatre une liste pour les blocs verticaux)."""
    out = []
    for m in re.finditer(r'<text\b([^>]*)>([^<]*)</text>', svg):
        if "\u2669=" in m.group(2):
            attrs = m.group(1)
            assert "transform" not in attrs, "tempo pivot\u00e9 ! " + attrs
            y = float(re.search(r'y="([\d.]+)', attrs).group(1))
            xs = [float(v) for v in re.search(r'x="([^"]+)"', attrs).group(1).split()]
            fs = float(re.search(r'font-size="([\d.]+)"', attrs).group(1))
            out.append((attrs, m.group(2), y, xs, fs))
    return out


def choshi_first_y(svg):
    ys = []
    for m in re.finditer(r'<text\b([^>]*)>([^<]*)</text>', svg):
        if CHOSHI in m.group(2):
            ys.append(float(re.search(r'y="([^"]+)"', m.group(1)).group(1).split()[0]))
    for m in re.finditer(r'<text\b([^>]*)>([^<]*)</text>', svg):
        for ch in CHOSHI:
            if m.group(2) == ch:
                ys.append(float(re.search(r'y="([\d.]+)', m.group(1)).group(1)))
    return min(ys)


# 1. parsing : forme s\u00e9par\u00e9e et forme coll\u00e9e @speed120
with contextlib.redirect_stderr(io.StringIO()):
    assert k.parse_kkml("@speed 120\n::tab\n" + GO + "\n::\n").meta["speed"] == "120"
    assert k.parse_kkml("@speed120\n::tab\n" + GO + "\n::\n").meta["speed"] == "120"
print("OK parsing @speed 120 et @speed120")

# 2. helper _speed_text
song = k.parse_kkml(SRC)
assert k._speed_text(song) == "\u2669=120"
assert k._speed_text(k.parse_kkml("::tab\n" + GO + "\n::\n")) == ""
print("OK _speed_text : \u2669=120, vide sans @speed")

# 3. les 6 layouts rendent \u2669=120, horizontal (pas de transform), fs 12 (tuto : 25 px)
svgs = {}
for layout in LAYOUTS:
    svgs[layout] = render(layout)
    n = sum(len(speed_els(p)) for p in svgs[layout])
    assert n >= 1, "pas de \u2669= dans " + layout
    for page in svgs[layout]:
        for attrs, txt, y, xs, fs in speed_els(page):
            assert txt == "\u2669=120", txt
            if layout == "tuto":
                assert fs == 25, (layout, fs)   # max(10, int(720*0.035))
            else:
                assert fs == 12, (layout, fs)
print("OK \u2669=120 rendu dans les 6 layouts, non pivot\u00e9, fs 12 (25 px en tuto)")

# 4. horizontal : \u2669=120 avant @choshi dans le flux de la ligne titre
sh = svgs["horizontal"][0]
assert sh.index("\u2669=120") < sh.index(CHOSHI), "speed pas avant @choshi en horizontal"
print("OK horizontal : \u2669=120 \u00e0 droite du titre, avant @choshi")

# 5. vertical : sous le titre, centr\u00e9 sur la colonne titre, au-dessus de @choshi
sv = svgs["vertical"][0]
(_a, _t, sy, sxs, _fs) = speed_els(sv)[0]
cx_speed = sxs[0] + k._h_text_w("\u2669=120", 12) / 2
m = re.search(r'<text x="([\d. ]+)" y="([\d. ]+)"[^>]*font-size="26"[^>]*>\u30c6\u30b9\u30c8</text>', sv)
assert m, "titre vertical non trouv\u00e9"
title_x = float(m.group(1).split()[0])
assert abs(cx_speed - title_x) < 0.01, (cx_speed, title_x)   # centr\u00e9 sur le titre
assert sy < choshi_first_y(sv), "speed pas au-dessus de @choshi en vertical"
print("OK vertical : \u2669=120 centr\u00e9 sur le titre (x=%.1f), au-dessus de @choshi (y=%.0f < %.0f)"
      % (cx_speed, sy, choshi_first_y(sv)))

# 6. chindami / nomura / mega : sous le titre, au-dessus de @choshi
for layout in ("chindami", "nomura", "mega"):
    page1 = svgs[layout][0]
    (_a, _t, sy, _xs, _fs) = speed_els(page1)[0]
    assert sy < choshi_first_y(page1), (layout, sy)
    if layout == "mega":
        # r\u00e9p\u00e9t\u00e9 sur chaque page comme la colonne titre
        for page in svgs[layout]:
            assert len(speed_els(page)) == 1, "mega : \u2669= attendu sur chaque page"
print("OK chindami/nomura/mega : \u2669=120 au-dessus de @choshi (mega : chaque page)")

# 7. tuto : page de titre, sous le titre, au-dessus de @choshi, fs 25 px
tuto1 = svgs["tuto"][0]
(_a, _t, sy, sxs, fs) = speed_els(tuto1)[0]
assert len(svgs["tuto"]) >= 2 and all(not speed_els(p) for p in svgs["tuto"][1:]), \
    "tuto : \u2669= attendu uniquement sur la page de titre"
assert sy < choshi_first_y(tuto1), "tuto : speed pas au-dessus de @choshi"
assert sxs[0] == 640 and 'text-anchor="middle"' in _a   # centr\u00e9 (W=1280)
print("OK tuto : page de titre, centr\u00e9, fs 25 px, au-dessus de @choshi")

# 8. sans @speed : aucun \u2669= dans aucun layout
for layout in LAYOUTS:
    for page in render(layout, "@title t\n@choshi " + CHOSHI + "\n::tab\n" + GO + "\n::\n"):
        assert not speed_els(page), "tempo rendu sans @speed en " + layout
print("OK aucun \u2669= sans @speed")

# 9. cleaner : @speed conserv\u00e9 tel quel, idempotent
out = c.clean(SRC)
assert "@speed 120" in out.splitlines(), out
assert c.clean(out) == out
print("OK cleaner conserve @speed (idempotent)")

# 10. pas de WARNING au rendu d'un morceau avec @speed
err = io.StringIO()
with contextlib.redirect_stderr(err):
    k.parse_kkml(SRC)
    k.render_svg(k.parse_kkml(SRC), layout="vertical")
    k.render_svg(k.parse_kkml(SRC), layout="mega")
assert "WARNING" not in err.getvalue(), err.getvalue()
print("OK aucun WARNING avec @speed")

print("OK tests @speed -> \u2669=120 (6 layouts)")
