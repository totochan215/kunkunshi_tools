#!/usr/bin/env python3
"""kkml_cleaner.py — normalise un fichier KKML vers sa forme canonique.

Usage :
    python3 kkml_cleaner.py morceau.kkml            # réécrit le fichier en place
    python3 kkml_cleaner.py -n morceau.kkml         # mode test : affiche sur stdout
    python3 kkml_cleaner.py -n -o nettoyé.kkml m.kkml

Règles (voir AGENTS.md, section « Long terme ») :
- normalisation des formes : pleine chasse → demi-largeur, romaji/chiffres →
  kanji kandokoro, kanji composites → katakana+kanji, repos → ◯,
  `::tab-lyrics`/`::tab-vocals` → `::vocal` ;
- ordre des sections : `::tab` `::vocal` `::lyrics` ;
- métadonnées : toutes regroupées en haut du fichier ; `@format` `@version`
  `@title` toujours en premier (si présents), puis les autres métadonnées
  présentes dans leur ordre d'apparition dans le fichier ; `@format KKML`
  est ajouté s'il est absent ;
- séparateurs : une et une seule ligne vide entre le bloc des métadonnées et
  la première section, et entre chaque section (aucune ligne vide en tête
  si pas de métadonnées, aucune en fin de fichier) ;
- complétion structurelle : `::vocal` manquante créée (cases vides alignées),
  `::vocal` désalignée réalignée si le total boucle (sinon avertissement),
  `::lyrics` manquante créée vide, `::tab` implicite rendue explicite,
  `::tab` manquante créée vide ;
- `@cells_per_dan n` présent → repli de `::tab` à n cellules/ligne puis
  alignement de `::vocal` dessus ; absent → sauts de ligne conservés
  (`@cols` = ancien nom, renommé avec une info) ;
- idempotent : cleaner(cleaner(x)) == cleaner(x).

Diagnostics sur stderr : info (normalisation appliquée), avertissement
(rééalignement refusé…), erreur fatale (KKML illisible, exit 1).
"""

import argparse
import re
import sys

import kkml2svg as k


def info(msg):
    print(f"kkml_cleaner: info: {msg}", file=sys.stderr)


def warn(msg):
    print(f"kkml_cleaner: AVERTISSEMENT: {msg}", file=sys.stderr)


def die(msg):
    print(f"kkml_cleaner: ERREUR: {msg}", file=sys.stderr)
    sys.exit(1)


def normalize_tab_line(tokens):
    """Normalise une ligne de ::tab (liste de tokens) vers la forme canonique."""
    out = []
    for tk in tokens:
        if tk in k.EMPTY_INPUT_VARIANTS:
            info(f"'{tk}' normalisé en '{k.EMPTY_TOKEN}' (case vide)")
            out.append(k.EMPTY_TOKEN)
            continue
        tk2, changed = k._normalize_tab_token(tk)
        if changed:
            info(f"'{tk}' normalisé en '{tk2}'")
        out.append(tk2)
    return [k.REST_TOKEN if tk in k.REST_VARIANTS else tk for tk in out]


def normalize_vocal_line(tokens):
    out = []
    for tk in tokens:
        if tk in k.EMPTY_INPUT_VARIANTS:
            info(f"'{tk}' normalisé en '{k.EMPTY_TOKEN}' (case vide, ::vocal)")
            out.append(k.EMPTY_TOKEN)
        else:
            out.append(tk)
    return out


def reflow_lines(flat_tokens, per_line):
    """Replie un flux de tokens en lignes de `per_line` tokens (dernier dan partiel)."""
    return [flat_tokens[i:i + per_line] for i in range(0, len(flat_tokens), per_line)]


def clean(text):
    """Retourne le KKML nettoyé (str). Lève ValueError si illisible."""
    if not text.strip():
        die("fichier vide")
    try:
        song = k.parse_kkml(text)
    except Exception as e:
        die(f"KKML malformé, illisible par le parser : {e}")

    # --- métadonnées : toutes regroupées en haut ; @format/@version/@title
    # toujours en premier (si présents), puis les autres présentes dans leur
    # ordre d'apparition dans le fichier. Dédup : première occurrence prime. ---
    meta = {}
    for key, val in song.meta.items():
        if key not in meta:
            meta[key] = val
    # ordre d'apparition des clés @ dans le fichier (mêmes normalisations que
    # le parser : préfixe connu collé, @cols/@page_dans renommés)
    file_keys = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("::"):
            continue
        m = re.match(r"@(\S+)\s*(.*)", s)
        if not m:
            continue
        key = m.group(1)
        if key not in k.META_KEYS and len(key) > 1:
            for mk in sorted(k.META_KEYS, key=len, reverse=True):
                if key.startswith(mk) and len(key) > len(mk):
                    key = mk
                    break
        if key == "cols":
            key = "cells_per_dan"
        elif key == "page_dans":
            key = "dans_per_page"
        if key not in file_keys:
            file_keys.append(key)
    # @cells_per_dan est ignoré par le parser de kkml2svg (indication de mise
    # en page) : le relire dans le texte source (@cols = ancien nom, renommé).
    mcols = re.search(r"^\s*@(cells_per_dan|cols)\s+(\S+)", text, re.M)
    if mcols:
        key, val = mcols.group(1), mcols.group(2)
        if key == "cols":
            info("@cols renommé en @cells_per_dan")
            key = "cells_per_dan"
        meta.setdefault(key, val)
    # @layout / @dans_per_page lus hors song.meta (@page_dans = ancien nom)
    if getattr(song, "page_dans", None) is not None:
        meta.setdefault("dans_per_page", str(song.page_dans))
    if "layout" in file_keys:
        meta.setdefault("layout", song.layout)
    # @format KKML ajouté s'il est absent (épinglé en première ligne ensuite)
    if "format" not in meta:
        info("@format KKML ajouté (absent du fichier)")
        meta["format"] = "KKML"
        if "format" not in file_keys:
            file_keys.insert(0, "format")

    # --- sections : normalisation + complétion structurelle ---
    blocks = song.blocks
    tab_blks = [b for b in blocks if b.kind == "tab"]
    vocal_blks = [b for b in blocks if b.kind == "vocal"]
    lyrics_blks = [b for b in blocks if b.kind == "lyrics"]

    # 1. ::tab implicite -> explicite : parse_kkml crée déjà un Block("tab")
    #    implicite ; rien à faire ici si saw_marker, sinon info.
    if tab_blks and "::tab" not in text and "::section" not in text and "::song" not in text:
        info("section ::tab implicite rendue explicite")

    # 2. ::tab manquante -> créée vide
    if not tab_blks:
        info("section ::tab manquante, créée vide")
        tab_blks = [k.Block("tab", None)]

    # normaliser le contenu de ::tab (lignes de tokens)
    for b in tab_blks:
        b.lines = [normalize_tab_line(ln) for ln in b.lines]

    # 3. repli selon @cells_per_dan si présent
    cols = None
    if "cells_per_dan" in meta:
        try:
            cols = int(meta["cells_per_dan"])
        except ValueError:
            warn(f"@cells_per_dan non entier ({meta['cells_per_dan']!r}), ignoré")
    if cols and cols > 0:
        for b in tab_blks:
            flat = [tk for ln in b.lines for tk in ln]
            new_lines = reflow_lines(flat, cols)
            if len(new_lines) != len(b.lines) or any(
                    new_lines[i] != b.lines[i] for i in range(min(len(new_lines), len(b.lines)))):
                info(f"::tab replié à {cols} cellules/ligne (@cells_per_dan)")
            b.lines = new_lines

    # 4. ::vocal : manquante -> créée alignée ; désalignée -> réalignée si boucle.
    #    Le ::vocal brut est aplati (comme dans kkml2svg) pour comparer les
    #    totaux, puis replié selon la structure des lignes de ::tab.
    def vocal_flat(blines):
        return [tk for ln in blines for tk in ln]

    if not vocal_blks:
        info("section ::vocal manquante, créée avec cases vides alignées sur ::tab")
        v = k.Block("vocal", None)
        for b in tab_blks[:1]:
            v.lines = [[k.EMPTY_TOKEN] * len(ln) for ln in b.lines]
        vocal_blks = [v]
    else:
        v = vocal_blks[0]
        v.lines = [normalize_vocal_line(ln) for ln in v.lines]
        if tab_blks:
            tab = tab_blks[0]
            tab_shapes = [len(ln) for ln in tab.lines]
            tab_total = sum(tab_shapes)
            voc_total = len(vocal_flat(v.lines))
            voc_shapes = [len(ln) for ln in v.lines]
            if voc_total == tab_total and voc_shapes != tab_shapes:
                flat = vocal_flat(v.lines)
                v.lines = []
                pos = 0
                for n in tab_shapes:
                    v.lines.append(flat[pos:pos + n])
                    pos += n
                info("::vocal réalignée ligne à ligne sur ::tab")
            elif voc_total != tab_total:
                warn(f"::vocal désalignée de ::tab ({voc_total} vs {tab_total} cellules) : PAS de réalignement")

    # 5. ::lyrics manquante -> créée vide
    if not lyrics_blks:
        info("section ::lyrics manquante, créée vide")
        lyrics_blks = [k.Block("lyrics", None)]

    # --- réassemblage dans l'ordre canonique : tab, vocal, lyrics, puis le reste ---
    ordered = tab_blks + vocal_blks + lyrics_blks
    seen = {id(b) for b in ordered}
    for b in blocks:
        if id(b) not in seen:
            ordered.append(b)

    out = []
    head_keys = ("format", "version", "title")
    ordered_keys = ([kk for kk in head_keys if kk in file_keys]
                    + [kk for kk in file_keys if kk not in head_keys])
    for key in ordered_keys:
        if key in meta:
            out.append(f"@{key} {meta[key]}")
    for key, val in meta.items():  # sécurité : clés non vues au scan raw
        if key not in file_keys:
            out.append(f"@{key} {val}")
    # une et une seule ligne vide entre le bloc des métadonnées et la première
    # section (et aucune ligne vide en tête si pas de métadonnées), puis une
    # seule ligne vide entre chaque section
    if out and ordered:
        out.append("")
    for b in ordered:
        head = "::" + b.kind + (f" {b.label}" if b.label else "")
        out.append(head)
        lines = b.lines
        if getattr(b, "leading_straddle", None):
            # straddle de tête '/B' : réémis en tout premier token du bloc
            lead_tok = "/" + b.leading_straddle
            if lines:
                lines = [[lead_tok] + list(lines[0])] + list(lines[1:])
            else:
                lines = [[lead_tok]]
        for ln in lines:
            if isinstance(ln, list):
                out.append(" ".join(ln))
            else:
                out.append(ln)
        out.append("::")
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Normalise un fichier KKML vers sa forme canonique (idempotent).")
    ap.add_argument("input", help="fichier KKML d'entrée")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="mode test : affiche le résultat sans écraser l'original")
    ap.add_argument("-o", "--output", help="fichier de sortie (avec -n, ou à la place de l'entrée)")
    args = ap.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die(f"lecture impossible : {e}")

    cleaned = clean(text)

    if args.dry_run:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(cleaned)
            info(f"résultat écrit dans {args.output} (original intact)")
        else:
            sys.stdout.write(cleaned)
    else:
        target = args.output or args.input
        with open(target, "w", encoding="utf-8") as f:
            f.write(cleaned)
        info(f"fichier nettoyé : {target}")


if __name__ == "__main__":
    main()
