# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
kkml2pdf.py — Convertit un fichier KKML en PDF multipage.

Usage:
    python3 kkml2pdf.py chanson.kkml -o chanson.pdf
    python3 kkml2pdf.py chanson.kkml            # -> chanson.pdf (même nom)
    cat chanson.kkml | python3 kkml2pdf.py -     # depuis stdin -> output.pdf

Réservé à ce stade aux layouts dont le format de page est prédéfini en cm :
    chindami   page 23 x 15 cm paysage
    nomura     page A4 portrait 21 x 29,7 cm
    mega       page A3 paysage 42 x 29,7 cm
Les layouts libres (vertical, horizontal, tuto — page à taille variable selon
le contenu) sont refusés : utiliser kkml2svg.py puis l'export du logiciel
d'édition.

Chaîne : kkml2svg (importé) rend chaque page en un SVG autonome
(width/height en cm, via render_svg qui retourne la liste des pages) ->
conversion page par page en PDF 1 page -> fusion en un seul PDF multipage.

Moteur SVG -> PDF (détecté automatiquement, --engine pour forcer) :
    rsvg-convert   binaire librsvg (paquet librsvg2-bin)
    inkscape       binaire Inkscape 1.x
    cairosvg       module python `pip install cairosvg` (nécessite libcairo)
Fusion des pages (détectée automatiquement, --merger pour forcer) :
    pypdf          module python `pip install pypdf`
    pdfunite       binaire poppler-utils
    gs             binaire ghostscript
La taille de page PDF (MediaBox) est celle du SVG en cm, prise en charge par
le moteur ; l'embed des polices CJK est du ressort du moteur.

Options CLI : -o/--output, -c/--cells-per-dan, -l/--layout,
-p/--dans-per-page, --engine, --merger, --keep-temp DIR.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import kkml2svg as k

# Layouts à format de page prédéfini en cm : (largeur, hauteur) en cm.
LAYOUTS_CM = {
    "chindami": (23.0, 15.0),
    "nomura": (21.0, 29.7),
    "mega": (42.0, 29.7),
}

CM = k.CM  # 1 cm en points (28,3465), même constante que kkml2svg


class UnsupportedLayout(Exception):
    """Layout sans format de page en cm prédéfini."""


class EngineUnavailable(Exception):
    """Moteur SVG->PDF ou outil de fusion demandé indisponible."""


# --------------------------------------------------------------------------- #
# 1. Rendu kkml2svg : liste des pages SVG
# --------------------------------------------------------------------------- #

def render_pages(text, layout=None, cols=None, page_dans=None):
    """Parse le KKML et rend toutes les pages.
    -> (layout_effectif, [svg_page_1, ...]). Lève UnsupportedLayout si le
    layout effectif n'a pas de format cm prédéfini."""
    song = k.parse_kkml(text)
    eff = layout or song.layout
    if eff not in LAYOUTS_CM:
        raise UnsupportedLayout(
            f"layout '{eff}' sans format de page en cm prédéfini — kkml2pdf "
            f"ne gère à ce stade que : "
            + ", ".join(f"{n} ({w:g} x {h:g} cm)" for n, (w, h) in LAYOUTS_CM.items())
            + ". Utilisez kkml2svg.py pour ce layout.")
    svgs = k.render_svg(song, cols=cols, layout=layout, page_dans=page_dans)
    return eff, svgs


_SVG_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.S)


def _attr(tag, name):
    m = re.search(name + r'="([^"]*)"', tag)
    return m.group(1) if m else None


def page_size_cm(svg):
    """(largeur, hauteur) en cm lus sur la racine <svg> (width/height en cm).
    None si la racine n'est pas en cm."""
    m = _SVG_ROOT_RE.search(svg)
    if not m:
        return None
    tag = m.group(0)
    w, h = _attr(tag, "width"), _attr(tag, "height")
    if not w or not h or not w.endswith("cm") or not h.endswith("cm"):
        return None
    return float(w[:-2]), float(h[:-2])


# --------------------------------------------------------------------------- #
# 2. Moteur SVG -> PDF (une page)
# --------------------------------------------------------------------------- #

def _cairosvg_disponible():
    try:
        import cairosvg  # noqa: F401 — l'import échoue sans libcairo
        return True
    except Exception:
        return False


def engine_disponible(name):
    if name == "rsvg-convert":
        return shutil.which("rsvg-convert") is not None
    if name == "inkscape":
        return shutil.which("inkscape") is not None
    if name == "cairosvg":
        return _cairosvg_disponible()
    return False


ENGINES = ("rsvg-convert", "inkscape", "cairosvg")


def detect_engine(name="auto"):
    """Nom du moteur SVG->PDF à utiliser. 'auto' : premier disponible."""
    if name != "auto":
        if engine_disponible(name):
            return name
        raise EngineUnavailable(f"moteur SVG->PDF '{name}' indisponible")
    for e in ENGINES:
        if engine_disponible(e):
            return e
    raise EngineUnavailable(
        "aucun moteur SVG->PDF disponible — installez rsvg-convert "
        "(librsvg2-bin), inkscape, ou `pip install cairosvg` (libcairo requis) ; "
        "--engine pour forcer un moteur précis")


_PDF_TIMEOUT = 10.0   # attente max de stabilisation d'un PDF produit (s)


def _pdf_complet(path, timeout=_PDF_TIMEOUT):
    """Vrai si le PDF existe, commence par '%PDF-' et contient un marqueur
    %%EOF dans son dernier tampon — en attendant (jusqu'à `timeout` s) que la
    taille se stabilise : certains moteurs (ex. inkscape sur macOS) rendent la
    main avant d'avoir tout écrit sur disque."""
    p = Path(path)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            size = p.stat().st_size
        except OSError:
            size = -1
        if size > 0:
            with open(p, "rb") as f:
                head = f.read(8)
                f.seek(max(0, size - 2048), os.SEEK_SET)
                tail = f.read()
            if head.startswith(b"%PDF-") and b"%%EOF" in tail:
                return True
        time.sleep(0.2)
    return False


def convert_page(engine, svg_path, pdf_path):
    """Convertit un SVG (1 page) en PDF 1 page. `engine` : nom détecté ou
    fonction appelable (svg_path, pdf_path) — utile pour les tests."""
    if callable(engine):
        engine(Path(svg_path), Path(pdf_path))
    elif engine == "rsvg-convert":
        cmd = ["rsvg-convert", "-f", "pdf", "-o", str(pdf_path), str(svg_path)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(
                f"{engine} a échoué (rc={r.returncode}) sur {svg_path} : "
                f"{r.stderr.strip() or r.stdout.strip()}")
    elif engine == "inkscape":
        cmd = ["inkscape", str(svg_path), "--export-type=pdf",
               f"--export-filename={pdf_path}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(
                f"{engine} a échoué (rc={r.returncode}) sur {svg_path} : "
                f"{r.stderr.strip() or r.stdout.strip()}")
    elif engine == "cairosvg":
        import cairosvg
        cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
    else:
        raise EngineUnavailable(f"moteur inconnu : {engine}")
    if not Path(pdf_path).exists():
        raise RuntimeError(f"{engine} n'a produit aucun PDF pour {svg_path}")
    if not _pdf_complet(pdf_path, timeout=_PDF_TIMEOUT):
        raise RuntimeError(
            f"{engine} a produit un PDF incomplet (pas de marqueur %%EOF) "
            f"pour {svg_path} — réessayez, ou changez de moteur "
            f"(--engine rsvg-convert|cairosvg|inkscape)")


# --------------------------------------------------------------------------- #
# 3. Fusion des PDF 1 page en un PDF multipage
# --------------------------------------------------------------------------- #

def merger_disponible(name):
    if name == "pypdf":
        try:
            import pypdf  # noqa: F401
            return True
        except Exception:
            return False
    if name == "pdfunite":
        return shutil.which("pdfunite") is not None
    if name == "gs":
        return shutil.which("gs") is not None
    return False


MERGERS = ("pypdf", "pdfunite", "gs")


def detect_merger(name="auto"):
    """Nom de l'outil de fusion PDF. 'auto' : premier disponible."""
    if name != "auto":
        if merger_disponible(name):
            return name
        raise EngineUnavailable(f"outil de fusion PDF '{name}' indisponible")
    for m in MERGERS:
        if merger_disponible(m):
            return m
    raise EngineUnavailable(
        "aucun outil de fusion PDF disponible — installez `pip install pypdf`, "
        "poppler-utils (pdfunite) ou ghostscript (gs) ; --merger pour forcer")


def merge_pdfs(merger, pdf_paths, out_path):
    """Fusionne les PDF 1 page (dans l'ordre) en un PDF multipage.
    `merger` : nom détecté ou fonction appelable (pdf_paths, out_path)."""
    if callable(merger):
        merger([Path(p) for p in pdf_paths], Path(out_path))
        return
    pdf_paths = [str(p) for p in pdf_paths]
    if merger == "pypdf":
        from pypdf import PdfWriter
        w = PdfWriter()
        for p in pdf_paths:
            w.append(p)
        with open(out_path, "wb") as f:
            w.write(f)
    elif merger == "pdfunite":
        cmd = ["pdfunite", *pdf_paths, str(out_path)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"pdfunite a échoué : {r.stderr.strip()}")
    elif merger == "gs":
        cmd = ["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
               f"-sOutputFile={out_path}", *pdf_paths]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"gs a échoué : {r.stderr.strip()}")
    else:
        raise EngineUnavailable(f"outil de fusion inconnu : {merger}")
    if not Path(out_path).exists():
        raise RuntimeError(f"{merger} n'a produit aucun PDF : {out_path}")


# --------------------------------------------------------------------------- #
# 4. Pipeline complet
# --------------------------------------------------------------------------- #

def produce_pdf(svgs, out_path, engine, merger, workdir=None):
    """Écrit les SVG dans workdir, convertit chaque page en PDF 1 page puis
    fusionne. -> (out_path, nombre de pages)."""
    own_tmp = workdir is None
    if own_tmp:
        tmp = tempfile.TemporaryDirectory(prefix="kkml2pdf-")
        workdir = Path(tmp.name)
    else:
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
    try:
        svg_paths, pdf_paths = [], []
        for i, svg in enumerate(svgs, 1):
            svg_path = workdir / f"page-{i}.svg"
            svg_path.write_text(svg, encoding="utf-8")
            size = page_size_cm(svg)
            if size is None:
                print(f"kkml2pdf: WARNING: page {i} sans width/height en cm "
                      f"— taille de page PDF laissée au moteur", file=sys.stderr)
            else:
                print(f"page {i}/{len(svgs)} : {size[0]:g} x {size[1]:g} cm",
                      file=sys.stderr)
            pdf_path = workdir / f"page-{i}.pdf"
            convert_page(engine, svg_path, pdf_path)
            svg_paths.append(svg_path)
            pdf_paths.append(pdf_path)
        merge_pdfs(merger, pdf_paths, out_path)
        print(f"OK: {out_path}  ({len(pdf_paths)} page(s), "
              f"{Path(out_path).stat().st_size} octets)", file=sys.stderr)
        return out_path, len(pdf_paths)
    finally:
        if own_tmp:
            tmp.cleanup()


# --------------------------------------------------------------------------- #
# 5. CLI
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(
        description="KKML -> PDF multipage (layouts à format cm prédéfini : "
                    "chindami, nomura, mega)")
    ap.add_argument("input", help="fichier .kkml ou '-' pour stdin")
    ap.add_argument("-o", "--output", help="fichier PDF de sortie")
    ap.add_argument("-c", "--cells-per-dan", dest="cols", type=int,
                    help="cellules par dan (ignoré par les layouts à page fixe)")
    ap.add_argument("-l", "--layout",
                    choices=["vertical", "horizontal", "nomura", "chindami",
                             "tuto", "mega"],
                    help="force le layout (surcharge @layout)")
    ap.add_argument("-p", "--dans-per-page", "--page-dans", type=int,
                    dest="page_dans",
                    help="nombre max de dans par page (surcharge @dans_per_page)")
    ap.add_argument("--engine", choices=["auto", *ENGINES], default="auto",
                    help="moteur SVG->PDF (défaut : auto)")
    ap.add_argument("--merger", choices=["auto", *MERGERS], default="auto",
                    help="outil de fusion des pages PDF (défaut : auto)")
    ap.add_argument("--keep-temp", metavar="DIR",
                    help="conserve les SVG et PDF intermédiaires dans DIR")
    args = ap.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
        out_path = args.output or "output.pdf"
    else:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
        out_path = args.output or (args.input.rsplit(".", 1)[0] + ".pdf")

    try:
        layout, svgs = render_pages(text, layout=args.layout, cols=args.cols,
                                    page_dans=args.page_dans)
    except UnsupportedLayout as e:
        print(f"kkml2pdf: ERROR: {e}", file=sys.stderr)
        return 2
    print(f"layout {layout} : {len(svgs)} page(s) "
          f"({LAYOUTS_CM[layout][0]:g} x {LAYOUTS_CM[layout][1]:g} cm)",
          file=sys.stderr)

    try:
        engine = detect_engine(args.engine)
        merger = detect_merger(args.merger)
    except EngineUnavailable as e:
        print(f"kkml2pdf: ERROR: {e}", file=sys.stderr)
        return 1
    print(f"moteur SVG->PDF : {engine} ; fusion : {merger}", file=sys.stderr)

    try:
        produce_pdf(svgs, out_path, engine, merger,
                    workdir=args.keep_temp)
    except (RuntimeError, EngineUnavailable) as e:
        print(f"kkml2pdf: ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
