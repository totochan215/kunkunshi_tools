# -*- coding: utf-8 -*-
"""Tests de la conversion Portama -> KKML de テスト節 (« test bushi ») et du
rendu de la correction manuelle de l'utilisateur (samples/kkml/テスト節.kkml).

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
- la correction manuelle rend sans avertissement (vertical/horizontal/mega)
  et correspond au convertisseur après normalisation, sauf deux PUA où la
  correction de l'utilisateur diffère de la table de docs/portama-format.md
  (E014 : イ尺 écrit vs 下尺 documenté ; E028 : イ上 écrit vs イ五 documenté).

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
KKML_PATH = ROOT / "samples" / "kkml" / "テスト節.kkml"


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
assert voc[0] == ["-"] * 12
assert voc[1] == ["-"] * 6 + [".(", ".)"] + ["-"] * 4, voc[1]
assert voc[4] == ["-"] * 3
assert "::vocal" in kkml
print("OK ::vocal : .( .) en ligne 2 positions 7-8, lignes paddées à `-`")

# --- 3. La sortie du convertisseur rend sans avertissement ------------------
for layout in ("vertical", "horizontal", "mega"):
    _, e = render(kkml, layout)
    assert "AVERTISSEMENT" not in e, (layout, e)
print("OK sortie convertisseur sans avertissement (vertical/horizontal/mega)")

# --- 4. La correction manuelle de l'utilisateur rend sans avertissement -----
user_kkml = open(KKML_PATH, encoding="utf-8").read()
for layout in ("vertical", "horizontal", "mega"):
    _, e = render(user_kkml, layout)
    assert "AVERTISSEMENT" not in e, (layout, e)
print("OK samples/kkml/テスト節.kkml (correction manuelle) sans avertissement")

# --- 5. Correction manuelle == convertisseur après normalisation ------------
# (sauf E014/E028 où la correction diffère de la table doc : voir docstring)
u_tab = tab_lines(k.parse_kkml(user_kkml))
c_tab = tab_lines(k.parse_kkml(kkml))
diffs = [(i, j, a, b) for i, (la, lb) in enumerate(zip(u_tab, c_tab))
         for j, (a, b) in enumerate(zip(la, lb)) if a != b]
assert diffs == [(3, 1, "イ" + SHI, "下" + SHI),   # E014 : correction イ尺, doc 下尺
                 (4, 1, "イ" + "上", "イ" + "五")], diffs  # E028 : correction イ上, doc イ五
assert vocal_lines(k.parse_kkml(user_kkml)) == vocal_lines(k.parse_kkml(kkml))
print("OK correction manuelle = convertisseur après normalisation "
      "(écarts documentés E014/E028 exceptés)")

# --- 6. Variantes de saisie normalisées au parsing ---------------------------
song = k.parse_kkml(f"::tab\n合# 合b {KOU}上 　{REST_WHITE} {SHI_SHARP}\n::\n")
toks = tab_lines(song)[0]
assert toks == [f"合{SHARP}", f"合{FLAT}", f"{RO}上", REST, SHI_SHARP], toks
print("OK variantes : # -> ♯, b -> ♭, 口上 -> ロ上, ⚪︎ -> ◯, 尺♯ intact")

# --- 7. Cas spécial 尺♯ : pas de ♯ séparé avec @shaku_sharp off --------------
out = []
k.render_cell(out, SHI_SHARP, 42, 29, 22,
              opts={"shaku_sharp": False, "shaku_circled": False})
svg = "".join(out)
assert SHARP not in svg and SHI in svg, svg
out = []
k.render_cell(out, SHI_SHARP, 42, 29, 22,
              opts={"shaku_sharp": True, "shaku_circled": False})
svg = "".join(out)
assert SHI in svg and SHARP in svg and "tspan" in svg, svg
# et sur une autre note, ♯ est bien un suffixe séparé (haut-droite)
out = []
k.render_cell(out, f"合{SHARP}", 42, 29, 22, opts={"shaku_sharp": False})
svg = "".join(out)
assert svg.count("<text") == 2 and SHARP in svg, svg
print("OK 尺♯ : masqué avec @shaku_sharp off (pas de régression), ♯ suffixe sur 合♯")

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

v = p2k.dan_to_vocal([{"note": ""}, {"note": chr(0xE000), "isSmall": True,
                                        "vocalPosMarkers": {"mid": "vocalStart"}},
                      {"note": ""}, {"note": chr(0xE000), "isSmall": True,
                                     "vocalPosMarkers": {"mid": "vocalEnd"}}])
assert v == [".(", ".)"], v
print("OK dan_to_vocal : mid vocalStart/vocalEnd -> .( / .)")

print("\nTous les tests testbushi passent.")
