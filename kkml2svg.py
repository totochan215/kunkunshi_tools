# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
kkml2svg.py — Convertit un fichier KKML (Kunkunshi Markup Language)
en une tablature 工工四 au format SVG.

Usage:
    python3 kkml2svg.py chanson.kkml -o chanson.svg
    python3 kkml2svg.py chanson.kkml            # -> chanson.svg (même nom)
    cat chanson.kkml | python3 kkml2svg.py -     # depuis stdin -> stdout

Layout vertical (défaut) : les cases se lisent de haut en bas et de
droite à gauche, comme dans les kunkunshi traditionnels.
Layout horizontal : gauche à droite, haut en bas (style songbook).

Métadonnée @layout vertical|horizontal dans le .kkml, ou -l/--layout en CLI.

Options supplémentaires en-tête KKML (défauts : @layout vertical,
@marker on, @font_style mincho, @shaku_circled on, @shaku_sharp on) :
    @marker off           → masque la colonne marker (défaut: on)
    @font_style serif|gothic|mincho → style de police (défaut: mincho)
    @shaku_circled off    → 尺 rendus sans cercle (défaut: on, entourés)
    @shaku_sharp off      → masque les ♯ des 尺♯ (défaut: on, ♯ visibles)
    @author Nom          → auteur (défaut: vide)
    @end_circle off      → désactive le marqueur de fin de chanson (cercle creux)
                           dans la colonne marker, au bas de la dernière case remplie
                           (défaut: on)
    @lyrics_size small|medium|big → taille de police des couplets
                           (small=50%, medium=75%, big=100% de la taille des kanjis)

Ruby (guide phonétique) dans @title et ::lyrics :
    Mono-ruby  : 安《あ》            — dernier caractère avant 《》
    Group-ruby : ｛安里屋｝《あさとや》 — ｛｝ délimite le groupe de base
    Jukugo     : ｛安《あ》里《さ》｝  — groupe avec annotations individuelles
    Taille ruby = 50% de la base. À droite en vertical, au-dessus en horizontal.
"""
import sys
import re
import argparse

# --------------------------------------------------------------------------- #
# 1. Définition des caractères de position reconnus
# --------------------------------------------------------------------------- #
# 14 positions de base (ordre croissant, 本調子) : 合乙老 (corde grave),
# 四上中尺 (corde moyenne), 工五六七八九十 (corde aiguë).
# 下 n'est PAS une position autonome : préfixe de demi-ton (下老, 下尺),
# au même titre que イ/ロ (octave/corde). Exception : 下八, kandokoro à part
# entière (女絃, 無名指, octave de 中 — traité 野村流, 増訂琉球音樂樂典 p. 14),
# rendu condensé comme 下老. 三力土一二 retirés le 16 sept. 2026 :
# noms de notes gongche (工尺譜), jamais attestés comme positions de sanshin.
POSITION_CHARS = set("合乙老下四上中尺工五六七八九十")
SPECIAL_CHARS = set("○〇▲Ⓡ□×◯・#")
# Échelle du ruby par rapport à la taille de base (paramètre interne,
# non exposé comme en-tête KKML : @ruby_size volontairement absent pour le moment)
RUBY_SCALE = 0.5
EMPTY_TOKEN = "-"
SUSTAIN_TOKEN = "."
REST_TOKEN = "◯"
REST_VARIANTS = {"◯", "○", "〇", "O", "o", "0"}
REPEAT_START = "|:"
REPEAT_END = ":|"

# Normalisation d'entrée pleine chasse (IME japonais) — blocs tab/tab-lyrics.
# Objectif : un fichier tapé avec une méthode de saisie japonaise (pleine
# chasse) reste valide. Les équivalents pleine chasse des séparateurs et
# suffixes ASCII sont convertis vers la forme canonique au parsing.
# NB : ー (chōonpu) n'est converti en - (case vide) QUE dans les blocs de
# tablature — dans ::vocal / ::lyrics il reste une voyelle longue légitime.
FULLWIDTH_MAP = {
    '／': '/',    # croches, accords
    '：': ':',    # shuffle
    '｜': '|',    # marques de répétition, séparateur tab-lyrics
    '＃': '♯',    # 尺＃ → 尺♯
    '#':  '♯',
    '＋': '+',    # accords (variante +)
    '＊': '*',
    '＾': '^',
    '＜': '<',
    '＝': '=',
    '（': '(',    # 声だし
    '）': ')',    # 声切り
}

# Variantes de saisie de la case vide : uniquement en token ISOLÉ.
# ー/ｰ/－ collé à un kanji (ex. 中ー) reste un token non reconnu (le chōonpu
# est une voyelle longue légitime ailleurs, on ne devine pas l'intention).
EMPTY_INPUT_VARIANTS = {'ー', 'ｰ', '－'}


def _normalize_tab_token(tok):
    """Convertit les variantes pleine chasse d'un token de tablature vers
    la forme canonique. Renvoie (token, a_été_modifié)."""
    out = ''.join(FULLWIDTH_MAP.get(ch, ch) for ch in tok)
    return out, out != tok

# Suffixes de technique (souhou) — apposés après le caractère de position
TECHNIQUE_SUFFIXES = {
    '*': {'name': 'uchi-utu',  'type': 'char',   'symbol': '｀', 'pos': 'top-right',
          'dx': 0.50, 'dy': 0.05, 'scale': 1.1},
    '^': {'name': 'kaki-utu',  'type': 'char',   'symbol': '┗', 'pos': 'top-right',
          'rotate': 180, 'scale': 0.75, 'dx': 0.85, 'dy': -1.20},
    'v': {'name': 'aki-utu',   'type': 'char',   'symbol': 'V',  'pos': 'bottom-left',
          'dx': 0.45, 'dy': 0.15},
    '<': {'name': 'kachi-utu', 'type': 'char',   'symbol': '┗', 'pos': 'bottom-left',
          'dx': 0.45, 'dy': 0.15},
    's': {'name': 'kuubanchi', 'type': 'small'},
    '=': {'name': 'taachi',    'type': 'line',   'pos': 'right'},
    # 声だし/声切り (koe-dashi / koe-kiri) : bornes de chant ○/□ pour le
    # chanteur (respirations). D'après 世禮 (増訂琉球音樂樂典 p. 9 et 26) :
    # à l'intérieur de la case, côté droit — pas dans la colonne marker.
    # Syntaxe mnémotechnique : ( = on commence à chanter, ) = on s'arrête.
    '(': {'name': 'koe-dashi (声だし)', 'type': 'char', 'symbol': '○',
          'pos': 'inside-right', 'dx': 0.30, 'dy': 0.35, 'scale': 0.55},
    ')': {'name': 'koe-kiri (声切り)',   'type': 'char', 'symbol': '□',
          'pos': 'inside-right', 'dx': 0.30, 'dy': 0.35, 'scale': 0.55},
}
# Positions hautes (préfixes イ / ロ)
#   イ  = 人偏 (亻) — 1 octave au-dessus du kanji de droite
#   ロ  = 口偏 (口) — même hauteur que le kanji de droite, autre corde
# Rendu : préfixe + kanji condensés en demi-largeur (comme 下老)
HIGH_PREFIX_I = "イ"   # 1オクターブ上
HIGH_PREFIX_RO = "ロ"  # 同音・別弦
HIGH_POS_KANJI = {"合", "乙", "老", "四", "上", "尺", "工", "五", "中"}
# Tokens valides : イ+kanji et ロ+kanji. On autorise tout préfixe 1-char + kanji.
HIGH_PREFIXES = {HIGH_PREFIX_I, HIGH_PREFIX_RO}

TECHNIQUE_CHARS = set(TECHNIQUE_SUFFIXES.keys())

# Marqueurs de couplet :
#   一、 etc.  → numéro de couplet (CJK + 、), indent sous le 、
#   ⚫︎ ou ・  → marqueur générique, indent sous le caractère suivant
#   女　/ 男　  → couplet chanté par femmes/hommes, indent sous l'espace full-width
VERSE_NUM_RE = re.compile(r'^([一二三四五六七八九十]+)、')
# ⚫ ・ ● : indent sous le caractère suivant (offset 1)
VERSE_MARK_RE = re.compile(r'^[⚫・●]')
VERSE_GENDER_RE = re.compile(r'^([男女][　\s])')  # 女/男 + espace full-width


def _verse_indent_len(first_line):
    """Retourne le nombre de caractères à sauter pour l'indentation du couplet,
    ou 0 si pas de marqueur reconnu."""
    m = VERSE_NUM_RE.match(first_line)
    if m:
        return len(m.group(0))
    m = VERSE_GENDER_RE.match(first_line)
    if m:
        return len(m.group(0))
    m = VERSE_MARK_RE.match(first_line)
    if m:
        return 2   # indent SOUS le caractère suivant (1 cran plus bas)
    return 0

# Font stacks pour les styles japonais
FONT_STYLE_SERIF = "serif"  # défaut (comportement historique)
FONT_STYLE_MINCHO = ("Hiragino Mincho ProN, YuMincho, 'MS PMincho', "
                     "Noto Serif CJK JP, serif")
FONT_STYLE_GOTHIC = ("Hiragino Kaku Gothic ProN, 'Yu Gothic', Meiryo, "
                     "MS Gothic, Noto Sans CJK JP, sans-serif")
FONT_STYLES = {
    "mincho": FONT_STYLE_MINCHO,
    "gothic": FONT_STYLE_GOTHIC,
    "serif": FONT_STYLE_SERIF,
}


# --------------------------------------------------------------------------- #
# 2. Parseur KKML
# --------------------------------------------------------------------------- #
# Clés de métadonnées reconnues (pour la tolérance @cléValeur collée)
META_KEYS = {"title", "tuning", "cols", "layout", "marker", "end_circle",
             "lyrics_size", "genre", "author", "composer", "lyricist",
             "origin", "shaku_circled", "shaku_sharp", "speed", "font_style"}
class Song:
    def __init__(self):
        self.meta = {}
        self.blocks = []
        self.cols = 12         # lignes par colonne (mode vertical) — défaut
        self.layout = "vertical"


class Block:
    def __init__(self, kind, label=None):
        self.kind = kind
        self.label = label
        self.lines = []


def parse_kkml(text):
    song = Song()
    lines = text.splitlines()
    i = 0
    n = len(lines)
    current = None
    saw_marker = False
    warned_implicit = False
    while i < n:
        line = lines[i].rstrip()
        stripped = line.strip()

        if stripped.startswith("#"):
            i += 1
            continue

        # ligne vide : préserver comme séparateur de couplet dans un bloc lyrics
        if stripped == "":
            if current is not None and current.kind == "lyrics":
                current.lines.append("")
            i += 1
            continue

        # Métadonnées @clé valeur. L'espace séparateur est toléré absent :
        # une clé connue collée à sa valeur (@title｛安波節｝…, saisie IME où
        # l'espace pleine chasse est facile à omettre) est reconnue, avec
        # une info stderr une seule fois par clé. Les clés inconnues
        # suivent le comportement historique (@mot seul = clé, valeur vide
        # après espaces éventuels).
        m = re.match(r"@(\S+)\s*(.*)", stripped)
        key, val = (m.group(1), m.group(2).strip()) if m else (None, None)
        if m and key not in META_KEYS and len(key) > 1:
            for mk in META_KEYS:
                if key.startswith(mk) and len(key) > len(mk):
                    _info_input_variant("@" + key, "@" + mk + " " + key[len(mk):])
                    val = key[len(mk):] + ((" " + val) if val else "")
                    key = mk
                    break
        if m and not stripped.startswith("::"):
            if key == "cols":
                try:
                    song.cols = int(val)
                except ValueError:
                    pass
            elif key == "layout":
                song.layout = val if val in ("vertical", "horizontal") else "vertical"
            else:
                song.meta[key] = val
            i += 1
            continue

        # fermeture explicite — AVANT l'ouverture
        if stripped == "::":
            current = None
            saw_marker = True
            i += 1
            continue

        if stripped.startswith("::"):
            current = None
            saw_marker = True
            rest = stripped[2:].strip()
            parts = rest.split(None, 1)
            kind = parts[0] if parts else "tab"
            label = parts[1] if len(parts) > 1 else None
            current = Block(kind, label)
            song.blocks.append(current)
            i += 1
            continue

        # Tolérance : aucune section :: déclarée mais des lignes de
        # tablature présentes -> section ::tab implicite (info stderr,
        # une seule fois par fichier).
        if current is None and not saw_marker:
            if not warned_implicit:
                warned_implicit = True
                print("kkml2svg: aucune section :: déclarée ; "
                      "les lignes de tablature sont traitées comme "
                      "une section ::tab implicite",
                      file=sys.stderr)
            current = Block("tab", None)
            song.blocks.append(current)
            continue   # retraiter la ligne dans le bloc implicite

        if current is not None:
            if current.kind == "tab":
                toks = stripped.split()
                # Espaces multiples / U+3000 : déjà tolérés par split().
                # Normaliser les variantes pleine chasse (IME), puis les
                # variantes de repos vers le token canonique ◯.
                norm = []
                for tk in toks:
                    if tk in EMPTY_INPUT_VARIANTS:
                        _info_input_variant(tk, EMPTY_TOKEN)
                        norm.append(EMPTY_TOKEN)
                        continue
                    tk2, changed = _normalize_tab_token(tk)
                    if changed:
                        _info_input_variant(tk, tk2)
                    norm.append(tk2)
                current.lines.append(
                    [REST_TOKEN if tk in REST_VARIANTS else tk for tk in norm]
                )
            elif current.kind == "lyrics":
                # Tolérance IME : ｜ (U+FF5C, barre pleine chasse) = |.
                # Normalisé au parsing pour que la construction des colonnes
                # et l'estimation de largeur ne voient qu'une seule forme.
                if "｜" in stripped:
                    _info_input_variant("｜", "|")
                    stripped = stripped.replace("｜", "|")
                current.lines.append(stripped)
            elif current.kind == "tab-lyrics":
                # Le séparateur | accepte sa variante pleine chasse ｜ ;
                # le côté positions est normalisé comme un bloc tab.
                if "|" in stripped or "｜" in stripped:
                    sep = "|" if "|" in stripped else "｜"
                    left, right = stripped.rsplit(sep, 1)
                    left = ''.join(FULLWIDTH_MAP.get(c, c) for c in left)
                    if sep == "｜":
                        _info_input_variant("｜", "|")
                    current.lines.append((left.split(), right.split()))
                else:
                    left = ''.join(FULLWIDTH_MAP.get(c, c) for c in stripped)
                    current.lines.append((left.split(), []))
            elif current.kind == "vocal":
                # Syllabes vocales : une ligne par ligne de tablature
                # Chaque ligne contient des syllabes séparées par des espaces
                current.lines.append(stripped.split())
            i += 1
            continue

        i += 1

    return song


# --------------------------------------------------------------------------- #
# 3. Rendu SVG
# --------------------------------------------------------------------------- #
def render_svg(song, cols=None, layout=None, cell_w=52, cell_h=58, font_size=22):
    if cols is None:
        cols = song.cols
    if layout is None:
        layout = song.layout

    title = song.meta.get("title", "")
    tuning = song.meta.get("tuning", "本調子")

    # Regrouper les blocs en sections
    sections = []   # (section_title, content, kind, vocal_flat=None)
    cur_title = None
    last_tab_index = -1
    last_tab_blk = None
    for blk in song.blocks:
        if blk.kind == "section":
            cur_title = blk.label
            continue
        if blk.kind == "tab":
            flat = []
            for toks in blk.lines:
                flat.extend(toks)
            sections.append((cur_title, flat, "tab", None))
            last_tab_index = len(sections) - 1
            last_tab_blk = blk
            cur_title = None
        elif blk.kind == "tab-lyrics":
            sections.append((cur_title, blk.lines, "tab-lyrics", None))
            last_tab_index = len(sections) - 1
            last_tab_blk = None   # ::vocal ne se paire qu'avec ::tab
            cur_title = None
        elif blk.kind == "lyrics":
            sections.append((cur_title, blk.lines, "lyrics", None))
            cur_title = None
        elif blk.kind == "vocal":
            # Syllabes vocales : 1 token (séparé par espaces) = 1 syllabe.
            # Un token peut faire plusieurs caractères (ぐゎ, てぃ, よー…).
            # Chaque ligne de ::vocal correspond à la ligne de ::tab de même
            # index ; on aplatit avec padding par ligne pour que la syllabe i
            # reste alignée sur la note i même si une ligne de chant a moins
            # de syllabes que la ligne de tab (ex. intro uta-mochi).
            if last_tab_index >= 0 and last_tab_blk is not None:
                vocal_flat = []
                for j, tab_toks in enumerate(last_tab_blk.lines):
                    syls = blk.lines[j] if j < len(blk.lines) else []
                    n = len(tab_toks)
                    padded = list(syls[:n]) + ["-"] * max(0, n - len(syls))
                    vocal_flat.extend(padded)
                sec_title, tab_content, tab_kind, _ = sections[last_tab_index]
                sections[last_tab_index] = (sec_title, tab_content, tab_kind, vocal_flat)
            else:
                # Pas de bloc ::tab précédent : aplatir tel quel (non rendu)
                vocal_flat = []
                for syls in blk.lines:
                    vocal_flat.extend(syls)
                sections.append((cur_title, [], "vocal", vocal_flat))
            cur_title = None

    # --- Pré-calcul des dimensions --- #
    MARGIN_L = 16
    MARGIN_R = 16
    MARGIN_T = 16
    header_h = 70  # titre + accordage + métas
    if layout == "vertical" and (song.meta.get("title") or song.meta.get("tuning", "本調子")):
        header_h = 40  # titre/accordage rendus verticalement, en-tête réduit
    # Le ruby du titre horizontal a besoin de ~13px au-dessus
    if layout != "vertical" and title and _has_ruby(_parse_ruby(title)):
        header_h = max(header_h, 80)
    marker = song.meta.get("marker", "on") == "on"

    opts = {
        'shaku_circled': song.meta.get('shaku_circled', 'on') == 'on',
        'shaku_sharp': song.meta.get('shaku_sharp', 'on') == 'on',
        'end_circle': song.meta.get('end_circle', 'on') == 'on',
        'lyrics_size': song.meta.get('lyrics_size', 'medium'),
        'font_family': FONT_STYLES.get(
            song.meta.get('font_style', 'mincho'), FONT_STYLE_MINCHO),
    }

    font_family = opts.get('font_family', 'serif')
    if layout == "vertical":
        svg = _render_vertical(song, sections, cols, cell_w, cell_h,
                                font_size, MARGIN_L, MARGIN_R, MARGIN_T, header_h,
                                marker, opts)
    else:
        svg = _render_horizontal(song, sections, cols, cell_w, cell_h,
                                 font_size, MARGIN_L, MARGIN_R, MARGIN_T, header_h,
                                 marker, opts)
    # Post-traitement : remplacer la police serif par défaut par le style choisi
    if font_family != 'serif':
        svg = svg.replace('font-family="serif"', f'font-family="{font_family}"')
    return svg


# --------------------------------------------------------------------------- #
# 3a. Rendu vertical (haut→bas, droite→gauche)
# --------------------------------------------------------------------------- #
def _render_vertical(song, sections, rows_per_col, cell_w, cell_h,
                     fs, ml, mr, mt, header_h, marker=False, opts=None):
    title = song.meta.get("title", "")
    tuning = song.meta.get("tuning", "本調子")

    GAP_HEADER = 30       # saut après l'en-tête, avant la tablature
    VERSE_GAP = 16        # saut entre les couplets (ligne vide dans ::lyrics)
    
    # Syllabes vocales présentes (pairées à un ::tab ou autonomes)
    # → la colonne marker est forcée
    has_vocal = any(s[3] or s[2] == "vocal" for s in sections)
    marker = marker or has_vocal
    marker_w = cell_w // 2 if marker else 0

    # --- Syllabes vocales --- #
    # Taille de police pour les syllabes : min(35% de cell_h, 80% de marker_w)
    SYLLABLE_FS = min(int(cell_h * 0.35), int(marker_w * 0.8)) if marker_w > 0 else int(fs * 0.6)
    SYLLABLE_SP = int(SYLLABLE_FS * 0.9)  # espacement vertical entre syllabes

    # --- Colonne titre vertical (à droite de la grille) --- #
    TITLE_W = 36
    TITLE_GAP = 10
    TITLE_SPACING = 30    # espacement vertical entre caractères du titre
    TUNING_SPACING = 22   # espacement vertical entre caractères de l'accordage
    title_ruby_w = _ruby_needs_extra_width(title, 26) if title else 0
    # largeur de la colonne titre : présente dès que titre OU accordage affiché
    title_offset = (TITLE_W + TITLE_GAP + title_ruby_w) if (title or tuning) else 0
    genre = song.meta.get("genre", "")
    author = song.meta.get("author", "")
    show_genre = genre and genre != author
    title_total_h = (len(title) * TITLE_SPACING +
                     len(tuning) * TUNING_SPACING +
                     (len(genre) if show_genre else 0) * TUNING_SPACING +
                     len(author) * TUNING_SPACING + 20) if (title or tuning) else 0

    # --- Paroles verticales (à gauche de la grille) --- #
    # Taille des couplets selon @lyrics_size : small=50%, medium=75%, big=100% de fs
    lyrics_size = opts.get('lyrics_size', 'medium') if opts else 'medium'
    LYRICS_FS = int(fs * {'small': 0.5, 'medium': 0.75, 'big': 1.0}.get(lyrics_size, 0.75))
    LYRICS_SP = int(LYRICS_FS * 1.2)    # espacement vertical entre caractères
    LYRICS_COL_W = int(LYRICS_FS * 1.33)  # largeur d'une colonne de couplet
    LYRICS_VERSE_GAP = int(LYRICS_COL_W * 0.8)  # gap horizontal entre colonnes

    prepared = []  # (sec_title, data, kind, vocal_data=None)
    for items in sections:
        sec_title = items[0]
        content = items[1]
        kind = items[2]
        vocal_lines = items[3] if len(items) > 3 else None
        
        if kind == "tab":
            columns = _wrap_vertical(content, rows_per_col)
            vocal_data = _wrap_vertical(vocal_lines, rows_per_col) if vocal_lines else None
            prepared.append((sec_title, columns, kind, vocal_data))
        elif kind == "tab-lyrics":
            # aplatir en liste de (pos, syl) puis wrapper verticalement
            flat = []
            for pos_list, syl_list in content:
                n = max(len(pos_list), len(syl_list))
                for j in range(n):
                    p = pos_list[j] if j < len(pos_list) else ""
                    s = syl_list[j] if j < len(syl_list) else ""
                    flat.append((p, s))
            columns = _wrap_vertical(flat, rows_per_col)
            prepared.append((sec_title, columns, kind, None))
        elif kind == "vocal":
            # Standalone vocal without tab - wrap and store
            vocal_data = _wrap_vertical(vocal_lines, rows_per_col) if vocal_lines else None
            prepared.append((sec_title, [], kind, vocal_data))
        else:  # lyrics
            prepared.append((sec_title, content, kind, None))

    # Calculer le nombre max de colonnes parmi toutes les sections tab
    max_cols = 1
    max_col_height = rows_per_col
    for items in prepared:
        kind = items[2]
        data = items[1]
        if kind in ("tab", "tab-lyrics"):
            max_cols = max(max_cols, len(data))

    # Calculer l'espace pour les paroles verticales
    lyrics_sections = [(s[0], s[1]) for s in prepared if s[2] == "lyrics"]
    if lyrics_sections:
        n_verses = 0
        for _, data in lyrics_sections:
            for verse in _split_verses(data):
                n_verses += len(_lyrics_columns(verse))
        lyrics_total_w = (n_verses * LYRICS_COL_W +
                          max(n_verses - 1, 0) * LYRICS_VERSE_GAP)
        # Calculer la largeur de ruby maximale dans les paroles (le ruby
        # va vers la droite, vers la grille)
        max_ruby_w = 0
        if lyrics_size:
            for _, data in lyrics_sections:
                for verse in _split_verses(data):
                    for line in verse:
                        for seg in line.split('|'):
                            if seg:
                                rw = _ruby_needs_extra_width(seg, LYRICS_FS)
                                max_ruby_w = max(max_ruby_w, rw)
        lyrics_offset = (lyrics_total_w + 12 + LYRICS_COL_W + max_ruby_w
                         if n_verses > 0 else 0)
    else:
        lyrics_total_w = 0
        lyrics_offset = 0

    group_w = cell_w + marker_w
    total_w = max_cols * group_w + ml + mr + title_offset + lyrics_offset
    total_h = header_h + mt + GAP_HEADER

    # estimer hauteur totale
    prev_kind = None
    for items in prepared:
        sec_title = items[0]
        data = items[1]
        kind = items[2]
        if sec_title:
            total_h += 22
        if kind in ("tab", "tab-lyrics") and prev_kind in ("tab", "tab-lyrics", None):
            total_h += max_col_height * cell_h + 6
        elif kind == "lyrics":
            pass  # paroles rendues verticalement à gauche, pas de hauteur supplémentaire
        else:
            total_h += len(data) * 20 + 6
        prev_kind = kind

    # s'assurer que la hauteur couvre le titre vertical (ou l'accordage seul)
    if title or tuning:
        total_h = max(total_h, header_h + mt + GAP_HEADER + title_total_h)

    # s'assurer que la hauteur couvre les paroles verticales (une colonne
    # de couplet peut être plus haute que la grille — ex. 安波節)
    if lyrics_sections:
        ly0 = header_h + mt + GAP_HEADER
        lyrics_bottom = ly0 + LYRICS_FS
        for _, data in lyrics_sections:
            for verse in _split_verses(data):
                for col, indent in _lyrics_columns_layout(verse):
                    if not col:
                        continue
                    h = (indent * LYRICS_SP
                         + sum(len(ln) for ln in col) * LYRICS_SP
                         + (len(col) - 1) * LYRICS_SP)
                    lyrics_bottom = max(lyrics_bottom, ly0 + LYRICS_FS + h)
        total_h = max(total_h, lyrics_bottom + mt)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}">'
    )
    out.append('<rect width="100%" height="100%" fill="white"/>')

    # En-tête : métadonnées secondaires uniquement (genre, compositeur…)
    y = mt + 18
    meta_extras = []
    for k in ("composer", "lyricist", "origin"):
        if k in song.meta and song.meta[k]:
            meta_extras.append(song.meta[k])
    if meta_extras:
        out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                   f'font-size="12" fill="#777">{escape("  ".join(meta_extras))}</text>')

    y = header_h + mt + GAP_HEADER

    # Trouver l'index de la dernière section tab/tab-lyrics pour end_circle
    last_tab_idx = -1
    for si, items in enumerate(prepared):
        kind = items[2]
        if kind in ("tab", "tab-lyrics"):
            last_tab_idx = si
    do_end_circle = opts.get('end_circle', False) if opts else False

    prev_kind = None
    for si, items in enumerate(prepared):
        sec_title = items[0]
        data = items[1]
        kind = items[2]
        vocal_data = items[3] if len(items) > 3 else None
        if sec_title:
            out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                       f'font-size="14" fill="#333">{escape(sec_title)}</text>')
            y += 20

        is_last_tab = (si == last_tab_idx)
        ec = do_end_circle and is_last_tab

        if kind == "tab":
            y = _draw_vertical_tab(out, data, rows_per_col, ml, y,
                                   cell_w, cell_h, fs, total_w, mr, marker_w,
                                   title_offset, opts, end_circle=ec,
                                   vocal_data=vocal_data, syllable_fs=SYLLABLE_FS)
            y += 6
        elif kind == "tab-lyrics":
            y = _draw_vertical_tab_lyrics(out, data, rows_per_col, ml, y,
                                          cell_w, cell_h, fs, total_w, mr,
                                          marker_w, title_offset, opts,
                                          end_circle=ec)
            y += 6
        else:  # lyrics — rendu vertical après la grille, ignoré ici
            pass
        prev_kind = kind

    # --- Paroles verticales à gauche de la grille --- #
    if lyrics_sections:
        ly0 = header_h + mt + GAP_HEADER
        vi = 0
        for _, data in lyrics_sections:
            for verse in _split_verses(data):
                # Construire les colonnes via le helper partagé
                # (même logique que l'estimation de largeur).
                # Layout partagé avec l'estimation de hauteur :
                # une colonne avec marqueur de couplet démarre en haut,
                # une colonne de continuation s'indente sous le marqueur.
                layout = _lyrics_columns_layout(verse)
                for col_lines, verse_indent in layout:
                    vx = (ml + lyrics_total_w
                          - vi * (LYRICS_COL_W + LYRICS_VERSE_GAP)
                          - LYRICS_COL_W / 2)
                    cy = ly0 + LYRICS_FS
                    if verse_indent > 0:
                        cy += verse_indent * LYRICS_SP
                    for li, line in enumerate(col_lines):
                        # Saut de ligne dans la même colonne = 1 espace
                        if li > 0:
                            cy += LYRICS_SP
                        cy = _render_vertical_text(out, line, vx, cy,
                                                   LYRICS_FS, "#333", LYRICS_SP)
                    vi += 1

    # --- Titre vertical à droite de la grille --- #
    if title or tuning:
        tx = total_w - mr - TITLE_W / 2
        ty = header_h + mt + GAP_HEADER
        if title:
            ty_end = _render_vertical_text(out, title, tx, ty + 20, 26, "black",
                                           TITLE_SPACING)
        else:
            ty_end = ty
        ty2 = ty_end
        for i, ch in enumerate(tuning):
            _vertical_char(out, ch, tx, ty2 + i * TUNING_SPACING + 15, 15, "#555")
        # Genre et auteur sous l'accordage
        genre = song.meta.get("genre", "")
        author = song.meta.get("author", "")
        show_genre = genre and genre != author
        ty3 = ty2 + len(tuning) * TUNING_SPACING + 15
        if show_genre:
            for i, ch in enumerate(genre):
                _vertical_char(out, ch, tx, ty3 + i * TUNING_SPACING + 15, 15, "#777")
            ty3 += len(genre) * TUNING_SPACING + 15
        for i, ch in enumerate(author):
            _vertical_char(out, ch, tx, ty3 + i * TUNING_SPACING + 15, 15, "#777")

    out.append("</svg>")
    return "\n".join(out)


def _wrap_vertical(items, rows_per_col):
    """Découpe une liste plate en colonnes verticales de rows_per_col éléments."""
    columns = []
    for i in range(0, len(items), rows_per_col):
        columns.append(items[i : i + rows_per_col])
    return columns


def _lyrics_columns(verse):
    """Construit les colonnes d'un couplet de paroles.

    Règle : chaque | (où qu'il soit dans la ligne) ferme la colonne
    courante et ouvre la suivante ; || ferme la colonne et insère en
    plus une colonne blanche (séparation de couplets). Une ligne sans
    aucun | s'enchaîne dans la colonne courante (saut de ligne = 1
    espace). Segment vide entre deux | = colonne blanche.
    Utilisé à la fois pour l'estimation de largeur du canevas et pour
    le rendu — source unique pour éviter toute dérive entre les deux."""
    columns = []
    current_col = []

    def _flush():
        nonlocal current_col
        if current_col:
            columns.append(current_col)
            current_col = []

    for line in verse:
        parts = line.split('|')
        for k, part in enumerate(parts):
            if k == 0:
                # Début de ligne : préserver l'indentation éventuelle,
                # mais retirer les espaces de fin (avant un |).
                part = part.rstrip()
                if part:
                    current_col.append(part)
            else:
                # | rencontré : fermer la colonne, ouvrir la suivante.
                # Les espaces autour du | (ex. "phrase|　奥ぬ…" ou
                # "phrase | suite") sont du formatage visuel du KKML
                # brut : ils sont retirés pour ne pas décaler l'aligne-
                # ment des colonnes au rendu. Un segment réduit à des
                # espaces équivaut au segment vide correspondant.
                part = part.strip()
                _flush()
                if part:
                    current_col.append(part)
                elif k < len(parts) - 1:
                    # segment vide entre deux | = colonne blanche (||)
                    columns.append([])
                # segment vide final (ligne finissant par |) : simple fin
                # de colonne, rien à faire
    _flush()
    return columns


def _lyrics_columns_layout(verse):
    """Layout complet d'un couplet : liste de (col_lines, indent).

    Source unique pour le rendu ET pour l'estimation de hauteur.
    Règle d'indentation : une colonne qui commence par un marqueur de
    couplet (一、二、… 女　男　) est alignée en haut (indent 0) et définit
    l'indentation courante pour les colonnes de continuation du même
    couplet (après |), qui s'indentent sous le marqueur. Une colonne
    blanche (après ||) réinitialise l'indentation courante : le couplet
    suivant, même sans marqueur, ne s'indente pas sous le précédent."""
    layout = []
    cur_marker_indent = 0
    for col in _lyrics_columns(verse):
        if col:
            own = _verse_indent_len(col[0])
            if own > 0:
                indent = 0
                cur_marker_indent = own
            else:
                indent = cur_marker_indent
        else:
            indent = 0
            cur_marker_indent = 0
        layout.append((col, indent))
    return layout


def _split_verses(lines):
    """Découpe une liste de lignes de paroles en couplets
    (séparés par des lignes vides). Renvoie une liste de listes de lignes."""
    verses = []
    current = []
    for ln in lines:
        if ln == "":
            if current:
                verses.append(current)
                current = []
        else:
            current.append(ln)
    if current:
        verses.append(current)
    return verses


# Petits kana combinants (うちなぐち) : s'attachent au caractère principal
# pour former une seule syllabe — ぐゎ, くゎ, てぃ, でぃ, とぅ, づぅ, ふぃ…
# En écriture verticale ils se placent SOUS le caractère principal.
SMALL_KANA = set("ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ")


def _draw_vertical_vocal(out, vocal_lines, rows_per_col, ml, y0,
                           cell_w, cell_h, fs, total_w, mr, marker_w=0,
                           title_offset=0, opts=None, syllable_fs=None):
    """Rend des syllabes vocales dans la colonne marker.
    Un token = une syllabe. Les tokens multi-caractères (ぐゎ, てぃ, よー…)
    sont empilés verticalement : caractère principal aligné sur la note,
    caractères combinants (petits kana, ー) en dessous. Le chevauchement
    de la bordure inférieure de la case est accepté.
    """
    if marker_w == 0 or syllable_fs is None or syllable_fs <= 0:
        return

    group_w = cell_w + marker_w
    step = int(syllable_fs * 0.85)  # espacement des caractères combinants

    for ci, vocal_col in enumerate(vocal_lines):
        x = total_w - mr - title_offset - (ci + 1) * group_w
        for ri, syllable in enumerate(vocal_col):
            if ri >= rows_per_col:
                break
            cy = y0 + ri * cell_h
            # Position dans la colonne marker (à droite de la case)
            sx = x + cell_w + marker_w / 2
            sy = cy + cell_h / 2 + syllable_fs / 3  # centré sur la note
            if not syllable or syllable == "-":
                continue
            for k, ch in enumerate(syllable):
                yy = sy + k * step
                if ch == "ー":
                    # voyelle longue : trait vertical en écriture verticale
                    ry = yy - syllable_fs * 0.35
                    out.append(f'<text x="{sx}" y="{yy}" text-anchor="middle" '
                               f'font-family="serif" font-size="{syllable_fs}" '
                               f'fill="#333" '
                               f'transform="rotate(90 {sx} {ry})">'
                               f'{escape(ch)}</text>')
                else:
                    out.append(f'<text x="{sx}" y="{yy}" text-anchor="middle" '
                               f'font-family="serif" font-size="{syllable_fs}" '
                               f'fill="#333">{escape(ch)}</text>')


def _draw_vertical_tab(out, columns, rows_per_col, ml, y0,
                       cell_w, cell_h, fs, total_w, mr, marker_w=0,
                       title_offset=0, opts=None, end_circle=False,
                       vocal_data=None, syllable_fs=None):
    """Dessine des colonnes verticales, de droite à gauche.
    Deux passes : d'abord tous les rectangles (grille), puis toutes les notes
    par-dessus, pour que les notes à cheval ne soient pas masquées.
    vocal_data : colonnes de syllabes vocales à rendre dans la colonne marker
    syllable_fs : taille de police des syllabes
    """
    n_cols = len(columns)
    if n_cols == 0:
        return y0
    group_w = cell_w + marker_w
    col_h = rows_per_col * cell_h

    # Passe 1 : tous les rectangles de la grille
    col_positions = []
    for ci, col in enumerate(columns):
        x = total_w - mr - title_offset - (ci + 1) * group_w
        col_positions.append((x, col))
        for ri in range(rows_per_col):
            cy = y0 + ri * cell_h
            out.append(f'<rect x="{x}" y="{cy}" width="{cell_w}" '
                       f'height="{cell_h}" fill="none" stroke="#bbb" '
                       f'stroke-width="0.75"/>')
        if marker_w > 0:
            mx = x + cell_w
            out.append(f'<rect x="{mx}" y="{y0}" width="{marker_w}" '
                       f'height="{col_h}" fill="none" stroke="#bbb" '
                       f'stroke-width="0.75"/>')

    # Passe 2 : toutes les notes par-dessus la grille
    # Les flèches de répétition vont dans la colonne marker (à droite de chaque pile)
    for x, col in col_positions:
        for ri in range(rows_per_col):
            cy = y0 + ri * cell_h
            tok = col[ri] if ri < len(col) else ""
            rs, base_tok, re_ = _strip_repeat_marks(tok)
            render_cell(out, base_tok, x + cell_w / 2, cy + cell_h / 2, fs,
                        cell_w, cell_h, opts)
            if rs and marker_w > 0:
                _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'start')
            if re_ and marker_w > 0:
                _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'end')

    # Passe 3 : rendre les syllabes vocales dans la colonne marker
    if vocal_data is not None and marker_w > 0 and syllable_fs is not None:
        _draw_vertical_vocal(out, vocal_data, rows_per_col, ml, y0,
                             cell_w, cell_h, fs, total_w, mr, marker_w,
                             title_offset, opts, syllable_fs)

    # Marqueur de fin de chanson : dans le marker de la dernière colonne,
    # à la hauteur du bas de la dernière case remplie
    if end_circle and marker_w > 0 and n_cols > 0:
        last_x, last_col = col_positions[-1]
        # Trouver la dernière case remplie (token non vide et non "-")
        last_filled_cy = None
        for ri in range(rows_per_col - 1, -1, -1):
            tok = last_col[ri] if ri < len(last_col) else ""
            if tok and tok != "-":
                last_filled_cy = y0 + ri * cell_h
                break
        if last_filled_cy is not None:
            _render_end_circle(out, last_x + cell_w, last_filled_cy,
                               cell_h, marker_w)

    return y0 + col_h


def _draw_vertical_tab_lyrics(out, columns, rows_per_col, ml, y0,
                              cell_w, cell_h, fs, total_w, mr, marker_w=0,
                              title_offset=0, opts=None, end_circle=False):
    """Colonnes verticales droite→gauche, cellule = position (haut) + syllabe (bas).
    Deux passes : rectangles d'abord, puis notes/syllabes par-dessus."""
    group_w = cell_w + marker_w
    col_h = rows_per_col * cell_h

    # Passe 1 : tous les rectangles
    col_positions = []
    for ci, col in enumerate(columns):
        x = total_w - mr - title_offset - (ci + 1) * group_w
        col_positions.append((x, col))
        for ri in range(rows_per_col):
            cy = y0 + ri * cell_h
            out.append(f'<rect x="{x}" y="{cy}" width="{cell_w}" '
                       f'height="{cell_h}" fill="none" stroke="#bbb" '
                       f'stroke-width="0.75"/>')
        if marker_w > 0:
            mx = x + cell_w
            out.append(f'<rect x="{mx}" y="{y0}" width="{marker_w}" '
                       f'height="{col_h}" fill="none" stroke="#bbb" '
                       f'stroke-width="0.75"/>')

    # Passe 2 : notes et syllabes par-dessus
    # Les flèches de répétition vont dans la colonne marker (à droite de chaque pile)
    for x, col in col_positions:
        for ri in range(rows_per_col):
            cy = y0 + ri * cell_h
            if ri < len(col):
                pair = col[ri]
                pos_tok, syl = pair if isinstance(pair, tuple) else (pair, "")
            else:
                pos_tok, syl = "", ""
            rs, base_tok, re_ = _strip_repeat_marks(pos_tok)
            render_cell(out, base_tok, x + cell_w / 2, cy + cell_h * 0.38,
                        fs - 2, cell_w, cell_h, opts)
            if syl:
                out.append(f'<text x="{x + cell_w/2}" y="{cy + cell_h*0.82}" '
                           f'text-anchor="middle" font-family="sans-serif" '
                           f'font-size="10" fill="#666">{escape(syl)}</text>')
            if rs and marker_w > 0:
                _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'start')
            if re_ and marker_w > 0:
                _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'end')

    # Marqueur de fin de chanson
    if end_circle and marker_w > 0 and len(col_positions) > 0:
        last_x, last_col = col_positions[-1]
        last_filled_cy = None
        for ri in range(rows_per_col - 1, -1, -1):
            if ri < len(last_col):
                pair = last_col[ri]
                pos_tok = pair if isinstance(pair, str) else pair[0]
            else:
                pos_tok = ""
            if pos_tok and pos_tok != "-":
                last_filled_cy = y0 + ri * cell_h
                break
        if last_filled_cy is not None:
            _render_end_circle(out, last_x + cell_w, last_filled_cy,
                               cell_h, marker_w)

    return y0 + col_h


# --------------------------------------------------------------------------- #
# 3b. Rendu horizontal (gauche→droite, haut→bas) — mode songbook
# --------------------------------------------------------------------------- #
def _render_horizontal(song, sections, cols, cell_w, cell_h,
                       fs, ml, mr, mt, header_h, marker=False, opts=None):
    title = song.meta.get("title", "")
    tuning = song.meta.get("tuning", "本調子")

    prepared = []
    for items in sections:
        sec_title, content, kind = items[0], items[1], items[2]
        if kind == "tab":
            rows = _wrap_horizontal(content, cols)
            prepared.append((sec_title, rows, kind))
        elif kind == "tab-lyrics":
            prepared.append((sec_title, content, kind))
        else:
            prepared.append((sec_title, content, kind))

    GAP_HEADER = 30
    GAP_TAB_LYRICS = 30
    # Taille des couplets selon @lyrics_size
    lyrics_size = opts.get('lyrics_size', 'medium') if opts else 'medium'
    h_lyrics_fs = int(fs * {'small': 0.5, 'medium': 0.75, 'big': 1.0}.get(lyrics_size, 0.75))
    h_lyrics_sp = int(h_lyrics_fs * 1.2)  # espacement vertical entre lignes de couplets
    total_w = cols * cell_w + ml + mr
    total_h = header_h + mt + GAP_HEADER
    prev_kind = None
    for sec_title, data, kind in prepared:
        if sec_title:
            total_h += 22
        if kind == "lyrics" and prev_kind in ("tab", "tab-lyrics"):
            total_h += GAP_TAB_LYRICS
        if kind == "tab":
            total_h += len(data) * cell_h + 6
        elif kind == "tab-lyrics":
            total_h += len(data) * (cell_h + 8) + 6
        else:
            total_h += len(data) * h_lyrics_sp + 6
            if kind == "lyrics":
                total_h += 16 * data.count("")
        prev_kind = kind

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}">'
    )
    out.append('<rect width="100%" height="100%" fill="white"/>')

    y = mt + 26
    # Le titre avec ruby nécessite plus de hauteur d'en-tête
    if title and _has_ruby(_parse_ruby(title)):
        y_ruby = y - 26 * 0.55  # ruby au-dessus du titre
        _render_horizontal_text(out, title, ml, y, 26, "black")
    elif title:
        out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                   f'font-size="26" fill="black">{escape(title)}</text>')
    if tuning:
        y += 22
        out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                   f'font-size="15" fill="#555">{escape(tuning)}</text>')
    y += 14
    # Genre et auteur
    genre = song.meta.get("genre", "")
    author = song.meta.get("author", "")
    show_genre = genre and genre != author
    header_meta = []
    if show_genre:
        header_meta.append(genre)
    if author:
        header_meta.append(author)
    if header_meta:
        y += 14
        out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                   f'font-size="12" fill="#777">{escape("  ".join(header_meta))}</text>')
    meta_extras = []
    for k in ("composer", "lyricist", "origin"):
        if k in song.meta and song.meta[k]:
            meta_extras.append(song.meta[k])
    if meta_extras:
        y += 14
        out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                   f'font-size="12" fill="#777">{escape("  ".join(meta_extras))}</text>')

    y = header_h + mt + GAP_HEADER
    # Trouver la dernière section tab/tab-lyrics pour end_circle
    last_tab_idx = -1
    for si, (_, _, kind) in enumerate(prepared):
        if kind in ("tab", "tab-lyrics"):
            last_tab_idx = si
    do_end_circle = opts.get('end_circle', False) if opts else False
    h_marker_w = cell_w * 0.15  # marker_w synthétique en mode horizontal
    h_last_filled = None

    prev_kind = None
    for si, (sec_title, data, kind) in enumerate(prepared):
        if kind == "lyrics" and prev_kind in ("tab", "tab-lyrics"):
            y += GAP_TAB_LYRICS
        if sec_title:
            out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                       f'font-size="14" fill="#333">{escape(sec_title)}</text>')
            y += 20
        if kind == "tab":
            for row in data:
                for idx, tok in enumerate(row):
                    x = ml + idx * cell_w
                    out.append(f'<rect x="{x}" y="{y}" width="{cell_w}" '
                               f'height="{cell_h}" fill="none" '
                               f'stroke="#999" stroke-width="0.75"/>')
                    rs, base_tok, re_ = _strip_repeat_marks(tok)
                    render_cell(out, base_tok, x + cell_w / 2, y + cell_h / 2, fs,
                                cell_w, cell_h, opts)
                    if rs:
                        _render_repeat_arrow(out, x + cell_w * 0.85,
                                             y, cell_h, cell_w * 0.15, 'start')
                    if re_:
                        _render_repeat_arrow(out, x + cell_w * 0.85,
                                             y, cell_h, cell_w * 0.15, 'end')
                    if tok and tok != "-":
                        h_last_filled = (x + cell_w * 0.85, y)
                y += cell_h
            y += 6
            if do_end_circle and si == last_tab_idx and h_last_filled:
                _render_end_circle(out, h_last_filled[0], h_last_filled[1],
                                   cell_h, h_marker_w)
        elif kind == "tab-lyrics":
            for pos_list, syl_list in data:
                n = max(len(pos_list), len(syl_list))
                for j in range(n):
                    x = ml + j * cell_w
                    out.append(f'<rect x="{x}" y="{y}" width="{cell_w}" '
                               f'height="{cell_h}" fill="none" '
                               f'stroke="#bbb" stroke-width="0.75"/>')
                    pt = pos_list[j] if j < len(pos_list) else ""
                    st = syl_list[j] if j < len(syl_list) else ""
                    rs, base_pt, re_ = _strip_repeat_marks(pt)
                    render_cell(out, base_pt, x + cell_w / 2, y + cell_h * 0.38,
                                fs - 2, cell_w, cell_h, opts)
                    out.append(f'<text x="{x + cell_w/2}" y="{y + cell_h*0.82}" '
                               f'text-anchor="middle" font-family="sans-serif" '
                               f'font-size="10" fill="#666">{escape(st)}</text>')
                    if rs:
                        _render_repeat_arrow(out, x + cell_w * 0.85,
                                             y, cell_h, cell_w * 0.15, 'start')
                    if re_:
                        _render_repeat_arrow(out, x + cell_w * 0.85,
                                             y, cell_h, cell_w * 0.15, 'end')
                    if pt and pt != "-":
                        h_last_filled = (x + cell_w * 0.85, y)
                y += cell_h + 8
            y += 6
            if do_end_circle and si == last_tab_idx and h_last_filled:
                _render_end_circle(out, h_last_filled[0], h_last_filled[1],
                                   cell_h, h_marker_w)
        else:
            for ln in data:
                if ln == "":
                    y += int(h_lyrics_fs * 1.0)
                else:
                    if _has_ruby(_parse_ruby(ln)):
                        _render_horizontal_text(out, ln, ml, y, h_lyrics_fs, "#444")
                    else:
                        out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                                   f'font-size="{h_lyrics_fs}" fill="#444">{escape(ln)}</text>')
                    y += h_lyrics_sp
            y += 6
        prev_kind = kind

    out.append("</svg>")
    return "\n".join(out)


def _wrap_horizontal(tokens, cols):
    return [tokens[i : i + cols] for i in range(0, len(tokens), cols)]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _render_techniques(out, suffixes, cx, cy, cell_w, cell_h, fs, text_w=None):
    """Dessine les marques de technique (souhou) autour de la cellule.

    Les marques de type 'char' sont rendues dans la même police (serif) et la
    même taille (fs) que la note, positionnées en haut-droite (ou bas-gauche)
    du caractère concerné.

    Règle : l'encre visible du signe ne doit pas chevaucher l'encre visible
    de la note. Chaque signe a ses propres offsets (dx, dy) pour respecter
    cette règle selon la forme de son glyphe.

    text_w : largeur du texte rendu (textLength). Quand fournie, les marqueurs
    sont positionnés par rapport au bord du texte au lieu du centre de la
    cellule — évite le chevauchement avec les tokens multi-caractères (下老,
    positions hautes). On utilise text-anchor="start" (top-right) ou "end"
    (bottom-left) pour que le glyphe parte du bord, ce qui est robuste aux
    variations de largeur entre polices.
    """
    gap = fs * 0.05
    for suffix in suffixes:
        tech = TECHNIQUE_SUFFIXES[suffix]
        ttype = tech['type']
        if ttype == 'char':
            sym = tech['symbol']
            dx = tech.get('dx', 0.22)
            dy = tech.get('dy', 0.05)
            scale = tech.get('scale', 1.0)
            rotate = tech.get('rotate', 0)
            tech_fs = int(fs * 1.1 * scale)
            if tech['pos'] == 'inside-right':
                # ○/□ 声だし・声切り : petit glyphe DANS la case, côté
                # droit, centré verticalement (区画中右方, traité 野村流).
                out.append(f'<text x="{cx + cell_w * tech["dx"]}" '
                           f'y="{cy + fs * tech["dy"]}" '
                           f'text-anchor="middle" font-family="serif" '
                           f'font-size="{int(fs * scale)}" '
                           f'fill="black">{escape(sym)}</text>')
                continue
            if text_w is not None:
                # Positionnement par rapport au bord réel du texte.
                # text-anchor est géré par le renderer SVG selon la police,
                # donc le glyphe ne chevauche jamais le texte.
                if tech['pos'] == 'top-right':
                    tx = cx + text_w / 2 + gap
                    # rotate 180 inverse gauche/droite : anchor "end" place
                    # le glyphe à droite après rotation
                    anchor = "end" if rotate else "start"
                else:  # bottom-left
                    tx = cx - text_w / 2 - gap
                    anchor = "start" if rotate else "end"
                ty = cy + 7 + fs * dy
            else:
                if tech['pos'] == 'top-right':
                    tx = cx + fs * dx
                else:
                    tx = cx - fs * dx
                ty = cy + 7 + fs * dy
                anchor = "middle"
            if rotate:
                out.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                           f'font-family="serif" font-size="{tech_fs}" '
                           f'fill="black" '
                           f'transform="rotate({rotate} {tx} {ty})">'
                           f'{escape(sym)}</text>')
            else:
                out.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                           f'font-family="serif" font-size="{tech_fs}" '
                           f'fill="black">{escape(sym)}</text>')
        elif ttype == 'line':
            if text_w is not None:
                lx = cx + text_w / 2 + gap
            else:
                lx = cx + fs * 0.42
            out.append(f'<line x1="{lx}" y1="{cy - fs * 0.40}" '
                       f'x2="{lx}" y2="{cy + fs * 0.40}" '
                       f'stroke="black" stroke-width="1.2"/>')


def _strip_repeat_marks(tok):
    """Détache |: (début) et :| (fin) d'un token.
    Retourne (repeat_start, base_tok, repeat_end) où repeat_start/repeat_end
    sont des booléens et base_tok est le token sans les marqueurs."""
    rs = False
    re_ = False
    if tok.startswith(REPEAT_START):
        rs = True
        tok = tok[len(REPEAT_START):]
    if tok.endswith(REPEAT_END):
        re_ = True
        tok = tok[:-len(REPEAT_END)]
    return rs, tok, re_


def _render_repeat_arrow(out, x_left, cy, cell_h, marker_w, arrow_type):
    """Dessine une flèche de répétition en graphiques vectoriels SVG.

    La flèche part de la bordure gauche de la colonne marker (x_left),
    va horizontalement vers la droite sur 66% de marker_w, puis descend
    (ou monte) verticalement, et se termine par un triangle creux.

    arrow_type: 'start' = flèche descendante (~80% haut), 'end' = flèche montante (~80% bas).
    x_left = bordure gauche de la colonne marker.
    cy = position verticale du haut de la case."""
    sw = 1.2  # stroke-width
    h_len = marker_w * 0.66  # longueur du trait horizontal
    v_len = h_len  # trait vertical au moins aussi long que l'horizontal
    tri_size = marker_w * 0.22  # demi-largeur du triangle
    tri_h = 3 ** 0.5 * tri_size  # hauteur triangle équilatéral

    if arrow_type == 'start':
        # Part à ~80% du haut : trait horizontal à cell_h * 0.20
        hy = cy + cell_h * 0.20
        # Trait horizontal : de x_left à x_left + h_len
        hx = x_left + h_len
        out.append(f'<line x1="{x_left}" y1="{hy}" x2="{hx}" y2="{hy}" '
                   f'stroke="black" stroke-width="{sw}"/>')
        # Trait vertical : de hy vers le bas sur v_len
        vy = hy + v_len
        out.append(f'<line x1="{hx}" y1="{hy}" x2="{hx}" y2="{vy}" '
                   f'stroke="black" stroke-width="{sw}"/>')
        # Triangle creux pointant vers le bas, sommet à (hx, vy + tri_h)
        tip_y = vy + tri_h
        out.append(f'<polygon points="{hx - tri_size},{vy} '
                   f'{hx + tri_size},{vy} {hx},{tip_y}" '
                   f'fill="none" stroke="black" stroke-width="{sw}"/>')
    else:
        # Part à ~80% du bas : trait horizontal à cell_h * 0.80
        hy = cy + cell_h * 0.80
        hx = x_left + h_len
        out.append(f'<line x1="{x_left}" y1="{hy}" x2="{hx}" y2="{hy}" '
                   f'stroke="black" stroke-width="{sw}"/>')
        # Trait vertical : de hy vers le haut sur v_len
        vy = hy - v_len
        out.append(f'<line x1="{hx}" y1="{hy}" x2="{hx}" y2="{vy}" '
                   f'stroke="black" stroke-width="{sw}"/>')
        # Triangle creux pointant vers le haut, sommet à (hx, vy - tri_h)
        tip_y = vy - tri_h
        out.append(f'<polygon points="{hx - tri_size},{vy} '
                   f'{hx + tri_size},{vy} {hx},{tip_y}" '
                   f'fill="none" stroke="black" stroke-width="{sw}"/>')


def _render_end_circle(out, x_left, cy, cell_h, marker_w):
    """Dessine un marqueur de fin de chanson : même géométrie que la flèche
    montante ('end'), mais avec un cercle creux au lieu d'un triangle.

    Le cercle a un diamètre égal à la base du triangle (2 * tri_size).
    La barre verticale touche le cercle sans le pénétrer.
    x_left = bordure gauche de la colonne marker.
    cy = position verticale du haut de la case."""
    sw = 1.2
    h_len = marker_w * 0.66
    v_len = h_len
    tri_size = marker_w * 0.22  # demi-largeur du triangle (= rayon du cercle)
    r = tri_size

    # Même positionnement que la flèche 'end' : horizontal à cell_h * 0.80
    hy = cy + cell_h * 0.80
    hx = x_left + h_len
    out.append(f'<line x1="{x_left}" y1="{hy}" x2="{hx}" y2="{hy}" '
               f'stroke="black" stroke-width="{sw}"/>')
    # Trait vertical vers le haut sur v_len
    vy = hy - v_len
    out.append(f'<line x1="{hx}" y1="{hy}" x2="{hx}" y2="{vy}" '
               f'stroke="black" stroke-width="{sw}"/>')
    # Cercle creux au-dessus de la barre : la barre touche le bas du cercle
    circle_cy = vy - r
    out.append(f'<circle cx="{hx}" cy="{circle_cy}" r="{r}" '
               f'fill="none" stroke="black" stroke-width="{sw}"/>')


def _note_svg(note, font_size, opts=None):
    """Contenu SVG pour une note. Si la note est 尺♯, le ♯ est rendu
    en tspan plus petit (65%) sans modifier la taille ni la position du 尺.
    Si opts['shaku_sharp'] est False, le ♯ est masqué (rendu en 尺 simple)."""
    if note == "尺♯":
        if opts is not None and not opts.get('shaku_sharp', True):
            return escape("尺")
        return (f'{escape("尺")}'
                f'<tspan font-size="{int(font_size * 0.65)}" '
                f'dx="0" dy="0">♯</tspan>')
    return escape(note)


_WARNED_TOKENS = set()


def _info_input_variant(orig, canon):
    """Info stderr (une seule fois par paire) : une variante de saisie
    pleine chasse a été normalisée vers la forme canonique."""
    key = (orig, canon)
    if key not in _INFO_INPUT_SEEN:
        _INFO_INPUT_SEEN.add(key)
        print(f"kkml2svg: entrée '{orig}' normalisée en '{canon}' "
              f"(variante de saisie acceptée)",
              file=sys.stderr)


_INFO_INPUT_SEEN = set()


def _warn_unknown_token(tok):
    """Alerte stderr une seule fois par token non reconnu (anti-spam)."""
    if tok not in _WARNED_TOKENS:
        _WARNED_TOKENS.add(tok)
        print(f"AVERTISSEMENT : token non reconnu {tok!r} "
              f"(rendu dégradé : 3 premiers caractères condensés)",
              file=sys.stderr)


def render_cell(out, tok, cx, cy, fs, cell_w=52, cell_h=58, opts=None):
    """Affiche un token dans une cellule.

    Modes rythmiques :
      中        → noire (note seule, centrée, pleine taille)
      合/工     → croche (合 centrée + 工 à cheval sur le bord inférieur)
      合:工     → shuffle 早弾き (deux notes égales, empilées)
      合工尺    → token non reconnu : alerte stderr + rendu dégradé
                  (3 premiers caractères max, condensés)

    Tokens spéciaux :
      -        → case vide
      .        → tenuto (・)
      ◯        → repos (cercle) — variantes O, 0, ⚪ etc. normalisées
      |: :|    → marques de répétition (↓ ↑)

    Suffixes de technique (souhou), apposés après le kanji :
      *  → uchi-utu  (｀ en haut-droite, même police et taille que la note)
      ^  → kaki-utu  (┗ roté 180° en haut-droite)
      v  → aki-utu   (V en bas-gauche, même police et taille que la note)
      <  → kachi-utu (┗ en bas-gauche, même police et taille que la note)
      s  → kuubanchi (rendre le kanji plus petit, jeu faible)
      =  → taachi    (trait vertical à droite, plusieurs cordes)

    Les marques diacritiques (*, ^, v, <) sont rendues dans la même police
    (serif) et la même taille (effective_fs) que la note. Elles ne modifient
    ni le centrage ni la taille de la note (sauf 's' qui réduit la taille).

    Positions étendues :
      尺♯       → rendu en 尺♯ si @shaku_sharp on (défaut), sinon 尺 simple ; jamais entouré
      下尺      → 尺 entouré d'un cercle
      下老      → deux caractères condensés en demi-largeur
      下八      → deux caractères condensés (patron 下老, sans cercle)
      イ下尺    → position haute イ + 下尺, 3 caractères condensés (large), sans cercle

    尺 entouré (@shaku_circled on) :
      尺 (noire)       → cercle autour du 尺 centré
      尺/B (croche)    → cercle autour du 尺 (note principale, centrée)
      A/尺 (croche)    → cercle autour du 尺 (note à cheval, en bas)
      尺♯, 下尺       → non affectés par @shaku_circled

    Positions hautes (préfixe イ) :
      イ尺      → イ (1 octave au-dessus) + 尺, condensés en demi-largeur
      Tokens valides : イ+{合,乙,老,四,上,中,尺,工,五,六,七}
      Rendu identique au patron 下老 (deux textes à 62%, offset ±cell_w*0.18)
    """
    if opts is None:
        opts = {}

    if tok in (EMPTY_TOKEN, "", None):
        return

    if tok == SUSTAIN_TOKEN:
        out.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="#888">・</text>')
        return

    # Repos (cercle)
    if tok == REST_TOKEN:
        out.append(f'<text x="{cx}" y="{cy+7}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="black">'
                   f'{escape(REST_TOKEN)}</text>')
        return

    # Marques de répétition
    if tok == REPEAT_START:
        out.append(f'<text x="{cx}" y="{cy+8}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="black">'
                   f'↓</text>')
        return
    if tok == REPEAT_END:
        out.append(f'<text x="{cx}" y="{cy+8}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="black">'
                   f'↑</text>')
        return

    # Extraire les suffixes de technique depuis la fin du token
    tech_suffixes = []
    base_tok = tok
    while len(base_tok) > 1 and base_tok[-1] in TECHNIQUE_CHARS:
        tech_suffixes.insert(0, base_tok[-1])
        base_tok = base_tok[:-1]

    is_small = 's' in tech_suffixes
    effective_fs = int(fs * 0.67) if is_small else fs

    # 尺♯ — jamais entouré
    if base_tok == "尺♯":
        out.append(f'<text x="{cx}" y="{cy+7}" text-anchor="middle" '
                  f'font-family="serif" font-size="{effective_fs}" '
                  f'fill="black">{_note_svg(base_tok, effective_fs, opts)}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # 下尺 → 尺 entouré d'un cercle
    if base_tok == "下尺":
        r = effective_fs * 0.6325
        out.append(f'<circle cx="{cx}" cy="{cy+2}" r="{r}" '
                   f'fill="none" stroke="black" stroke-width="1"/>')
        out.append(f'<text x="{cx}" y="{cy+7}" text-anchor="middle" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black">{escape("尺")}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # 下老 → deux caractères condensés en demi-largeur via textLength
    if base_tok == "下老":
        target_w = effective_fs * 1.0
        y_text = cy + 7
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape("下老")}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=effective_fs * 1.0)
        return

    # 下八 → kandokoro propre (女絃 sous 八, octave de 中) : deux caractères
    # condensés via textLength, même patron que 下老, SANS cercle.
    if base_tok == "下八":
        target_w = effective_fs * 1.0
        y_text = cy + 7
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape("下八")}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=effective_fs * 1.0)
        return

    # Positions hautes : イ尺, ロ五, イ工, etc. (préfixe + kanji condensés)
    # Deux caractères dans un seul <text> avec textLength à 120% de la largeur
    # d'un kanji. lengthAdjust="spacingAndGlyphs" compresse légèrement les
    # glyphes ; à 120% la déformation reste minime et lisible (vs 100% pour 下老).
    if (len(base_tok) == 2
            and base_tok[0] in HIGH_PREFIXES
            and base_tok[1] in HIGH_POS_KANJI):
        target_w = effective_fs * 1.2
        y_text = cy + 7
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape(base_tok)}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=effective_fs * 1.2)
        return

    # Position haute 3 caractères : イ下尺 (préfixe + 下尺)
    # 3 caractères condensés via textLength. Pas de cercle autour du 尺
    # dans ce composé (décision du 16 sept. 2026) : le 下 reste visible,
    # le rendu suit le patron de 下老 élargi à 3 caractères.
    if (len(base_tok) == 3
            and base_tok[0] in HIGH_PREFIXES
            and base_tok[1:] == "下尺"):
        target_w = effective_fs * 1.8
        y_text = cy + 7
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape(base_tok)}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=target_w)
        return

    # Accords (jusqu'à 3 notes simultanées) : note-note[-note]
    # Rendu : caractères empilés verticalement, taille 72%.
    if "-" in base_tok and len(base_tok) > 1:
        chord_notes = [n for n in base_tok.split("-") if n]
        if len(chord_notes) >= 2:
            n = len(chord_notes)
            step = effective_fs * 0.82
            start = cy - (n - 1) * step / 2
            small = int(effective_fs * 0.72)
            for j, c in enumerate(chord_notes):
                out.append(f'<text x="{cx}" y="{start + j*step + small/3}" '
                           f'text-anchor="middle" font-family="serif" '
                           f'font-size="{small}" fill="black">'
                           f'{escape(c)}</text>')
            _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
            return

    if "/" in base_tok:
        parts = base_tok.split("/", 1)
        main_note = parts[0]
        straddle_note = parts[1] if len(parts) > 1 else ""

        # Extraire les techniques de la note principale (avant le /)
        main_tech = []
        while len(main_note) > 1 and main_note[-1] in TECHNIQUE_CHARS:
            main_tech.insert(0, main_note[-1])
            main_note = main_note[:-1]

        # Cercle autour du 尺 principal si @shaku_circled on
        if main_note == "尺" and opts.get('shaku_circled'):
            r = effective_fs * 0.6325
            out.append(f'<circle cx="{cx}" cy="{cy+2}" r="{r}" '
                       f'fill="none" stroke="black" stroke-width="1"/>')
        out.append(f'<text x="{cx}" y="{cy+7}" text-anchor="middle" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black">{_note_svg(main_note, effective_fs, opts)}</text>')
        # Techniques de la note principale
        if main_tech:
            _render_techniques(out, main_tech, cx, cy, cell_w, cell_h, effective_fs)

        if straddle_note:
            ss_pos = int(fs * 0.713)
            straddle_y = cy + cell_h * 0.50 + ss_pos/3
            ss = int(effective_fs * 0.713)
            # Cercle autour du 尺 à cheval si @shaku_circled on
            if straddle_note == "尺" and opts.get('shaku_circled'):
                r = ss * 0.713
                out.append(f'<circle cx="{cx}" cy="{straddle_y - ss * 0.35}" r="{r}" '
                           f'fill="none" stroke="black" stroke-width="0.8"/>')
            out.append(f'<text x="{cx}" y="{straddle_y}" '
                       f'text-anchor="middle" font-family="serif" '
                       f'font-size="{ss}" fill="black">'
                       f'{_note_svg(straddle_note, ss, opts)}</text>')
            # Les techniques de fin de token s'appliquent à la note à cheval :
            if tech_suffixes:
                _render_techniques(out, tech_suffixes, cx, straddle_y - 7,
                                   cell_w, cell_h, effective_fs)
        else:
            # Pas de note à cheval : les techniques s'appliquent à la note principale
            _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # --- shuffle 早弾き : A:B (deux notes égales, empilées) --- #
    if ":" in base_tok:
        parts = base_tok.split(":", 1)
        sh_pos = int(fs * 0.72)
        sh = int(effective_fs * 0.72)
        out.append(f'<text x="{cx}" y="{cy - fs * 0.18 + sh_pos/3}" '
                   f'text-anchor="middle" font-family="serif" '
                   f'font-size="{sh}" fill="black">{_note_svg(parts[0], sh, opts)}</text>')
        lower = parts[1] if len(parts) > 1 else ""
        if lower:
            out.append(f'<text x="{cx}" y="{cy + fs * 0.42 + sh_pos/3}" '
                       f'text-anchor="middle" font-family="serif" '
                       f'font-size="{sh}" fill="black">'
                       f'{_note_svg(lower, sh, opts)}</text>')
        _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # --- note simple (noire) --- #
    if len(base_tok) == 1:
        if base_tok == "尺" and opts.get('shaku_circled'):
            r = effective_fs * 0.6325
            out.append(f'<circle cx="{cx}" cy="{cy+2}" r="{r}" '
                       f'fill="none" stroke="black" stroke-width="1"/>')
        out.append(f'<text x="{cx}" y="{cy+7}" text-anchor="middle" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black">{escape(base_tok)}</text>')
    else:
        # Token non reconnu (ni position simple, ni étendue, ni séparateur).
        # Repli dégradé assumé : premiers caractères (3 max) rendus condensés
        # via textLength (patron イ中 à 120% pour 2 car., イ下尺 à 180% pour 3),
        # et alerte stderr (une seule fois par token unique).
        _warn_unknown_token(base_tok)
        shown = base_tok[:3]
        target_w = effective_fs * (1.2 if len(shown) == 2 else 1.8)
        out.append(f'<text x="{cx - target_w/2}" y="{cy+7}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">{escape(shown)}</text>')

    _render_techniques(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)


def escape(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


# --------------------------------------------------------------------------- #
# Helpers de rendu vertical
# --------------------------------------------------------------------------- #
# Caractères à pivoter de 90° sens horaire en texte vertical
# （ U+FF08, ） U+FF09, ( U+0028, ) U+0029
# 「 U+300C, 」 U+300D, 『 U+300E, 』 U+300F
VERTICAL_ROTATE_CHARS = set("（）()「」『』")


def _vertical_char(out, ch, x, y, fs, fill, family="serif"):
    """Rend un caractère en texte vertical.

    Les parenthèses （）() sont pivotées de 90° dans le sens horaire,
    comme l'exige la typographie japonaise verticale.
    """
    if ch in VERTICAL_ROTATE_CHARS:
        cy = y - fs * 0.35  # centre visuel approximatif du glyphe
        out.append(f'<text x="{x}" y="{y}" text-anchor="middle" '
                   f'font-family="{family}" font-size="{fs}" '
                   f'fill="{fill}" '
                   f'transform="rotate(90 {x} {cy})">'
                   f'{escape(ch)}</text>')
    else:
        out.append(f'<text x="{x}" y="{y}" text-anchor="middle" '
                   f'font-family="{family}" font-size="{fs}" '
                   f'fill="{fill}">{escape(ch)}</text>')


# --------------------------------------------------------------------------- #
# Ruby (guide phonétique)
# --------------------------------------------------------------------------- #
# Syntaxe KKML :
#   Mono-ruby :  安《あ》         — 1 caractère de base, 1 annotation
#   Group-ruby : ｛安里屋｝《あさとや》 — n caractères de base, 1 annotation groupée
#   Jukugo-ruby : ｛安《あ》里《さ》屋《や》｝ — groupe avec annotations individuelles
#
# Le ruby est rendu à droite de la base en mode vertical, au-dessus en
# mode horizontal. Taille = 50% de la base. Contact cadre-à-cadre (pas
# d'interstice). Le bloc ruby est centré sur le bloc base.

RUBY_OPEN  = "｛"   # U+FF5B
RUBY_CLOSE = "｝"   # U+FF5D
ANNOT_OPEN = "《"   # U+300A
ANNOT_CLOSE = "》"  # U+300B


def _parse_ruby(text):
    """Découpe une chaîne en segments avec ou sans ruby.
    Retourne une liste de dicts : plain, mono, group, jukugo."""
    segments = []
    i = 0
    n = len(text)
    plain_start = i

    while i < n:
        # Groupe ｛...｝
        if text[i] == RUBY_OPEN:
            if i > plain_start:
                segments.append({"type": "plain", "text": text[plain_start:i]})
            i += 1  # skip ｛
            group_start = i
            depth = 1
            while i < n and depth > 0:
                if text[i] == RUBY_OPEN:
                    depth += 1
                elif text[i] == RUBY_CLOSE:
                    depth -= 1
                if depth > 0:
                    i += 1
            group_content = text[group_start:i]
            i += 1  # skip ｝
            plain_start = i

            if ANNOT_OPEN in group_content:
                # Jukugo-ruby : annotations individuelles dans le groupe
                items = []
                ji = 0
                base_start = ji
                while ji < len(group_content):
                    if group_content[ji] == ANNOT_OPEN:
                        if ji > base_start:
                            base_chars = group_content[base_start:ji]
                            close_idx = group_content.index(ANNOT_CLOSE, ji)
                            ruby_text = group_content[ji+1:close_idx]
                            items.append((base_chars, ruby_text))
                            ji = close_idx + 1
                            base_start = ji
                        else:
                            close_idx = group_content.index(ANNOT_CLOSE, ji)
                            ji = close_idx + 1
                            base_start = ji
                    else:
                        ji += 1
                if base_start < len(group_content):
                    for ch in group_content[base_start:]:
                        items.append((ch, None))
                segments.append({"type": "jukugo", "items": items})
            else:
                # Group-ruby simple : ｛base｝《ruby》
                if i < n and text[i:i+1] == ANNOT_OPEN:
                    close_idx = text.index(ANNOT_CLOSE, i)
                    ruby_text = text[i+1:close_idx]
                    segments.append({"type": "group",
                                     "base": group_content, "ruby": ruby_text})
                    i = close_idx + 1
                    plain_start = i
                else:
                    # Groupe sans annotation -> plain
                    segments.append({"type": "plain", "text": group_content})

        elif text[i:i+1] == ANNOT_OPEN:
            # Mono-ruby : base = dernier caractère du texte précédent
            base_text = text[plain_start:i]
            close_idx = text.index(ANNOT_CLOSE, i)
            ruby_text = text[i+1:close_idx]
            if len(base_text) > 0:
                if len(base_text) > 1:
                    segments.append({"type": "plain", "text": base_text[:-1]})
                segments.append({"type": "mono",
                                 "base": base_text[-1], "ruby": ruby_text})
            i = close_idx + 1
            plain_start = i
        else:
            i += 1

    if plain_start < n:
        segments.append({"type": "plain", "text": text[plain_start:]})

    return segments


def _has_ruby(segments):
    return any(s["type"] in ("mono", "group", "jukugo") for s in segments)


def _ruby_needs_extra_width(text, fs):
    """Largeur supplémentaire pour le ruby à droite (0 si pas de ruby)."""
    segments = _parse_ruby(text)
    if not _has_ruby(segments):
        return 0
    ruby_fs = int(fs * RUBY_SCALE)
    return int(fs * 0.75 + ruby_fs * 0.5)


def _render_vertical_ruby(out, segments, x, y, fs, fill, sp, family="serif"):
    """Rend des segments ruby en mode vertical (ruby à droite).
    x = position horizontale du texte de base
    y = position verticale de départ (baseline du 1er caractère)
    fs = taille de base, sp = espacement vertical entre caractères de base
    Retourne le y après le dernier segment."""
    ruby_fs = int(fs * RUBY_SCALE)
    ruby_x = x + fs * 0.75  # ruby à droite, espacé de la base
    ruby_sp = sp * 0.55     # espacement ruby plus serré (car plus petit)
    # _vertical_char place y à la baseline ; le centre visuel est à y - fs*0.35.
    # Pour aligner le centre du ruby sur le centre de la base, il faut
    # compenser la différence de hauteur : baseline_ruby = baseline_base - (fs - ruby_fs)*0.35
    badj = (fs - ruby_fs) * 0.35

    for seg in segments:
        if seg["type"] == "plain":
            for ch in seg["text"]:
                _vertical_char(out, ch, x, y, fs, fill, family)
                y += sp

        elif seg["type"] == "mono":
            _vertical_char(out, seg["base"], x, y, fs, fill, family)
            if seg["ruby"]:
                n_ruby = len(seg["ruby"])
                # Centre visuel du kanji : y - fs*0.35
                # Centre du bloc ruby : ruby_start + (n_ruby-1)*ruby_sp/2 - ruby_fs*0.35
                # Égaliser les deux : ruby_start = y - fs*0.35 + ruby_fs*0.35 - (n_ruby-1)*ruby_sp/2
                ruby_start = y - (fs - ruby_fs) * 0.35 - (n_ruby - 1) * ruby_sp / 2
                for j, rc in enumerate(seg["ruby"]):
                    _vertical_char(out, rc, ruby_x, ruby_start + j * ruby_sp,
                                   ruby_fs, fill, family)
            y += sp

        elif seg["type"] == "group":
            n_base = len(seg["base"])
            for j, ch in enumerate(seg["base"]):
                _vertical_char(out, ch, x, y + j * sp, fs, fill, family)
            if seg["ruby"]:
                n_ruby = len(seg["ruby"])
                base_block_h = (n_base - 1) * sp
                ruby_block_h = (n_ruby - 1) * ruby_sp
                ruby_y = y + (base_block_h - ruby_block_h) / 2 - badj
                for j, rc in enumerate(seg["ruby"]):
                    _vertical_char(out, rc, ruby_x, ruby_y + j * ruby_sp,
                                   ruby_fs, fill, family)
            y += n_base * sp

        elif seg["type"] == "jukugo":
            for base, ruby in seg["items"]:
                if len(base) > 1:
                    # Mini-groupe dans le jukugo
                    n_base = len(base)
                    for j, ch in enumerate(base):
                        _vertical_char(out, ch, x, y + j * sp, fs, fill, family)
                    if ruby:
                        n_ruby = len(ruby)
                        base_block_h = (n_base - 1) * sp
                        ruby_block_h = (n_ruby - 1) * ruby_sp
                        ruby_y = y + (base_block_h - ruby_block_h) / 2 - badj
                        for j, rc in enumerate(ruby):
                            _vertical_char(out, rc, ruby_x,
                                           ruby_y + j * ruby_sp,
                                           ruby_fs, fill, family)
                    y += n_base * sp
                else:
                    _vertical_char(out, base, x, y, fs, fill, family)
                    if ruby:
                        n_ruby = len(ruby)
                        ruby_start = y - (fs - ruby_fs) * 0.35 - (n_ruby - 1) * ruby_sp / 2
                        for j, rc in enumerate(ruby):
                            _vertical_char(out, rc, ruby_x,
                                           ruby_start + j * ruby_sp,
                                           ruby_fs, fill, family)
                    y += sp

    return y


def _render_vertical_text(out, text, x, y, fs, fill, sp, family="serif"):
    """Rend un texte en mode vertical, avec ou sans ruby.
    Sans ruby : rendu caractère par caractère (compatibilité ascendante).
    Avec ruby : utilise _render_vertical_ruby."""
    segments = _parse_ruby(text)
    if not _has_ruby(segments):
        for ch in text:
            _vertical_char(out, ch, x, y, fs, fill, family)
            y += sp
        return y
    return _render_vertical_ruby(out, segments, x, y, fs, fill, sp, family)


def _render_horizontal_ruby(out, segments, x, y, fs, fill, family="serif"):
    """Rend des segments ruby en mode horizontal (ruby au-dessus de la base).
    x = position horizontale de départ
    y = position verticale du texte de base (baseline)
    Retourne le x après le dernier segment."""
    ruby_fs = int(fs * RUBY_SCALE)
    ruby_y = y - fs * 0.55  # ruby au-dessus, contact cadre-à-cadre
    char_w = fs * 0.55       # largeur approximative d'un caractère CJK
    ruby_char_w = ruby_fs * 0.55

    for seg in segments:
        if seg["type"] == "plain":
            out.append(f'<text x="{x}" y="{y}" font-family="{family}" '
                       f'font-size="{fs}" fill="{fill}">'
                       f'{escape(seg["text"])}</text>')
            x += len(seg["text"]) * char_w

        elif seg["type"] == "mono":
            base, ruby = seg["base"], seg["ruby"]
            out.append(f'<text x="{x}" y="{y}" font-family="{family}" '
                       f'font-size="{fs}" fill="{fill}">{escape(base)}</text>')
            if ruby:
                rw = len(ruby) * ruby_char_w
                rx = x + (char_w - rw) / 2
                out.append(f'<text x="{rx}" y="{ruby_y}" '
                           f'font-family="{family}" font-size="{ruby_fs}" '
                           f'fill="{fill}">{escape(ruby)}</text>')
            x += char_w

        elif seg["type"] == "group":
            n_base = len(seg["base"])
            base_w = n_base * char_w
            out.append(f'<text x="{x}" y="{y}" font-family="{family}" '
                       f'font-size="{fs}" fill="{fill}">'
                       f'{escape(seg["base"])}</text>')
            if seg["ruby"]:
                n_ruby = len(seg["ruby"])
                ruby_w = n_ruby * ruby_char_w
                rx = x + (base_w - ruby_w) / 2
                out.append(f'<text x="{rx}" y="{ruby_y}" '
                           f'font-family="{family}" font-size="{ruby_fs}" '
                           f'fill="{fill}">{escape(seg["ruby"])}</text>')
            x += base_w

        elif seg["type"] == "jukugo":
            for base, ruby in seg["items"]:
                if len(base) > 1:
                    n_base = len(base)
                    base_w = n_base * char_w
                    out.append(f'<text x="{x}" y="{y}" '
                               f'font-family="{family}" font-size="{fs}" '
                               f'fill="{fill}">{escape(base)}</text>')
                    if ruby:
                        n_ruby = len(ruby)
                        ruby_w = n_ruby * ruby_char_w
                        rx = x + (base_w - ruby_w) / 2
                        out.append(f'<text x="{rx}" y="{ruby_y}" '
                                   f'font-family="{family}" '
                                   f'font-size="{ruby_fs}" '
                                   f'fill="{fill}">{escape(ruby)}</text>')
                    x += base_w
                else:
                    out.append(f'<text x="{x}" y="{y}" '
                               f'font-family="{family}" font-size="{fs}" '
                               f'fill="{fill}">{escape(base)}</text>')
                    if ruby:
                        rw = len(ruby) * ruby_char_w
                        rx = x + (char_w - rw) / 2
                        out.append(f'<text x="{rx}" y="{ruby_y}" '
                                   f'font-family="{family}" '
                                   f'font-size="{ruby_fs}" '
                                   f'fill="{fill}">{escape(ruby)}</text>')
                    x += char_w

    return x


def _render_horizontal_text(out, text, x, y, fs, fill, family="serif"):
    """Rend un texte en mode horizontal, avec ou sans ruby.
    Sans ruby : un seul élément <text> (compatibilité ascendante).
    Avec ruby : utilise _render_horizontal_ruby."""
    segments = _parse_ruby(text)
    if not _has_ruby(segments):
        out.append(f'<text x="{x}" y="{y}" font-family="{family}" '
                   f'font-size="{fs}" fill="{fill}">{escape(text)}</text>')
        return x + len(text) * fs * 0.55
    return _render_horizontal_ruby(out, segments, x, y, fs, fill, family)


# --------------------------------------------------------------------------- #
# 4. CLI
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="KKML -> 工工四 SVG converter")
    ap.add_argument("input", help="fichier .kkml ou '-' pour stdin")
    ap.add_argument("-o", "--output", help="fichier SVG de sortie")
    ap.add_argument("-c", "--cols", type=int,
                    help="lignes par colonne (vertical) ou colonnes par rangée (horizontal)")
    ap.add_argument("-l", "--layout", choices=["vertical", "horizontal"],
                    help="force le layout (surcharge @layout)")
    args = ap.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
        out_path = args.output or "output.svg"
    else:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
        out_path = args.output or (args.input.rsplit(".", 1)[0] + ".svg")

    song = parse_kkml(text)
    svg = render_svg(song, cols=args.cols, layout=args.layout)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK: {out_path}  ({len(svg)} octets)", file=sys.stderr)


if __name__ == "__main__":
    main()
