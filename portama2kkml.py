#!/usr/bin/env python3
"""Convertit un fichier JSON Portama (portama.com/kunkun4) en KKML.

Usage :
    python3 portama2kkml.py input.json [-o output.kkml]
    cat input.json | python3 portama2kkml.py - > output.kkml

Le format KKML produit est compatible avec le convertisseur kkml2kunkunshi.py.
"""

import json
import sys
import argparse

# ---------------------------------------------------------------------------
# Correspondance PUA → kanji (confirmée sur 3 fichiers Portama, tous 本調子)
# ---------------------------------------------------------------------------
PUA_TO_KANJI = {
    0xE000: "合",
    0xE001: "乙",
    0xE002: "老",
    0xE010: "四",
    0xE011: "上",
    0xE012: "中",
    0xE013: "尺",
    0xE020: "工",
    0xE021: "五",
    0xE022: "六",
    0xE023: "七",
    0xE024: "八",
    0xE030: "○",  # silence / repos
}

# Accordages Portama → KKML
CHOSHI_MAP = {
    "hon": "本調子",
    "ni": "二調子",
    "san": "三調子",
    # À compléter selon les fichiers futurs
}

def portama_title_to_kkml(title):
    """Convertit le titre Portama en titre KKML avec ruby.

    Portama encode la lecture en segments inline `base[lecture]`
    (ex. 十九[じゅうく]の春[はる]). Le KKML utilise le group-ruby
    `｛base｝《lecture》`.

    Règle : les segments annotés forment UN seul groupe couvrant du
    premier au dernier. Le texte interstitiel ENTRE deux segments
    annotés va dans la base ET dans la lecture (kana lu tel quel :
    十九[じゅうく]の春[はる] → ｛十九の春｝《じゅうくのはる》).
    Le texte AVANT le premier / APRÈS le dernier segment annoté reste
    hors groupe, en clair (国頭[くんじゃん]ジントヨー →
    ｛国頭｝《くんじゃん》ジントヨー). Un titre sans crochets est
    retourné tel quel."""
    import re, unicodedata
    matches = list(re.finditer(r"([^\[]*)\[([^\]]*)\]", title))
    if not matches:
        return title

    def _leading_kana(s):
        """Initial kana of a base (hiragana/katakana, including ー):
        particles such as の, read as-is, interstitial between two
        annotated segments. The kanji tail is the base covered by the
        following [reading]."""
        i = 0
        while i < len(s):
            c = s[i]
            if 0x3040 <= ord(c) <= 0x30FF or c == "ー":
                i += 1
            else:
                break
        return s[:i], s[i:]

    out = [title[:matches[0].start()]]
    group_base = ""
    reading = ""
    for k, m in enumerate(matches):
        base_k = m.group(1)
        reading_k = m.group(2)
        if k > 0:
            # The base of segment k can begin with interstitial kana
            # (ex. の in 十九[じゅうく]の春[はる]) : read as-is.
            kana, base_k = _leading_kana(base_k)
            group_base += kana
            reading += kana
        group_base += base_k
        reading += reading_k
    out.append(f"｛{group_base}｝《{reading}》")
    out.append(title[matches[-1].end():])
    return "".join(out)


# Ornements Portama → suffixes souhou KKML
# "u" et "k" confirmés par le corpus. Les autres restent des hypothèses.
ORN_TO_SUFFIX = {
    "u": "*",   # uchi-utu (打音) — confirmé (かぎやで風節, てぃんさぐぬ花)
    "k": "^",   # kaki-utu (掛音) — confirmé (十九の春 : 9 occurrences,
                # validées manuellement par l'utilisateur)
    # Hypothèses (non confirmées) :
    # "a": "v",  # aki-utu ?
    # "c": "<",  # kachi-utu ?
    # "t": "=",  # taachi ?
}


def pua_to_kanji(pua_char):
    """Convertit un caractère PUA Portama en kanji kunkunshi."""
    if not pua_char:
        return ""
    cp = ord(pua_char[0])
    return PUA_TO_KANJI.get(cp, "?")


def cell_to_note(cell, is_main):
    """Convertit une cellule Portama en token KKML (kanji + suffixes).

    Retourne None si la cellule est vide (pas de note).
    """
    note = cell.get("note", "")
    if not note:
        return None

    kanji = pua_to_kanji(note)
    if not kanji:
        return None

    # Dièse (accidental sharp) → 尺♯ (seulement pour 尺)
    if cell.get("acc") == "sharp" and kanji == "尺":
        kanji = "尺♯"

    # Ornements (souhou)
    orn = cell.get("orn", "")
    suffix = ORN_TO_SUFFIX.get(orn, "")

    # isSmall sur la note principale → kuubanchi (suffixe s)
    if is_main and cell.get("isSmall", False):
        suffix += "s"

    return kanji + suffix


def dan_to_tokens(dan):
    """Convertit un dan (tableau de 24 cellules) en liste de tokens KKML.

    Structure : 12 paires (main, straddle).
    - Main seule → noire : A
    - Main + straddle → croche : A/B  (si main isSmall=false)
    - Main + straddle, main isSmall → shuffle : A:B  (si main isSmall=true)
    - RepeatStart → préfixe |: sur le token
    - RepeatEnd → suffixe :| sur le token
    """
    tokens = []
    pairs = [(dan[i], dan[i + 1]) for i in range(0, len(dan) - 1, 2)]

    for main_cell, straddle_cell in pairs:
        main_note = cell_to_note(main_cell, is_main=True)
        straddle_note = cell_to_note(straddle_cell, is_main=False)

        prefix = ""
        suffix = ""

        if main_cell.get("repeatStart"):
            prefix = "|:"
        if main_cell.get("repeatEnd") or straddle_cell.get("repeatEnd"):
            suffix = ":|"

        if main_note is None:
            # Pas de note principale : case vide (ou juste repeat marker)
            if prefix or suffix:
                tokens.append(prefix + "-" + suffix)
            else:
                tokens.append("-")
            continue

        if straddle_note is not None:
            # Deux notes dans la paire
            if main_cell.get("isSmall", False):
                # Shuffle 早弾き (deux notes égales, petites)
                token = f"{prefix}{main_note}:{straddle_note}{suffix}"
            else:
                # Croche (main pleine taille + straddle petite)
                token = f"{prefix}{main_note}/{straddle_note}{suffix}"
        else:
            # Noire (note principale seule)
            token = f"{prefix}{main_note}{suffix}"

        tokens.append(token)

    return tokens


def convert_portama_to_kkml(data):
    """Convertit les données JSON Portama en texte KKML."""
    lines = []

    # Métadonnées
    title = data.get("title", "")
    if title:
        lines.append(f"@title {portama_title_to_kkml(title)}")

    choshi = data.get("choshi", "")
    tuning = CHOSHI_MAP.get(choshi, choshi)
    if tuning:
        lines.append(f"@tuning {tuning}")

    # Nombre de colonnes : cellsPerDan / 2 = nombre de notes par dan
    cells_per_dan = data.get("cellsPerDan", 24)
    notes_per_dan = cells_per_dan // 2
    if notes_per_dan:
        lines.append(f"@cols {notes_per_dan}")

    # Marqueur activé par défaut dans Portama
    lines.append("@marker on")

    lines.append("")
    lines.append("::tab")

    score = data.get("score", [])
    for dan in score:
        tokens = dan_to_tokens(dan)
        lines.append(" ".join(tokens))

    lines.append("::")

    # Paroles (si présentes et non vide)
    lyrics_data = data.get("allLyricsData", {})
    has_lyrics = False
    for page_key, frames in lyrics_data.items():
        for frame in frames:
            content = frame.get("content", "").strip()
            if content and content != "歌詞を入力":
                has_lyrics = True
                lines.append("")
                lines.append("::lyrics")
                lines.append(content)
                lines.append("::")
                break
        if has_lyrics:
            break

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Convertit un fichier JSON Portama en KKML"
    )
    parser.add_argument("input", help="Fichier JSON Portama (ou - pour stdin)")
    parser.add_argument("-o", "--output", help="Fichier KKML de sortie (défaut: stdout)")
    args = parser.parse_args()

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

    kkml = convert_portama_to_kkml(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(kkml)
    else:
        sys.stdout.write(kkml)


if __name__ == "__main__":
    main()
