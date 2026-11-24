# -*- coding: utf-8 -*-
"""Tests de la conversion Portama -> KKML de テスト節 (« test bushi ») et du
rendu de la correction manuelle de l'utilisateur (tests/fixtures/synthetic/テスト節.kkml).

Couvre :
- PUA composites (E003-E008, E014-E018, E025-E028) -> positions condensées
  (下老, ロ上, イ合, 下尺, イ五, ... selon docs/portama-format.md) ;
- acc sharp/flat sur TOUTE note -> suffixes ♯/♭ (cas spécial 尺♯ préservé,
  option @shaku_sharp) ;
- vocalRepStart/End -> (: / :) ; repeatStart/End -> |: / :| ;
- paire « à cheval seule » (main vide) -> -/B ; cellule terminale impaire
  d'un dan conservée (plus perdue) ;
- vocalPosMarkers (cellule isSmall, mid) -> section ::vocal avec .( / .) ;
- variantes de saisie acceptées par kkml2svg : 口+kanji -> ロ+kanji,
  ⚪︎ (U+26AA + U+FE0E) -> repos ◯, `#` -> ♯, `b` -> ♭ ;
- la correction manuelle (révisée par l'utilisateur) rend sans avertissement
  (vertical/horizontal/mega) et correspond au convertisseur à l'identique
  après normalisation (variantes 口→ロ, ○/⚪︎→◯).

Usage :
    python3 tests/test_testbushi.py
"""
import contextlib
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k
import portama2kkml as p2k

SHARP = chr(0x266F)      # ♯
FLAT = chr(0x266D)       # ♭
REST = chr(0x25EF)       # ◯ silence (token canonique)
REST_WHITE = chr(0x26AA) + chr(0xFE0E)  # ⚪︎ variante saisie (avec sélecteur)
KOU = chr(0x53E3)        # 口 radical (variante de ロ)
RO = chr(0x30ED)         # ロ katakana (canonique)
SHI = chr(0x5C3A)        # 尺
SHI_SHARP = SHI + SHARP  # 尺♯ (cas spécial @shaku_sharp)
Y1, Y2, Y4 = chr(0x3280), chr(0x3281), chr(0x3283)

JSON_PATH = ROOT / "samples" / "portama-json" / "テスト節.json"
KKML_PATH = ROOT / "tests" / "fixtures" / "synthetic" / "テスト節.kkml"


def render(kkml, layout="vertical"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svgs = k.render_svg(k.parse_kkml(kkml), layout=layout)
    return svgs, err.getvalue()


def tab_lines(song):
    return [ln for b in song.blocks if b.kind == "tab" for ln in b.lines]


def vocal_lines(song):
    return [ln for b in song.blocks if b.kind == "vocal" for ln in b.lines]


# --- 1. Conversion du JSON Portama : tokens attendus, aucun `?` -------------
data = json.load(open(JSON_PATH, encoding="utf-8"))
with contextlib.redirect_stderr(io.StringIO()):  # les _info vont sur stderr
    kkml = p2k.convert_portama_to_kkml(data)

tab = tab_lines(k.parse_kkml(kkml))
assert len(tab) == 5, tab
expected = [
    f"合 合^ 合' 合\" 合{SHARP} 合{FLAT} |:合 合:| (:合 合:) 合 合".split(),
    f"-/合 -/合^ -/合' -/合\" -/合{SHARP} -/合{FLAT} -/合 -/合 - 合{Y1} 合{Y2} 合{Y4}".split(),
    "合 乙 老 下老 ロ上 ロ中 ロ尺 イ合 イ乙 四 上 中".split(),
    "尺 下尺 ロ五 イ老 イ四 イ上 工 五 六 七 八 九".split(),
    f"イ工 イ五 {REST}".split(),  # E030 = ○ (U+25CB) -> normalisé en ◯ au parsing
]
assert tab == expected, f"\nobtenu : {tab}\nattendu: {expected}"
assert "?" not in kkml
print("OK conversion テスト節.json : 5 dans, tokens exacts, aucun `?`")

# métadonnées de compatibilité présentes
for m in ("@musicno 0", "@chogen 7", "@speed 120", "@rythm 0", "@rythm_mode 0"):
    assert m in kkml, m
print("OK métadonnées @musicno/@chogen/@speed/@rythm/@rythm_mode émises")

# --- 2. Section ::vocal : marqueurs mid des cellules à cheval --------------
voc = vocal_lines(k.parse_kkml(kkml))
assert len(voc) == 5, voc
assert voc[0] == ["-"] * 10 + ["(", ")"], voc[0]
assert voc[1] == [")"] + ["-"] * 5 + [".(", ".)"] + ["-"] * 4, voc[1]
assert voc[4] == ["-"] * 3
assert "::vocal" in kkml
print("OK ::vocal : ( ) en ligne 1 pos. 11-12 et ) en ligne 2 pos. 1 (cellules principales), "
      ".( .) en ligne 2 pos. 7-8 (cellules à cheval mid)")

# --- 3. La sortie du convertisseur rend sans avertissement ------------------
for layout in ("vertical", "horizontal", "mega"):
    _, e = render(kkml, layout)
    assert "WARNING" not in e, (layout, e)
print("OK sortie convertisseur sans avertissement (vertical/horizontal/mega)")

# --- 4. La correction manuelle de l'utilisateur rend sans avertissement -----
user_kkml = open(KKML_PATH, encoding="utf-8").read()
for layout in ("vertical", "horizontal", "mega"):
    _, e = render(user_kkml, layout)
    assert "WARNING" not in e, (layout, e)
print("OK tests/fixtures/synthetic/テスト節.kkml (correction manuelle) sans avertissement")

# --- 5. Correction manuelle == convertisseur après normalisation ------------
u_tab = tab_lines(k.parse_kkml(user_kkml))
c_tab = tab_lines(k.parse_kkml(kkml))
assert u_tab == c_tab, (u_tab, c_tab)
assert vocal_lines(k.parse_kkml(user_kkml)) == vocal_lines(k.parse_kkml(kkml))
print("OK correction manuelle = convertisseur à l'identique après normalisation")

# --- 6. Variantes de saisie normalisées au parsing ---------------------------
song = k.parse_kkml(f"::tab\n合# 合b {KOU}上 　{REST_WHITE} {SHI_SHARP}\n::\n")
toks = tab_lines(song)[0]
assert toks == [f"合{SHARP}", f"合{FLAT}", f"{RO}上", REST, SHI_SHARP], toks
print("OK variantes : # -> ♯, b -> ♭, 口上 -> ロ上, ⚪︎ -> ◯, 尺♯ intact")

# --- 7. 尺♯ décomposé au rendu comme toute note altérée (2026-11-23) ------------
# @shaku_sharp off (défaut) : le ♯ est masqué, rendu en 尺 simple
out = []
k.render_cell(out, SHI_SHARP, 42, 29, 22,
              opts={"shaku_sharp": False, "shaku_circled": False})
svg = "".join(out)
assert SHARP not in svg and SHI in svg, svg
# @shaku_sharp on : la note 尺 garde EXACTEMENT la position/taille de 尺 seul, le ♯
# est une marque séparée (haut-droite), identique à celle de 合♯ — plus de tspan inline
out = []
k.render_cell(out, SHI_SHARP, 42, 29, 22,
              opts={"shaku_sharp": True, "shaku_circled": False})
svg_sharp = "".join(out)
assert svg_sharp.count("<text") == 2 and SHI in svg_sharp and SHARP in svg_sharp, svg_sharp
assert "tspan" not in svg_sharp, svg_sharp
out = []
k.render_cell(out, SHI, 42, 29, 22, opts={"shaku_sharp": True, "shaku_circled": False})
svg_plain = "".join(out)
import re as _re
note = lambda svg: _re.search(r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*font-size="(\d+)"[^>]*>尺</text>', svg).groups()
assert note(svg_sharp) == note(svg_plain), (note(svg_sharp), note(svg_plain))
mark = lambda svg: _re.search(r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*font-size="(\d+)"[^>]*>♯</text>', svg).groups()
out = []
k.render_cell(out, f"合{SHARP}", 42, 29, 22, opts={"shaku_sharp": False})
svg_gou = "".join(out)
assert mark(svg_sharp) == mark(svg_gou), (mark(svg_sharp), mark(svg_gou))
# cerclage : un shaku altéré n'est JAMAIS cerclé ; 尺 simple cerclé centré en (cx, cy)
out = []
k.render_cell(out, SHI_SHARP, 42, 29, 22,
              opts={"shaku_sharp": True, "shaku_circled": True})
assert "<circle" not in "".join(out), "".join(out)
out = []
k.render_cell(out, SHI, 42, 29, 22, opts={"shaku_sharp": True, "shaku_circled": True})
svg = "".join(out)
assert '<circle cx="42" cy="29"' in svg, svg  # centrage unifié (cx, cy), plus cy+2
# croches : cercle sur le shaku principal / à cheval (codepoint corrigé 尖->尺)
for tok in (f"尺/合", f"合/尺"):
    out = []
    k.render_cell(out, tok, 42, 29, 22, opts={"shaku_circled": True, "shaku_sharp": True})
    assert "<circle" in "".join(out), tok
out = []
k.render_cell(out, f"合/尺♯", 42, 29, 22, opts={"shaku_circled": True, "shaku_sharp": True})
assert "<circle" not in "".join(out), "".join(out)  # shaku à cheval altéré : pas de cercle
print("OK 尺♯ : décomposé au rendu (note identique à 尺 seul, ♯ = marque standard), masqué avec @shaku_sharp off, jamais cerclé si altéré ; cercles croches OK")

# --- 8. Unités : paire à cheval seule, cellule terminale impaire -------------
dan = [{"note": ""}, {"note": chr(0xE000), "isSmall": True},
        {"note": chr(0xE030)}]  # 3 cellules -> 2 paires, la dernière seule
toks = p2k.dan_to_tokens(dan)
assert toks == [f"-/合", chr(0x25CB)], toks
print("OK -/B pour paire à cheval seule ; cellule terminale impaire conservée")

dan = [{"note": chr(0xE000), "vocalRepStart": True},
       {}, {"note": chr(0xE000), "vocalRepEnd": True}, {}]
toks = p2k.dan_to_tokens(dan)
assert toks == [f"(:合", f"合:)"], toks
print("OK vocalRepStart/End -> (:合 / 合:)")

v = p2k.dan_to_vocal([{"note": chr(0xE000), "vocalPosMarkers": {"mid": "vocalStart"}},
                      {},
                      {"note": ""}, {"note": chr(0xE000), "isSmall": True,
                                     "vocalPosMarkers": {"mid": "vocalEnd"}}])
assert v == ["(", ".)"], v
print("OK dan_to_vocal : cellule principale -> ( / ), cellule à cheval mid -> .( / .)")

# combinaison des deux marqueurs dans une même paire : token nu (ex. "()")
v = p2k.dan_to_vocal([{"note": "", "vocalPosMarkers": {"mid": "vocalStart"}},
                      {"note": "", "isSmall": True, "vocalPosMarkers": {"mid": "vocalEnd"}}])
assert v == ["()"], v
print("OK dan_to_vocal : marqueurs principal + à cheval combinés en ()")

# paires vides terminales retirées de ::tab
dan = [{"note": chr(0xE000)}, {}, {"note": ""}, {"note": "", "isSmall": True},
        {"note": ""}, {}]
assert p2k.dan_to_tokens(dan) == ["合"], p2k.dan_to_tokens(dan)
print("OK paires vides terminales retirées de la ligne ::tab")

# --- 9. テスト節-2 : dan 5 à 11 cellules, marqueurs vocaux sur cases vides -----
JSON2 = ROOT / "samples" / "portama-json" / "テスト節-2.json"
KKML2 = ROOT / "tests" / "fixtures" / "synthetic" / "テスト節-2.kkml"
data2 = json.load(open(JSON2, encoding="utf-8"))
with contextlib.redirect_stderr(io.StringIO()):
    kkml2 = p2k.convert_portama_to_kkml(data2)
tab2 = tab_lines(k.parse_kkml(kkml2))
assert tab2[4] == ["イ工", "イ五", REST], tab2[4]  # 3 paires vides terminales retirées
voc2 = vocal_lines(k.parse_kkml(kkml2))
assert voc2[4] == ["-", "-", "-", "()", ".(", ")"], voc2[4]
u2 = open(KKML2, encoding="utf-8").read()
assert tab_lines(k.parse_kkml(u2)) == tab2
uv = vocal_lines(k.parse_kkml(u2))
# seul écart connu : dernier token `).` (tenuto ajouté à la main) vs `)` du convertisseur
assert uv[:4] == voc2[:4] and uv[4] == voc2[4][:5] + [")."], (uv[4], voc2[4])
for layout in ("vertical", "horizontal", "mega"):
    _, e = render(kkml2, layout)
    assert "WARNING" not in e, (layout, e)
    _, e = render(u2, layout)
    assert "WARNING" not in e, (layout, e)
print("OK テスト節-2 : ::tab sans paires vides terminales, ::vocal avec () .( ), "
      "rendu sans avertissement (convertisseur et correction)")

# --- 10. テスト節-3 : positions top/bot des cellules à cheval -----------------
JSON3 = ROOT / "samples" / "portama-json" / "テスト節-3.json"
data3 = json.load(open(JSON3, encoding="utf-8"))
with contextlib.redirect_stderr(io.StringIO()):
    kkml3 = p2k.convert_portama_to_kkml(data3)
tab3 = tab_lines(k.parse_kkml(kkml3))
assert tab3[4] == ["イ工", "イ五", REST], tab3[4]
voc3 = vocal_lines(k.parse_kkml(kkml3))
# dan 5 (16 cellules) : ( ) combinés, .( mid seul, )( main mid + bot, ) top seul
assert voc3[4] == ["-", "-", "-", "()", ".(", ")(", "-", ")"], voc3[4]
# unités : top → nu, mid → 1 point, bot → 2 points (cellule à cheval seule)
v = p2k.dan_to_vocal([{"note": ""}, {"note": "", "isSmall": True, "vocalPosMarkers": {"top": "vocalStart"}},
                      {"note": ""}, {"note": "", "isSmall": True, "vocalPosMarkers": {"mid": "vocalEnd"}},
                      {"note": ""}, {"note": "", "isSmall": True, "vocalPosMarkers": {"bot": "vocalStart"}}])
assert v == ["(", ".)", "..("], v
for layout in ("vertical", "horizontal", "mega"):
    _, e = render(kkml3, layout)
    assert "WARNING" not in e, (layout, e)
print("OK テスト節-3 : top → ( ), mid → .( .), bot → ..( ..), combinaison )( , rendu sans avertissement")

print("\nTous les tests testbushi passent.")
