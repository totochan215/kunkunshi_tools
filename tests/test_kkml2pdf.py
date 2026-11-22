# -*- coding: utf-8 -*-
"""Tests de kkml2pdf.py (KKML -> PDF multipage, layouts à format cm prédéfini).

Stdlib uniquement : le test de bout en bout CLI passe par un faux
`rsvg-convert` (écrit dans un répertoire temporaire mis en tête du PATH) qui
produit un PDF 1 page minimal dont le MediaBox est lu sur le SVG en cm ; la
fusion est faite par pypdf quand le module est présent, sinon on vérifie
seulement l'ordre d'appel. Les assertions pypdf sont sautées (SKIP) sinon.

Usage :
    python3 tests/test_kkml2pdf.py
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k
import kkml2pdf as p

CM = 28.3465  # 1 cm en pt (même constante que kkml2svg)


def minimal_pdf_bytes(w_pt, h_pt):
    """PDF 1.4 minimal valide : 1 page, MediaBox [0 0 w_pt h_pt], contenu vide."""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %g %g] "
         "/Resources << >> /Contents 4 0 R >>" % (w_pt, h_pt)).encode(),
        b"<< /Length 0 >>\nstream\n\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref))
    return bytes(out)


def write_minimal_pdf(path, w_pt, h_pt):
    Path(path).write_bytes(minimal_pdf_bytes(w_pt, h_pt))


def fake_engine(svg_path, pdf_path):
    """Faux moteur SVG->PDF : MediaBox lu sur la racine SVG (cm -> pt)."""
    svg = Path(svg_path).read_text(encoding="utf-8")
    w, h = p.page_size_cm(svg)
    write_minimal_pdf(pdf_path, w * CM, h * CM)


# Faux binaire rsvg-convert pour le test CLI (autonome, stdlib).
STUB_RSVG = '''#!/usr/bin/env python3
import re, sys
args = sys.argv[1:]
out = inp = None
i = 0
while i < len(args):
    if args[i] == "-o":
        out = args[i + 1]; i += 2
    elif args[i] == "-f":
        i += 2
    else:
        inp = args[i]; i += 1
svg = open(inp, encoding="utf-8").read()
tag = re.search(r"<svg\\b[^>]*>", svg, re.S).group(0)
def a(n):
    m = re.search(n + r\'="([^"]*)"\', tag)
    return m.group(1)
w = float(a("width")[:-2]) * 28.3465
h = float(a("height")[:-2]) * 28.3465
objs = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %g %g] "
     "/Resources << >> /Contents 4 0 R >>" % (w, h)).encode(),
    b"<< /Length 0 >>\\nstream\\n\\nendstream",
]
out_b = bytearray(b"%PDF-1.4\\n")
offs = []
for n, o in enumerate(objs, 1):
    offs.append(len(out_b))
    out_b += b"%d 0 obj\\n" % n + o + b"\\nendobj\\n"
xref = len(out_b)
out_b += b"xref\\n0 %d\\n" % (len(objs) + 1)
out_b += b"0000000000 65535 f \\n"
for off in offs:
    out_b += b"%010d 00000 n \\n" % off
out_b += (b"trailer\\n<< /Size %d /Root 1 0 R >>\\nstartxref\\n%d\\n%%%%EOF\\n"
          % (len(objs) + 1, xref))
open(out, "wb").write(bytes(out_b))
'''

# 1. Taille de page en cm lue sur la racine SVG, par layout
for lay, (w, h) in p.LAYOUTS_CM.items():
    text = f"@title test\n@layout {lay}\n::tab\n合 五 四\n五 合\n::\n"
    svg = k.render_svg(k.parse_kkml(text))[0]
    assert p.page_size_cm(svg) == (w, h), (lay, p.page_size_cm(svg))
    print(f"OK page_size_cm {lay} : {w:g} x {h:g} cm")

# 2. Layout libre (vertical) : racine en pt, pas en cm
svg = k.render_svg(k.parse_kkml("::tab\n合\n::\n"))[0]
assert p.page_size_cm(svg) is None
print("OK page_size_cm vertical (page en pt) : None")

# 3. Garde : layouts sans format cm refusés
for text in ("@layout vertical\n::tab\n合\n::\n",   # explicite
             "::tab\n合\n::\n",                       # défaut = vertical
             "@layout tuto\n::tab\n合\n::\n"):        # tuto = canvas px
    try:
        p.render_pages(text)
        raise AssertionError("garde non déclenchée")
    except p.UnsupportedLayout as e:
        assert "cm" in str(e) and "chindami" in str(e)
print("OK garde : vertical/défaut/tuto refusés (UnsupportedLayout)")

# 4. Surcharge de layout (-l) : vertical -> mega accepté
lay, svgs = p.render_pages("::tab\n合\n::\n", layout="mega")
assert lay == "mega" and len(svgs) == 1
print("OK surcharge layout : -l mega retenu malgré l'absence de @layout")

# 5. Pagination : nomura à 10 dans -> 2 pages, toutes à la même taille A4
lines = "\n".join(" ".join(["合"] * 12) for _ in range(10))
lay, svgs = p.render_pages("@title t\n@layout nomura\n::tab\n" + lines + "\n::\n")
assert lay == "nomura" and len(svgs) == 2, len(svgs)
assert all(p.page_size_cm(s) == (21.0, 29.7) for s in svgs)
print(f"OK multipage : nomura 10 dans -> {len(svgs)} pages A4 21 x 29,7 cm")

# 6. Pipeline produce_pdf avec faux moteur ; fusion pypdf si dispo, sinon
#    enregistrement de l'ordre des pages
with tempfile.TemporaryDirectory() as td:
    work = Path(td) / "work"
    out = Path(td) / "out.pdf"
    if importlib.util.find_spec("pypdf"):
        p.produce_pdf(svgs, out, engine=fake_engine, merger="pypdf", workdir=work)
        from pypdf import PdfReader
        rd = PdfReader(str(out))
        assert len(rd.pages) == 2, len(rd.pages)
        for pg in rd.pages:
            mb = pg.mediabox
            assert abs(float(mb.width) - 21 * CM) < 0.01, float(mb.width)
            assert abs(float(mb.height) - 29.7 * CM) < 0.01, float(mb.height)
        print("OK produce_pdf + fusion pypdf : 2 pages, MediaBox A4 en pt")
    else:
        recorded = []

        def rec_merger(pdfs, out_path):
            recorded.extend(pdfs)
            write_minimal_pdf(out_path, 100, 100)

        p.produce_pdf(svgs, out, engine=fake_engine, merger=rec_merger,
                      workdir=work)
        assert [q.name for q in recorded] == ["page-1.pdf", "page-2.pdf"]
        print("OK produce_pdf + fusion simulée : ordre des pages conservé "
              "(SKIP vérif pypdf, module absent)")
    assert (work / "page-1.svg").exists() and (work / "page-2.pdf").exists()
    print("OK --keep-temp : SVG et PDF intermédiaires conservés")

# 7. CLI : garde -> exit 2 avec message
with tempfile.TemporaryDirectory() as td:
    kkml = Path(td) / "v.kkml"
    kkml.write_text("@layout vertical\n::tab\n合\n::\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "kkml2pdf.py", str(kkml),
                        "-o", str(Path(td) / "v.pdf")],
                       capture_output=True, text=True)
    assert r.returncode == 2, (r.returncode, r.stderr)
    assert "ERREUR" in r.stderr and "chindami" in r.stderr, r.stderr
    print("OK CLI garde : layout vertical -> exit 2 + message d'erreur")

# 8. CLI de bout en bout avec faux rsvg-convert en tête du PATH
have_merger = (importlib.util.find_spec("pypdf") is not None
               or shutil.which("pdfunite") or shutil.which("gs"))
if not have_merger:
    print("SKIP CLI end-to-end : aucun outil de fusion disponible")
else:
    with tempfile.TemporaryDirectory() as td:
        bindir = Path(td) / "bin"
        bindir.mkdir()
        stub = bindir / "rsvg-convert"
        stub.write_text(STUB_RSVG, encoding="utf-8")
        stub.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
        kkml = Path(td) / "c.kkml"
        kkml.write_text("@layout chindami\n::tab\n合 五\n::\n", encoding="utf-8")
        out = Path(td) / "c.pdf"
        keep = Path(td) / "temp"
        r = subprocess.run([sys.executable, str(ROOT / "kkml2pdf.py"),
                            str(kkml), "-o", str(out), "--keep-temp", str(keep)],
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0, (r.returncode, r.stderr)
        assert out.exists() and "OK:" in r.stderr
        assert (keep / "page-1.svg").exists() and (keep / "page-1.pdf").exists()
        if importlib.util.find_spec("pypdf"):
            from pypdf import PdfReader
            rd = PdfReader(str(out))
            assert len(rd.pages) == 1
            mb = rd.pages[0].mediabox
            assert abs(float(mb.width) - 23 * CM) < 0.01, float(mb.width)
            assert abs(float(mb.height) - 15 * CM) < 0.01, float(mb.height)
        # stdin -> output.pdf dans le cwd
        r2 = subprocess.run([sys.executable, str(ROOT / "kkml2pdf.py"), "-"],
                            input="@layout mega\n::tab\n合\n::\n",
                            capture_output=True, text=True, env=env, cwd=td)
        assert r2.returncode == 0, (r2.returncode, r2.stderr)
        assert (Path(td) / "output.pdf").exists()
        if importlib.util.find_spec("pypdf"):
            from pypdf import PdfReader
            rd = PdfReader(str(Path(td) / "output.pdf"))
            mb = rd.pages[0].mediabox
            assert abs(float(mb.width) - 42 * CM) < 0.01, float(mb.width)
            assert abs(float(mb.height) - 29.7 * CM) < 0.01
        print("OK CLI end-to-end (faux rsvg-convert) : chindami 23x15 cm, "
              "stdin mega -> output.pdf A3 42x29,7 cm, --keep-temp OK")

# 9. convert_page : validation du PDF produit (marqueur %%EOF) — évite le
#    « EOF marker not found » de pypdf quand un moteur (ex. inkscape sur macOS)
#    rend la main avant d'avoir fini d'écrire le fichier.
import threading
import time
p._PDF_TIMEOUT = 0.5
with tempfile.TemporaryDirectory() as td:
    svg = Path(td) / "p.svg"
    svg.write_text("<svg/>", encoding="utf-8")
    out_ok = Path(td) / "ok.pdf"
    p.convert_page(lambda s_, o: write_minimal_pdf(o, 100, 100), svg, out_ok)
    assert out_ok.exists() and p._pdf_complet(out_ok, timeout=0.5)

    def engine_tronque(s_, o):   # PDF sans %%EOF (fichier incomplet)
        Path(o).write_bytes(minimal_pdf_bytes(100, 100)[:-20])
    try:
        p.convert_page(engine_tronque, svg, Path(td) / "bad.pdf")
        raise AssertionError("garde non déclenchée")
    except RuntimeError as e:
        assert "%%EOF" in str(e), e

    def engine_lent(s_, o):      # écriture en deux fois (taille qui se stabilise)
        data = minimal_pdf_bytes(100, 100)
        Path(o).write_bytes(data[:-10])
        def fin():
            time.sleep(0.3)
            with open(o, "ab") as f:
                f.write(data[-10:])
        threading.Thread(target=fin).start()
    out_late = Path(td) / "late.pdf"
    p.convert_page(engine_lent, svg, out_late)
    assert p._pdf_complet(out_late, timeout=2.0)
    print("OK convert_page : PDF tronqué détecté (RuntimeError %%EOF), "
          "écriture différée attendue jusqu'à stabilisation")

print("Tous les tests kkml2pdf passent.")
