#!/usr/bin/env python3
"""kkml_beautify.py — aligne les débuts de cellules dans ::tab et ::vocal.

Usage :
    python3 kkml_beautify.py morceau.kkml            # réécrit le fichier en place
    python3 kkml_beautify.py -n morceau.kkml         # mode test : affiche sur stdout
    python3 kkml_beautify.py -n -o beau.kkml m.kkml

Dans les sections `::tab` et `::vocal`, les tokens sont d'abord normalisés
(comme kkml_clean), puis complétés d'espaces simples pour que les débuts
de chaque cellule soient alignés en colonnes — à condition que l'éditeur
ouvre le fichier avec une police à chasse fixe (les caractères CJK pleine
chasse comptent double, les combinants comptent 0). Le dernier token d'une
ligne n'est pas complété (pas d'espace en fin de ligne). Un straddle de tête
`/B` (1er token de la 1re ligne de `::tab`) sort de la grille d'alignement :
émis tel quel + 1 espace, les colonnes sont calculées sur la note suivante.
Partout ailleurs, le fichier est inchangé.
Idempotent : `beautify(beautify(x)) == beautify(x)`.
"""

import argparse
import contextlib
import io
import re
import sys
import unicodedata

import kkml_clean as c

# sections alignées : ::tab/::vocal + alias tolérés (::tabs/::vocals, rectifiés
# par le cleaner) — l'en-tête est émis tel quel, seul le corps est aligné
SECTION_RE = re.compile(r"^::(tabs?|vocals?)(?:\s|$)")
TAB_KINDS = ("tab", "tabs")


def disp_width(s):
    """Largeur d'affichage en chasse fixe : CJK pleine chasse = 2,
    caractère combinant = 0, sinon 1."""
    return sum(0 if unicodedata.combining(ch)
               else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
               for ch in s)


def beautify_body(body, normalize, is_tab=False):
    """Normalise puis aligne les tokens d'un bloc ::tab/::vocal (lignes brutes)."""
    norm = []
    with contextlib.redirect_stderr(io.StringIO()):   # normalisation silencieuse
        for ln in body:
            norm.append(normalize(ln.split()) if ln.strip() else [])
    # Straddle de tête '/B' (1er token de la 1re ligne d'un bloc ::tab) : sorti
    # de la grille d'alignement et émis tel quel + 1 espace — les colonnes sont
    # calculées sur les notes (le token suivant), pas sur le '/B'.
    lead = None
    if is_tab and norm and norm[0] and norm[0][0].startswith("/"):
        lead = norm[0].pop(0)
    col_w = []
    for toks in norm:
        for j, tk in enumerate(toks):
            w = disp_width(tk)
            if j >= len(col_w):
                col_w.append(w)
            elif w > col_w[j]:
                col_w[j] = w
    out = []
    for idx, toks in enumerate(norm):
        if not toks:
            out.append("")
            continue
        parts = []
        last = len(toks) - 1
        for j, tk in enumerate(toks):
            if j < last:
                parts.append(tk + " " * (col_w[j] - disp_width(tk) + 1))
            else:
                parts.append(tk)          # pas d'espace en fin de ligne
        line = "".join(parts)
        if idx == 0 and lead is not None:
            line = lead + " " + line
        out.append(line)
    return out


def beautify(text):
    """Retourne le KKML beautifié (str)."""
    lines = text.splitlines()
    out = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        m = SECTION_RE.match(ln)
        if m:
            kind = m.group(1)
            out.append(ln)
            i += 1
            body = []
            # le corps s'arrête à TOUTE ligne '::...' (fermeture '::' ou
            # prochain en-tête de section) — reprise par la boucle externe
            while i < n and not lines[i].startswith("::"):
                body.append(lines[i])
                i += 1
            is_tab = kind in TAB_KINDS
            normalize = c.normalize_tab_line if is_tab else c.normalize_vocal_line
            out.extend(beautify_body(body, normalize, is_tab=is_tab))
        else:
            out.append(ln)
            i += 1
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def main():
    ap = argparse.ArgumentParser(
        description="Aligne les débuts de cellules dans ::tab/::vocal (chasse fixe). "
                    "Idempotent.")
    ap.add_argument("input", help="fichier KKML d'entrée")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="mode test : affiche le résultat sans écraser l'original")
    ap.add_argument("-o", "--output", help="fichier de sortie (avec -n, ou à la place de l'entrée)")
    args = ap.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"kkml_beautify: ERROR: lecture impossible : {e}", file=sys.stderr)
        sys.exit(1)

    result = beautify(text)

    if args.dry_run:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"kkml_beautify: INFO: résultat écrit dans {args.output} (original intact)",
                  file=sys.stderr)
        else:
            sys.stdout.write(result)
    else:
        target = args.output or args.input
        with open(target, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"kkml_beautify: INFO: fichier beautifié : {target}", file=sys.stderr)


if __name__ == "__main__":
    main()
