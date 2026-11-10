import subprocess, sys, os, tempfile
os.chdir('/workspace/github__totochan215__kunkunshi_tools')

def run_clean(text):
    with tempfile.NamedTemporaryFile('w', suffix='.kkml', delete=False, encoding='utf-8') as f:
        f.write(text); path = f.name
    r = subprocess.run([sys.executable, 'kkml_cleaner.py', '-n', path],
                       capture_output=True, text=True)
    os.unlink(path)
    return r.stdout, r.stderr, r.returncode

# 1. ::vocal manquante -> créée alignée
t1 = "@title test\n\n::tab\n合 工 尺\n五 合\n::\n"
out, err, rc = run_clean(t1)
assert rc == 0
assert "::vocal\n- - -\n- -\n::" in out, out
print("OK vocal manquante créée")

# 2. ::vocal désalignée mais total identique -> réalignée
t2 = "@title t\n::tab\n合 工 尺\n五 合\n::\n::vocal\n- - - -\n-\n::\n"
out, err, rc = run_clean(t2)
assert "::vocal\n- - -\n- -\n::" in out, out
print("OK vocal réalignée (total boucle)")

# 3. total ne boucle pas -> avertissement, pas de réalignement
t3 = "@title t\n::tab\n合 工 尺\n五 合\n::\n::vocal\n- - - - - -\n::\n"
out, err, rc = run_clean(t3)
assert "AVERTISSEMENT" in err and "PAS de réalignement" in err, err
assert "- - - - - -" in out
print("OK avertissement si total ne boucle pas")

# 4. ::lyrics manquante -> créée vide
t4 = "@title t\n::tab\n合\n::\n"
out, err, rc = run_clean(t4)
assert "::lyrics\n::" in out
print("OK lyrics créée vide")

# 5. ::tab implicite -> explicite (info)
t5 = "@title t\n合 工\n"
out, err, rc = run_clean(t5)
assert "::tab\n合 工\n::" in out and "info" in err
print("OK tab implicite -> explicite")

# 6. ::tab manquante -> créée vide
t6 = "@title t\n::lyrics\n一、test\n::\n"
out, err, rc = run_clean(t6)
assert "::tab\n::" in out
print("OK tab manquante créée vide")

# 7. @cells_per_dan présent -> repli ; absent -> conservé
t7 = "@cells_per_dan 2\n::tab\n合 工 尺 五\n::\n"
out, err, rc = run_clean(t7)
assert "合 工\n尺 五" in out, out
print("OK @cells_per_dan replie ::tab")
t8 = "::tab\n合 工 尺 五\n::\n"
out, err, rc = run_clean(t8)
assert "合 工 尺 五\n" in out
print("OK sans @cells_per_dan, sauts de ligne conservés")

# 8. alias tab-lyrics -> vocal
t9 = "::tab\n合\n::\n::tab-lyrics\nあ\n::\n"
out, err, rc = run_clean(t9)
assert "::vocal\nあ\n::" in out
print("OK alias tab-lyrics -> vocal")

# 9. normalisation pleine chasse + romaji
t10 = "::tab\n合／工 ＋ 四\n::\n"
out, err, rc = run_clean(t10)
assert "合/工 + 四" in out, out
print("OK normalisation pleine chasse")

# 10. idempotence sur entrée sale
for src in (t1, t2, t3, t7, t9, t10):
    o1, _, _ = run_clean(src)
    o2, _, _ = run_clean(o1)
    assert o1 == o2, f"non idempotent:\n{o1}\n---\n{o2}"
print("OK idempotence sur tous les cas")

# 11. erreur fatale : fichier illisible (section jamais fermée n'est pas fatal,
# mais un contenu binaire oui)
r = subprocess.run([sys.executable, 'kkml_cleaner.py', '-n', '/dev/null'],
                   capture_output=True, text=True)
assert r.returncode == 1 and "ERREUR" in r.stderr
print("OK erreur fatale fichier vide")

# 12. normalisation ＂ (U+FF02) -> " (nuchi-utu)
t12 = "::tab\n合＂\n::\n"
out, err, rc = run_clean(t12)
assert '合"' in out, out
o2, _, _ = run_clean(out)
assert out == o2, 'non idempotent'
print("OK normalisation ＂ -> \" (nuchi-utu), idempotent")

# 13. rendu kkml2svg : 合" produit le glyphe ゜ (U+309C)
sys.path.insert(0, os.getcwd())
import kkml2svg as _k
_svg = _k.render_svg(_k.parse_kkml('::tab\n合\"\n::\n'))[0]
assert '゜' in _svg and '合' in _svg
print("OK rendu nuchi-utu : glyphe ゜ dans le SVG")

# 14. layout tuto : bloc 1280x720, page titre + pages tab (8 cases/dan, 7 dans/page)
t14 = "@title t\n@layout tuto\n::tab\n合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合\n::\n::lyrics\ntest\n::\n"
song = _k.parse_kkml(t14)
assert song.layout == "tuto"
svgs = _k.render_svg(song)
assert all('width="1280"' in s and 'height="720"' in s for s in svgs), 'canvas non WxH'
assert len(svgs) == 3, len(svgs)  # 1 titre + 1 tab (20/8 = 3 dans <= 7) + 1 lyrics
svgs2 = _k.render_svg(_k.parse_kkml(t14.replace('合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合', '合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合 合')))
assert len(svgs2) == 4, len(svgs2)  # 60/8 = 8 dans -> 2 pages tab
print("OK layout tuto : pages 1280x720, 8 cases/dan, 7 dans/page")

# 15. layout tuto + titre avec ruby (mono/group/jukugo) : pas de KeyError
t15 = "@title 安《あ》｛安里屋｝《あさとや》｛安《あ》里《さ》｝\n@layout tuto\n::tab\n合\n::\n"
svgs15 = _k.render_svg(_k.parse_kkml(t15))
assert all('width="1280"' in s and 'height="720"' in s for s in svgs15)
assert len(svgs15) == 2
print("OK tuto + titre ruby (mono/group/jukugo), pages 1280x720")

# 16. tuto : bande marker à droite + straddle sur la bordure droite
GO = chr(0x5408); GO5 = chr(0x5DE5); A = chr(0x3042)
t16 = "@layout tuto\n::tab\n" + GO + "/" + GO5 + " " + GO + "\n::\n::vocal\n" + A + " -\n::\n"
svgs16 = _k.render_svg(_k.parse_kkml(t16))
tab16 = svgs16[1]
assert tab16.count('<line') >= 1, 'pas de séparateur marker'
import re as _re
mv = [(float(m.group(1)), float(m.group(2))) for m in _re.finditer(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*fill="#333">', tab16)]
assert mv and abs(mv[0][0] - 89.125) < 0.5, mv  # syllabe centrée sur sa case
assert 65 < mv[0][1] < 114.29, mv  # en bas de la case, au-dessus de la bordure inférieure (16+98.29)
st = [m for m in _re.finditer(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*fill="black">' + GO5 + r'</text>', tab16)]
assert st and abs(float(st[0].group(1)) - 162.25) < 0.5, st  # straddle CENTRÉ sur la bordure droite (162.25)
print("OK tuto : bande marker à droite + straddle sur bordure droite")

# 17. token ":X" (ex. "(:X" après strip des parenthèses) : note centrée, pas décalée
GO = chr(0x5408)
svgs17 = _k.render_svg(_k.parse_kkml("@layout tuto\n::tab\n:" + GO + " " + GO + ":\n::\n"))
t17 = svgs17[1]
import re as _re17
centres = {89.125, 235.375}  # centres des cases 0 et 1 (cell_w=146.25)
for m in _re17.finditer(r'<text x="([\d.]+)" y="[\d.]+"[^>]*fill="black">' + GO + r'</text>', t17):
    assert any(abs(float(m.group(1)) - c) < 0.5 for c in centres), m.group(1)  # centré sur sa case
print("OK ':X' / 'X:' -> note centrée taille pleine")

# 18. tuto : croche A/B -> note et straddle centrés entre eux verticalement
GO, GO5 = chr(0x5408), chr(0x5DE5)
s18 = _k.render_svg(_k.parse_kkml("@layout tuto\n::tab\n" + GO + "/" + GO5 + "\n::\n"))[1]
import re as _re18
ms = list(_re18.finditer(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*font-size="(\d+)" fill="black">([^<]+)</text>', s18))
pair = [(float(m.group(2)), int(m.group(3)), m.group(4)) for m in ms if m.group(4) in (GO, GO5)]
assert len(pair) == 2, pair
(y_main, fs_main, _), (y_str, fs_str, _) = pair
# centre optique = baseline - 0.318 * taille (convention du code) -> doit être égal
c_main = y_main - 0.318 * fs_main
c_str = y_str - 0.318 * fs_str
assert abs(c_main - c_str) < 0.6, (c_main, c_str)
print("OK tuto : note et straddle centrés entre eux verticalement")
