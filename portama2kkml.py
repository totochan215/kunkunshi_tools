#!/usr/bin/env python3
"""Convertit un fichier JSON Portama (portama.com/kunkun4) en KKML.

Usage :
    python3 portama2kkml.py input.json [-o output.kkml]
    cat input.json | python3 portama2kkml.py - > output.kkml

Le format KKML produit est compatible avec le convertisseur kkml2svg.py.
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
    0xE003: "下老",      # 下老 (composite)
    0xE004: "ロ上",      # ロ上 (composite)
    0xE005: "ロ中",      # ロ中 (composite)
    0xE006: "ロ尺",      # ロ尺 (composite)
    0xE007: "イ合",      # イ合 (composite)
    0xE008: "イ乙",      # イ乙 (composite)
    0xE010: "四",
    0xE011: "上",
    0xE012: "中",
    0xE013: "尺",
    0xE014: "下尺",      # 下尺 (composite, encerclé au rendu)
    0xE015: "ロ五",      # ロ五 (composite)
    0xE016: "イ老",      # イ老 (composite)
    0xE017: "イ四",      # イ四 (composite)
    0xE018: "イ上",      # イ上 (composite)
    0xE020: "工",
    0xE021: "五",
    0xE022: "六",
    0xE023: "七",
    0xE024: "八",
    0xE025: "九",
    0xE026: "イ尺",      # イ尺 (composite)
    0xE027: "イ工",      # イ工 (composite)
    0xE028: "イ五",      # イ五 (composite)
    0xE030: "○",            # silence (repos) — normalisé en ◯ par kkml2svg
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
    "u": "'",   # uchi-utu (打音) — confirmé (かぎやで風節, てぃんさぐぬ花)
    "k": "^",   # kaki-utu (掛音) — confirmé (十九の春 : 9 occurrences,
                # validées manuellement par l'utilisateur)
    "nu": '"',  # nuchi-utu = uchi-nuchi-utu (打ち抜き音, PUA U+E033)
                # suffixe `"` (U+0022), jumeau de `'` (uchi-utu) ; `n` exclu (collision romaji)
    # Hypothèses (non confirmées) :
    # "a": "v",  # aki-utu ?
    # "c": "<",  # kachi-utu ?
    # "t": "=",  # taachi ?
}


# Doigtés (yubii) Portama -> suffixes KKML ㊀-㊃ (U+3280-U+3283, suffixe de
# note dans ::tab, ex. 合㊀). cell.yubii = 1-4 ; les PUA U+E041-E044 peuvent
# aussi apparaître comme `note` (yubii encodé directement dans la position).
YUBII_INT_TO_SUFFIX = {1: '㊀', 2: '㊁', 3: '㊂', 4: '㊃'}
YUBII_PUA_TO_SUFFIX = {0xE041: '㊀', 0xE042: '㊁', 0xE043: '㊂', 0xE044: '㊃'}


def pua_to_kanji(pua_char):
    """Convertit un caractère PUA Portama en kanji kunkunshi."""
    if not pua_char:
        return ""
    cp = ord(pua_char[0])
    return PUA_TO_KANJI.get(cp, "?")


def cell_to_note(cell, is_main):
    """Convertit une cellule Portama en token KKML (kanji + suffixes).

    Retourne (token, yubii) : token None si la cellule est vide (pas de note),
    yubii = suffixe ㊀-㊃ (U+3280-U+3283) si la cellule porte un doigté
    (champ `yubii`, ou note PUA U+E041-E044).
    """
    note = cell.get("note", "")
    yubii = YUBII_INT_TO_SUFFIX.get(cell.get("yubii", 0), "")
    if not note:
        return None, yubii

    if note and ord(note[0]) in YUBII_PUA_TO_SUFFIX:
        # yubii encodé comme note PUA : pas de note de base, juste le doigté
        return None, YUBII_PUA_TO_SUFFIX[ord(note[0])] or yubii

    kanji = pua_to_kanji(note)
    if not kanji:
        return None, yubii

    # Altération (acc) : sharp sur 尺 → 尺♯ (cas spécial @shaku_sharp) ;
    # sinon ♯/♭ en suffixe sur n'importe quelle note (ex. 合♯, 合♭).
    acc = cell.get("acc", "")
    if acc == "sharp" and kanji == "尺":
        kanji = "尺♯"
    acc_suffix = ""
    if acc in ("sharp", "flat") and kanji != "尺♯":
        acc_suffix = "♯" if acc == "sharp" else "♭"

    # Ornements (souhou)
    orn = cell.get("orn", "")
    suffix = acc_suffix + ORN_TO_SUFFIX.get(orn, "")

    # isSmall sur la note principale → kuubanchi (suffixe s)
    if is_main and cell.get("isSmall", False):
        suffix += "s"

    return kanji + suffix, yubii


def dan_to_tokens(dan):
    """Convertit un dan (tableau de cellules) en liste de tokens KKML.

    Structure : paires (main, straddle) — index pair = note principale,
    index impair = note à cheval. Une cellule terminale isolée (dan de
    longueur impaire) est traitée comme une note principale seule.
    - Main seule → noire : A
    - Main + straddle → croche : A/B  (si main isSmall=false)
    - Main + straddle, main isSmall → shuffle : A:B  (si main isSmall=true)
    - Main vide + straddle → note à cheval seule : -/B
    - Main vide + straddle vide → case vide : -
    - repeatStart → préfixe |: ; repeatEnd → suffixe :|
    - vocalRepStart → préfixe (: ; vocalRepEnd → suffixe :)
    """
    tokens = []
    n = len(dan)
    pairs = [(dan[i], dan[i + 1] if i + 1 < n else {}) for i in range(0, n, 2)]

    for main_cell, straddle_cell in pairs:
        main_note, main_yubii = cell_to_note(main_cell, is_main=True)
        straddle_note, straddle_yubii = cell_to_note(straddle_cell, is_main=False)
        # Un seul doigté par case KKML : priorité à la note principale.
        yubii = main_yubii or straddle_yubii

        # `(:` doit précéder `|:` (désambiguation au parsing de ::tab).
        prefix = ""
        if main_cell.get("vocalRepStart") or straddle_cell.get("vocalRepStart"):
            prefix += "(:"
        if main_cell.get("repeatStart") or straddle_cell.get("repeatStart"):
            prefix += "|:"
        suffix = ""
        if main_cell.get("vocalRepEnd") or straddle_cell.get("vocalRepEnd"):
            suffix += ":)"
        if main_cell.get("repeatEnd") or straddle_cell.get("repeatEnd"):
            suffix += ":|"

        if main_note is None and straddle_note is None:
            # Case vide (éventuellement avec marqueurs de boucle)
            tokens.append(f"{prefix}-{suffix}{yubii}")
        elif main_note is None:
            # Note à cheval seule (main vide) : -/B
            tokens.append(f"{prefix}-/{straddle_note}{suffix}{yubii}")
        elif straddle_note is not None:
            # Deux notes dans la paire
            if main_cell.get("isSmall", False):
                # Shuffle 早弾き (deux notes égales, petites)
                tokens.append(f"{prefix}{main_note}:{straddle_note}{suffix}{yubii}")
            else:
                # Croche (main pleine taille + straddle petite)
                tokens.append(f"{prefix}{main_note}/{straddle_note}{suffix}{yubii}")
        else:
            # Noire (note principale seule)
            tokens.append(f"{prefix}{main_note}{suffix}{yubii}")

    return tokens


# Marqueurs vocaux Portama (vocalPosMarkers) → tokens de la section ::vocal.
# Seuls les marqueurs d'une cellule à cheval (isSmall) sont encodés, à la
# position de la paire dans la ligne ::vocal : mid + vocalStart → ".(" ,
# mid + vocalEnd → ".)" (le point = hauteur milieu de la case). Les marqueurs
# des cellules principales et les positions top/bottom ne sont pas supportés
# (journalisés et ignorés).
VOCAL_POS_MARKER_TOKEN = {
    "mid": {"vocalStart": ".(", "vocalEnd": ".)"},
}


def _info(msg):
    print(f"portama2kkml: {msg}", file=sys.stderr)


def dan_to_vocal(dan):
    """Ligne ::vocal associée à un dan : un token par paire (comme ::tab),
    `-` par défaut. Voir VOCAL_POS_MARKER_TOKEN pour les marqueurs encodés."""
    line = []
    n = len(dan)
    for i in range(0, n, 2):
        main_cell = dan[i]
        small_cell = dan[i + 1] if i + 1 < n else {}
        tok = "-"
        vpm = small_cell.get("vocalPosMarkers") or {}
        for pos, kind in vpm.items():
            tok2 = VOCAL_POS_MARKER_TOKEN.get(pos, {}).get(kind, "")
            if tok2:
                tok = tok2
            elif kind:
                _info(f"vocalPosMarkers pos={pos!r} kind={kind!r} non supporté (ignoré)")
        if main_cell.get("vocalPosMarkers"):
            _info("vocalPosMarkers sur cellule principale ignoré "
                  "(seules les cellules à cheval isSmall sont encodées dans ::vocal)")
        line.append(tok)
    return line


# Métadonnées de compatibilité Portama : clé KKML -> champ JSON Portama.
# Les valeurs sont des chaînes côté JSON (sauf musicno, entier) et sont
# stockées telles quelles dans KKML, pour permettre le round-trip.
META_TO_PORTAMA_FIELD = {
    "musicno": "musicno",
    "chogen": "chogen",
    "speed": "speed",
    "rythm": "rhythm",
    "rythm_mode": "rhythmMode",
}


def portama_fields_from_meta(meta):
    """Sens inverse (kkml2portama) : reconstruit les champs Portama depuis les
    métadonnées KKML. -> dict {champ Portama: valeur typée}."""
    out = {}
    for key, field in META_TO_PORTAMA_FIELD.items():
        val = meta.get(key, "")
        if val == "":
            continue
        if field == "musicno":
            try:
                out[field] = int(val)
                continue
            except ValueError:
                pass  # valeur non entière : on garde la chaîne brute
        out[field] = val
    return out


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
        lines.append(f"@cells_per_dan {notes_per_dan}")

    # Marqueur activé par défaut dans Portama
    lines.append("@marker on")

    # Métadonnées de compatibilité Portama, émises telles quelles quand le
    # champ est présent dans le JSON (présence/absence préservée pour le
    # round-trip ; ordre = ordre canonique du cleaner).
    for key, field in META_TO_PORTAMA_FIELD.items():
        if field in data and data[field] not in (None, ""):
            lines.append(f"@{key} {data[field]}")

    lines.append("")
    lines.append("::tab")

    score = data.get("score", [])
    for dan in score:
        tokens = dan_to_tokens(dan)
        lines.append(" ".join(tokens))

    lines.append("::")

    # Section ::vocal : une ligne par dan, un token par paire (comme ::tab),
    # émise dès qu'un marqueur vocal est présent.
    vocal_lines = [dan_to_vocal(dan) for dan in score]
    if any(any(t != "-" for t in line) for line in vocal_lines):
        lines.append("")
        lines.append("::vocal")
        for line in vocal_lines:
            lines.append(" ".join(line))
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
