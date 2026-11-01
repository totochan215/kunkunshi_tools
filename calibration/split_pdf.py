#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Split un PDF en pages individuelles (outil de calibrage, hors pipeline).

Usage :
    python3 calibration/split_pdf.py RECUEIL.pdf SORTIE/ [-f FIRST] [-t LAST] [-p PREFIX]

Produit dans SORTIE/ :
    <PREFIX>-pNNN.pdf   une page par fichier, N = numéro de page PDF (1-based, %03d)
    <PREFIX>-manifest.json   manifeste : page_pdf, fichier, taille, (page_imprimée à remplir)

Dépendance : pip install pypdf   (script perso, pas dans le pipeline du dépôt)

Convention : déposer le PDF complet dans le dossier Drive idoine (voir
calibration/README.md), lancer ce script en local, puis uploader les pages
splittées dans le même dossier Drive. Les pages d'index seront ensuite
OCRisées séparément (indiquer les numéros de page PDF concernés).
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Split PDF -> 1 fichier par page")
    ap.add_argument("pdf", help="PDF complet en entrée")
    ap.add_argument("sortie", help="dossier de sortie (créé si absent)")
    ap.add_argument("-f", "--first", type=int, default=1, help="première page PDF (1-based)")
    ap.add_argument("-t", "--last", type=int, default=None, help="dernière page PDF (incluse)")
    ap.add_argument("-p", "--prefix", default=None, help="préfixe de sortie (défaut: nom du PDF)")
    args = ap.parse_args()

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        sys.exit("pip install pypdf  (script perso, hors pipeline)")

    src = Path(args.pdf)
    out_dir = Path(args.sortie)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or src.stem

    reader = PdfReader(str(src))
    n = len(reader.pages)
    last = args.last or n
    manifest = {"document": src.name, "nb_pages_pdf": n,
                "split_first": args.first, "split_last": last, "pages": []}
    for i in range(args.first - 1, min(last, n)):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        fname = f"{prefix}-p{i + 1:03d}.pdf"
        fpath = out_dir / fname
        with open(fpath, "wb") as f:
            writer.write(f)
        manifest["pages"].append({
            "page_pdf": i + 1,
            "fichier": fname,
            "taille_octets": fpath.stat().st_size,
            "page_imprimee": None,   # à corriger manuellement (peut différer de page_pdf)
        })
        print(f"p{i + 1:03d} -> {fname}  ({fpath.stat().st_size} o)")
    mpath = out_dir / f"{prefix}-manifest.json"
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"manifeste: {mpath}  ({len(manifest['pages'])} pages)")


if __name__ == "__main__":
    main()
