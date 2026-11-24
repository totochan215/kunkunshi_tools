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
song = k.parse_kkml(f"::tab\n合# 合b {KOU}上 　{REST_WHITE} {SHI_SHARP} {chr(0x5C3B)} {chr(0x5C16)}♯\n::\n")
toks = tab_lines(song)[0]
assert toks == [f"合{SHARP}", f"合{FLAT}", f"{RO}上", REST, SHI_SHARP, SHI, f"{SHI}{SHARP}"], toks
print("OK variantes : # -> ♯, b -> ♭, 口上 -> ロ上, ⚪︎ -> ◯, 尺♯ intact, 尻/尖 -> 尺 (jamais de 尻 ni 尖 en KKML)")

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
# croches : cercle sur le shaku principal / à cheval (codepoint corrigé 尖 U+5C16 → 尺 U+5C3A ; jamais de 尻 U+5C3B ni 尖 U+5C16 en KKML)
for tok in (f"尺/合", f"合/尺"):
    out = []
    k.render_cell(out, tok, 42, 29, 22, opts={"shaku_circled": True, "shaku_sharp": True})
    assert "<circle" in "".join(out), tok
out = []
k.render_cell(out, f"合/尺♯", 42, 29, 22, opts={"shaku_circled": True, "shaku_sharp": True})
assert "<circle" not in "".join(out), "".join(out)  # shaku à cheval altéré : pas de cercle
print("OK 尺♯ : décomposé au rendu (note identique à 尺 seul, ♯ = marque standard), masqué avec @shaku_sharp off, jamais cerclé si altéré ; cercles croches OK")

# --- 7b. Condensation unifiée des composites (2026-11-23) : règle CONDENSE_W = {2: 120%, 3: 180%}
def _tl(tok):
    out = []
    k.render_cell(out, tok, 42, 29, 22, opts={"shaku_circled": False, "shaku_sharp": True})
    m = _re.search(r'textLength="([\d.]+)"', "".join(out))
    return float(m.group(1)) if m else None
w2 = {_tl(t) for t in ("下老", "下八", "イ合", "ロ尺")}
assert w2 == {22 * 1.2}, w2  # même largeur pour tous les composites à 2 caractères (下, イ, ロ)
assert _tl("イ下尺") == 22 * 1.8, _tl("イ下尺")
print("OK condensation unifiée : 2 car. -> 120% de fs partout (下老/下八/イX/ロX), 3 car. -> 180% (イ下尺)")

# --- 7c. Membres composites d'accords/shuffle condensés à leur fs RÉELLE (2026-11-23) ----
def _els(tok):
    out = []
    k.render_cell(out, tok, 42, 29, 22, opts={"shaku_circled": False, "shaku_sharp": True})
    return _re.findall(r'<text[^>]*font-size="([\d.]+)"([^>]*)>([^<]*)</text>', "".join(out))
chord = _els("尺=ロ合")           # accord : membres à CHORD_RATIO de fs
small = int(22 * k.CHORD_RATIO)
tl_ro = [float(_re.search(r'textLength="([\d.]+)"', a).group(1)) for fs, a, c in chord
         if c == "ロ合" and "textLength" in a]
assert tl_ro == [small * 1.2], (chord, tl_ro)   # condensé à la fs réduite, pas à 22
assert all("textLength" not in a for fs, a, c in chord if c == "尺")  # note simple : pas de TL
shuf = _els("イ合:尺")            # shuffle 2 notes : membres à SHUFFLE_RATIO
sh = 22 * k.SHUFFLE_RATIO  # le shuffle garde sh en float (effective_fs * SHUFFLE_RATIO)
tl_i = [float(_re.search(r'textLength="([\d.]+)"', a).group(1)) for fs, a, c in shuf
        if c == "イ合" and "textLength" in a]
assert tl_i == [sh * 1.2], (shuf, tl_i)
print("OK membres composites d'accord/shuffle condensés à leur fs réelle (CONDENSE_W × small/sh)")

# --- 7d. Taux kuubanchi/straddle/accord/shuffle (2026-11-23) : constantes séparées, alignées ----
assert k.KUUBANCHI_RATIO == k.STRADDLE_RATIO and k.CHORD_RATIO == k.SHUFFLE_RATIO
assert k.STRADDLE_RATIO == 0.713 and k.SHUFFLE_RATIO == 0.8
# kuubanchi seul : fs * KUUBANCHI_RATIO ; sur un straddle : les taux se multiplient
els_s = _els("合s")
assert els_s[0][0] == str(int(22 * k.KUUBANCHI_RATIO)), els_s
els_bs = _els("合/尺s")   # s s'applique au straddle ; effective_fs (main) inclut déjà s
main_fs = [fs for fs, a, c in els_bs if c == "合"][0]
strad_fs = [fs for fs, a, c in els_bs if c == "尺"][0]
assert float(main_fs) == int(22 * k.KUUBANCHI_RATIO), els_bs
assert float(strad_fs) == int(int(22 * k.KUUBANCHI_RATIO) * k.STRADDLE_RATIO), els_bs  # multiplication
print("OK taux : KUUBANCHI_RATIO=STRADDLE_RATIO=%.3f, CHORD_RATIO=SHUFFLE_RATIO=%.2f ; kuubanchi×straddle multipliés" % (k.STRADDLE_RATIO, k.SHUFFLE_RATIO))

# --- 7e. Marques ancrées au coin du token / au bas de la case (retours visuels PR #98) ---
# Altération sur composite (ex. ロ尺♭, 下八♭) : la marque est ancrée au BORD DROIT
# du token condensé (text_w), ancre middle — plus centrée sur la case (avant : ancre start en cx).
# Même y qu'une altération sur note simple ; x proche de celui de 合♯ (note seule), clampé dans la case.
_cx, _cy, _fs, _cw, _ch = 42, 29, 22, 52, 58
_ro_shi = chr(0x30ED) + SHI          # ロ尺 (position haute reconnue)
_ge_hachi = chr(0x4E0B) + chr(0x516B)  # 下八
for tok in (_ro_shi + FLAT, _ge_hachi + FLAT):
    out = []
    k.render_cell(out, tok, _cx, _cy, _fs, cell_w=_cw, cell_h=_ch,
                  opts={"shaku_circled": False, "shaku_sharp": True})
    m = _re.search(r'<text x="([\d.-]+)" y="([\d.-]+)" text-anchor="(\w+)"[^>]*font-size="(\d+)"[^>]*>' + FLAT + r'</text>', "".join(out))
    x, y, anc, tfs = float(m.group(1)), float(m.group(2)), m.group(3), int(m.group(4))
    tw = _fs * k.CONDENSE_W[2]                     # largeur du token condensé
    dx = k.TECHNIQUE_SUFFIXES[FLAT]["dx"]
    exp_x = min(_cx + tw / 2 + _fs * (dx - 0.5), _cx + _cw / 2 - tfs / 2)  # bord droit, clampé
    assert anc == "middle" and abs(x - exp_x) < 1e-9, (tok, x, exp_x)
    assert x > _cx + tw / 2, (tok, x)               # à droite du bord droit du token
out = []
k.render_cell(out, f"{chr(0x5408)}{SHARP}", _cx, _cy, _fs, opts={"shaku_sharp": True})
m_s = _re.search(r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*>' + SHARP + r'</text>', "".join(out))
x_simple, y_simple = float(m_s.group(1)), float(m_s.group(2))
assert abs(y - y_simple) < 1e-9 and abs(x - x_simple) < _fs * 0.2, (x, x_simple, y, y_simple)
# aki-utu 'v' : ancre 'cell-bottom' -> ty = bas de case - note_fs*drop (presque au bas de la case)
for tok in (_ge_hachi + "v", f"{chr(0x5408)}v", f"{chr(0x5408)}/{SHI}v"):  # composite / note / straddle
    out = []
    k.render_cell(out, tok, _cx, _cy, _fs, cell_w=_cw, cell_h=_ch, opts={})
    m = _re.search(r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*>\u2228</text>|<text x="([\d.-]+)" y="([\d.-]+)"[^>]*>' + chr(0x2228) + r'</text>', "".join(out))
    xv, yv = (float(m.group(1)), float(m.group(2))) if m.group(1) else (float(m.group(3)), float(m.group(4)))
    note_fs = _fs
    if "/" in tok:
        note_fs = int(int(_fs * k.KUUBANCHI_RATIO) * k.STRADDLE_RATIO) if "s" in tok else int(_fs * k.STRADDLE_RATIO)
    exp_y = _cy + _ch / 2 - note_fs * k.TECHNIQUE_SUFFIXES["v"]["drop"]
    assert abs(yv - exp_y) < 1e-9, (tok, yv, exp_y)   # bas de case = _cy + _ch/2 = 58
    assert yv > _cy + _ch / 2 - note_fs * 0.2          # presque touchant le bas
print("OK marques au coin du token (altération composite = coin haut-droit comme note simple) ; aki-utu v ancré au bas de la case")




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
