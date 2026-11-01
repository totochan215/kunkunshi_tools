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

# 7. @cols présent -> repli ; absent -> conservé
t7 = "@cols 2\n::tab\n合 工 尺 五\n::\n"
out, err, rc = run_clean(t7)
assert "合 工\n尺 五" in out, out
print("OK @cols replie ::tab")
t8 = "::tab\n合 工 尺 五\n::\n"
out, err, rc = run_clean(t8)
assert "合 工 尺 五\n" in out
print("OK sans @cols, sauts de ligne conservés")

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
