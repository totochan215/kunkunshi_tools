# -*- coding: utf-8 -*-
"""Tests de l'échappement des délimiteurs ruby \《 \》 \｛ \｝ (antislash).

Implémenté le 2026-11-20 : les délimiteurs 《》 ｛｝ restent ceux du KKML
(TODO de docs/kkml-format.md fermé — pas de passage aux yamakakko 〈〉), et
un antislash devant l'un de ces 4 caractères produit le caractère littéral
(antislash retiré) dans les paroles et les métadonnées, sans interprétation
ruby. Ailleurs, l'antislash reste littéral.

Usage :
    python3 tests/test_escape.py
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

# 1. _unescape / _escape
assert k._unescape("a\\《b\\》c\\｛d\\｝e") == "a《b》c｛d｝e"
assert k._unescape("a\\xb\\") == "a\\xb\\"   # antislash ailleurs = littéral
assert k._unescape("a\\\\《") == "a\\《"          # 1er antislash littéral, le 2e échappe
assert k._escape("a《b｝") == "a\\《b\\｝"
assert k._unescape(k._escape("x《》｛｝y\\z")) == "x《》｛｝y\\z"
print("OK _unescape/_escape (antislash retiré seulement devant 《》｛｝)")

# 2. _parse_ruby : syntaxe historique inchangée
assert k._parse_ruby("安《あ》") == [{"type": "mono", "base": "安", "ruby": "あ"}]
assert k._parse_ruby("｛安里屋｝《あさとや》") == [
    {"type": "group", "base": "安里屋", "ruby": "あさとや"}]
assert k._parse_ruby("｛安《あ》里《さと》｝") == [
    {"type": "jukugo", "items": [("安", "あ"), ("里", "さと")]}]
print("OK _parse_ruby : mono/group/jukugo historiques inchangés")

# 3. délimiteurs échappés = texte littéral, dans les 3 syntaxes
assert k._parse_ruby("a\\《b") == [{"type": "plain", "text": "a《b"}]
assert k._parse_ruby("x\\《y》z") == [{"type": "plain", "text": "x《y》z"}]
assert k._parse_ruby("ab\\《cd》安《あ》") == [
    {"type": "plain", "text": "ab《cd》"},
    {"type": "mono", "base": "安", "ruby": "あ"}]
assert k._parse_ruby("｛a\\｝b｝《x》") == [{"type": "group", "base": "a｝b", "ruby": "x"}]
assert k._parse_ruby("｛安\\《x》里《さと》｝") == [
    {"type": "jukugo", "items": [("安《x》里", "さと")]}]
assert k._parse_ruby("安《a\\》b》") == [{"type": "mono", "base": "安", "ruby": "a》b"}]
print("OK _parse_ruby : \\《 \\》 \\｛ \\｝ littéraux (mono/group/jukugo + annotation)")

# 4. annotation non fermée : toujours une erreur (régression)
try:
    k._parse_ruby("安《あ")
    raise AssertionError("ValueError attendue")
except ValueError:
    pass
print("OK annotation non fermée -> ValueError (comportement historique)")

# 5. _lyr_line_segments : paire échappée = 1 unité affichée, conservée dans le segment
segs = k._lyr_line_segments("a\\《b安《あ》")
assert segs == [("a\\《b", False, 3), ("安《あ》", True, 1)], segs
segs = k._lyr_line_segments("｛ab\\｝c｝《xy》")
assert segs == [("｛ab\\｝c｝《xy》", True, 4)], segs
# base échappée juste avant une annotation : l'antislash reste collé à l'atome
segs = k._lyr_line_segments("x\\《《r》")
assert segs == [("x", False, 1), ("\\《《r》", True, 1)], segs
assert k._parse_ruby(segs[1][0]) == [{"type": "mono", "base": "《", "ruby": "r"}]
print("OK _lyr_line_segments : unités affichées + atomes intacts avec échappement")

# 6. _cap_lyr_column : la coupe ne sépare jamais un antislash de son délimiteur
subs = k._cap_lyr_column(["ab\\《cdef"], 0, 4, kinsoku="simple")
assert subs[0][0][0] == "ab" and subs[1][0][0] == "\\《cd", subs
assert k._parse_ruby(subs[1][0][0]) == [{"type": "plain", "text": "《cd"}]
subs = k._cap_lyr_column(["ab\\《cdef"], 0, 3, kinsoku="off")
assert subs[0][0][0] == "ab" and subs[1][0][0].startswith("\\《"), subs
plain = "".join(k._title_plain(t) for lines, _i in subs for t in lines)
assert plain == "ab《cdef", plain
print("OK _cap_lyr_column : coupe jamais dans une paire \\X (kinsoku simple et off)")

# 7. _h_lyrics_atoms : les atomes ré-échappés se re-parsent au même texte affiché
for src in ["安\\《x》", "｛a\\｝b｝《xy》", "｛安《あ》\\《里《さと》｝", "ab安《あ》\\》", "x\\｛y"]:
    atoms = k._h_lyrics_atoms(src, 17)
    rejoined = "".join(a for a, _w in atoms)
    assert k._title_plain(rejoined) == k._title_plain(src), (src, atoms)
    assert k._has_ruby(k._parse_ruby(rejoined)) == k._has_ruby(k._parse_ruby(src)), src
assert any(a == "\\《" for a, _w in k._h_lyrics_atoms("安\\《x》", 17))
print("OK _h_lyrics_atoms : ré-échappement à la ré-émission KKML (round-trip)")

# 8. _title_plain (métadonnées dc:title) : antislash retiré, ruby exclu
assert k._title_plain("安\\《a》｛里｝《さと》") == "安《a》里"
print("OK _title_plain : métadonnées avec délimiteurs échappés")

# 9. E2E render : vertical, horizontal, chindami — 《》｛｝ littéraux rendus, aucun antislash
kkml = ("@title t\\《u》\\｛v\\｝安《あ》\n"
        "::tab\n合 工 工 工\n::\n"
        "::lyrics\n一、x\\《y》z安《あ》\n::\n")
for layout in ("vertical", "horizontal", "chindami"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        pages = k.render_svg(k.parse_kkml(kkml), layout=layout)
    assert "AVERTISSEMENT" not in err.getvalue(), (layout, err.getvalue())
    svg = "".join(pages)
    assert "\\" not in svg, (layout, "antislash fuite dans le SVG")
    assert "《" in svg and "》" in svg, (layout, "《》 littéraux absents du rendu")
    if layout == "chindami":
        assert "<dc:title>t《u》｛v｝安</dc:title>" in svg, "dc:title avec littéraux"
print("OK e2e render (vertical/horizontal/chindami) : littéraux rendus, pas d'antislash, dc:title OK")

# 10. CLI
with tempfile.NamedTemporaryFile("w", suffix=".kkml", delete=False,
                                 encoding="utf-8") as f:
    f.write("@title t\\《u》\n::tab\n合 工\n::\n::lyrics\nx\\《y》\n::\n")
    kkml_path = f.name
with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
    svg_path = f.name
r = subprocess.run([sys.executable, str(ROOT / "kkml2svg.py"), kkml_path,
                    "-l", "vertical", "-o", svg_path],
                   capture_output=True, text=True)
assert r.returncode == 0 and "AVERTISSEMENT" not in r.stderr, r.stderr
svg = open(svg_path, encoding="utf-8").read()
assert "\\" not in svg and "《" in svg
print("OK CLI kkml2svg (rc=0, 《 littéral rendu sans antislash)")

print("\nTous les tests d'échappement passent.")
