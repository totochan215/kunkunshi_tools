# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
kkml2svg.py — Rend un fichier KKML (Kunkunshi Markup Language)
en une tablature 工工四 (kunkunshi) au format SVG.

Usage:
    python3 kkml2svg.py chanson.kkml -o chanson.svg
    python3 kkml2svg.py chanson.kkml            # -> chanson.svg (même nom)
    cat chanson.kkml | python3 kkml2svg.py -     # depuis stdin -> stdout

Layout vertical (défaut) : les cases se lisent de haut en bas et de
droite à gauche, comme dans les kunkunshi traditionnels.
Layout horizontal : de gauche à droite et de haut en bas (style songbook).

Métadonnée @layout vertical|horizontal|nomura|chindami|tuto|mega dans le .kkml, ou -l/--layout en CLI.

Options supplémentaires en-tête KKML (défauts : @layout vertical,
@marker on, @font_style mincho, @shaku_circled off, @shaku_sharp off) :
    @marker off           → masque la colonne marker (défaut: on)
    @font_style serif|gothic|mincho → style de police (défaut: mincho)
    @shaku_circled on     → 尺 entourés d'un cercle (défaut: off, sans cercle)
    @shaku_sharp on       → 尺♯ rendus avec le symbole ♯ (défaut: off, rendu en 尺 simple)
    @author Nom          → auteur (défaut: vide)
    @source Texte        → source de la version du morceau (texte libre ;
                           NON affiché dans le SVG, information KKML ; défaut: vide)
    @end_circle off      → désactive le marqueur de fin de chanson (cercle creux)
                           dans la colonne marker, au bas de la dernière case remplie
                           (défaut: on)
    @show_dots on        → affiche les points ・ (U+30FB) de positionnement des
                           syllabes ::vocal dans la colonne/ligne marker
                           (défaut: off, masqués — les syllabes gardent leur position)
    @lyrics_size small|medium|big → taille de police des couplets
                           (small=50%, medium=75%, big=100% de la taille des kanjis)

Ruby (guide phonétique) dans @title et ::lyrics :
    Mono-ruby  : 安《あ》            — dernier caractère avant 《》
    Group-ruby : ｛安里屋｝《あさとや》 — ｛｝ délimite le groupe de base
    Jukugo     : ｛安《あ》里《さ》｝  — groupe avec annotations individuelles
    Taille ruby = 50% de la base. À droite en vertical, au-dessus en horizontal.
    Échappement : \《 \》 \｛ \｝ = caractère littéral (l'antislash n'est retiré
    que devant ces 4 délimiteurs ; ailleurs il reste littéral).
"""
import sys
import re
import unicodedata
import argparse
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# 1. Définition des caractères de position reconnus
# --------------------------------------------------------------------------- #
# 14 positions de base (ordre croissant, 本調子) : 合乙老 (corde grave),
# 四上中尺 (corde moyenne), 工五六七八九十 (corde aiguë).
# 下 n'est PAS une position autonome : préfixe de demi-ton (下老, 下尺),
# au même titre que イ/ロ (octave/corde). Exception : 下八, kandokoro à part
# entière (女絃, 無名指, octave de 中 — traité 野村流, 増訂琉球音樂樂典 p. 14),

POSITION_CHARS = set("合乙老下四上中尺工五六七八九十")
SPECIAL_CHARS = set("○〇▲Ⓡ□×◯・#")

# Échelle du ruby par rapport à la taille de base (paramètre interne,
# non exposé comme en-tête KKML : @ruby_size volontairement absent pour le moment)
RUBY_SCALE = 0.5
EMPTY_TOKEN = "-"
SUSTAIN_TOKEN = "."
# Ordre commun des blocs de métadonnées après le titre (ordre par défaut de
# tous les layouts ; surchargeable par layout via LayoutSpec.meta_order) :
# auteur, compositeur, parolier (personnes), puis genre et origine
# (classification), enfin l'accordage : @choshi (défaut 本調子) ;
# genre n'est pas répété s'il égale author. @source et @comment ne sont PAS
# affichés : information stockée dans le KKML uniquement.
META_ORDER = ("author", "composer", "lyricist", "genre", "origin", "choshi")

# Types de sections KKML (constante globale) : ::part (titre de chanson en
# medley), ::tab, ::vocal, ::lyrics et les marqueurs de saut ::block/::page
# (mega). Chaque LayoutSpec déclare lesquels il rend via 'render_sections'
# (défaut : tous).
SECTION_KINDS = ("part", "tab", "vocal", "lyrics", "block", "page")


def _speed_text(song):
    """Texte du tempo @speed rendu horizontal : ♩=valeur (sans espace),
    ou chaîne vide si @speed est absent."""
    v = song.meta.get("speed", "").strip()
    return f"♩={v}" if v else ""


def _meta_blocks(song, speed_h=False, order=None):
    """Blocs de métadonnées dans l'ordre commun META_ORDER (order = surcharge
    par layout, LayoutSpec.meta_order ; défaut META_ORDER).
    Retourne une liste de (texte, taille_police, fill) — le bloc choshi
    porte la taille/fill de l'accordage (15, #555), les autres 12, #777.
    Le genre n'est pas répété s'il est identique à l'auteur.
    speed_h=True : le tempo @speed (♩=..., fs 12, #555) est inséré
    juste avant le bloc choshi (dernier ; en fin de liste si choshi
    n'est pas dans order)."""
    blocks = []
    genre = song.meta.get("genre", "")
    author = song.meta.get("author", "")
    order = META_ORDER if order is None else order
    for k in order:
        if k == "choshi":
            if speed_h:
                st = _speed_text(song)
                if st:
                    blocks.append((st, 12, "#555"))
            val = song.meta.get("choshi", "本調子")
            if val:
                blocks.append((val, 15, "#555"))
        else:
            val = song.meta.get(k, "")
            if not val or (k == "genre" and val == author):
                continue
            blocks.append((val, 12, "#777"))
    if speed_h and "choshi" not in order:
        st = _speed_text(song)
        if st:
            blocks.append((st, 12, "#555"))
    return blocks
REST_TOKEN = "◯"
REST_VARIANTS = {"◯", "○", "〇", "⚪"}  # O/o/0 retirés : collision romaji
REPEAT_START = "|:"
REPEAT_END = ":|"

# Marqueurs de répétition du chant (Portama vocalRepStart/vocalRepEnd).
# DÉPRÉCIÉ (2026-11-01) : |( et )| entrent en conflit avec le shuffle A:B et la
# barre | (saut de ligne de couplet). Encore acceptés avec un WARNING ;
# la boucle vocale se note désormais dans ::vocal avec (: ... :).
VREPEAT_START = "|("
VREPEAT_END = ")|"

# Caractères des marqueurs de répétition/boucles (|: :| (| )| ( )) : aucun
# n'est une variante de repos, donc sert à isoler la "base" d'un token.
_MARKER_CHARS = frozenset("|():")


def _normalize_rest_token(tk):
    """Variante de repos -> token canonique ◯ (REST_TOKEN). Au-delà du token
    exact (⚪ ○ 〇 ◯), gère les tokens composites : si la base une fois les
    marqueurs |: :| (| )| ( ) retirés est une variante de repos (ex. |:⚪),
    la variante est remplacée dans le token (ex. |:◯)."""
    if tk in REST_VARIANTS:
        return REST_TOKEN
    if any(c in _MARKER_CHARS for c in tk) and \
            "".join(c for c in tk if c not in _MARKER_CHARS) in REST_VARIANTS:
        for v in REST_VARIANTS:
            if v != REST_TOKEN:
                tk = tk.replace(v, REST_TOKEN)
    return tk

# Normalisation d'entrée pleine chasse (IME japonais) — sections tab/vocal.
# Objectif : un fichier tapé avec une méthode de saisie japonaise (pleine
# chasse) reste valide. Les équivalents pleine chasse des séparateurs et
# suffixes ASCII sont convertis vers la forme canonique au parsing.
# NB : ー (chōonpu) n'est converti en - (case vide) QUE dans les sections de
# tablature — dans ::vocal / ::lyrics il reste une voyelle longue légitime.
FULLWIDTH_MAP = {
    '／': '/',    # deux croches
    '：': ':',    # croche pointée + double croche (shuffle)
    '｜': '|',    # marques de répétition, séparateur de couplets
    '＃': '♯',    # dièse
    '#':  '♯',    # dièse
    '＋': '+',    # accords (canonique + ; ー/－ retirés : confondus avec la
                  # case vide, voir EMPTY_INPUT_VARIANTS pour le token isolé)
    '＊': '*',    # uchi-utu (alias déprécié)
    '｀': "'",    # uchi-utu (apostrophe pleine chasse)
    '＂': '"',    # nuchi-utu (guillemet pleine chasse)
    '＾': '^',    # kaki-utu
    '＜': '<',    # kachi-utu
    '＝': '=',    # accord (variante pleine chasse de = ; + reste canonique)
    '（': '(',    # koe-dashi 声だし
    '）': ')',    # koe-kiri 声切り
    # Jamais de 尻 (U+5C3B) ni de 尖 (U+5C16) en KKML : le kandokoro shaku
    # s'écrit 尺 U+5C3A (confusions fréquentes 尻/尖/尺) — alias normalisés ici.
    '尻': '尺',
    '尖': '尺',
}

# Variantes de saisie de la case vide : uniquement en token ISOLÉ.
# ー/ｰ/－ collé à un kanji (ex. 中ー) reste un token non reconnu (le chōonpu
# est une voyelle longue légitime ailleurs, on ne devine pas l'intention).
EMPTY_INPUT_VARIANTS = {'ー', 'ｰ', '－'}

# Variantes de saisie des doigtés (yubii) : formes parenthésées (U+3220-U+3223,
# « variante 2 » de notation.md) normalisées en numéraux encerclés ㊀-㊃
# (U+3280-U+3283), forme canonique.
YUBII_INPUT_VARIANTS = {'㈠': '㊀', '㈡': '㊁', '㈢': '㊂', '㈣': '㊃'}

# Kandokoro saisis en romaji (Hepburn/Kunrei tolérés) -> kanji canonique.
# Token entier uniquement : les suffixes de technique restent accolés au kanji.
ROMAJI_TO_KANJI = {
    "ai": "合",
    "otsu": "乙", "ro": "老", "rou": "老", "rō": "老",
    "shi": "四", "yon": "四",
    "jo": "上", "jou": "上", "jō": "上", "jyo": "上", "jyou": "上", "jyō": "上",
    "naka": "中", "chu": "中", "chuu": "中", "chū": "中",
    "shaku": "尺",
    "ko": "工", "kou": "工", "kō": "工",
    "go": "五",
    "roku": "六",
    "shichi": "七", "nana": "七",
    "hachi": "八",
    "kyu": "九", "kyuu": "九", "kyū": "九",
    "ju": "十", "juu": "十", "jū": "十", "jyu": "十", "jyuu": "十", "jyū": "十",
}

# Chiffres romains -> kandokoro kanji (token entier).
DIGIT_TO_KANJI = {
    "4": "四", "5": "五", "6": "六", "7": "七",
    "8": "八", "9": "九", "10": "十",
}

# Kanjis composites (radical 亻/口 accolé, hérités du gongchepu) ->
# préfixe katakana + kanji canonique.
COMPOSITE_TO_TOKEN = {
    "仮": "イ合", "俵": "イ乙", "伶": "イ老", "伍": "イ四", "仪": "イ上",
    "仲": "イ中", "伬": "イ尺", "仜": "イ工", "仐": "イ五", "俈": "イ八",
    "俇": "イ九",
    "噺": "ロ五", "唸": "ロ尺", "叿": "ロ工", "唌": "ロ四", "哈": "ロ合",
    "呾": "ロ老", "𠮟": "ロ七", "叱": "ロ七", "咈": "ロ八", "㕤": "ロ九",
}

def _normalize_tab_token(tok):
    """Convertit les variantes de saisie d'un token de tablature vers la
    forme canonique : pleine chasse (FULLWIDTH_MAP), kanjis composites,
    romaji et chiffres (token entier). Renvoie (token, a_été_modifié)."""
    out = ''.join(FULLWIDTH_MAP.get(ch, ch) for ch in tok)
    for ch, repl in YUBII_INPUT_VARIANTS.items():
        if ch in out:
            _info_input_variant(ch, repl)
            out = out.replace(ch, repl)
    for ch, repl in COMPOSITE_TO_TOKEN.items():
        if ch in out:
            _info_input_variant(ch, repl)
            out = out.replace(ch, repl)
    canon = ROMAJI_TO_KANJI.get(out, DIGIT_TO_KANJI.get(out))
    if canon is not None and canon != out:
        _info_input_variant(out, canon)
        out = canon
    # `-` et `=` restent des séparateurs d'accord valides (non canoniques ;
    # `+` est canonique) : on ne les normalise PAS en `+`, le rendu des accords
    # les accepte tous. Seul le token `-` isolé = case vide.
    # Préfixe 口 (U+53E3, radical) accepté comme variante de ロ (U+30ED) pour les
    # positions hautes 2 caractères (ex. 口上 = ロ上) :
    if len(out) == 2 and out[0] == "口" and out[1] in HIGH_POS_KANJI:
        _info_input_variant(out, "ロ" + out[1])
        out = "ロ" + out[1]
    # Bémol ASCII `b` en suffixe d'une position (ex. 合b = 合♭) ; `#` → ♯ via FULLWIDTH_MAP :
    if len(out) == 2 and out[0] in POSITION_CHARS and out[1] == "b":
        out = out[0] + "♭"
    # sélecteurs de variante (U+FE00-FE0F) retirés des tokens ::tab/::vocal :
    out = "".join(c for c in out if c not in VARIATION_SELECTORS)
    return out, out != tok

# Suffixes de technique (souhou) — apposés après le caractère de position
TECHNIQUE_SUFFIXES = {
    # uchi-utu : apostrophe ASCII ' (canonique). Alias : ｀ (normalisé
    # via FULLWIDTH_MAP) et * / ＊ (dépréciés, gardés pour compat).
    # Calibrage des positions : corrections manuelles sous Inkscape sur grille
    # de test + 3 partitions (nov. 2026). Positionnement relatif à la TAILLE
    # DE LA NOTE (note_fs), pas à la taille de l'ornement : la marque reste
    # collée au coin du kanji, note pleine ou petite (croche à cheval).
    # ' et ^ ne partagent PLUS une position moyenne : le calibrage montre
    # des réglages distincts (｀ descend sur le coin haut-droit, ⌝ reste
    # près de la tête de la note).
    # Ancrage 'corner': 'top-right' (2026-11-23) : uchi/nuchi/kaki s'ancrent sur le
    # COIN HAUT-DROIT du rectangle englobant de la note rendue (note seule,
    # composite condensé, ou groupe d'accord) : tx = cx + box_w/2 + note_fs*dx,
    # ty = box_top + note_fs*dy. box_w = largeur RENDUE (note_fs, textLength du
    # composite, largeur max des membres d'un accord) ; box_top = sommet em de la
    # note (base_y − note_fs, ou du membre le plus haut pour un accord).
    # Taille : tech_fs = int(note_fs*1.1*scale) — proportionnelle à la fs de la
    # note de rattachement, facteur propre à chaque ornement, INDÉPENDANTE de la
    # condensation du composite. dx/dy sont mesurés depuis le coin (dx = ex-dx − 0,5 ;
    # dy depuis le sommet em). Calibrage 2026-11-24 (corrections manuelles Inkscape
    # sur la grille composites, 6 layouts, facteurs moyennés par ornement) :
    # ' dx 0,00 dy 0,91 ; " dx 0,60 dy 1,02 ; ^ dx −0,07 dy 0,42 ;
    # altérations ♯/♭ dx 0,20 dy 0,80.
    "'": {'name': 'uchi-utu',  'type': 'char',   'symbol': '｀', 'pos': 'top-right',
          'corner': 'top-right', 'dx': 0.0, 'dy': 0.91, 'scale': 1.21},
    '*': {'name': 'uchi-utu',  'type': 'char',   'symbol': '｀', 'pos': 'top-right',
          'corner': 'top-right', 'dx': 0.0, 'dy': 0.91, 'scale': 1.21},
    # nuchi-utu = uchi-nuchi-utu (打ち抜き音) : hammer-on SANS tenir la note.
    # Suffixe `"` (U+0022), jumeau de `'` (uchi-utu tenu) ; `n` reste EXCLU
    # (collision romaji : yon, bon...). Glyphe rendu : ゜ (U+309C, apostrophe
    # vide), pendant creux du ｀ plein de uchi-utu. ＂ (U+FF02) normalisé en `"`.
    # Position : à DROITE de la note, à mi-hauteur du kanji (calibrage nov. 2026).
    '"': {'name': 'nuchi-utu (uchi-nuchi-utu)', 'type': 'char', 'symbol': '゜',
          'pos': 'top-right', 'corner': 'top-right', 'dx': 0.60, 'dy': 1.02, 'scale': 1.21},
    # Calibrage complémentaire (correction manuelle Inkscape, Hiragino Mincho ProN,
    # nomura 十九の春, nov. 2026) : ⌝ décalé de -3/+3 pt sur note à cheval (note_fs = ss = 18)
    # dx etait deja x note_fs : dx 0.63 - 3/18 = 0.4633. dy etait x fs (26) : pour
    # reproduire +3 pt a ss=18 -> dy = (26*-0.42 + 3)/18 = -0.44 (maintenant x note_fs).
    '^': {'name': 'kaki-utu',  'type': 'char',   'symbol': '⌝', 'pos': 'top-right',
          'corner': 'top-right', 'scale': 0.91, 'dx': -0.07, 'dy': 0.42},
    # aki-utu : chevron ∨ U+2228 (sans serif ; le V en porterait), scale 0,80
    # (test visuel PR #98). Ancrage 'cell-bottom' (retour visuel PR #98) : le chevron
    # descend jusqu'au bas de la case (ty = bas_case − note_fs*drop), il ne flotte
    # plus au milieu de la case.
    'v': {'name': 'aki-utu',   'type': 'char',   'symbol': '\u2228', 'pos': 'bottom-left',
          'dx': 0.57, 'anchor': 'cell-bottom', 'drop': 0.12, 'scale': 0.80},
    # kachi-utu : ⌞ (U+231E, coin bas-gauche), pendant du ⌝ (kaki-utu).
    # Calibrage Inkscape nov. 2026 (2e tour, glyphe ⌞) : le coin se place
    # au contact du bas-gauche du kanji, PAS au coin de la case.
    '<': {'name': 'kachi-utu', 'type': 'char',   'symbol': '⌞', 'pos': 'bottom-left',
          'dx': 0.57, 'dy': 0.44},
    's': {'name': 'kuubanchi', 'type': 'small'},

    # 声切り (koe-kiri) : borne de fin de chant □ pour le chanteur.
    # D'après 世禮 (増訂琉球音樂樂典 p. 9 et 26) : à l'intérieur de la
    # case, côté droit — pas dans la colonne marker. Suffixe : la bouche
    # se ferme APRÈS la note. (La borne d'ouverture ○ 声だし est un
    # PRÉFIXE : la bouche s'ouvre AVANT la note, ex. (中.)
    ')': {'name': 'koe-kiri (声切り)',   'type': 'char', 'symbol': '□',
          'pos': 'inside-right', 'dx': 0.36, 'dy': 0.318, 'scale': 0.42},

    # Doigtés (yubii) : suffixes ㊀-㊃ (U+3280-U+3283) apposés à la note dans
    # ::tab (ex. 合㊀), JAMAIS des positions autonomes (confusion avec le
    # silence ◯). Portama : champ cell.yubii 1-4 (PUA U+E041-E044).
    # Position (retour visuel PR #98) : fs ≈ 0,735 × fs note (12,5/17, calibrage
    # PDF Portama). Layouts VERTICAUX ('pos': 'left-third') : centre du 1er tiers
    # GAUCHE de la case (tx = cx − cell_w/3), ancré verticalement sur la CENTERLINE
    # de la note porteuse ('anchor': 'note-center') — plusieurs notes par case
    # (main + straddle). Layout HORIZONTAL ('pos_h': 'bottom-third') : tiers
    # INFÉRIEUR de la case, sur la centerline de la note (tx = cx). Tuto : non
    # affichés (opts 'render_yubii' off — collision avec la ligne vocale).
    # Ajustements ultérieurs prévus (roadmap).
    '㊀': {'name': 'yubii 1 (index 人差指)',   'type': 'char', 'symbol': '㊀',
          'pos': 'left-third', 'pos_h': 'bottom-third', 'anchor': 'note-center', 'scale': 0.67},
    '㊁': {'name': 'yubii 2 (majeur 中指)',  'type': 'char', 'symbol': '㊁',
          'pos': 'left-third', 'pos_h': 'bottom-third', 'anchor': 'note-center', 'scale': 0.67},
    '㊂': {'name': 'yubii 3 (non précisé 無名指)', 'type': 'char', 'symbol': '㊂',
          'pos': 'left-third', 'pos_h': 'bottom-third', 'anchor': 'note-center', 'scale': 0.67},
    '㊃': {'name': 'yubii 4 (auriculaire 小指)', 'type': 'char', 'symbol': '㊃',
          'pos': 'left-third', 'pos_h': 'bottom-third', 'anchor': 'note-center', 'scale': 0.67},

    # Altérations en suffixe sur TOUTE note (ex. 合♯, 合♭) — Portama acc sharp/flat.
    # ASCII `#` → ♯ via FULLWIDTH_MAP ; `b` → ♭ via _normalize_tab_token.
    # Calibrage PDF Portama (テスト節.pdf) : marque en haut-droite de la note, fs ≈ 0,53 × fs
    # note (9/17), dx ≈ +0,87 × note_fs, baseline ≈ −0,2 × fs. Au rendu, `尺♯` est
    # décomposé comme toute altération (render_cell : @shaku_sharp masque le ♯).
    '♯': {'name': 'dièse (altération)', 'type': 'char', 'symbol': '♯',
          'pos': 'top-right', 'corner': 'top-right', 'dx': 0.20, 'dy': 0.80, 'scale': 0.48},
    '♭': {'name': 'bémol (altération)', 'type': 'char', 'symbol': '♭',
          'pos': 'top-right', 'corner': 'top-right', 'dx': 0.20, 'dy': 0.80, 'scale': 0.48},
}
# Positions hautes (préfixes イ / ロ)
#   イ  = 人偏 (亻) — 1 octave au-dessus du kanji de droite
#   ロ  = 口偏 (口) — même hauteur que le kanji de droite, autre corde
# Rendu : préfixe + kanji condensés en demi-largeur (comme 下老)
HIGH_PREFIX_I = "イ"   # i- 1オクターブ上
HIGH_PREFIX_RO = "ロ"  # ro- / ko- 同音・別弦
HIGH_POS_KANJI = {"合", "乙", "老", "四", "上", "尺", "工", "五", "中"}
# Tokens valides : イ+kanji et ロ+kanji. On autorise tout préfixe 1-char + kanji.
HIGH_PREFIXES = {HIGH_PREFIX_I, HIGH_PREFIX_RO}
# Condensation des positions étendues (composites) : textLength en fraction de fs selon
# le nombre de caractères — règle UNIQUE pour tous les préfixes (下, イ, ロ) :
CONDENSE_W = {2: 1.2, 3: 1.8}  # 2 car. -> 120% de fs, 3 car. -> 180% (calibrage Inkscape nov. 2026)

# Taux de r\u00e9duction de taille (fractions de fs) \u2014 constantes S\u00c9PAR\u00c9ES mais align\u00e9es
# deux \u00e0 deux (d\u00e9cision 2026-11-23) : kuubanchi sur straddle, accord sur shuffle.
# Si un kuubanchi tombe sur un straddle, les taux se MULTIPLIENT
# (ss = int(int(fs*KUUBANCHI_RATIO) * STRADDLE_RATIO)).
STRADDLE_RATIO = 0.713            # note \u00e0 cheval (croche A/B)
KUUBANCHI_RATIO = STRADDLE_RATIO  # kuubanchi (s) align\u00e9 sur le straddle
SHUFFLE_RATIO = 0.8               # shuffle (A:B)
CHORD_RATIO = SHUFFLE_RATIO       # accord (A=B, A-B, A+B) align\u00e9 sur le shuffle


def _condensed_attrs(tok, fs):
    """Attributs textLength pour un membre COMPOSITE d'accord/shuffle : condensé via
    CONDENSE_W à sa fs RÉELLE (réduite : 72% en accord, 80%/60% en shuffle), pas à la fs
    de case. Token simple (1 car.) : aucun attribut."""
    if len(tok) > 1:
        return (f' textLength="{fs * CONDENSE_W.get(min(len(tok), 3), 1.8):g}"'
                f' lengthAdjust="spacingAndGlyphs"')
    return ''

TECHNIQUE_CHARS = set(TECHNIQUE_SUFFIXES.keys())

# Caractères de doigté (yubii) : suffixes de note uniquement, jamais des
# positions de grille (les ㊀-㊃ ne figurent PAS dans POSITION_CHARS).
YUBII_CHARS = {"㊀", "㊁", "㊂", "㊃"}

# Marqueurs de couplet :
#   一、 etc.  → numéro de couplet (CJK + 、), indent sous le 、
#   ⚫︎ ou ・  → marqueur générique, indent sous le caractère suivant
#   女　/ 男　  → couplet chanté par femmes/hommes, indent sous l'espace full-width
VERSE_NUM_RE = re.compile(r'^([一二三四五六七八九十]+)、')
# ⚫ ・ ● : indent sous le caractère suivant (offset 1)
VERSE_MARK_RE = re.compile(r'^[⚫⚪○・●]')
# 女/男 (+女) suivis d'une virgule pleine chasse 、 OU d'un espace (full-width ou non)
VERSE_GENDER_RE = re.compile(r'^([男女]+[、　\s])')
# ①-⑳ (U+2460-U+2473) : numéro de couplet, virgule pleine chasse 、 facultative après
VERSE_CIRCLED_RE = re.compile(r'^([①-⑳]、?)')


# Hayashi （…） : ligne ENTIÈREMENT parenthésée (pleine ou demi-chasse,
# avec ou sans annotations ｛…｝《…》) = interjection entre deux couplets
# (ex. だんじゅかりゆし （いめのかじありよ船《ふに》）). Un hayashi n'est
# PAS un couplet : il ne porte pas de marqueur, n'ouvre pas de couplet,
# ne compte pas dans la numérotation (marqueurs numéraux) ni dans
# l'indentation cible de la section ; il se rend en colonne propre,
# alignée en haut (indent 0).
HAYASHI_RE = re.compile(r'^[（(].*[)）]$')


def _is_hayashi(line):
    s = line.strip()
    return len(s) >= 2 and HAYASHI_RE.match(s) is not None


def _verse_indent_len(first_line):
    """Retourne le nombre de caractères à sauter pour l'indentation du couplet,
    ou 0 si pas de marqueur reconnu."""
    m = VERSE_NUM_RE.match(first_line)
    if m:
        return len(m.group(0))
    m = VERSE_GENDER_RE.match(first_line)
    if m:
        return len(m.group(0))
    m = VERSE_CIRCLED_RE.match(first_line)
    if m:
        return len(m.group(0))
    m = VERSE_MARK_RE.match(first_line)
    if m:
        return 2   # indent SOUS le caractère suivant (1 cran plus bas)
    return 0


def _verse_indent_target(lines):
    """Indentation uniforme des colonnes de continuation d'une section de
    paroles : les en-têtes de couplets occupent TOUJOURS 3 caractères
    pleine chasse (marqueur + espaces pleine chasse de remplissage :
    ー、　 / 女、　 / 男、　 / 十二、 / 男女、), donc l'indent cible vaut
    3 pour tout marqueur d'au plus 3 caractères — un marqueur suivi du
    texte sur la même ligne s'interprète comme « marqueur + espaces
    jusqu'à 3 » (ex. 安波節 「一、安波ぬ…」 -> indent 3). Un marqueur
    PLUS LONG que 3 caractères (ex. 二十二、) élargit l'indent de toute
    la section (max(3, longueur))."""
    entries = []
    for ln in lines:
        m = VERSE_NUM_RE.match(ln)
        if m:
            entries.append(len(m.group(0)))
            continue
        m = VERSE_GENDER_RE.match(ln)
        if m:
            entries.append(len(m.group(0)))
            continue
        m = VERSE_CIRCLED_RE.match(ln)
        if m:
            entries.append(len(m.group(0)))
            continue
        if VERSE_MARK_RE.match(ln):
            entries.append(2)
    if not entries:
        return 0
    return max(3, max(entries))


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
# Variantes phonétiques des sections de paroles. `::lyrics` est un alias
# de `::lyrics-ruby` (kanji avec support des rubys). Toutes les variantes
# partagent la grammaire et le rendu de la section `::lyrics` ; la variante est
# conservée sur la section (Block.variant) pour distinguer les versions
# destinées aux japonais (kanji/ruby) des versions destinées aux
# étrangers (romaji) ou aux kanas seuls.
LYRICS_VARIANTS = {"lyrics-kanji", "lyrics-romaji", "lyrics-kana", "lyrics-ruby"}

# Alias de noms de sections acceptés au parsing (rectifiés par kkml_clean) :
# fautes de frappe usuelles + anciens noms de ::part (::song depuis le 2026-11-23,
# et ::section avant, trop générique, ::tab étant déjà une section)
SECTION_ALIASES = {"tabs": "tab", "vocals": "vocal", "lyric": "lyrics",
                   "parts": "part", "songs": "part", "section": "part", "song": "part"}

# Alias de clés de métadonnées acceptés au parsing (rectifiés par kkml_clean) :
# @tuning = ancien nom de @choshi (le champ JSON Portama s'appelle `choshi`)
META_ALIASES = {"tuning": "choshi", "arrow_fill": "rep_fill"}  # @arrow_fill = ancien nom de @rep_fill

# Clés de métadonnées reconnues (pour la tolérance @cléValeur collée) —
# "tuning" y reste pour la forme collée @tuningValeur (alias, voir META_ALIASES)
META_KEYS = {"title", "choshi", "tuning", "cols", "cells_per_dan", "layout", "marker", "end_circle", "show_dots",
             "lyrics_size", "genre", "author", "composer", "lyricist",
             "origin", "source", "shaku_circled", "shaku_sharp", "speed", "font_style",
             "mega_dans",
             "page_dans", "dans_per_page", "tuto_block", "kinsoku", "page_base",
             # attributs de design surchargeables par mise en page (défaut = LayoutSpec)
             "text_color", "frame_color", "frame_width", "cell_color", "cell_width",
             "arrow_color", "arrow_width", "rep_fill", "vrep_fill", "circle_width", "arrow_fill",  # arrow_fill = alias de rep_fill (forme collée)
             # compatibilité Portama (valeurs stockées telles quelles dans song.meta)
             "musicno", "chogen", "base_note", "rythm", "rythm_mode"}
class Song:
    def __init__(self):
        self.meta = {}
        self.blocks = []
        self.cols = 12         # DEPRECATED : @cells_per_dan n'est plus une propriété de la chanson ; défaut de mise en page = 12 (vertical/horizontal)
        self.layout = "vertical"
        self.page_dans = None  # dans max par page (pagination), None = illimité


class Block:
    def __init__(self, kind, label=None):
        self.kind = kind
        self.label = label
        self.lines = []
        self.variant = None  # variante phonétique des sections lyrics-*
        self.leading_straddle = None  # token '/B' en tête de bloc ::tab : straddle sur le bord précédent de la 1re case


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

        # ligne vide : préserver comme séparateur de couplet dans une section lyrics
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
            # préfixe le plus long d'abord : @rythm_mode0 ne doit pas matcher @rythm
            for mk in sorted(META_KEYS, key=len, reverse=True):
                if key.startswith(mk) and len(key) > len(mk):
                    _info_input_variant("@" + key, "@" + mk + " " + key[len(mk):])
                    val = key[len(mk):] + ((" " + val) if val else "")
                    key = mk
                    break
        if m and not stripped.startswith("::"):
            if key in META_ALIASES:
                # alias d'ancien nom (@tuning -> @choshi) : rectifié par le cleaner
                _info_input_variant("@" + key, "@" + META_ALIASES[key])
                key = META_ALIASES[key]
            if key in ("cols", "cells_per_dan"):
                # @cells_per_dan (ex-@cols) est une indication de mise en page
                # (cellules par dan), pas une caractéristique de la chanson :
                # ignoré au parsing, le layout applique son propre défaut
                # (ou -c en CLI pour vertical/horizontal).
                pass
            elif key in ("dans_per_page", "page_dans"):
                if key == "page_dans":
                    _info_input_variant("@page_dans", "@dans_per_page")  # ancien nom, accept\u00e9
                try:
                    song.page_dans = int(val)
                except ValueError:
                    pass
            elif key == "layout":
                song.layout = val if val in ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega") else "vertical"
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
            variant = None
            if kind in ("tab-lyrics", "tab-vocals"):
                # Alias dépréciés de ::vocal (section unique pour le chant
                # syllabique aligné sur les temps).
                _info_input_variant("::" + kind, "::vocal")
                kind = "vocal"
            if kind in LYRICS_VARIANTS:
                variant = kind[len("lyrics-"):]
                kind = "lyrics"
            if kind in SECTION_ALIASES:
                # Alias acceptés (fautes de frappe usuelles, ancien nom) :
                # rectifiés en nom canonique par le cleaner
                _info_input_variant("::" + kind, "::" + SECTION_ALIASES[kind])
                kind = SECTION_ALIASES[kind]
            if kind in ("block", "page"):
                # Marqueurs de saut (layout mega uniquement) : ::block ferme le
                # bloc courant, ::page ferme la page courante, même non pleins.
                # Sans contenu ; ignorés par les autres layouts.
                if label:
                    print(f"kkml2svg: WARNING: ::{kind} n'a pas de contenu (label {label!r} ignoré)",
                          file=sys.stderr)
                label = None
            current = Block(kind, label)
            current.variant = variant
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
            continue   # retraiter la ligne dans la section implicite

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
                    # Désambiguation : `(:` / `:)` sont les marqueurs de
                    # boucle vocale (vocalRepStart/End Portama) composés avec
                    # les cases de ::tab — ils PASSENT TELS QUELS et sont
                    # déléggués à _strip_repeat_marks au rendu (symbole
                    # └○/┘● en colonne marker). Les ( ) NUS restent réservés
                    # à ::vocal : avertis + ignorés ici.
                    bare = tk
                    if bare.startswith('(:'):
                        bare = bare[2:]
                    if bare.endswith(':)'):
                        bare = bare[:-2]
                    if '(' in bare or ')' in bare:
                        _warn_once(f"'{tk}' : ( ) koedashi/koekiri ignoré dans ::tab (réservé à ::vocal)")
                        tk = bare.replace('(', '').replace(')', '')
                        if not tk:
                            continue
                    tk2, changed = _normalize_tab_token(tk)
                    if changed:
                        _info_input_variant(tk, tk2)
                    norm.append(tk2)
                norm = [_normalize_rest_token(tk) for tk in norm]
                # Token de tête "/B" d'un bloc ::tab : note à cheval sur le bord
                # PRÉCÉDENT de la première case (rang -1 ; haut en vertical, gauche en
                # horizontal) — ne consomme PAS de case.
                if not current.lines and norm and norm[0].startswith("/"):
                    lead = norm[0][1:]
                    while len(lead) > 1 and lead[-1] in TECHNIQUE_CHARS:
                        _warn_once(f"techniques ignorées sur le straddle de tête '{norm[0]}'")
                        lead = lead[:-1]
                    if lead:
                        current.leading_straddle = _normalize_rest_token(lead)
                    else:
                        _warn_once("'/' seul en tête de ::tab : ignoré")
                    norm = norm[1:]
                stray = [tk for tk in norm if tk.startswith("/")]
                if stray:
                    _warn_once(f"tokens {stray} commençant par '/' hors tête de bloc ::tab : ignorés "
                               f"(straddle de tête = '/B' en tout premier token du bloc)")
                    norm = [tk for tk in norm if not tk.startswith("/")]
                current.lines.append(norm)
            elif current.kind == "lyrics":
                # Tolérance IME : ｜ (U+FF5C, barre pleine chasse) = |.
                # Normalisé au parsing pour que la construction des colonnes
                # et l'estimation de largeur ne voient qu'une seule forme.
                if "｜" in stripped:
                    _info_input_variant("｜", "|")
                    stripped = stripped.replace("｜", "|")
                current.lines.append(stripped)
            elif current.kind == "vocal":
                # Syllabes vocales : une ligne par ligne de tablature
                # Chaque ligne contient des syllabes séparées par des espaces.
                # Un ー/ｰ/－ ISOLÉ = case vide (comme dans ::tab) ; collé à une
                # syllabe (よー) il reste la voyelle longue.
                norm = []
                for tk in stripped.split():
                    # Échappement : \ー (antislash + choonpu ー/ｰ/－) = choonpu
                    # LITTÉRAL seul dans la case (voyelle longue isolée, ex.
                    # 唐船ドーイ) — jamais pris pour une case vide.
                    if tk.startswith("\\") and tk[1:] in EMPTY_INPUT_VARIANTS:
                        if tk[1:] != chr(0x30FC):
                            _info_input_variant(tk, "\\" + chr(0x30FC))
                        tk = "\\" + chr(0x30FC)
                    if tk in EMPTY_INPUT_VARIANTS:
                        _info_input_variant(tk, EMPTY_TOKEN)
                        norm.append(EMPTY_TOKEN)
                        continue
                    # Désambiguation : boucles |: :| |( )| appartiennent à
                    # ::tab exclusivement — jamais reprises dans ::vocal.
                    # `(:` / `:)` restent des boucles vocales (admises ici).
                    for loop in (REPEAT_START, REPEAT_END, VREPEAT_START, VREPEAT_END):
                        if loop in tk and not tk.startswith("(:") and not tk.endswith(":)"):
                            _warn_once(f"'{tk}' : marqueur de boucle {loop!r} ignoré dans ::vocal (réservé à ::tab)")
                            tk = tk.replace(loop, '')
                            if not tk:
                                break
                    if tk:
                        norm.append(tk)
                current.lines.append(norm)
            i += 1
            continue

        i += 1

    return song


# --------------------------------------------------------------------------- #
# 3. Rendu SVG
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Spécifications de mise en page (une par layout) — toutes les constantes sont
# stockées en POINTS (pt), quelle que soit l'unité native de sortie SVG du
# layout : "pt" pour les pages à format fixe (nomura, chindami, mega), "px"
# pour les layouts libres (vertical, horizontal, tuto). Conversion px = pt/PX
# (exacte pour nos valeurs : ce sont des px entiers). Modèle de cadre générique :
# le cadre est écarté du bord de la feuille par les marges (margin_*) ; à
# l'intérieur, le padding (pad_*) définit le hanmen réel. frame_width = 0 ->
# cadre non tracé : le cadre virtuel se confond avec le hanmen (padding = 0).
# cell_w/cell_h = 0 -> dérivés de la page (tuto). marker_w > 0
# -> largeur marker absolue (chindami), sinon marker_ratio x cell.
# --------------------------------------------------------------------------- #
PX = 0.75          # 1 px (96 dpi) = 0,75 pt
CM = 28.3465       # 1 cm en points (1 pt = 1/72 in, universel PDF/CSS/SVG)


@dataclass(frozen=True)
class LayoutSpec:
    name: str
    unit: str = "pt"                 # unité native de sortie SVG
    page_w: float = 0                # 0 = taille libre (contenu)
    page_h: float = 0
    page_cm: tuple = ()              # (w_cm, h_cm) pour _svg_open_print
    margin_t: float = 0              # marges = écart bord de feuille -> cadre
    margin_b: float = 0
    margin_l: float = 0
    margin_r: float = 0
    pad_t: float = 0                 # padding à l'intérieur du cadre -> hanmen
    pad_b: float = 0
    pad_l: float = 0
    pad_r: float = 0
    dan_gap: float = 0               # nomura : marge de dan M entre les dans
    max_dans: int = 0                # dans max par page = dans_per_block hors mega (nomura 7, chindami 15, tuto 7)
    title_w: float = 0               # colonne titre verticale
    title_gap: float = 0
    genre_w: float = 0              # chindami : pitch de la colonne @genre (4 mm)
    genre_gap: float = 0            # chindami : gap tab<->genre et genre<->titre (1 mm)
    title_spacing: float = 0
    tuning_spacing: float = 0
    md_spacing: float = 0             # avance titre->1re méta et méta->méta (@choshi exclu si ancré en bas)
    title_fs: float = 0
    meta_fs: float = 0
    header_h: float = 0              # en-tête sans titre
    header_h_title: float = 0        # en-tête avec titre (vertical)
    gap_header: float = 0            # air en-tête -> tablature
    cell_w: float = 0                # 0 = dérivé de la page (tuto)
    cell_h: float = 0
    fs: float = 0                    # 0 = max(fs_min, fs_ratio x cell_h)
    fs_ratio: float = 0
    fs_min: int = 8
    cells_per_dan: int = 12          # cases par dan (ex-cells_per_dan / cells_per_dan)
    blocks: int = 1                  # blocs horizontaux par page (mega : 2 ; sinon bloc unique)
    block_gap: float = 0             # gap entre blocs (mega)
    dans_per_block: int = 0          # dans par bloc, 0 = illimité (hors mega = max_dans)
    marker_ratio: float = 0.5        # marker = ratio x cell (0 = pas de marker)
    marker_w: float = 0              # absolu (pt) si > 0 (chindami)
    pile_w: float = 0                # chindami : pas de pile absolu si > 0
    lyr_gap: float = 0               # gap paroles <-> grille
    lyr_size: dict = field(default_factory=lambda: {"small": 0.5, "medium": 0.75, "big": 1.0})
    lyr_fs: float = 0                # fs paroles ABSOLUE en pt (0 = dérivée : lyr_size x fs ; chindami : 10,8)
    lyr_sp_ratio: float = 1.2
    lyr_col_w_ratio: float = 1.33
    lyr_verse_gap_ratio: float = 0.8
    lyr_inline_max_ratio: float = 0   # mega : seuil paroles inline 1re page (ratio largeur utile)
    syl_cell_ratio: float = 0.26     # syllabe marker : min(ratio x cell_h, ...)
    syl_marker_ratio: float = 0.8
    syl_fs_ratio: float = 0.6        # repli si pas de marker (horizontal/tuto)
    # Attributs de design (surchargeables par métadonnées @*_color/@*_width/@rep_fill/@vrep_fill/@circle_width) :
    # couleurs au format HTML (#rgb, #rrggbb ou nom), épaisseurs en pt
    text_color: str = "#000000"      # couleur de tout le texte (fill racine SVG)
    frame_color: str = "#333333"     # filet de cadre de page
    frame_width: float = 0           # épaisseur du filet de cadre ; 0 = non tracé
    cell_color: str = "#bbbbbb"      # grille des cases (et bande marker)
    cell_width: float = 0.75         # épaisseur des filets de cases
    arrow_color: str = "#bbbbbb"     # flèches de répétition (et symboles vocaux ⚪⚫)
    arrow_width: float = 0.75        # épaisseur des flèches de boucles
    rep_fill: bool = False           # têtes des FLÈCHES de répétition instrumentale remplies (on) ou creuses (off)
    vrep_fill: bool = False          # DISQUES de répétition vocale remplis (on) ou creux (off) — séparé de rep_fill
    circle_width: float = 1.0      # épaisseur du CERCLE de 尺 (@shaku_circled on), unité native — méta @circle_width
    page_no_fs: float = 11
    # Quelles métadonnées et quelles sections ce layout rend (surcharge des
    # constantes globales META_ORDER / SECTION_KINDS) : meta_order = clés de
    # META_ORDER affichées, dans cet ordre (@title et @speed restent toujours
    # affichés) ; render_sections = types de sections rendus. render_koe /
    # render_yubii = symboles koedashi/koekiri ◯/□ et doigtés ①-④ rendus
    # dans les cases.
    meta_order: tuple = META_ORDER
    render_sections: tuple = SECTION_KINDS
    render_koe: bool = True
    render_yubii: bool = True

    def u(self, v_pt):
        """valeur en pt -> unité native du layout (int si valeur entière exacte)."""
        v = v_pt / PX if self.unit == "px" else v_pt
        return int(v) if isinstance(v, float) and v.is_integer() else v

    def frame_rect(self):
        """Cadre en pt (x0, y0, x1, y1) : écarté du bord de la feuille par les
        marges. Page libre (page_w = 0) : cadre virtuel = hanmen."""
        return (self.margin_l, self.margin_t,
                self.page_w - self.margin_r, self.page_h - self.margin_b)

    def hanmen_rect(self):
        """Hanmen en pt (x0, y0, x1, y1) : à l'intérieur du cadre, diminué du
        padding. Si frame_width = 0 et padding = 0, le hanmen = le cadre."""
        x0, y0, x1, y1 = self.frame_rect()
        return (x0 + self.pad_l, y0 + self.pad_t, x1 - self.pad_r, y1 - self.pad_b)


VERTICAL = LayoutSpec(
    name="vertical", unit="px",
    margin_t=16 * PX, margin_b=16 * PX, margin_l=16 * PX, margin_r=16 * PX,
    header_h=70 * PX, header_h_title=10 * PX, gap_header=30 * PX,
    cell_w=52 * PX, cell_h=58 * PX, fs=22 * PX, cells_per_dan=12,
    marker_ratio=0.5,
    title_w=36 * PX, title_gap=10 * PX, title_spacing=30 * PX, tuning_spacing=22 * PX,
    title_fs=26 * PX, meta_fs=15 * PX,
    md_spacing=15 * PX,
    lyr_gap=12 * PX)

HORIZONTAL = LayoutSpec(
    name="horizontal", unit="px",
    margin_t=16 * PX, margin_b=16 * PX, margin_l=16 * PX, margin_r=16 * PX,
    header_h=26 * PX, header_h_title=47 * PX, gap_header=0,   # 47 = 26 + 6 + 15 (H_TITLE_AIR)
    cell_w=52 * PX, cell_h=58 * PX, fs=22 * PX, cells_per_dan=12,
    marker_ratio=0.5,             # marker_h = cell_h // 2 (bande sous la rangée)
    title_fs=26 * PX, meta_fs=12 * PX,
    md_spacing=20 * PX,
    lyr_gap=12 * PX,
    cell_color="#999999", arrow_color="#999999")

NOMURA = LayoutSpec(
    name="nomura", unit="pt",
    page_w=21 * CM, page_h=29.7 * CM, page_cm=(21, 29.7),
    # Constantes primaires mesurées (scans) : cadre 559.3 x 745.9, centré sur
    # la page -> les marges en sont dérivées ; M = dan_gap = padding du cadre
    # (cadre<->dans, unique : aussi entre les dans). Le reste est dérivé dans
    # _render_nomura : 7 dans = 14 sous-colonnes (notes+marker) dans le hanmen
    # moins 6*M ; 12 cases dans la hauteur du hanmen.
    margin_l=(21 * CM - 559.3) / 2.0, margin_r=(21 * CM - 559.3) / 2.0,
    margin_t=(29.7 * CM - 745.9) / 2.0, margin_b=(29.7 * CM - 745.9) / 2.0,
    pad_l=14.5, pad_r=14.5, pad_t=14.5, pad_b=14.5,
    frame_width=1.5,              # filet de cadre tracé (frame_color #333333)
    dan_gap=14.5, max_dans=7, cells_per_dan=12, dans_per_block=7,
    md_spacing=8,
    marker_ratio=1.0,             # sous-colonne marker = pleine case
    fs=26.0,
    cell_color="#333333", cell_width=0.6, arrow_color="#333333", arrow_width=0.6, page_no_fs=13,
    meta_order=("choshi",))   # nomura : seule la colonne titre (titre, tempo, @choshi) affiche des méta

CHINDAMI = LayoutSpec(
    name="chindami", unit="pt",
    page_w=23 * CM, page_h=15 * CM, page_cm=(23, 15),
    # mesures recueil Chindami Kunkunshi Hyoukashuu (2026-11-24) : marges mesurées
    # au BLOC de tablature (haut ≈ 1 cm, bas ≈ 1,3 cm, droite/gauche ≈ 1,5 cm) ; la
    # colonne titre est posée DANS la marge droite (bord droit à ≈ 0,75 cm du bord
    # droit de la page). Cadre virtuel non tracé (frame_width = 0) ; la grille
    # occupe tout le hanmen (padding 0, pas de gap entre piles, dan_gap = 0).
    margin_l=1.5 * CM, margin_r=1.5 * CM,
    margin_t=1 * CM, margin_b=1.3 * CM,
    cell_w=65 / 2.785, cell_h=83 / 2.785, pile_w=97 / 2.785, marker_w=32 / 2.785,
    dan_gap=0, max_dans=16, cells_per_dan=12, dans_per_block=16, fs=12,  # max 16 dans constaté
    title_w=6 * CM / 10, title_gap=0.15 * CM, genre_w=0.4 * CM, genre_gap=0.1 * CM,  # mesures recueil 2026-11-25 : 1,5 + 6,0 + 7,5 = 15 mm au total (hors ruby) : pitch titre 6 mm ancré à 0,75 cm du bord droit, gap tab->titre 1,5 mm ; genre : 1 mm + pitch 4 mm + 1 mm
    title_fs=17.5, title_spacing=17.5,  # fs titre = fs @choshi (4,3 cm / 7 car. pour てぃんさぐぬ花)
    md_spacing=6,
    page_no_fs=10,                       # n° de page ≈ 2,5 mm de haut, baseline à 0,7 cm du bord bas
    lyr_gap=12, lyr_fs=10.8,   # 0,9 x fs=12, int() -> 10
    cell_color="#000000", arrow_color="#000000",   # une seule couleur : le noir
    cell_width=0.4, arrow_width=0.4,               # filets fins (0,4 pt, essai 2026-11-25 ; cercles de 尺 restent 0,5 pt)
    rep_fill=True,   # flèches de boucles instrumentales PLEINES (recueil 2026-11-24) ; disques vocaux creux
    circle_width=0.5,  # cercles de 尺 (@shaku_circled) : 0,5 pt (recueil 2026-11-24)
    meta_order=("genre", "choshi"))  # genre entre colonne @choshi et bloc tab ; sinon titre + @musicno + tempo + @choshi

TUTO = LayoutSpec(
    name="tuto", unit="px",
    page_w=1280 * PX, page_h=720 * PX,          # @tuto_block, défaut 1280x720
    margin_t=16 * PX, margin_b=16 * PX, margin_l=16 * PX, margin_r=16 * PX,
    cell_w=0, cell_h=0, fs=0, fs_ratio=0.38,    # dérivés du bloc (voir _render_tuto)
    cells_per_dan=8, max_dans=7, dans_per_block=7,  # 8 cases/dan, 7 dans/page
    marker_ratio=0,                              # pas de bande marker en tuto
    md_spacing=43.2 * PX,                        # gap entre blocs de la page de titre (H*0.06 à H=720)
    cell_color="#999999",
    # tuto : tablature + vocal en cellule (::lyrics exclu), pas de ◯/□ ni de
    # yubii (collision avec la ligne vocale en bas de case) ; page de titre :
    # genre, auteur, compositeur, parolier, origine, puis @choshi sous le tempo
    meta_order=("genre", "author", "composer", "lyricist", "origin", "choshi"),
    render_sections=("tab", "vocal"), render_koe=False, render_yubii=False)

MEGA = LayoutSpec(
    name="mega", unit="pt",
    page_w=42 * CM, page_h=29.7 * CM, page_cm=(42, 29.7),
    margin_t=40, margin_b=40, margin_l=40, margin_r=40,
    blocks=2, block_gap=30, cells_per_dan=12, dans_per_block=32,
    fs_ratio=0.38, marker_ratio=0.5,
    title_w=36, title_gap=10, title_spacing=30, tuning_spacing=22,
    title_fs=26, meta_fs=15, md_spacing=15,
    lyr_gap=12, lyr_inline_max_ratio=0.15,
    meta_order=("genre", "author", "choshi"))   # mega : colonne titre = genre, auteur, @choshi en bas

LAYOUTS = {"vertical": VERTICAL, "horizontal": HORIZONTAL, "nomura": NOMURA,
           "chindami": CHINDAMI, "tuto": TUTO, "mega": MEGA}


_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})|[A-Za-z]+")


def _meta_color(meta, key):
    """Métadonnée couleur au format HTML (#rgb/#rrggbb/#rrggbbaa ou nom CSS) ;
    None si absente, WARNING + None si invalide."""
    v = meta.get(key, "").strip()
    if not v:
        return None
    if _COLOR_RE.fullmatch(v):
        return v
    print(f"kkml2svg: WARNING: @{key} {v!r} n'est pas une couleur HTML valide "
          f"(#rgb, #rrggbb ou nom CSS), valeur de la mise en page conservée",
          file=sys.stderr)
    return None


def _meta_pt(meta, key, zero_ok=False):
    """Métadonnée épaisseur en pt (float > 0, ou >= 0 si zero_ok — ex.
    @frame_width 0 = cadre non tracé) ; None si absente,
    WARNING + None si invalide."""
    v = meta.get(key, "").strip()
    if not v:
        return None
    try:
        f = float(v)
    except ValueError:
        f = -1.0
    if f < 0 or (f == 0 and not zero_ok):
        print(f"kkml2svg: WARNING: @{key} {v!r} doit être un nombre "
              f"{'positif ou nul' if zero_ok else 'strictement positif'} (pt), "
              f"valeur de la mise en page conservée", file=sys.stderr)
        return None
    return f


def _meta_page_base(meta):
    """@page_base : numéro affiché sur la 1re page (entier >= 1, défaut 1)."""
    v = meta.get("page_base", "").strip()
    if not v:
        return 1
    try:
        n = int(v)
    except ValueError:
        n = 0
    if n < 1:
        print(f"kkml2svg: WARNING: @page_base {v!r} doit être un entier >= 1, "
              f"défaut 1 appliqué", file=sys.stderr)
        return 1
    return n


def _draw_page_no(out, n, x, y, fs, anchor="middle", fill="#555"):
    """Numéro de page –n– (layouts à page fixe : nomura/chindami/mega)."""
    out.append(f'<text x="{x:g}" y="{y:.2f}" text-anchor="{anchor}" '
               f'font-family="serif" font-size="{fs:g}" fill="{fill}">–{n}–</text>')


def _apply_text_color(svg, color):
    """Pose la couleur de texte sur la racine SVG et retire les fill explicites
    des <text> (ils héritent alors de la racine)."""
    svg = re.sub(r'(<text\b[^>]*?) fill="[^"]*"', lambda m: m.group(1), svg)
    return svg.replace("<svg ", f'<svg fill="{color}" ', 1)


def _draw_frame(out, spec, opts=None):
    """Trace le filet de cadre de page (layouts à page imposée) : écarté du bord
    de la feuille par les marges. Tracé seulement si frame_width > 0 (méta
    @frame_width ou défaut du layout) ; sinon le cadre reste virtuel et se
    confond avec le hanmen."""
    o = opts or {}
    fsw = o.get('frame_width')
    if fsw is None:
        fsw = spec.frame_width
    if not fsw or fsw <= 0:
        return
    fcol = o.get('frame_color') or spec.frame_color
    x0, y0, x1, y1 = spec.frame_rect()
    out.append(f'<rect x="{spec.u(x0)}" y="{spec.u(y0)}" '
               f'width="{spec.u(x1 - x0)}" height="{spec.u(y1 - y0)}" '
               f'fill="none" stroke="{fcol}" stroke-width="{spec.u(fsw):g}"/>')


def render_svg(song, cols=None, layout=None, cell_w=None, cell_h=None, font_size=None,
               page_dans=None, kinsoku=None):
    if layout is None:
        layout = song.layout
    if page_dans is None:
        page_dans = song.page_dans
    spec = LAYOUTS[layout]
    if cell_w is None:
        cell_w = spec.u(spec.cell_w) if spec.cell_w else 52
    if cell_h is None:
        cell_h = spec.u(spec.cell_h) if spec.cell_h else 58
    if font_size is None:
        font_size = spec.u(spec.fs) if spec.fs else 22
    # @cells_per_dan n'est PAS une caractéristique de la chanson : c'est une
    # propriété de mise en page. Chaque layout a son propre défaut
    # (vertical/horizontal : 12, chindami/nomura : imposé par la page), et
    # -c ne s'applique qu'aux layouts libres (vertical/horizontal).
    if cols is None:
        cols = spec.cells_per_dan if layout == "tuto" else 12
    if layout in ("chindami", "nomura", "mega"):
        cols = None  # ignoré : le layout fixe ses propres cases/dan

    title = song.meta.get("title", "")
    tuning = song.meta.get("choshi", "本調子")

    # Regrouper les sections en 4-uplets
    sections = []   # (section_title, content, kind, vocal_flat=None, lead_straddle=None)
    cur_title = None
    last_tab_index = -1
    last_tab_blk = None
    for blk in song.blocks:
        if blk.kind == "part":
            cur_title = blk.label
            continue
        if blk.kind in ("block", "page"):
            # Marqueur de saut mega : conservé dans l'ordre du flux
            sections.append((cur_title, [], blk.kind, None, None))
            continue
        if blk.kind == "tab":
            flat = []
            for toks in blk.lines:
                flat.extend(toks)
            sections.append((cur_title, flat, "tab", None, getattr(blk, "leading_straddle", None)))
            last_tab_index = len(sections) - 1
            last_tab_blk = blk
            cur_title = None
        elif blk.kind == "lyrics":
            sections.append((cur_title, blk.lines, "lyrics", None, None))
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
                sec_title, tab_content, tab_kind, _, lead0 = sections[last_tab_index]
                sections[last_tab_index] = (sec_title, tab_content, tab_kind, vocal_flat, lead0)
            else:
                # Pas de section ::tab précédente : aplatir tel quel (non rendu)
                vocal_flat = []
                for syls in blk.lines:
                    vocal_flat.extend(syls)
                sections.append((cur_title, [], "vocal", vocal_flat, None))
            cur_title = None

    # Sections rendues : constante du layout (spec.render_sections, défaut =
    # SECTION_KINDS = toutes). La section ::vocal rattachée à un ::tab voyage
    # dans le 4-uplet du tab (vocal_flat) : elle n'est conservée (rendée avec
    # son tab) que si le layout déclare aussi "vocal" — sinon tab sans vocal.
    sections = [s for s in sections if s[2] in spec.render_sections]
    if "vocal" not in spec.render_sections:
        sections = [(s[0], s[1], s[2], None, s[4]) if s[2] == "tab" else s
                    for s in sections]

    # --- Pré-calcul des dimensions (constantes du spec, en unité native) --- #
    # Page libre (vertical/horizontal) : le hanmen = marges + padding
    # (padding 0 -> hanmen = marges, comportement historique).
    MARGIN_L = spec.u(spec.margin_l + spec.pad_l)
    MARGIN_R = spec.u(spec.margin_r + spec.pad_r)
    MARGIN_T = spec.u(spec.margin_t + spec.pad_t)
    header_h = spec.u(spec.header_h)  # vertical sans titre
    if layout == "vertical" and (song.meta.get("title") or ("choshi" in spec.meta_order and song.meta.get("choshi", "本調子"))):
        # Titre/accordage/parolier/compositeur/origine rendus verticalement
        # à droite : l'en-tête haut-gauche est vide, marge de tête minimale.
        header_h = spec.u(spec.header_h_title)
    if layout != "vertical":
        # horizontal : header_h est recalculé dans _render_horizontal à
        # partir des règles verticales recyclées (air titre → tablature) ;
        # la valeur passée ici est ignorée par ce renderer.
        header_h = 26 + 8
    marker = song.meta.get("marker", "on") == "on"

    # Kinsoku JLREQ au repli des paroles (::lyrics) : CLI > méta @kinsoku >
    # défaut ('simple', sauf nomura 'off' — ce layout ne replie pas les
    # paroles au caractère, fidélité grille).
    if kinsoku is None:
        kinsoku = song.meta.get("kinsoku", "off" if layout == "nomura" else "simple")
    if kinsoku not in ("simple", "strict", "off"):
        print(f"kkml2svg: WARNING: kinsoku inconnu {kinsoku!r} (simple|strict|off), "
              f"défaut appliqué", file=sys.stderr)
        kinsoku = "off" if layout == "nomura" else "simple"

    opts = {
        'shaku_circled': song.meta.get('shaku_circled', 'off') == 'on',
        'shaku_sharp': song.meta.get('shaku_sharp', 'off') == 'on',
        'end_circle': song.meta.get('end_circle', 'on') == 'on',
        'show_dots': song.meta.get('show_dots', 'off') == 'on',
        'lyrics_size': song.meta.get('lyrics_size', 'medium'),
        'kinsoku': kinsoku,
        'render_koe': spec.render_koe,      # constante du layout (tuto : off, pas de ○/□)
        'render_yubii': spec.render_yubii,  # idem yubii (tuto : off, collision avec la ligne vocale)
        'font_family': FONT_STYLES.get(
            song.meta.get('font_style', 'mincho'), FONT_STYLE_MINCHO),
    }

    # Attributs de design : la métadonnée KKML surcharge le défaut du layout
    # (champs LayoutSpec) ; les valeurs invalides sont ignorées avec un warning.
    opts['text_color'] = _meta_color(song.meta, 'text_color') or spec.text_color
    opts['frame_color'] = _meta_color(song.meta, 'frame_color') or spec.frame_color
    _fw = _meta_pt(song.meta, 'frame_width', zero_ok=True)   # 0 = cadre non tracé
    opts['frame_width'] = spec.frame_width if _fw is None else _fw
    opts['cell_color'] = _meta_color(song.meta, 'cell_color') or spec.cell_color
    opts['cell_width'] = _meta_pt(song.meta, 'cell_width') or spec.cell_width
    opts['circle_width'] = _meta_pt(song.meta, 'circle_width') or spec.circle_width
    opts['arrow_color'] = _meta_color(song.meta, 'arrow_color') or spec.arrow_color
    opts['arrow_width'] = _meta_pt(song.meta, 'arrow_width') or spec.arrow_width
    for _fk in ('rep_fill', 'vrep_fill'):
        _fv = song.meta.get(_fk, '').strip().lower()
        if _fv in ('on', 'off'):
            opts[_fk] = (_fv == 'on')
        else:
            if _fv:
                print(f"kkml2svg: WARNING: @{_fk} {_fv!r} doit être 'on' ou 'off', "
                      f"valeur de la mise en page conservée", file=sys.stderr)
            opts[_fk] = getattr(spec, _fk)

    font_family = opts.get('font_family', 'serif')
    if layout not in ("vertical", "horizontal", "mega") and any(
            len(s) > 4 and s[4] for s in sections):
        print("kkml2svg: WARNING: straddle de tête '/B' non supporté en layout "
              f"{layout!r} (vertical/horizontal/mega seulement), ignoré",
              file=sys.stderr)
    if layout == "chindami":
        svgs = _render_chindami(song, sections, font_size, marker, opts, spec=spec)
    elif layout == "nomura":
        svgs = _render_nomura(song, sections, font_size, marker, opts, spec=spec)
    elif layout == "tuto":
        svgs = _render_tuto(song, sections, cols, page_dans, marker, opts, spec=spec)
    elif layout == "mega":
        svgs = _render_mega(song, sections, marker, opts, page_dans=page_dans, spec=spec)
    elif layout == "vertical":
        svgs = _render_vertical(song, sections, cols, cell_w, cell_h,
                                font_size, MARGIN_L, MARGIN_R, MARGIN_T, header_h,
                                marker, opts, page_dans=page_dans, spec=spec)
    else:
        svgs = [_render_horizontal(song, sections, cols, cell_w, cell_h,
                                   font_size, MARGIN_L, MARGIN_R, MARGIN_T, header_h,
                                   marker, opts, spec=spec)]

    # Post-traitement : remplacer la police serif par défaut par le style choisi
    if font_family != 'serif':
        svgs = [s.replace('font-family="serif"', f'font-family="{font_family}"')
                for s in svgs]
    # Post-traitement : couleur de texte (métadonnée @text_color ou défaut du
    # layout ; noir = rendu historique, inchangé octet par octet)
    if opts.get('text_color') and opts['text_color'].lower() not in ('black', '#000000'):
        svgs = [_apply_text_color(s, opts['text_color']) for s in svgs]
    return svgs


# --------------------------------------------------------------------------- #
# 3a. Rendu vertical (haut→bas, droite→gauche)
# --------------------------------------------------------------------------- #
def _render_vertical(song, sections, cells_per_dan, cell_w, cell_h,
                     fs, ml, mr, mt, header_h, marker=False, opts=None,
                     page_dans=None, spec=None):
    title = song.meta.get("title", "")
    tuning = song.meta.get("choshi", "本調子")

    spec = spec or VERTICAL
    MD_SP = spec.u(spec.md_spacing)  # avance avant chaque bloc méta (titre -> 1re méta, méta -> méta)
    GAP_HEADER = spec.u(spec.gap_header)       # saut après l'en-tête, avant la tablature
    VERSE_GAP = 16        # saut entre les couplets (ligne vide dans ::lyrics)
    
    # Syllabes vocales présentes (pairées à un ::tab ou autonomes)
    # → la colonne marker est forcée
    has_vocal = any(s[3] or s[2] == "vocal" for s in sections)
    marker = marker or has_vocal
    marker_w = int(cell_w * spec.marker_ratio) if marker else 0

    # --- Syllabes vocales --- #
    # Taille de police pour les syllabes : min(35% de cell_h, 80% de marker_w)
    SYLLABLE_FS = (min(int(cell_h * spec.syl_cell_ratio), int(marker_w * spec.syl_marker_ratio))
                   if marker_w > 0 else int(fs * spec.syl_fs_ratio))
    SYLLABLE_SP = int(SYLLABLE_FS * 0.9)  # espacement vertical entre syllabes

    # --- Colonne titre vertical (à droite de la grille) --- #
    TITLE_W = spec.u(spec.title_w)
    TITLE_GAP = spec.u(spec.title_gap)
    TITLE_SPACING = spec.u(spec.title_spacing)    # espacement vertical entre caractères du titre
    TUNING_SPACING = spec.u(spec.tuning_spacing)  # espacement vertical entre caractères de l'accordage
    title_ruby_w = _ruby_needs_extra_width(title, 26) if title else 0
    # largeur de la colonne titre : présente dès que titre OU accordage affiché
    title_offset = (TITLE_W + TITLE_GAP + title_ruby_w) if (title or ("choshi" in spec.meta_order and tuning)) else 0
    genre = song.meta.get("genre", "")
    author = song.meta.get("author", "")
    # Hauteurs réelles (l'écartement ruby allonge les blocs) via le plan
    def _meta_block_h(text, mfs, msp):
        if not text:
            return 0
        return _plan_vertical_ruby(_parse_ruby(_link_free(text)), mfs, msp)[1]
    def _v_block_h(text, mfs, msp, lead):
        # msp None = bloc horizontal (tempo ♩=...) : une ligne de hauteur mfs
        if msp is None:
            return lead + mfs
        return lead + _meta_block_h(text, mfs, msp)
    # Blocs de la colonne titre : le titre, puis les métadonnées dans
    # l'ordre commun META_ORDER (accordage en dernier) —
    # (texte, fs, espacement, fill, avance verticale avant la baseline)
    v_blocks = []
    if title:
        v_blocks.append((title, 26, TITLE_SPACING, "black", 20))
    for k in spec.meta_order:
        if k == "choshi":
            st = _speed_text(song)
            if st:
                # tempo ♩=... : ligne HORIZONTALE (msp None), centrée
                # dans la colonne titre, au-dessus de @choshi
                v_blocks.append((st, 12, None, "#555", MD_SP))
            val = tuning
        else:
            val = song.meta.get(k, "")
            if k == "genre" and val == author:
                continue
        if val:
            v_blocks.append((val, 15, TUNING_SPACING,
                             "#555" if k == "choshi" else "#777", MD_SP))
    # Règle alignée (layouts libres) : les métadonnées s'ajoutent SOUS le
    # titre dans la MÊME colonne, autant que de besoin, SANS repli en
    # colonne suivante ; la hauteur de page grandit pour couvrir tout le
    # flux (titre + métadonnées).
    title_total_h = (sum(_v_block_h(text, mfs, msp, lead)
                         for text, mfs, msp, _fill, lead in v_blocks)
                     + (10 if v_blocks else 0))

    # --- Paroles verticales (à gauche de la grille) --- #
    # Taille des couplets selon @lyrics_size : small=50%, medium=75%, big=100% de fs
    lyrics_size = opts.get('lyrics_size', 'medium') if opts else 'medium'
    LYRICS_FS = int(fs * spec.lyr_size.get(lyrics_size, 0.75))
    LYRICS_SP = int(LYRICS_FS * spec.lyr_sp_ratio)      # espacement vertical entre caractères
    LYRICS_COL_W = int(LYRICS_FS * spec.lyr_col_w_ratio)  # largeur d'une colonne de couplet
    LYRICS_VERSE_GAP = int(LYRICS_COL_W * spec.lyr_verse_gap_ratio)  # gap horizontal entre colonnes

    prepared = []  # (sec_title, data, kind, vocal_data=None, lead=None)
    for items in sections:
        sec_title = items[0]
        content = items[1]
        kind = items[2]
        vocal_lines = items[3] if len(items) > 3 else None
        lead = items[4] if len(items) > 4 else None
        
        if kind == "tab":
            columns = _wrap_vertical(content, cells_per_dan)
            vocal_data = _wrap_vertical(vocal_lines, cells_per_dan) if vocal_lines else None
            prepared.append((sec_title, columns, kind, vocal_data, lead))
        elif kind == "vocal":
            # Standalone vocal without tab - wrap and store
            vocal_data = _wrap_vertical(vocal_lines, cells_per_dan) if vocal_lines else None
            prepared.append((sec_title, [], kind, vocal_data, None))
        else:  # lyrics
            prepared.append((sec_title, content, kind, None, None))

    # --- Pagination (SVG multipage) --- #
    # Découpe des sections tab en pages de page_dans dans max,
    # sur le modèle des PDF Portama (12 piles/page max). Les sections
    # lyrics et le titre vertical sont répétés sur chaque page.
    def _page_slice(sec, start, end):
        sec_title, data, kind = sec[0], sec[1], sec[2]
        vocal = sec[3] if len(sec) > 3 else None
        if vocal is not None:
            vocal = vocal[start:end]
        lead = sec[4] if len(sec) > 4 and start == 0 else None
        return (sec_title, data[start:end], kind, vocal, lead)

    def _page_slice_rest(sec, data):
        vocal = sec[3] if len(sec) > 3 else None
        lead = sec[4] if len(sec) > 4 else None
        return (sec[0], data, sec[2], vocal, lead)

    pages = [prepared]
    if page_dans:
        n_tab_cols = sum(len(s[1]) for s in prepared
                         if s[2] == "tab")
        if n_tab_cols > page_dans:
            pages = []
            remaining = list(prepared)
            while any(len(s[1]) > 0 for s in remaining
                     if s[2] == "tab"):
                budget = page_dans
                first = not pages
                page_secs = []
                new_remaining = []
                for sec in remaining:
                    kind = sec[2]
                    data = sec[1]
                    if kind == "tab":
                        take = min(budget, len(data))
                        if take > 0:
                            page_secs.append(_page_slice(sec, 0, take))
                            data = data[take:]
                            budget -= take
                        if data:
                            new_remaining.append(_page_slice_rest(sec, data))
                        else:
                            if take > 0:
                                new_remaining.append((sec[0], [], sec[2], None))
                            else:
                                new_remaining.append(sec)
                    else:
                        # lyrics et sections non tab : sur la 1re page seulement
                        if first:
                            page_secs.append(sec)
                        new_remaining.append(sec)
                if not any(s[1] for s in page_secs
                           if s[2] == "tab"):
                    break  # sécurité contre boucle infinie
                pages.append(page_secs)
                remaining = new_remaining
                if len(pages) > 200:
                    break  # sécurité

    # Nombre max de colonnes d'une page (toutes pages : rendu à largeur
    # constante, la page la plus large gouverne total_w)
    max_cols = 1
    max_col_height = cells_per_dan
    for page_secs in pages:
        for items in page_secs:
            kind = items[2]
            data = items[1]
            if kind == "tab":
                max_cols = max(max_cols, len(data))

    # Calculer l'espace pour les paroles verticales
    # --- Rendu : un SVG complet par page --- #
    result = []
    for page_secs in pages:
        lyrics_sections = [(s[0], s[1]) for s in page_secs if s[2] == "lyrics"]
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
            lyrics_offset = (lyrics_total_w + spec.u(spec.lyr_gap) + LYRICS_COL_W + max_ruby_w
                             if n_verses > 0 else 0)
        else:
            lyrics_total_w = 0
            lyrics_offset = 0

        group_w = cell_w + marker_w
        total_w = max_cols * group_w + ml + mr + title_offset + lyrics_offset
        total_h = header_h + mt + GAP_HEADER

        # estimer hauteur totale
        prev_kind = None
        for items in page_secs:
            sec_title = items[0]
            data = items[1]
            kind = items[2]
            if sec_title:
                total_h += 22
            if kind == "tab" and prev_kind in ("tab", None):
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
                base_indent = _verse_indent_target(data)
                for verse in _split_verses(data):
                    for col, indent in _lyrics_columns_layout(verse, base_indent):
                        if not col:
                            continue
                        h = (indent * LYRICS_SP
                             + sum(len(ln) for ln in col) * LYRICS_SP
                             + (len(col) - 1) * LYRICS_SP)
                        lyrics_bottom = max(lyrics_bottom, ly0 + LYRICS_FS + h)
            total_h = max(total_h, lyrics_bottom + mt)

        # Colonnes du titre vertical : flux de blocs dans la hauteur de
        # page ; un bloc qui ne tient pas passe ENTIERS en colonne
        # suivante (à gauche de la précédente, largeur TITLE_W)
        if v_blocks:
            v_top = header_h + mt + GAP_HEADER
            v_bottom = total_h - mt
            v_cols = 1
            vcy = v_top
            for text, mfs, msp, _fill, lead in v_blocks:
                bh = _v_block_h(text, mfs, msp, lead)
                if vcy + bh > v_bottom and vcy > v_top:
                    v_cols += 1
                    vcy = v_top
                vcy += bh
            total_w += (v_cols - 1) * TITLE_W

        out = []
        out.append('<?xml version="1.0" encoding="UTF-8"?>')
        out.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{total_w}" height="{total_h}" '
            f'viewBox="0 0 {total_w} {total_h}">'
        )
        out.append('<rect width="100%" height="100%" fill="white"/>')

        # En-tête haut-gauche : vide en vertical (toutes les métadonnées
        # secondaires — @lyricist, @composer, @origin — sont dans la colonne
        # titre verticale à droite)

        y = header_h + mt + GAP_HEADER

        # Trouver l'index de la dernière section tab pour end_circle
        last_tab_idx = -1
        for si, items in enumerate(page_secs):
            kind = items[2]
            if kind == "tab":
                last_tab_idx = si
        # @end_circle déprécié/ignoré : le ┘● est désormais rendu par le token
        # explicite )| (vocalRepEnd), cohérent avec Portama où le marqueur est
        # posé sur une cellule et non déduit de la dernière case remplie.
        do_end_circle = False

        prev_kind = None
        for si, items in enumerate(page_secs):
            sec_title = items[0]
            data = items[1]
            kind = items[2]
            vocal_data = items[3] if len(items) > 3 else None
            lead = items[4] if len(items) > 4 else None
            if sec_title:
                out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                           f'font-size="14" fill="#333">{escape(_unescape(sec_title))}</text>')
                y += 20

            is_last_tab = (si == last_tab_idx)
            ec = do_end_circle and is_last_tab

            if kind == "tab":
                y = _draw_vertical_tab(out, data, cells_per_dan, ml, y,
                                       cell_w, cell_h, fs, total_w, mr, marker_w,
                                       title_offset, opts, end_circle=ec,
                                       vocal_data=vocal_data, syllable_fs=SYLLABLE_FS,
                                       lead=lead)
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
                    layout = _lyrics_columns_layout(verse, _verse_indent_target(data))
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

        # --- Titre vertical à droite de la grille (flux de blocs) --- #
        if v_blocks:
            ty = header_h + mt + GAP_HEADER
            # Règle alignée : PAS de repli en colonne suivante — tous les
            # blocs s'empilent sous le titre dans la même colonne, la page
            # a grandi en conséquence (title_total_h couvre le flux entier).
            tx_cur = total_w - mr - TITLE_W / 2
            vcy = ty
            for text, mfs, msp, fill, lead in v_blocks:
                if msp is None:
                    # tempo ♩=... : ligne horizontale, text-anchor=middle sur tx_cur
                    # = centerline de base du titre (hors ruby)
                    _emit_centered_text(out, text, tx_cur, vcy + lead, mfs, fill,
                                        links=True)
                    vcy += lead + mfs
                else:
                    vcy = _vertical_grouped_text(out, text, tx_cur, vcy + lead,
                                                 mfs, fill, msp, links=True)

        out.append("</svg>")
        result.append("\n".join(out))
    return result


# --------------------------------------------------------------------------- #
# 3c. Rendu Nomura-ryu (page A4 portrait,工工四 traditionnel)
# --------------------------------------------------------------------------- #
# Modèle de page mesuré/spécifié sur les recueils Nomura-ryu (AGENTS.md) :
#   - page A4 portrait (595.28 x 841.89 pt), filet de cadre à ~48 pt des bords
#     (seul le numéro de page –n– est hors du filet, en haut, alterné gauche/droite)
#   - dans = colonnes de 12 cases empilées (haut->bas), lecture droite->gauche
#   - case plus haute que large : 31.7 pt (l) x 60.6 pt (h)
#   - sous-colonne marker à gauche des notes (côté lecture suivante),
#     même largeur qu'une case, séparée par un filet
#   - jusqu'à 7 dans par page ; le titre (p.1) et les paroles (dernière
#     colonne de la dernière page) consomment chacun l'équivalent d'un dan

# CM est défini avec les LayoutSpec (haut du fichier).


# --------------------------------------------------------------------------- #
# Kinsoku (禁則処理) — JLREQ (W3C, https://www.w3.org/TR/jlreq/), annexe A.
# Appliqué UNIQUEMENT au repli des paroles (::lyrics) dans _cap_lyr_column :
# ::tab et ::vocal ne sont jamais coupés au caractère.
# --------------------------------------------------------------------------- #
# 行頭禁則 (interdit en tête de ligne) : cl-02 fermetures, cl-05 ・：；,
# cl-06 。．, cl-07 、，, cl-09 々〻, cl-10 ー, cl-11 petits kana, cl-29 ‥…〆
# (+ variantes demi-chasse et ASCII usuelles).
KINSOKU_NO_LINE_START = set(
    "）｝］」』〕〉》】〗)]}"
    "・：；。．、，:;.,"
    "々〻〆‥…"
    "ーｰ"
    "ぁぃぅぇぉゃゅょっゎゕゖァィゥェォャュョッヮヵヶｧｨｩｪｫｬｭｮｯ"
)
# ！ ？ ne sont interdits en tête de ligne qu'en kinsoku strict.
KINSOKU_NO_LINE_START_STRICT = set("！？!?")
# 行末禁則 (interdit en fin de ligne) : cl-01 ouvrantes.
KINSOKU_NO_LINE_END = set("（｛［「『〔〈《【〖([{")


def _kinsoku_adjust_cut(text, cut, kinsoku):
    """Ajuste un point de coupe entre deux sous-colonnes de paroles selon le
    kinsoku JLREQ. `cut` = nombre de caractères placés sur la sous-colonne
    courante ; le reste `text[cut:]` démarre la sous-colonne suivante.
    - 行頭禁則 avec追い出し : un caractère interdit en tête de ligne remonte
      en fin de sous-colonne courante (celle-ci déborde de la longueur du
      bloc interdit — ぶら下げ des ponctuations) ;
    - 行末禁則 : une ouvrante (cl-01) ne termine pas une ligne, elle passe à
      la sous-colonne suivante.
    `kinsoku` : 'simple' (défaut), 'strict' (ajoute ！？ en tête), 'off'.
    """
    if kinsoku == "off" or cut <= 0:
        return cut
    cut = min(cut, len(text))
    strict = kinsoku == "strict"
    while cut < len(text) and (text[cut] in KINSOKU_NO_LINE_START
                               or (strict and text[cut] in KINSOKU_NO_LINE_START_STRICT)):
        cut += 1
    while cut > 1 and text[cut - 1] in KINSOKU_NO_LINE_END:
        cut -= 1
    return cut


def _lyr_line_segments(s):
    """Découpe une ligne de paroles en segments insécables pour le repli :
    (texte, atomique, unités d'affichage). Un groupe ruby composite
    ｛base｝《ruby》 ou une base suivie de son 《ruby》 forment UN segment
    atomique (le parseur ne doit jamais voir le groupe coupé en deux) ;
    les annotations 《…》 ne comptent pas dans les unités d'affichage.
    Les délimiteurs échappés (\《 \》 \｛ \｝) restent dans le texte du segment
    (la paire est conservée pour le re-parse) mais ne comptent que pour 1
    unité affichée."""
    segs, buf, i = [], '', 0
    def flush():
        nonlocal buf
        if buf:
            segs.append((buf, False, len(_unescape(buf))))
            buf = ''
    while i < len(s):
        c = s[i]
        if c == ESCAPE and i + 1 < len(s) and s[i + 1] in ESCAPABLE:
            buf += s[i:i + 2]  # paire échappée : conservée telle quelle, 1 unité affichée
            i += 2
        elif c == RUBY_OPEN:
            j = _find_unescaped(s, RUBY_CLOSE, i + 1)
            end = len(s) if j == -1 else j + 1
            if j != -1 and end < len(s) and s[end] == ANNOT_OPEN:
                k = _find_unescaped(s, ANNOT_CLOSE, end + 1)
                end = len(s) if k == -1 else k + 1
            flush()
            base_raw = s[i + 1:j] if j != -1 else s[i + 1:end]
            units = max(1, len(_unescape(base_raw)))
            segs.append((s[i:end], True, units))
            i = end
        elif c == ANNOT_OPEN:
            k = _find_unescaped(s, ANNOT_CLOSE, i + 1)
            end = len(s) if k == -1 else k + 1
            if buf:
                if len(buf) >= 2 and buf[-2] == ESCAPE and buf[-1] in ESCAPABLE:
                    prev, buf = buf[-2:], buf[:-2]  # base échappée : l'antislash va avec
                else:
                    prev, buf = buf[-1], buf[:-1]
                flush()
                segs.append((prev + s[i:end], True, 1))
            else:
                segs.append((s[i:end], True, 1))
            i = end
        else:
            buf += c
            i += 1
    flush()
    return segs


def _cap_lyr_column(col_lines, indent, max_u, kinsoku="simple"):
    """Replie une colonne de paroles en sous-colonnes de ≤ max_u unités
    (1 unité = 1 pas d'espacement lyr_sp = 1 glyphe de paroles, annotations
    ruby exclues). Layout chindami : la hauteur de page est IMPOSÉE, une
    colonne trop longue (couplet dépassant le bas de grille) est découpée
    en sous-colonnes ; une ligne trop longue est coupée au caractère,
    UNIQUEMENT entre segments atomiques (groupes ｛…｝《…》 et base+《…》
    jamais coupés : un crash _parse_ruby avait révélé le besoin).
    Le point de coupe respecte le kinsoku JLREQ (`_kinsoku_adjust_cut`,
    paramètre `kinsoku` = 'simple'|'strict'|'off', défaut 'simple') : un
    caractère interdit en tête de sous-colonne (行頭禁則) remonte en fin de
    sous-colonne précédente (追い出し), une ouvrante (行末禁則) passe à la
    sous-colonne suivante ; 'off' = coupe au caractère (historique).
    Indentation des sous-colonnes : la première sous-colonne garde l'indent
    de la colonne (marqueur en haut = 0) ; les sous-colonnes de CONTINUATION
    issues du découpage d'une colonne MARQUEUR s'alignent au niveau
    marqueur + 1 espace pleine chasse — un marqueur suivi du texte sur la
    même ligne s'interprète comme « marqueur　» (règle uniforme, cf.
    _verse_indent_target). Ex. だんじゅかりゆし couplet 1 : le marqueur 一、
    occupe 2 unités, だんじゅ… commence à l'unité 3 → la sous-colonne de
    continuation (ぇる…) démarre AUSSI à l'unité 3 (même niveau que だん).
    Une colonne sans marqueur repliée garde son indent pour toutes ses
    sous-colonnes."""
    def line_units(s):
        return sum(u for _t, _a, u in _lyr_line_segments(s)) if s else 0
    mk = _verse_indent_len(col_lines[0]) if col_lines else 0
    if indent == 0 and mk > 0:
        cont_indent = max(3, mk)   # en-tête toujours 3 caractères pleine chasse
    else:
        cont_indent = indent
    def cost(lines, ind):
        # hauteur en unités : indent + glyphes + sauts de ligne entre lignes
        if not lines:
            return 0
        return ind + sum(line_units(l) for l in lines) + len(lines) - 1
    if not col_lines or cost(col_lines, indent) <= max_u:
        return [(col_lines, indent)]
    subs, cur, li, cur_ind = [], [], '', indent
    def close_line():
        nonlocal li
        if li:
            cur.append(li)
            li = ''
    def close_sub():
        nonlocal cur, cur_ind
        close_line()
        if cur:
            subs.append((cur, cur_ind))
            cur_ind = cont_indent
        cur = []
    for ln in col_lines:
        if not ln:
            close_line()
            if not cur or cost(cur, cur_ind) + 1 <= max_u:
                cur.append(ln)  # ligne vide : gap d'une unité
            continue
        for text, atomic, u in _lyr_line_segments(ln):
            while True:
                if not (cur or li):
                    allowed = max_u - cur_ind
                else:
                    allowed = max_u - cost(cur + [li], cur_ind)
                if u <= allowed:
                    li += text
                    break
                if not atomic:
                    cut = _kinsoku_adjust_cut(text, allowed, kinsoku) if allowed > 0 else 0
                    if (cut > 0 and cut < len(text) and text[cut - 1] == ESCAPE
                            and text[cut] in ESCAPABLE):
                        cut -= 1  # ne jamais couper entre un antislash et le délimiteur échappé
                    if cut > 0:
                        li += text[:cut]
                        text = text[cut:]
                        u = len(_unescape(text))  # le reste est du texte clair : unités affichées
                    close_sub()
                    continue  # reste du texte clair : sous-colonne neuve
                close_sub()
                if u > max_u - cur_ind:
                    # segment insécable plus grand qu'une sous-colonne :
                    # accepté seul avec léger dépassement (jamais coupé)
                    li = text
                    close_sub()
                    break
                # retenter le segment atomique dans une sous-colonne neuve
        close_line()
    close_sub()
    return subs


def _render_chindami(song, sections, fs, marker=False, opts=None, spec=None):
    """Rendu multipage façon recueils Chindami Kunkunshi : page 23 x 15 cm
    paysage (sans liseré de page, cf. scans), piles de 12 cases lues haut->bas de droite->gauche,
    colonne marker = demi-case à droite de chaque pile, titre vertical à
    droite de la page 1 surmonté du numéro de morceau (@musicno, écriture
    horizontale : n° = 0 non écrit, > 999 tronqué mod 1000, pousse le
    titre vers le bas), paroles
    (::lyrics) en colonnes verticales à gauche de la dernière page.
    Retourne une liste de SVG (un par page)."""
    title = song.meta.get("title", "")
    tuning = song.meta.get("choshi", "本調子")
    musicno = song.meta.get("musicno", "")
    font_family = (opts or {}).get('font_family', 'serif')

    spec = spec or CHINDAMI
    # La colonne marker est cosubstantielle au layout chindami : forcer
    # @marker on, quelle que soit la méta (recueil 2026-11-24).
    marker = True
    MD_SP = spec.u(spec.md_spacing)  # gap titre -> méta (tempo)
    o = opts or {}
    cs = o.get('cell_color') or spec.cell_color
    csw = o.get('cell_width') or spec.cell_width
    acol = o.get('arrow_color') or spec.arrow_color
    asw = o.get('arrow_width') or spec.arrow_width
    rfill = bool(o.get('rep_fill', spec.rep_fill))
    vfill = bool(o.get('vrep_fill', spec.vrep_fill))
    cell_w = spec.cell_w
    cell_h = spec.cell_h
    marker_w = spec.marker_w if marker else 0.0
    group_w = spec.pile_w
    rows = spec.cells_per_dan
    fs = spec.fs
    fx0, fy0, fx1, fy1 = spec.frame_rect()   # cadre = marges depuis le bord (non tracé ici)
    page_base = _meta_page_base(song.meta)
    # Colonne titre posée dans la marge droite (bord droit à 0,75 cm du bord page) :
    # elle ne consomme PAS de largeur de grille, sauf titre long (saut de colonne
    # accepté -> le bloc de tab est repoussé à gauche d'autant).
    TF = spec.title_fs or 18
    TSP = spec.title_spacing or TF
    grid_h = rows * cell_h
    title_extra_w = 0
    if title:
        h_title = TF * 0.88 + (len(title) - 1) * TSP
        n_tcols = max(1, -(-int(h_title * 100) // int(grid_h * 100)))  # ceil
        title_extra_w = (n_tcols - 1) * spec.title_w
    syllable_fs = int(marker_w * 0.8) if marker_w > 0 else 0   # grand kana ≈ 80 % de la largeur du marker (recueil)
    # Géométrie de la marge droite (mesures recueil 2026-11-25) : la colonne titre est
    # ancrée à 0,75 cm du bord droit (pitch title_w = 6 mm) et ne bouge PAS ; c'est le bloc
    # de tab qui recule pour ménager le gap title_gap (1,5 mm) avant la colonne titre.
    # Avec @genre, une colonne genre (pitch genre_w = 4 mm, gaps genre_gap = 1 mm de chaque
    # côté) s'intercale entre les deux : le bloc de tab recule de 2*genre_gap + genre_w = 6 mm.
    TG = spec.u(spec.title_gap)
    GW = spec.u(getattr(spec, 'genre_w', 0) or 0)
    GG = spec.u(getattr(spec, 'genre_gap', 0) or 0)
    genre = song.meta.get("genre", "")
    author = song.meta.get("author", "")
    has_genre = "genre" in spec.meta_order and bool(genre) and genre != author
    tx0 = spec.page_w - 0.75 * CM - spec.title_w / 2
    title_col_left = tx0 - spec.title_w / 2
    tab_right_first = min(fx1, title_col_left - (2 * GG + GW if has_genre else TG))

    # Flux : aplatir les sections tab en colonnes de 12, avec vocal sync.
    tab_columns = []
    vocal_columns = []
    for sec in sections:
        kind = sec[2]
        content = sec[1]
        vocal_lines = sec[3] if len(sec) > 3 else None
        if kind == "tab":
            cols = _wrap_vertical(list(content), rows)
            tab_columns.extend(cols)
            if vocal_lines:
                vocal_columns.extend(_wrap_vertical(list(vocal_lines), rows))
            else:
                vocal_columns.extend([None] * len(cols))
        elif kind == "vocal":
            vflat = []
            for toks in content:
                vflat.extend(toks)
            vocal_columns.extend(_wrap_vertical(vflat, rows))
    if vocal_columns and len(vocal_columns) < len(tab_columns):
        vocal_columns.extend([None] * (len(tab_columns) - len(vocal_columns)))

    lyrics_sections = [(s[0], s[1]) for s in sections if s[2] == "lyrics"]

    # Pagination façon nomura : les paroles (::lyrics) occupent la place LIBRE
    # à gauche de la dernière page de musique ; si la largeur restante ne suffit
    # pas, les colonnes de paroles passent sur des pages dédiées (per_page
    # colonnes par page). Jamais de débordement hors page, jamais de pile perdue.
    max_dans = spec.max_dans
    lyr_fs0 = int(spec.lyr_fs) if spec.lyr_fs else int(spec.fs * spec.lyr_size.get("medium", 0.75))
    lyr_col_w0 = int(lyr_fs0 * 1.33)
    lyr_gap0 = int(lyr_col_w0 * 0.8)
    lyr_sp0 = int(lyr_fs0 * 1.2)
    # Hauteur disponible pour une colonne de paroles : la page est IMPOSÉE
    # (23 x 15 cm), un couplet plus long que la hauteur de grille est REPLIÉ
    # en sous-colonnes ; l'excédent de colonnes passe sur des pages dédiées.
    # haut d'encre de la première glyphe = haut de grille (baseline =
    # GRID_TOP + 0,88·fs) ; bas d'encre de la dernière ≤ bas de grille
    max_lyr_u = int((fy1 - fy0 - lyr_fs0)
                    // lyr_sp0) + 1
    lyr_cols = []
    for _, d in lyrics_sections:
        base_indent = _verse_indent_target(d)
        for verse in _split_verses(d):
            for col_lines, indent in _lyrics_columns_layout(verse, base_indent):
                lyr_cols.extend(_cap_lyr_column(col_lines, indent, max_lyr_u,
                                                kinsoku=(opts or {}).get("kinsoku", "simple")))
    # Marge grille ↔ paroles : spec.lyr_gap (12 pt, calibrée sur les
    # scans) GARANTIE entre le bord DROIT de l'encre des paroles (demi-em +
    # ruby, qui va vers la droite, vers la grille) et le bord gauche de la
    # pile la plus à gauche. La pagination réserve sep0 = G + fs/2 +
    # max_ruby_w (ruby global conservateur) ; le rendu positionne la
    # colonne la plus à droite à L_page - sep_page (ruby page-local).
    max_ruby_w = 0
    for _, d in lyrics_sections:
        for verse in _split_verses(d):
            for line in verse:
                for seg in line.split('|'):
                    if seg:
                        max_ruby_w = max(max_ruby_w,
                                         _ruby_needs_extra_width(seg, lyr_fs0))
    # pagination conservatrice : sep0 couvre la marge G + demi-em + ruby
    # global + demi-colonne (l'ancre droite laisse la place de la colonne
    # la plus à gauche dans la fenêtre fx0..anchor)
    lyr_sep0 = spec.lyr_gap + lyr_fs0 / 2 + max_ruby_w + lyr_col_w0 / 2
    frame_w = fx1 - fx0
    per_lyr_page = max(1, int(frame_w // (lyr_col_w0 + lyr_gap0)))

    pages = []  # (c0, c1, is_first, lyr_slice)
    i = 0
    first = True
    lyr_next = 0  # prochaine colonne de paroles à placer
    while i < len(tab_columns):
        remaining = len(tab_columns) - i
        budget = max_dans   # colonne titre dans la marge : ne consomme pas de dan
        take = min(budget, remaining)
        page_frame_w = ((tab_right_first - title_extra_w - fx0) if first else frame_w)
        take = min(take, max(1, int(page_frame_w // spec.pile_w)))
        # dernière page de musique : remplir l'espace libre à gauche des
        # piles avec autant de colonnes de paroles qu'il en tient
        # (L + P + title_offset + 12 ≤ largeur utile du cadre)
        lyr_slice = None
        if i + take >= len(tab_columns) and lyr_next < len(lyr_cols):
            avail_w = page_frame_w - take * spec.pile_w
            n_fit = 0
            while (lyr_next + n_fit < len(lyr_cols) and
                   (n_fit + 1) * lyr_col_w0 + n_fit * lyr_gap0 + lyr_sep0 <= avail_w):
                n_fit += 1
            if n_fit > 0:
                lyr_slice = (lyr_next, lyr_next + n_fit)
                lyr_next += n_fit
        pages.append((i, i + take, first, lyr_slice))
        i += take
        first = False
    if not pages:
        pages = [(0, 0, True, None)]
    # pages dédiées paroles pour l'excédent
    while lyr_next < len(lyr_cols):
        pages.append((0, 0, False,
                      (lyr_next, min(lyr_next + per_lyr_page, len(lyr_cols)))))
        lyr_next += per_lyr_page

    svgs = []
    for pno, (c0, c1, is_first, lyr_slice) in enumerate(pages, 1):
        n_cols = c1 - c0
        lyr_fs = int(spec.lyr_fs) if spec.lyr_fs else int(fs * spec.lyr_size.get("medium", 0.75))
        lyr_col_w = int(lyr_fs * 1.33)
        lyrics_here = lyr_cols[lyr_slice[0]:lyr_slice[1]] if lyr_slice else []
        # marge grille↔paroles recyclée du vertical (12 + LYRICS_COL_W +
        # max_ruby_w, ruby page-local comme en vertical)
        page_ruby_w = 0
        for col_lines, _i in lyrics_here:
            for ln in col_lines:
                if ln:
                    for seg in ln.split('|'):
                        if seg:
                            page_ruby_w = max(page_ruby_w,
                                              _ruby_needs_extra_width(seg, lyr_fs))
        # marge grille↔paroles : spec.lyr_gap garantie entre l'encre
        # droite des paroles (demi-em + ruby page-local, ruby vers la grille)
        # et le bord gauche de la pile la plus à gauche
        lyr_sep = spec.lyr_gap + lyr_fs / 2 + page_ruby_w
        total_w = spec.page_w
        total_h = spec.page_h
        out = _svg_open_print(total_w, total_h, 23, 15, title=title)  # page 23 x 15 cm, 600 dpi
        _draw_frame(out, spec, o)   # tracé seulement si frame_width > 0 (défaut 0 : aucun)

        # Titre vertical à droite de la page 1, surmonté du n° de morceau
        # en écriture HORIZONTALE. Règle (cf. scans chindami) : si le n°
        # existe, son haut d'encre est aligné sur le haut de grille et il
        # REPOUSSE le titre vers le bas (le titre n'est alors plus aligné
        # sur le haut de grille) ; sans n°, le haut d'encre du titre est
        # aligné sur le haut de grille. n° = 0 -> non écrit ; n° > 999 ->
        # tronqué à la valeur sous les milliers (mod 1000 ; 0 -> non écrit).
        mno = musicno
        try:
            n = int(mno)
            if n > 999:
                n %= 1000
            mno = str(n) if n else ""
        except ValueError:
            pass  # n° non numérique : rendu tel quel, pousse le titre pareil
        if is_first and (title or mno or _speed_text(song)):
            # colonne titre ancrée à 0,75 cm du bord droit page (pitch title_w = 6 mm) —
            # elle ne bouge pas si @genre est présent : c'est le bloc de tab qui recule
            tx = tx0
            # genre présent : colonne intercalée entre le bloc de tab et la colonne titre —
            # gap genre_gap (1 mm) avec le titre, pitch genre_w (4 mm), gap genre_gap (1 mm) avec le tab ;
            # fs ≈ 50 % fs titre, vertical entre yamakakko pivotés à 90°, centré sur le bloc de tab.
            if has_genre:
                gfs = TF * 0.5
                gx = title_col_left - GG - GW / 2   # centerline de la colonne genre
                gtxt = "\\" + chr(0x300A) + genre + "\\" + chr(0x300B)   # yamakakko échappés (sinon = délimiteurs ruby), pivotés à 90° en vertical
                gy = fy0 + grid_h / 2 - (len(gtxt) - 1) * gfs / 2 + gfs * 0.88
                _vertical_grouped_text(out, gtxt, gx, gy, gfs, "#000", gfs, font_family)
            if mno:
                MNO_FS = 11   # hauteur d'encre ≈ 4 mm ; haut d'encre à 1,4 cm du haut de page
                out.append(f'<text x="{tx}" y="{1.4 * CM + MNO_FS * 0.88:.2f}" '
                           f'text-anchor="middle" font-family="serif" '
                           f'font-size="{MNO_FS}" fill="#000">{escape(mno)}</text>')
                # écart n° -> haut du titre ≈ 0,4 cm ; haut du titre = baseline
                y_title = 1.4 * CM + MNO_FS + 0.4 * CM + TF * 0.88
            else:
                y_title = 2.1 * CM   # haut du titre = baseline à 2,1 cm du haut de page
            title_end = None
            if title:
                # titre long : réparti sur plusieurs colonnes verticales (saut de
                # colonne), le bloc de tab est repoussé à gauche d'autant
                per_col = max(1, int((grid_h - TF * 0.88) // TSP) + 1)
                chunks = [title[k:k + per_col] for k in range(0, len(title), per_col)]
                for ci, chunk in enumerate(chunks):
                    title_end = _vertical_grouped_text(out, chunk, tx - ci * spec.title_w,
                                          y_title, TF, "#000", TSP, font_family,
                                          links=True)
            st = _speed_text(song)
            if st:
                # tempo ♩=... : horizontal, centré sur tx, sous le titre, au-dessus de @choshi
                base_y = title_end if title_end is not None else y_title
                _emit_centered_text(out, st, tx, base_y + MD_SP + 10 * 0.88, 10, "#000")
            if tuning and "choshi" in spec.meta_order:
                # même fs que le titre, aligné horizontalement sur sa 1re colonne
                # (la plus à droite) ; bas du @choshi = baseline à 2,3 cm du bord bas page
                yb = spec.page_h - 2.3 * CM - (len(tuning) - 1) * TSP
                _vertical_grouped_text(out, tuning, tx, yb, TF, "#000", TSP, font_family)

        # Piles de droite à gauche (jamais décalées par les paroles : celles-ci
        # occupent l'espace libre à GAUCHE, réservé par la pagination)
        x_right = (tab_right_first if is_first else fx1) - (title_extra_w if is_first else 0)
        for ci in range(n_cols):
            x = x_right - (ci + 1) * group_w
            y0 = fy0
            # rectangles
            for ri in range(rows):
                cy = y0 + ri * cell_h
                out.append(f'<rect x="{x}" y="{cy}" width="{cell_w}" height="{cell_h}" '
                           f'fill="none" stroke="{cs}" stroke-width="{csw:g}"/>')
            if marker_w > 0:
                out.append(f'<rect x="{x+cell_w}" y="{y0}" width="{marker_w}" '
                           f'height="{rows*cell_h}" fill="none" stroke="{cs}" stroke-width="{csw:g}"/>')
            # SYMBOLES de contrôle d'abord (sous le texte : kandokoro et
            # syllabes au-dessus des flèches/répétitions)
            col = tab_columns[c0 + ci]
            vcol = vocal_columns[c0 + ci] if c0 + ci < len(vocal_columns) else None
            for ri in range(rows):
                cy = y0 + ri * cell_h
                tok = col[ri] if ri < len(col) else ""
                rs, _bt, re_, vs, ve, _koe = _strip_repeat_marks(tok)
                if marker_w > 0:
                    if rs:
                        _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'start',
                                             stroke=acol, sw=asw, filled=rfill)
                    if re_:
                        _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'end',
                                             stroke=acol, sw=asw, filled=rfill)
                    if vs:
                        _render_vrep_marker(out, x + cell_w, cy, cell_h, marker_w, 'start',
                                            stroke=acol, sw=asw, filled=vfill)
                    if ve:
                        _render_vrep_marker(out, x + cell_w, cy, cell_h, marker_w, 'end',
                                            stroke=acol, sw=asw, filled=vfill)
            # NOTES par-dessus grille et symboles
            for ri in range(rows):
                cy = y0 + ri * cell_h
                tok = col[ri] if ri < len(col) else ""
                rs, base_tok, re_, vs, ve, koe = _strip_repeat_marks(tok)
                if koe and tok.lstrip('|:').startswith('(') and not base_tok.startswith('('):
                    base_tok = '(' + base_tok  # koedashi : rendre ○ dans la case
                render_cell(out, base_tok, x + cell_w / 2, cy + cell_h / 2, fs,
                            cell_w, cell_h, opts)
            if vcol and marker_w > 0 and syllable_fs > 0:
                # _draw_vertical_vocal positionne via total_w/mr ; on lui passe
                # un mr fictif pour que la colonne tombe sur le x de la pile.
                fake_mr = total_w - (x + group_w)
                _draw_vertical_vocal(out, [vcol], rows, fx0, y0, cell_w, cell_h, fs,
                                     total_w, fake_mr, marker_w, 0, opts, syllable_fs)
        # Paroles verticales à gauche de la dernière page
        if lyrics_here:
            lyr_sp = int(lyr_fs * 1.2)
            # ancre DROITE : la colonne la plus à droite est posée à
            # (bord gauche de la pile la plus à gauche) - lyr_sep, ce qui
            # garantit la marge spec.lyr_gap entre son encre droite
            # (demi-em + ruby) et la grille ; pages dédiées paroles :
            # ancre = bord droit du cadre
            lyr_anchor = (x_right - n_cols * group_w) if n_cols > 0 else fx1
            vx = lyr_anchor - lyr_sep
            for col_lines, indent in lyrics_here:
                # haut d'encre de la première glyphe = haut de grille
                cy = fy0 + lyr_fs * 0.88
                cy += indent * lyr_sp
                for ln in col_lines:
                    # _render_vertical_text retourne la position après le
                    # dernier glyphe affiché (les annotations ruby ne
                    # consomment PAS d'unités) : n'ajouter qu'UN gap de
                    # ligne, jamais len(ln) brut (double avancement,
                    # débordement des colonnes rubyées)
                    cy = _vertical_grouped_text(out, ln, vx, cy, lyr_fs, "#000",
                                                lyr_sp, font_family)
                    cy += lyr_sp
                vx -= lyr_col_w + int(lyr_col_w * 0.8)
        # n° de page : baseline à 0,7 cm du bord inférieur de la feuille, centré en x
        _draw_page_no(out, page_base + pno - 1, total_w / 2,
                      total_h - 0.7 * CM, spec.page_no_fs, fill="#000")
        out.append('</svg>')
        svgs.append("\n".join(out))
    return svgs


def _render_nomura(song, sections, fs, marker=False, opts=None, spec=None):
    """Rendu multipage calqué sur les planches Nomura-ryu.

    Retourne une liste de SVG (un par page). Chaque dan est un groupe
    case-notes + marker ; la colonne marker héberge les syllabes vocales
    et les flèches de répétition. Le titre (vertical, calligraphique)
    occupe la colonne la plus à droite de la page 1 ; les paroles
    occupent la dernière colonne de la dernière page.
    """
    title = song.meta.get("title", "")
    tuning = song.meta.get("choshi", "本調子")
    # La colonne marker est cosubstantielle du layout nomura : forcer
    # @marker on, quelle que soit la méta (et même sans ::vocal).
    marker = True
    # Idem 尺♯ : toujours rendus en 尺 simples, jamais encerclés.
    if opts is not None:
        opts['shaku_sharp'] = False
        opts['shaku_circled'] = False

    spec = spec or NOMURA
    MD_SP = spec.u(spec.md_spacing)  # gap titre -> méta (tempo)
    o = opts or {}
    fcol = o.get('frame_color') or spec.frame_color
    _fsw = o.get('frame_width')
    fsw = spec.frame_width if _fsw is None else _fsw   # 0 = cadre non tracé
    cs = o.get('cell_color') or spec.cell_color
    csw = o.get('cell_width') or spec.cell_width
    acol = o.get('arrow_color') or spec.arrow_color
    asw = o.get('arrow_width') or spec.arrow_width
    rfill = bool(o.get('rep_fill', spec.rep_fill))
    vfill = bool(o.get('vrep_fill', spec.vrep_fill))
    fx0, fy0, fx1, fy1 = spec.frame_rect()      # cadre = marges depuis le bord
    page_base = _meta_page_base(song.meta)
    hx0, hy0, hx1, hy1 = spec.hanmen_rect()     # hanmen = cadre - padding
    cell_h = (fy1 - fy0 - 2 * spec.dan_gap) / spec.cells_per_dan
    cell_w = (fx1 - fx0 - 8 * spec.dan_gap) / 14.0
    marker_w = cell_w * spec.marker_ratio if marker else 0.0
    group_w = cell_w + marker_w
    rows = spec.cells_per_dan
    # Taille des notes ajustée visuellement ~26 pt (planches : encre ≈ 0,43 ×
    # case ; mincho moderne plus condensé que le pinceau d'origine).
    fs = 26.0

    # --- Flux : aplatir toutes les sections tab en colonnes de 12 --- #
    tab_columns = []
    vocal_columns = []
    for sec in sections:
        kind = sec[2]
        content = sec[1]
        vocal_lines = sec[3] if len(sec) > 3 else None
        if kind == "tab":
            flat = list(content)
            cols = _wrap_vertical(flat, rows)
            tab_columns.extend(cols)
            if vocal_lines:
                vocal_columns.extend(_wrap_vertical(list(vocal_lines), rows))
            else:
                vocal_columns.extend([None] * len(cols))
        elif kind == "vocal":
            vflat = []
            for toks in content:
                vflat.extend(toks)
            vocal_columns.extend(_wrap_vertical(vflat, rows))
    if vocal_columns and len(vocal_columns) < len(tab_columns):
        vocal_columns += [None] * (len(tab_columns) - len(vocal_columns))

    # --- Sections lyrics (couplets) : colonnes verticales --- #
    lyrics_sections = [(s[0], s[1]) for s in sections if s[2] == "lyrics"]

    # --- Pagination : 7 dans par page ; titre en p.1, paroles en dernière --- #
    # capacité par page : 7 - 1 (titre p.1) ; la dernière page réserve
    # autant de colonnes que nécessaire pour les couplets (>= 1 si paroles)
    lyrics_col_count = 0
    lyrics_layouts = []   # [(col_lines, indent)]
    # Hauteur disponible pour une colonne de paroles : le hanmen est IMPOSÉ
    # (page A4 fixe) — comme en chindami, une colonne trop longue est REPLIÉE
    # en sous-colonnes de ≤ max_lyr_u unités (_cap_lyr_column, kinsoku JLREQ) ;
    # les sous-colonnes comptent dans la pagination (elles consomment des dans
    # virtuels comme les colonnes pleines).
    lyr_col_w_n = group_w / 3.0
    lyr_fs_n = lyr_col_w_n * 0.7
    lyr_sp_n = lyr_fs_n * 1.2
    max_lyr_u = int((rows * cell_h - lyr_fs_n) // lyr_sp_n) + 1
    kinsoku_n = o.get("kinsoku", "off")
    for _, data in lyrics_sections:
        base_indent = _verse_indent_target(data)
        for verse in _split_verses(data):
            for col_lines, indent in _lyrics_columns_layout(verse, base_indent):
                if not col_lines:
                    continue
                for sub_lines, sub_ind in _cap_lyr_column(col_lines, indent, max_lyr_u,
                                                          kinsoku=kinsoku_n):
                    lyrics_layouts.append((sub_lines, sub_ind))
                    lyrics_col_count += 1

    # au plus 3 colonnes de couplets par dan virtuel
    LYRICS_MAX_COLS = 3
    lyrics_dans = (lyrics_col_count + LYRICS_MAX_COLS - 1) // LYRICS_MAX_COLS

    first_cap = spec.max_dans - (1 if (title or ("choshi" in spec.meta_order and tuning)) else 0)
    # La musique remplit les pages normalement (p.1 : 7 - 1 si titre,
    # puis 7 dans). Les couplets occupent les dans LIBRES de la dernière
    # page de musique ; l'excédent de dans virtuels passe sur des pages
    # suivantes dédiées aux couplets (7 dans virtuels max par page).
    # Jamais de débordement du cadre, jamais de dan de musique perdu.
    music_pages = []
    remaining = list(tab_columns)
    remaining_vocal = list(vocal_columns)
    pi = 0
    while remaining:
        cap = first_cap if pi == 0 else spec.max_dans
        take = remaining[:cap]
        take_v = remaining_vocal[:cap] if remaining_vocal else [None] * len(take)
        remaining = remaining[cap:]
        if remaining_vocal:
            remaining_vocal = remaining_vocal[cap:]
        music_pages.append((take, take_v))
        pi += 1

    # dans virtuels de couplets acceptés sur la dernière page de musique
    if music_pages:
        last_cols = music_pages[-1][0]
        last_cap = first_cap if len(music_pages) == 1 else spec.max_dans
        free = last_cap - len(last_cols)
    else:
        free = first_cap
    lyr_here = min(lyrics_dans, max(0, free))
    lyr_left = lyrics_dans - lyr_here

    pages = []          # (cols, vocal_cols, is_last, lyr_dans_here, lyr_col_offset)
    lyr_col_offset = 0
    for mi, (mcols, mcols_v) in enumerate(music_pages):
        is_last = (mi == len(music_pages) - 1) and lyr_left == 0
        here = lyr_here if mi == len(music_pages) - 1 else 0
        pages.append((mcols, mcols_v, is_last, here, lyr_col_offset))
        if here:
            lyr_col_offset += here * LYRICS_MAX_COLS
    if not music_pages:
        is_last = lyr_left == 0
        pages.append(([], [], is_last, lyr_here, 0))
        lyr_col_offset += lyr_here * LYRICS_MAX_COLS
    while lyr_left > 0:
        here = min(lyr_left, spec.max_dans)
        lyr_left -= here
        pages.append(([], [], lyr_left == 0, here, lyr_col_offset))
        lyr_col_offset += here * LYRICS_MAX_COLS

    # --- Géométrie page --- #
    grid_h = rows * cell_h
    # la grille occupe le hanmen (cadre - padding = marge de dan M)
    grid_y0 = hy0

    # 3 colonnes de couplets = 1 dan virtuel exactement
    LYRICS_COL_W = group_w / 3.0
    LYRICS_FS = LYRICS_COL_W * 0.7
    LYRICS_SP = LYRICS_FS * 1.2

    result = []
    n_pages = len(pages)
    for pi, (cols, cols_v, is_last, lyr_here, lyr_col_offset) in enumerate(pages):
        has_title_col = (pi == 0 and (title or ("choshi" in spec.meta_order and tuning)))
        n_lyr_on_page = lyr_here

        # colonnes occupées : titre (droite), dans, paroles (gauche)
        total_groups = len(cols)
        occupied = total_groups + (1 if has_title_col else 0) + n_lyr_on_page

        out = []
        out.append('<?xml version="1.0" encoding="UTF-8"?>')
        out.extend(_svg_open_print(spec.page_w, spec.page_h, 21, 29.7, title=title)[1:])  # A4, 600 dpi

        # filet de cadre (origine du placement relatif) ; tracé si frame_width > 0
        _draw_frame(out, spec, o)

        pno = page_base + pi
        if pno % 2 == 0:
            pnx, pnanchor = fx0, "start"
        else:
            pnx, pnanchor = fx1, "end"
        _draw_page_no(out, pno, pnx, fy0 - 8, spec.page_no_fs, pnanchor)

        # --- placement des groupes, droite -> gauche --- #
        # positions x (bord droit de chaque groupe), depuis le bord droit du
        # hanmen ; le premier groupe (titre ou dan) est décalé d'une marge de
        # dan du filet, comme sur les planches
        x_right = hx1
        # 1. colonne titre
        if has_title_col:
            # le bloc titre consomme un dan complet (cases + marker).
            # Centré exactement entre le filet droit de la première
            # colonne marker et le filet droit de la page ; calibré sur
            # les planches : démarrage ~1,8 case sous le haut de grille.
            tx = x_right - group_w / 2
            ty = grid_y0 + cell_h * 1.8
            if title:
                ty_end = _render_vertical_text(out, title, tx, ty,
                                               cell_h * 0.43, "black",
                                               cell_h * 0.5, links=True)
            else:
                ty_end = ty
            st = _speed_text(song)
            if st:
                # tempo ♩=... : horizontal, text-anchor=middle sur tx (centerline de
                # base du titre, hors ruby), sous le titre, au-dessus de @choshi
                _emit_centered_text(out, st, tx, ty_end + MD_SP + 12 * 0.88, 12, "#555")
            if tuning and "choshi" in spec.meta_order:
                tyb = grid_y0 + grid_h - 4 - len(tuning) * 20.0
                for i, ch in enumerate(tuning):
                    _vertical_char(out, ch, tx, tyb + i * 20.0, 13.0, "#555")
            x_right -= (group_w + spec.dan_gap)

        # 2. dans (cases + marker)
        for ci, col in enumerate(cols):
            vocal_col = cols_v[ci] if ci < len(cols_v) else None
            gx = x_right - group_w
            # cases [gx, gx+cell_w], marker à DROITE [gx+cell_w, gx+group_w]
            nx = gx                     # bord gauche des cases
            mx = gx + cell_w            # bord gauche du marker
            # filets du marker : deux verticales pleine hauteur + fermetures
            # horizontales haut/bas de la bande
            if marker_w > 0:
                out.append(f'<line x1="{mx}" y1="{grid_y0}" x2="{mx}" '
                           f'y2="{grid_y0 + grid_h}" stroke="{cs}" '
                           f'stroke-width="{csw:g}"/>')
                out.append(f'<line x1="{gx + group_w}" y1="{grid_y0}" '
                           f'x2="{gx + group_w}" y2="{grid_y0 + grid_h}" '
                           f'stroke="{cs}" stroke-width="{csw:g}"/>')
                out.append(f'<line x1="{mx}" y1="{grid_y0}" '
                           f'x2="{gx + group_w}" y2="{grid_y0}" '
                           f'stroke="{cs}" stroke-width="{csw:g}"/>')
                out.append(f'<line x1="{mx}" y1="{grid_y0 + grid_h}" '
                           f'x2="{gx + group_w}" y2="{grid_y0 + grid_h}" '
                           f'stroke="{cs}" stroke-width="{csw:g}"/>')
            # grille : cases empilées
            for ri in range(rows):
                cy = grid_y0 + ri * cell_h
                out.append(f'<rect x="{nx}" y="{cy}" width="{cell_w}" '
                           f'height="{cell_h}" fill="none" stroke="{cs}" '
                           f'stroke-width="{csw:g}"/>')
            # SYMBOLES de contrôle d'abord (sous le texte)
            for ri in range(rows):
                cy = grid_y0 + ri * cell_h
                tok = col[ri] if ri < len(col) else ""
                rs, _bt, re_, vs, ve, _koe = _strip_repeat_marks(tok)
                if marker_w > 0:
                    if rs:
                        _render_repeat_arrow(out, mx, cy, cell_h, marker_w, 'start',
                                             stroke=acol, sw=asw, filled=rfill)
                    if re_ and marker_w > 0:
                        _render_repeat_arrow(out, mx, cy, cell_h, marker_w, 'end',
                                             stroke=acol, sw=asw, filled=rfill)
                    if vs and marker_w > 0:
                        _render_vrep_marker(out, mx, cy, cell_h, marker_w, 'start',
                                            stroke=acol, sw=asw, filled=vfill)
                    if ve and marker_w > 0:
                        _render_vrep_marker(out, mx, cy, cell_h, marker_w, 'end',
                                            stroke=acol, sw=asw, filled=vfill)
            # NOTES par-dessus grille et symboles
            for ri in range(rows):
                cy = grid_y0 + ri * cell_h
                tok = col[ri] if ri < len(col) else ""
                rs, base_tok, re_, vs, ve, koe = _strip_repeat_marks(tok)
                if koe and tok.lstrip('|:').startswith('(') and not base_tok.startswith('('):
                    base_tok = '(' + base_tok  # koedashi : rendre ○ dans la case
                render_cell(out, base_tok, nx + cell_w / 2, cy + cell_h / 2,
                            fs, cell_w, cell_h, opts)
            # syllabes vocales dans le marker — logique points commune
            # (_vocal_elements) : chaque élément (point ・ ou syllabe) occupe une
            # sous-partie verticale de la case, bloc centré (comme _draw_vertical_vocal).
            if vocal_col and marker_w > 0:
                syl_fs = min(9.0, marker_w * 0.55)
                step = syl_fs * 1.15  # bien > fs : pas de chevauchement entre petits kana
                for ri, syllable in enumerate(vocal_col):
                    if ri >= rows:
                        break
                    if not syllable or syllable == "-":
                        continue
                    cy = grid_y0 + ri * cell_h
                    sx = gx + cell_w + marker_w / 2
                    elems = _vocal_elements(syllable)
                    n = max(len(elems), 1)
                    # Bornes de chant ( ) : ○/□ DANS la case (bord droit), alignés
                    # en hauteur sur l'élément (syllabe ou point, même masqué)
                    # auquel la borne est rattachée.
                    slots, _n = _vocal_paren_slots(syllable)
                    if slots and o.get('render_koe', True):
                        ss = int(fs * 0.42)
                        xk = gx + cell_w * 0.86
                        for ch, j in slots:
                            yk = cy + cell_h / 2 + cell_h * (j / n) + ss * 0.318
                            g = chr(0x25CB) if ch == "(" else chr(0x25A1)
                            out.append(f'<text x="{xk:g}" y="{yk:g}" text-anchor="middle" '
                                       f'font-family="serif" font-size="{ss}" fill="black">{g}</text>')
                    for j, el in enumerate(elems):
                        # 1er élément au centre de la case, puis cell_h * j/n (comme vertical/horizontal)
                        sy = cy + cell_h / 2 + cell_h * (j / n) + syl_fs / 3
                        if el == "" and o.get('show_dots'):
                            out.append(f'<text x="{sx}" y="{sy}" text-anchor="middle" '
                                       f'font-family="serif" font-size="{syl_fs}" '
                                       f'fill="#333">{chr(0x30FB)}</text>')
                        else:
                            for k, ch in enumerate(el):
                                yy = sy + k * step
                                if ch == "ー":
                                    ry = yy - syl_fs * 0.35
                                    out.append(f'<text x="{sx}" y="{yy}" text-anchor="middle" '
                                               f'font-family="serif" font-size="{syl_fs}" '
                                               f'fill="#333" '
                                               f'transform="rotate(90 {sx} {ry})">'
                                               f'{escape(ch)}</text>')
                                else:
                                    out.append(f'<text x="{sx}" y="{yy}" text-anchor="middle" '
                                               f'font-family="serif" font-size="{syl_fs}" '
                                               f'fill="#333">{escape(ch)}</text>')
            x_right -= (group_w + spec.dan_gap)

        # 3. paroles : colonnes verticales à gauche (dans virtuels de CETTE page)
        if lyr_here > 0:
            for vi, (col_lines, verse_indent) in enumerate(
                    lyrics_layouts[lyr_col_offset:lyr_col_offset + lyr_here * LYRICS_MAX_COLS]):
                # 3 colonnes par dan virtuel ; un dan supplémentaire est
                # sauté (marge M) pour la suite des couplets
                dan_i = vi // LYRICS_MAX_COLS
                col_i = vi % LYRICS_MAX_COLS
                vx = (x_right - LYRICS_COL_W / 2
                      - dan_i * (group_w + spec.dan_gap)
                      - col_i * LYRICS_COL_W)
                cy = grid_y0 + LYRICS_FS
                if verse_indent > 0:
                    cy += verse_indent * LYRICS_SP
                for li, line in enumerate(col_lines):
                    if li > 0:
                        cy += LYRICS_SP
                    cy = _render_vertical_text(out, line, vx, cy, LYRICS_FS,
                                               "#333", LYRICS_SP)

        out.append("</svg>")
        result.append("\n".join(out))
    return result


def _wrap_vertical(items, cells_per_dan):
    """Découpe une liste plate en colonnes verticales de cells_per_dan éléments."""
    columns = []
    for i in range(0, len(items), cells_per_dan):
        columns.append(items[i : i + cells_per_dan])
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


def _pad_inline_marker(ln):
    """Matérialise la règle « en-tête toujours 3 caractères pleine chasse »
    pour un marqueur INLINE (suivi du texte sur la même ligne) : le texte
    démarre au caractère 4. Les espaces pleine chasse déjà présents dans
    la source sont normalisés (même rendu avec ou sans espace explicite ;
    idempotent). Un marqueur SEUL sur sa ligne n'est PAS touché (pose
    historique validée : sauts de ligne), pas plus qu'un marqueur de
    3 caractères ou plus (aucun remplissage possible) ni une ligne sans
    marqueur."""
    m = (VERSE_NUM_RE.match(ln) or VERSE_GENDER_RE.match(ln)
         or VERSE_CIRCLED_RE.match(ln))
    if m:
        L = len(m.group(0))
        rest = ln[L:].lstrip("\u3000 \t")
        if not rest or L >= 3:
            return ln
        return ln[:L] + "\u3000" * (3 - L) + rest
    if VERSE_MARK_RE.match(ln):
        head = ln[0]
        if len(ln) > 1 and ln[1] in VARIATION_SELECTORS:
            head += ln[1]   # ⚪︎ : sélecteur de variante fait partie du marqueur
        rest = ln[len(head):].lstrip("\u3000 \t")
        if not rest:
            return ln
        return head + "\u3000" * 2 + rest
    return ln


def _lyrics_columns_layout(verse, base_indent=None):
    """Layout complet d'un couplet : liste de (col_lines, indent).

    Source unique pour le rendu ET pour l'estimation de hauteur.
    Règle d'indentation : une colonne qui commence par un marqueur de
    couplet (一、二、… 女　男　) est alignée en haut (indent 0) et définit
    l'indentation courante pour les colonnes de continuation du même
    couplet (après |), qui s'indentent sous le marqueur. Une colonne
    blanche (après ||) réinitialise l'indentation courante : le couplet
    suivant, même sans marqueur, ne s'indente pas sous le précédent.
    Chaque ligne commençant par un marqueur INLINE est normalisée par
    _pad_inline_marker (texte au caractère 4, cf. règle des en-têtes de
    3 caractères pleine chasse)."""
    layout = []
    cur_marker_indent = 0
    for col in _lyrics_columns(verse):
        col = [_pad_inline_marker(ln) if ln else ln for ln in col]
        if col:
            own = _verse_indent_len(col[0])
            if own > 0:
                indent = 0
                cur_marker_indent = own if base_indent is None else base_indent
            else:
                indent = cur_marker_indent
        else:
            indent = 0
            cur_marker_indent = 0
        # Hayashi （…） : règle typo japonaise — la parenthèse OUVRANTE pend
        # juste AU-DESSUS du premier caractère du texte (une position), le
        # texte s'alignant sur les autres continuations indentées (niveau
        # base_indent). Réalisé au niveau des données : la ligne reçoit
        # base_indent - 1 espaces pleine chasse EN TÊTE (les espaces
        # avancent le flux vertical sans encre, comme partout) : （ au
        # niveau base_indent - 1, いめ… au niveau base_indent.
        if (len(col) == 1 and base_indent is not None and base_indent >= 2
                and _is_hayashi(col[0])):
            s = col[0].strip()
            col = ["\u3000" * (base_indent - 1) + s]
            indent = 0
        layout.append((col, indent))
    return layout


def _split_verses(lines):
    """Découpe une liste de lignes de paroles en couplets.

    Séparateurs de couplet :
    - ligne vide (comportement historique) ;
    - marqueur de couplet en début de ligne (一、二、…, ①②③…, 女　, 男　,
      ⚫︎, ・, ○) : la ligne courante OUVRE un nouveau couplet,
      même sans ligne vide précédente (design flaw jukunoharu : couplets
      sans retour à la ligne).
    Un hayashi (ligne entièrement entre parenthèses, ex. （いめのかじ
    ありよ船）) ferme le couplet courant et forme une unité À PART :
    interjection entre deux couplets, jamais comptée comme couplet
    (n'incrémente pas le numéro)."""
    verses = []
    current = []
    for ln in lines:
        if _is_hayashi(ln):
            if current:
                verses.append(current)
                current = []
            verses.append([ln])
            continue
        if ln == "":
            if current:
                verses.append(current)
                current = []
            continue
        if current and _verse_indent_len(ln) > 0:
            verses.append(current)
            current = []
        current.append(ln)
    if current:
        verses.append(current)
    return verses


def _h_lyrics_atoms(segment, fs):
    """Découpe un segment de paroles (syntaxe ruby comprise) en atomes
    insécables : (chaîne KKML, largeur d'avance). Un caractère de base et
    sa part de ruby forment un seul atome ; le texte clair éclate par
    caractère (pour la coupe en fin de ligne)."""
    atoms = []
    combine = SMALL_KANA | {chr(0x3063), chr(0x30C3), chr(0x30FC),
                            chr(0x3095), chr(0x3096)}
    for seg in _parse_ruby(segment):
        if seg["type"] == "plain":
            for ch in seg["text"]:
                # petit kana / chōonpu : insécable du caractère précédent
                if ch in combine and atoms:
                    prev_s, prev_w = atoms[-1]
                    atoms[-1] = (prev_s + _escape(ch), prev_w + _char_w(ch, fs))
                else:
                    atoms.append((_escape(ch), _char_w(ch, fs)))
        elif seg["type"] == "mono":
            base, ruby = seg["base"], seg["ruby"] or ""
            atoms.append((f"{_escape(base)}{ANNOT_OPEN}{_escape(ruby)}{ANNOT_CLOSE}" if ruby else _escape(base),
                          _char_w(base, fs)))
        elif seg["type"] == "group":
            base, ruby = seg["base"], seg["ruby"] or ""
            n = len(base)
            for j, ch in enumerate(base):
                if ruby:
                    r = ruby[round(len(ruby) * j / n):
                             round(len(ruby) * (j + 1) / n)]
                    atoms.append((f"{RUBY_OPEN}{_escape(ch)}{RUBY_CLOSE}{ANNOT_OPEN}{_escape(r)}{ANNOT_CLOSE}" if r else _escape(ch),
                                  _char_w(ch, fs)))
                else:
                    atoms.append((_escape(ch), _char_w(ch, fs)))
        elif seg["type"] == "jukugo":
            for base, ruby in seg["items"]:
                atoms.append((f"{_escape(base)}{ANNOT_OPEN}{_escape(ruby)}{ANNOT_CLOSE}" if ruby else _escape(base),
                              sum(_char_w(c, fs) for c in base)))
    return atoms


def _h_lyrics_layout(data, fs, usable_w):
    """Transposition HORIZONTALE de la règle verticale des paroles
    (_lyrics_columns_layout) : chaque colonne verticale (délimitée par
    | / ||) devient une LIGNE ; les segments d'une même colonne se
    suivent sur la ligne séparés par une espace pleine chasse (comme
    espace pleine chasse (transposé de l'espace vertical de 1 LYRICS_SP
    en colonne) ; une colonne qui commence par un marqueur de couplet
    s'aligne à gauche (indent 0) et les continuations du couplet
    s'indentent sous SON marqueur + 1 espace pleine chasse (indent par
    couplet, ex. 女、-> 3, 男女、-> 4), pas à l'indentation uniforme de
    la section. Règle alignée (layouts libres) : PAS de repli — une
    colonne = une ligne, aussi longue soit-elle (usable_w = None →
    largeur infinie ; la page s'élargit à la ligne la plus longue). Le
    paramètre usable_w est conservé pour un éventuel repli explicite.
    Une ligne vide est insérée automatiquement entre chaque couplet.
    Retourne [(indent, texte_kkml), …] — texte vide = ligne blanche."""
    if usable_w is None:
        usable_w = float('inf')   # règle alignée : pas de repli
    if usable_w <= fs:
        usable_w = fs * 4
    lines = []
    base_indent = _verse_indent_target(data)
    verses = _split_verses(data)
    sep = "\u3000"   # espace pleine chasse entre segments d'une colonne

    def _flush(cur, indent):
        txt = "".join(cur).rstrip(sep)
        lines.append((indent, txt, _has_ruby(_parse_ruby(txt))))

    for vi, verse in enumerate(verses):
        if vi > 0:
            lines.append((0, "", False))   # saut de ligne automatique entre couplets
        # Indent PAR COUPLET (horizontal) : sous SON marqueur + 1 espace
        # pleine chasse, pas l'indentation uniforme de la section (女、-> 3,
        # 男女、-> 4). Même clamp que _verse_indent_target : marqueur numéral
        # > 2 caractères ramené à 2 si la section a 10 couplets ou moins.
        vindent = base_indent
        first = next((ln for ln in verse if ln), "")
        m = VERSE_NUM_RE.match(first)
        if m:
            vindent = max(3, len(m.group(0)))   # en-tête = 3 caractères pleine chasse
        elif _verse_indent_len(first) > 0:
            vindent = max(3, _verse_indent_len(first))
        for col, indent in _lyrics_columns_layout(verse, vindent):
            if not col:
                lines.append((0, "", False))
                continue
            # Couplets INDENTÉS : les retours à la ligne automatiques d'une
            # colonne qui commence par un marqueur reprennent à
            # l'indentation du couplet (marqueur + 1 espace pleine chasse),
            # pas à 0.
            cont_indent = (vindent if indent == 0 and vindent > 0
                           and _verse_indent_len(col[0]) > 0 else indent)
            cur_indent = indent
            cur, cur_w = [], 0.0
            for si, segment in enumerate(col):
                if si > 0:
                    cur.append(sep)
                    cur_w += fs
                for atom, w in _h_lyrics_atoms(segment, fs):
                    avail = usable_w - cur_indent * fs
                    if cur and cur_w + w > avail:
                        _flush(cur, cur_indent)
                        cur, cur_w = [], 0.0
                        cur_indent = cont_indent
                    cur.append(atom)
                    cur_w += w
            if cur:
                _flush(cur, cur_indent)
    return lines


def _h_lyrics_pitch(next_ruby, fs, base_sp):
    """Interligne horizontal entre deux lignes de paroles : comme en
    vertical (où la largeur de ruby est réservée via max_ruby_w entre les
    colonnes), la place du ruby — AU-DESSUS de la ligne, de 0,95·fs
    (ruby_y) à 0,95·fs + 0,88·ruby_fs du haut de son encre — est réservée
    dans l'interligne. L'encre de la ligne précédente descend à
    +0,12·fs de sa baseline ; +2 pt d'air. Transposé de la réservation
    verticale (max_ruby_w), à l'orientation près."""
    ruby_fs = int(fs * RUBY_SCALE)
    ascent = 0.95 * fs + 0.88 * ruby_fs if next_ruby else 0.88 * fs
    return max(base_sp, 0.12 * fs + ascent + 2)


# Petits kana combinants (うちなぐち) : s'attachent au caractère principal
# pour former une seule syllabe — ぐゎ, くゎ, てぃ, でぃ, とぅ, づぅ, ふぃ…
# En écriture verticale ils se placent SOUS le caractère principal.
VARIATION_SELECTORS = {chr(c) for c in range(0xFE00, 0xFE10)}
SMALL_KANA = set("ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ")


def _draw_vertical_vocal(out, vocal_lines, cells_per_dan, ml, y0,
                           cell_w, cell_h, fs, total_w, mr, marker_w=0,
                           title_offset=0, opts=None, syllable_fs=None):
    """Rend des syllabes vocales dans la colonne marker.
    Un token = une syllabe, sauf si le token contient des points `.` :
    le temps est alors divisé en (points + syllabes) parties égales et les
    syllabes sont réparties dans la case (ex. `.きゅ` = 2 sous-temps, きゅ
    sur le 2e). Les parenthèses de koedashi/koekiri s'associent à l'élément
    voisin (syllabe ou point) sans changer la répartition. Les tokens
    multi-caractères (ぐゎ, てぃ, よー…) sont empilés verticalement : caractère
    principal aligné sur sa position, caractères combinants (petits kana, ー)
    en dessous. Le chevauchement de la bordure inférieure de la case est
    accepté.
    """
    if marker_w == 0 or syllable_fs is None or syllable_fs <= 0:
        return

    group_w = cell_w + marker_w
    step = int(syllable_fs * 1.15)  # espacement des caractères combinants (bien > fs : pas de chevauchement)

    KOE_CHARS = {'(', ')'}

    def _emit(sx, yy, ch):
        if ch in KOE_CHARS:
            return  # parenthèses de ::vocal = position du koedashi/koekiri, déjà rendu dans la case
        if ch in VERTICAL_ROTATE_CHARS:
            # pivoté 90° (choonpu, romaji, chiffres...) : trait vertical en écriture verticale
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

    for ci, vocal_col in enumerate(vocal_lines):
        x = total_w - mr - title_offset - (ci + 1) * group_w
        for ri, token in enumerate(vocal_col):
            if ri >= cells_per_dan:
                break
            cy = y0 + ri * cell_h
            # Position dans la colonne marker (à droite de la case)
            sx = x + cell_w + marker_w / 2
            if not token or token == "-":
                continue
            # Logique commune des points et du vocal (_vocal_elements) :
            # chaque élément (point ・ ou syllabe) occupe une sous-partie
            # verticale de la case, bloc centré ; un token sans point occupe
            # toute la case (centré). Même règle qu'en horizontal/tuto.
            elems = _vocal_elements(token)
            n = max(len(elems), 1)
            # Bornes de chant ( ) : ○/□ DANS la case (bord droit), alignés en
            # hauteur sur l'élément (syllabe ou point, même masqué) auquel la
            # borne est rattachée — ( = élément après, ) = élément avant.
            slots, _n = _vocal_paren_slots(token)
            if slots and (opts or {}).get('render_koe', True):
                ss = int(fs * 0.42)
                xk = x + cell_w * 0.86
                for ch, j in slots:
                    yk = cy + cell_h / 2 + cell_h * (j / n) + ss * 0.318
                    g = chr(0x25CB) if ch == "(" else chr(0x25A1)
                    out.append(f'<text x="{xk:g}" y="{yk:g}" text-anchor="middle" '
                               f'font-family="serif" font-size="{ss}" fill="black">{g}</text>')
            for j, el in enumerate(elems):
                # 1er élément au CENTRE de la case, puis mêmes multiplicateurs
                # qu'en horizontal/tuto : y_i = centre + cell_h * i/n
                sy = cy + cell_h / 2 + cell_h * (j / n) + syllable_fs / 3
                if el == "" and (opts or {}).get('show_dots'):
                    # point : rendu ・ (même couleur que le texte, #333), occupe sa sous-partie
                    out.append(f'<text x="{sx}" y="{sy}" text-anchor="middle" '
                               f'font-family="serif" font-size="{syllable_fs}" '
                               f'fill="#333">{chr(0x30FB)}</text>')
                elif len(el) == 2 and el[1] in SMALL_KANA:
                    # Syllabe en 2 parties (grand kana + petit kana, ex. ちゅ) :
                    # en vertical, le petit kana est tassé à droite du grand, MÊME
                    # taille de police (le glyphe petit kana est nativement plus
                    # petit dans le cadratin : グヮ vs グワ) — JLREQ cl-11, comme
                    # dans les PDF Nomura/Portama.
                    _emit(sx, sy, el[0])
                    out.append(f'<text x="{sx + syllable_fs * 0.25:g}" y="{sy + syllable_fs * 0.60:g}" '
                               f'text-anchor="middle" font-family="serif" font-size="{syllable_fs}" '
                               f'fill="#333">{escape(el[1])}</text>')
                else:
                    yy = sy
                    k = 0
                    while k < len(el):
                        ch = el[k]
                        if _latin_run_char(ch):
                            run = []
                            while k < len(el) and _latin_run_char(el[k]):
                                run.append(el[k])
                                k += 1
                            ry = yy - syllable_fs * 0.35
                            out.append(f'<text x="{sx:g}" y="{yy:g}" font-family="serif" '
                                       f'font-size="{syllable_fs}" fill="#333" '
                                       f'transform="rotate(90 {sx:g} {ry:g})">'
                                       f'{escape("".join(run))}</text>')
                            yy += sum(_vstep(c, syllable_fs, step) for c in run)
                        else:
                            _emit(sx, yy, ch)
                            yy += _vstep(ch, syllable_fs, step)
                            k += 1


def _draw_lead_straddle(out, note, cx, cy_edge, cell_w, cell_h, fs, opts, orient="v"):
    """Straddle de tête '/B' : note à cheval sur le bord PRÉCÉDENT de la
    première case — supérieur en vertical, gauche en horizontal (miroir du
    straddle A/B par rapport au centre de la case). cy_edge = bord concerné
    (haut de la case en vertical, haut de la rangée en horizontal)."""
    ss = int(fs * STRADDLE_RATIO)
    ss_pos = int(fs * STRADDLE_RATIO)
    if orient == "h":
        x = cx - cell_w * 0.5
        y = cy_edge + cell_h / 2 + ss * 0.318
    else:
        # le glyphe s'étend VERS LE HAUT depuis la baseline : pour centrer le
        # glyphe sur le bord supérieur, la baseline est DANS la case
        # (miroir exact du straddle normal : bord_inf + ss_pos/3)
        x = cx
        y = cy_edge + ss_pos / 3
    if note == "尺" and opts and opts.get('shaku_circled'):
        r = ss * 0.713
        ccy = y - ss * 0.35 if orient == "v" else cy_edge + cell_h / 2 + 2
        out.append(f'<circle cx="{x}" cy="{ccy}" r="{r}" '
                   f'fill="none" stroke="black" stroke-width="0.8"/>')
    out.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="serif" '
               f'font-size="{ss}" fill="black">{_note_svg(note, ss, opts)}</text>')


def _draw_vertical_tab(out, columns, cells_per_dan, ml, y0,
                       cell_w, cell_h, fs, total_w, mr, marker_w=0,
                       title_offset=0, opts=None, end_circle=False,
                       vocal_data=None, syllable_fs=None, lead=None):
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
    col_h = cells_per_dan * cell_h
    o = opts or {}
    cs = o.get('cell_color') or '#bbbbbb'
    csw = o.get('cell_width') or 0.75
    acol = o.get('arrow_color') or '#bbbbbb'
    asw = o.get('arrow_width') or 0.75
    rfill = bool(o.get('rep_fill', False))
    vfill = bool(o.get('vrep_fill', False))

    # Passe 1 : tous les rectangles de la grille
    col_positions = []
    for ci, col in enumerate(columns):
        x = total_w - mr - title_offset - (ci + 1) * group_w
        col_positions.append((x, col))
        for ri in range(cells_per_dan):
            cy = y0 + ri * cell_h
            out.append(f'<rect x="{x}" y="{cy}" width="{cell_w}" '
                       f'height="{cell_h}" fill="none" stroke="{cs}" '
                       f'stroke-width="{csw:g}"/>')
        if marker_w > 0:
            mx = x + cell_w
            out.append(f'<rect x="{mx}" y="{y0}" width="{marker_w}" '
                       f'height="{col_h}" fill="none" stroke="{cs}" '
                       f'stroke-width="{csw:g}"/>')

    # Passe 2 : SYMBOLES de contrôle (flèches, répétitions du chant) — sous
    # le texte (les kandokoro et syllabes restent au-dessus de tout trait)
    for x, col in col_positions:
        for ri in range(cells_per_dan):
            cy = y0 + ri * cell_h
            tok = col[ri] if ri < len(col) else ""
            rs, _bt, re_, vs, ve, _koe = _strip_repeat_marks(tok)
            if marker_w > 0:
                if rs:
                    _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'start',
                                         stroke=acol, sw=asw, filled=rfill)
                if re_:
                    _render_repeat_arrow(out, x + cell_w, cy, cell_h, marker_w, 'end',
                                         stroke=acol, sw=asw, filled=rfill)
                if vs:
                    _render_vrep_marker(out, x + cell_w, cy, cell_h, marker_w, 'start',
                                        stroke=acol, sw=asw, filled=vfill)
                if ve:
                    _render_vrep_marker(out, x + cell_w, cy, cell_h, marker_w, 'end',
                                        stroke=acol, sw=asw, filled=vfill)

    # Marqueur de fin de chanson (symbole) : dans le marker de la dernière
    # colonne, à la hauteur du bas de la dernière case remplie — AVANT les
    # textes (passes 3 et 4)
    if end_circle and marker_w > 0 and n_cols > 0:
        last_x, last_col = col_positions[-1]
        # Trouver la dernière case remplie (token non vide et non "-")
        last_filled_cy = None
        for ri in range(cells_per_dan - 1, -1, -1):
            tok = last_col[ri] if ri < len(last_col) else ""
            if tok and tok != "-":
                last_filled_cy = y0 + ri * cell_h
                break
        if last_filled_cy is not None:
            _render_end_circle(out, last_x + cell_w, last_filled_cy,
                               cell_h, marker_w)

    # Passe 3 : toutes les NOTES par-dessus grille et symboles
    for x, col in col_positions:
        for ri in range(cells_per_dan):
            cy = y0 + ri * cell_h
            tok = col[ri] if ri < len(col) else ""
            rs, base_tok, re_, vs, ve, koe = _strip_repeat_marks(tok)
            if koe and tok.lstrip('|:').startswith('(') and not base_tok.startswith('('):
                base_tok = '(' + base_tok  # koedashi : rendre ○ dans la case
            render_cell(out, base_tok, x + cell_w / 2, cy + cell_h / 2, fs,
                        cell_w, cell_h, opts)

    # Straddle de tête (rang -1, token '/B') : au-dessus de la première case
    # de la première colonne (bord supérieur)
    if lead and col_positions:
        x0 = col_positions[0][0]
        _draw_lead_straddle(out, lead, x0 + cell_w / 2, y0, cell_w, cell_h, fs, opts)

    # Passe 4 : rendre les syllabes vocales dans la colonne marker
    if vocal_data is not None and marker_w > 0 and syllable_fs is not None:
        _draw_vertical_vocal(out, vocal_data, cells_per_dan, ml, y0,
                             cell_w, cell_h, fs, total_w, mr, marker_w,
                             title_offset, opts, syllable_fs)

    return y0 + col_h


# --------------------------------------------------------------------------- #
# 3b. Rendu horizontal (gauche→droite, haut→bas) — mode songbook
# --------------------------------------------------------------------------- #
def _h_repeat_arrow(out, x_left, y_top, cell_w, marker_h, arrow_type,
                    stroke="#999999", sw=0.75, filled=False):
    """Flèche de répétition dans la LIGNE marker horizontale (sous la rangée
    de cases) — transposée de _render_repeat_arrow (colonne marker
    verticale) : trait vertical depuis le haut de la ligne, puis coude
    horizontal dans le sens de lecture, un seul path, triangle creux au
    bout. 'start' (|:) pointe vers la droite (sens de lecture), 'end' (:|)
    vers la gauche.
    La queue (path en L) porte toujours fill="none" : même avec un <g> rempli (flèche pleine), elle n’est jamais remplie — un path ouvert serait fermé implicitement au remplissage, créant un triangle rectangle rempli au coude ; seule la tête (polygon) hérite du fill du groupe."""
    out.append(f'<g class="repeat-arrow" fill="{stroke if filled else "none"}" stroke="{stroke}" stroke-width="{sw:g}">')
    v_len = marker_h * 0.66   # trait vertical depuis le haut de la ligne
    h_len = v_len             # trait horizontal dans le sens de lecture
    tri_size = marker_h * 0.22
    tri_w = 3 ** 0.5 * tri_size
    vy = y_top + v_len
    if arrow_type == 'start':
        vx = x_left + cell_w * 0.20
        hx = vx + h_len
        out.append(f'<path d="M {vx:g} {y_top:g} L {vx:g} {vy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        out.append(f'<polygon points="{hx:g},{vy - tri_size:g} '
                   f'{hx:g},{vy + tri_size:g} {hx + tri_w:g},{vy:g}"/>')
    else:
        vx = x_left + cell_w * 0.80
        hx = vx - h_len
        out.append(f'<path d="M {vx:g} {y_top:g} L {vx:g} {vy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        out.append(f'<polygon points="{hx:g},{vy - tri_size:g} '
                   f'{hx:g},{vy + tri_size:g} {hx - tri_w:g},{vy:g}"/>')
    out.append('</g>')
def _h_vrep_marker(out, x_left, y_top, cell_w, marker_h, marker_type,
                   stroke="#999999", sw=0.75, filled=False):
    """Symbole de répétition du chant dans la ligne marker horizontale —
    transposé de _render_vrep_marker : barre verticale, montant horizontal,
    disque creux. 'end' ( )| ) : barre à ~80% de la case, montant vers la
    gauche, disque à gauche ; 'start' ( |( ) : miroir à ~20%, montant et
    disque vers la droite.
    La queue (path en L) porte toujours fill="none" : même avec un <g> rempli (flèche pleine), elle n’est jamais remplie — un path ouvert serait fermé implicitement au remplissage, créant un triangle rectangle rempli au coude ; seule la tête (cercle) hérite du fill du groupe."""
    out.append(f'<g class="vocal-rep" fill="{stroke if filled else "none"}" stroke="{stroke}" stroke-width="{sw:g}">')
    v_len = marker_h * 0.66
    r = marker_h * 0.22
    vy = y_top + v_len
    if marker_type == 'end':
        vx = x_left + cell_w * 0.80
        hx = vx - v_len
        out.append(f'<path d="M {vx:g} {y_top:g} L {vx:g} {vy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        out.append(f'<circle cx="{hx - r:g}" cy="{vy:g}" r="{r:g}"/>')
    else:
        vx = x_left + cell_w * 0.20
        hx = vx + v_len
        out.append(f'<path d="M {vx:g} {y_top:g} L {vx:g} {vy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        out.append(f'<circle cx="{hx + r:g}" cy="{vy:g}" r="{r:g}"/>')
    out.append('</g>')
def _draw_marker_line_vocal(out, vrow, row, ml, y_top, cell_w, marker_h,
                            syl_fs, show_dots=False, cell_h=0, note_fs=0):
    """Syllabes ::vocal dans la ligne marker horizontale (sous la rangée de
    cases) — transposée de _draw_vertical_vocal : éléments (points ・ et
    syllabes) répartis le long de la case (x_i = cx + cell_w·i/n, i=0 sous
    la note principale), caractères combinants enfilés vers la droite, ー
    non pivoté. Les parenthèses de koedashi/koekiri (positions déjà rendues
    dans les cases) sont ignorées."""
    if marker_h <= 0 or syl_fs <= 0:
        return
    sy = y_top + marker_h / 2 + syl_fs / 3
    step = int(syl_fs * 1.15)
    for idx in range(len(row)):
        if idx >= len(vrow):
            break
        syl = vrow[idx]
        if not syl or syl == "-":
            continue
        cx = ml + idx * cell_w + cell_w / 2
        elems = _vocal_elements(syl)
        n = max(len(elems), 1)
        # Bornes de chant ( ) : ○/□ DANS la case, alignés en x sur l'élément
        # (syllabe ou point, même masqué) auquel la borne est rattachée, et en y
        # sur la centerline du TIERS INFÉRIEUR de la case (y_top - cell_h/6).
        slots, _n = _vocal_paren_slots(syl)
        if slots and note_fs:
            ss = int(note_fs * 0.42)
            yk = (y_top - cell_h / 6 + ss * 0.318) if cell_h else sy
            for ch, j in slots:
                xk = cx + cell_w * (j / n)
                g = chr(0x25CB) if ch == "(" else chr(0x25A1)
                out.append(f'<text x="{xk:g}" y="{yk:g}" text-anchor="middle" '
                           f'font-family="serif" font-size="{ss}" fill="black">{g}</text>')
        for j, el in enumerate(elems):
            sx = cx + cell_w * (j / n)
            if el == "" and show_dots:
                out.append(f'<text x="{sx:g}" y="{sy:g}" text-anchor="middle" '
                           f'font-family="serif" font-size="{syl_fs}" '
                           f'fill="#333">{chr(0x30FB)}</text>')
            else:
                for k, ch in enumerate(el):
                    if ch in ('(', ')'):
                        continue
                    out.append(f'<text x="{sx + k * step:g}" y="{sy:g}" '
                               f'text-anchor="middle" font-family="serif" '
                               f'font-size="{syl_fs}" '
                               f'fill="#333">{escape(ch)}</text>')


def _render_horizontal(song, sections, cols, cell_w, cell_h,
                       fs, ml, mr, mt, header_h, marker=False, opts=None, spec=None):
    title = song.meta.get("title", "")
    tuning = song.meta.get("choshi", "本調子")

    prepared = []
    for items in sections:
        sec_title, content, kind = items[0], items[1], items[2]
        vocal = items[3] if len(items) > 3 else None
        lead = items[4] if len(items) > 4 else None
        if kind == "tab":
            rows = _wrap_horizontal(content, cols)
            vrows = _wrap_horizontal(vocal, cols) if vocal else []
            prepared.append((sec_title, rows, kind, vrows, lead))
        else:
            prepared.append((sec_title, content, kind, [], None))

    # Marges recyclées de la mise en page VERTICALE, transposées :
    # - titre → tablature : air d'encre = TITLE_GAP + demi-solde de la
    #   colonne titre (TITLE_W - 26) // 2, intégré au header_h
    #   (GAP_HEADER = 0) ; le ruby du titre reste dans la marge de tête.
    # - tablature → paroles : air = 12 + LYRICS_COL_W, même formule que
    #   lyrics_offset − lyrics_total_w en vertical ; le +6 résiduel du
    #   bloc tab et l'ascension d'encre du premier vers sont compensés.
    spec = spec or HORIZONTAL
    MD_SP = spec.u(spec.md_spacing)  # gap horizontal : titre -> méta et méta -> méta
    o = opts or {}
    cs = o.get('cell_color') or spec.cell_color
    csw = o.get('cell_width') or spec.cell_width
    acol = o.get('arrow_color') or spec.arrow_color
    asw = o.get('arrow_width') or spec.arrow_width
    rfill = bool(o.get('rep_fill', spec.rep_fill))
    vfill = bool(o.get('vrep_fill', spec.vrep_fill))
    GAP_HEADER = spec.u(spec.gap_header)
    # header_h = titre fs 26 + descente d'encre 6 + air (TITLE_GAP + demi-colonne) 15 = 47
    header_h = spec.u(spec.header_h_title) if title else spec.u(spec.header_h)
    # Marge droite élargie : straddle sur la bordure droite, ornements et
    # vocals peuvent déborder à droite du bloc de tablature (c'est normal) ;
    # une demi-case est le strict minimum.
    mr = max(mr, cell_w // 2)
    # Taille des couplets selon @lyrics_size
    lyrics_size = opts.get('lyrics_size', 'medium') if opts else 'medium'
    h_lyrics_fs = int(fs * spec.lyr_size.get(lyrics_size, 0.75))
    h_lyrics_sp = int(h_lyrics_fs * spec.lyr_sp_ratio)  # espacement vertical entre lignes de couplets
    H_LYRICS_COL_W = int(h_lyrics_fs * spec.lyr_col_w_ratio)  # = LYRICS_COL_W vertical
    # avancée y pour l'air recyclé (12 + H_LYRICS_COL_W d'air d'encre)
    GAP_TAB_LYRICS = spec.u(spec.lyr_gap) + H_LYRICS_COL_W + int(h_lyrics_fs * 0.88) - 6
    # Ligne marker (transposée de la colonne marker verticale) : sous chaque
    # rangée de cases ; forcée si ::vocal est présent, sinon @marker (défaut on)
    has_vocal = any(v for (_t, _d, k, v, *_r) in prepared if k == "tab" and v)
    marker_on = marker or has_vocal
    marker_h = int(cell_h * spec.marker_ratio) if marker_on else 0
    h_syl_fs = (min(int(cell_w * spec.syl_cell_ratio), int(marker_h * spec.syl_marker_ratio))
                if marker_h > 0 else 0)
    # Règle alignée (layouts libres) : les dimensions dépendent du CONTENU.
    # - métadonnées : flux sur la ligne du titre, sans repli ; la page
    #   s'élargit à la largeur du flux.
    # - paroles : PAS de repli sur la largeur de la grille ; chaque colonne
    #   verticale = une ligne, la page s'élargit à la ligne la plus longue.
    # Largeur du flux de métadonnées (une seule ligne, même simulation
    # que le rendu, blocs jamais scindés).
    h_sep_w = MD_SP
    meta_flow_w = _h_text_w(_link_free(title), 26) + (MD_SP if title else 0)
    if title and _has_ruby(_parse_ruby(_link_free(title))):
        meta_flow_w = _render_horizontal_text([], _link_free(title), ml, 0, 26, "black") - ml
        meta_flow_w += MD_SP
    for text, hfs, _fill in _meta_blocks(song, speed_h=True, order=spec.meta_order):
        meta_flow_w += _h_text_w(_link_free(text), hfs) + h_sep_w
    # Largeur des paroles sans repli (usable_w infini) : mesurée avec le
    # même moteur de rendu de texte (_render_horizontal_text → end x).
    lyrics_flow_w = 0.0
    for sec_title, data, kind, _v, *_r in prepared:
        if kind == "lyrics":
            for indent, txt, _rub in _h_lyrics_layout(data, h_lyrics_fs, None):
                w = (indent * h_lyrics_fs
                     + (_render_horizontal_text([], txt, 0, 0, h_lyrics_fs, "#444")
                        if txt else 0))
                lyrics_flow_w = max(lyrics_flow_w, w)
    total_w = max(cols * cell_w,
                  int(meta_flow_w) + ml,
                  int(lyrics_flow_w) + ml) + mr
    # (formule ci-dessus : max des largeurs de contenu + marges)
    total_w = max(cols * cell_w,
                  int(meta_flow_w) + ml,
                  int(lyrics_flow_w) + ml) + mr
    total_h = header_h + mt + GAP_HEADER
    prev_kind = None
    for sec_title, data, kind, _v, *_r in prepared:
        if sec_title:
            total_h += 22
        if kind in ("lyrics", "vocal") and prev_kind == "tab":
            total_h += GAP_TAB_LYRICS
        if kind == "tab":
            total_h += len(data) * (cell_h + marker_h) + 6
        elif kind == "lyrics":
            # même layout que le rendu (colonnes verticales → lignes,
            # indentation, interlignes élargies pour le ruby comme en
            # vertical) ; PAS de repli : usable_w=None → largeur infinie
            hl = _h_lyrics_layout(data, h_lyrics_fs, None)
            total_h += (len(hl) * h_lyrics_sp
                        + sum(max(0, _h_lyrics_pitch(hl[i + 1][2], h_lyrics_fs,
                                                     h_lyrics_sp) - h_lyrics_sp)
                              for i in range(len(hl) - 1))) + 6
        else:
            total_h += len(data) * h_lyrics_sp + 6
        prev_kind = kind

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}">'
    )
    out.append('<rect width="100%" height="100%" fill="white"/>')

    ty0 = mt + 26
    # Titre (ruby au-dessus si besoin)
    if title and _has_ruby(_parse_ruby(_link_free(title))):
        end_x = _render_horizontal_text(out, title, ml, ty0, 26, "black", links=True)
    elif title:
        segs = _split_links(title)
        if len(segs) == 1 and segs[0][0] == "text":
            out.append(f'<text x="{ml}" y="{ty0}" font-family="serif" '
                       f'font-size="26" fill="black">{escape(_unescape(title))}</text>')
            end_x = ml + sum(_char_w(c, 26) for c in _unescape(title))
        else:
            cx = ml
            for seg in segs:
                body = (f'<text x="{cx:g}" y="{ty0}" font-family="serif" '
                        f'font-size="26" fill="black">{escape(_unescape(seg[1]))}</text>')
                if seg[0] == "link":
                    out.append(_link_open(seg[2]))
                    out.append(body)
                    out.append("</a>")
                else:
                    out.append(body)
                cx += _h_text_w(seg[1], 26)
            end_x = cx
    else:
        end_x = ml
    # Métadonnées dans l'ordre commun (_meta_blocks) : toutes à la suite du
    # titre sur SA ligne, centrées verticalement sur lui (centres d'encre),
    # SANS repli (règle alignée : la page s'est élargie au flux entier).
    h_sep_w = MD_SP
    hx = end_x + MD_SP
    for text, hfs, fill in _meta_blocks(song, speed_h=True, order=spec.meta_order):
        # centre d'encre du bloc sur celui du titre (26pt)
        by = ty0 - 0.38 * (26 - hfs)
        hxe = _render_horizontal_text(out, text, hx, by, hfs, fill, links=True)
        hx = hxe + h_sep_w

    y = header_h + mt + GAP_HEADER
    # Trouver la dernière section tab/tab-lyrics pour end_circle
    last_tab_idx = -1
    for si, (_, _, kind, _v, *_r) in enumerate(prepared):
        if kind == "tab":
            last_tab_idx = si
    # @end_circle déprécié/ignoré : le ┘● est désormais rendu par le token
    # explicite )| (vocalRepEnd), cohérent avec Portama où le marqueur est
    # posé sur une cellule et non déduit de la dernière case remplie.
    do_end_circle = False
    h_marker_w = cell_w * 0.15  # marker_w synthétique en mode horizontal
    h_last_filled = None

    prev_kind = None
    for si, (sec_title, data, kind, vrows0, lead) in enumerate(prepared):
        if kind in ("lyrics", "vocal") and prev_kind == "tab":
            y += GAP_TAB_LYRICS
        if sec_title:
            out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                       f'font-size="14" fill="#333">{escape(_unescape(sec_title))}</text>')
            y += 20
        if kind == "tab":
            for ri, row in enumerate(data):
                # Passes par rangée (texte toujours au-dessus des filets et
                # des symboles de contrôle) : 1) bordures des cases + ligne
                # marker, 2) symboles de boucles, 3) notes, 4) vocaux
                row_syms, row_notes = [], []
                for idx, tok in enumerate(row):
                    x = ml + idx * cell_w
                    out.append(f'<rect x="{x}" y="{y}" width="{cell_w}" '
                               f'height="{cell_h}" fill="none" '
                               f'stroke="{cs}" stroke-width="{csw:g}"/>')
                    rs, base_tok, re_, vs, ve, koe = _strip_repeat_marks(tok)
                    if koe and tok.lstrip('|:').startswith('(') and not base_tok.startswith('('):
                        base_tok = '(' + base_tok  # koedashi : rendre ○ dans la case
                    row_notes.append((base_tok, x))
                    if rs:
                        row_syms.append(('a', 'start', x))
                    if re_:
                        row_syms.append(('a', 'end', x))
                    if vs:
                        row_syms.append(('v', 'start', x))
                    if ve:
                        row_syms.append(('v', 'end', x))
                    if tok and tok != "-":
                        h_last_filled = (x + cell_w * 0.85, y)
                # Ligne marker sous la rangée : bordure, symboles de contrôle
                # (flèches de répétition, répétitions du chant) et syllabes
                # vocales — transposés de la colonne marker verticale
                if marker_h > 0:
                    # La ligne marker s'arrête à DROITE DE LA DERNIÈRE CASE
                    # de la rangée (le dernier dan peut être incomplet)
                    out.append(f'<rect x="{ml}" y="{y + cell_h:g}" '
                               f'width="{len(row) * cell_w}" height="{marker_h}" '
                               f'fill="none" stroke="{cs}" stroke-width="{csw:g}"/>')
                    ym = y + cell_h
                    for kind_s, typ, x in row_syms:
                        if kind_s == 'a':
                            _h_repeat_arrow(out, x, ym, cell_w, marker_h, typ,
                                            stroke=acol, sw=asw, filled=rfill)
                        else:
                            _h_vrep_marker(out, x, ym, cell_w, marker_h, typ,
                                           stroke=acol, sw=asw, filled=vfill)
                # Notes par-dessus bordures et symboles
                for base_tok, x in row_notes:
                    render_cell(out, base_tok, x + cell_w / 2, y + cell_h / 2, fs,
                                cell_w, cell_h, opts, orient="h")
                # Straddle de tête (rang -1) : bord GAUCHE de la 1re case de la 1re rangée
                if ri == 0 and lead:
                    _draw_lead_straddle(out, lead, ml + cell_w / 2, y,
                                        cell_w, cell_h, fs, opts, orient="h")
                # Syllabes vocales en dernier (texte)
                if marker_h > 0 and vrows0 and ri < len(vrows0):
                    _draw_marker_line_vocal(out, vrows0[ri], row, ml,
                                            y + cell_h, cell_w, marker_h,
                                            h_syl_fs, show_dots=bool(o.get('show_dots')),
                                            cell_h=cell_h, note_fs=fs)
                y += cell_h + marker_h
            y += 6
            if do_end_circle and si == last_tab_idx and h_last_filled:
                _render_end_circle(out, h_last_filled[0], h_last_filled[1],
                                   cell_h, h_marker_w)
        else:
            if kind == "lyrics":
                # Transposition horizontale de la règle verticale :
                # colonnes → lignes, continuation indentée sous le marqueur,
                # interligne élargi quand la ligne suivante porte un ruby ;
                # PAS de repli (règle alignée, la page a grandi)
                hl = _h_lyrics_layout(data, h_lyrics_fs, None)
                for i, (indent, text, _rub) in enumerate(hl):
                    if text:
                        _render_horizontal_text(
                            out, text, ml + indent * h_lyrics_fs, y,
                            h_lyrics_fs, "#444")
                    nxt = hl[i + 1][2] if i + 1 < len(hl) else False
                    y += _h_lyrics_pitch(nxt, h_lyrics_fs, h_lyrics_sp)
            else:
                for ln in data:
                    if ln == "":
                        y += int(h_lyrics_fs * 1.0)
                    else:
                        if _has_ruby(_parse_ruby(ln)):
                            _render_horizontal_text(out, ln, ml, y, h_lyrics_fs, "#444")
                        else:
                            out.append(f'<text x="{ml}" y="{y}" font-family="serif" '
                                       f'font-size="{h_lyrics_fs}" fill="#444">{escape(_unescape(ln))}</text>')
                        y += h_lyrics_sp
            y += 6
        prev_kind = kind

    out.append("</svg>")
    return "\n".join(out)

# --------------------------------------------------------------------------- #
# 3c. Rendu tuto (tutoriels video) - horizontal, bloc de taille fixe en pixels
# --------------------------------------------------------------------------- #
# Spec : docs/svg-layout.md ("Mise en page pour tutoriel video"). Exemple :
# https://www.youtube.com/watch?v=GvcZoeCbIPQ, calibre sur la video :
# 8 cases/dan, 7 dans/page. Page 1 = titre/accordage/infos seuls ; pages
# suivantes = tablature horizontale (gauche->droite, haut->bas), canvas
# exactement WxH (@tuto_block, defaut 1280x720).


def _draw_vocal_cell(out, elements, x, y, cell_w, cell_h, syl_fs, syl_pad, show_dots=False):
    # Ligne marker virtuelle (layouts horizontaux : horizontal, tuto) :
    # les éléments du token vocal (points ・ et syllabes) vont en bas de case,
    # sans toucher la bordure, répartis en x_i = cx + cell_w * i/n
    # (i=0 sous la note principale ; n=2 -> bordure droite = straddle ;
    #  n=3 -> cx, cx+cw/3, cx+2cw/3 ; n=4 -> cx, cx+cw/4, cx+cw/2, cx+3cw/4).
    sy = y + cell_h - syl_pad
    n = len(elements)
    for i, part in enumerate(elements):
        sx = x + cell_w / 2 + cell_w * (i / n)
        if part == "":
            if show_dots:
                out.append(f'<text x="{sx:g}" y="{sy:g}" text-anchor="middle" '
                           f'font-family="serif" font-size="{syl_fs}" fill="#333">{chr(0x30FB)}</text>')
        else:
            out.append(f'<text x="{sx:g}" y="{sy:g}" text-anchor="middle" '
                       f'font-family="serif" font-size="{syl_fs}" fill="#333">{escape(part)}</text>')


def _split_syllables(text):
    # Découpe un texte japonais/uchinaguchi en syllabes : un petit kana
    # (ゃゅょっ ァュョッ …) ou un chōonpu ー se rattache à la syllabe
    # précédente (ちゅ -> [ちゅ], やっく -> [やっ, く], まーし -> [まー, し]).
    combine = SMALL_KANA | {chr(0x3063), chr(0x30C3), chr(0x30FC), chr(0x3095), chr(0x3096)}
    out = []
    for ch in text:
        if out and ch in combine:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def _vocal_elements(tok):
    # Aplatit un token ::vocal en éléments ordonnés : chaque '.' est UN
    # élément (point ・), chaque run de caractères est un groupe de syllabes
    # (découpé par _split_syllables). Les parenthèses (koedashi/koekiri) sont
    # du inline formatting : retirées, jamais comptées comme éléments.
    # Ex. ".ちゅ" -> ['', 'ちゅ'] ; "ぐさ" -> ['ぐ', 'さ'] ; "..." -> ['', '', ''] (3 points) ;
    # ".)" -> [''] (1 point, la parenthèse ne compte pas).
    if tok.startswith("\\") and tok[1:] in EMPTY_INPUT_VARIANTS:
        tok = chr(0x30FC)   # \ー échappé : choonpu littéral seul dans la case
    tok = tok.replace('(', '').replace(')', '')
    elems = []
    cur = ""
    for ch in tok:
        if ch == ".":
            if cur:
                elems.extend(_split_syllables(cur))
                cur = ""
            elems.append("")
        else:
            cur += ch
    if cur:
        elems.extend(_split_syllables(cur))
    return elems


def _vocal_paren_slots(tok):
    """Positions des bornes ( ) d'un token ::vocal, en index d'élément :
    `(` se rattache à l'élément juste APRÈS (index = nb d'éléments avant elle),
    `)` à l'élément juste AVANT (index = nb d'éléments avant − 1).
    Retourne (slots, n), n = nb total d'éléments (points `.` compris, même
    masqués par @show_dots off : l'alignement suit l'emplacement théorique)."""
    slots = []
    n = 0
    cur = ""
    for ch in tok:
        if ch == ".":
            if cur:
                n += len(_split_syllables(cur)); cur = ""
            n += 1
        elif ch == "(":
            if cur:
                n += len(_split_syllables(cur)); cur = ""
            slots.append(("(", n))
        elif ch == ")":
            if cur:
                n += len(_split_syllables(cur)); cur = ""
            slots.append((")", max(n - 1, 0)))
        else:
            cur += ch
    if cur:
        n += len(_split_syllables(cur))
    return slots, n


def _tuto_block_size(song):
    raw = (song.meta.get("tuto_block") or "").strip().lower()
    if raw:
        parts = raw.split("x")
        if len(parts) == 2:
            try:
                w, h = int(parts[0]), int(parts[1])
                if w > 0 and h > 0:
                    return w, h
            except ValueError:
                pass
        _warn_once("@tuto_block '%s' illisible, defaut %dx%d" % (raw, *(int(TUTO.page_w / PX), int(TUTO.page_h / PX))))
    return (int(TUTO.page_w / PX), int(TUTO.page_h / PX))


TARGET_DPI = 600  # résolution cible d'impression, déclarée dans le SVG (Inkscape la détecte)


def _title_plain(text):
    # Titre sans les rubys (texte de base seul) — pour les métadonnées.
    out = []
    for seg in _parse_ruby(text):
        if seg["type"] == "plain":
            out.append(seg["text"])
        elif seg["type"] in ("mono", "group"):
            out.append(seg["base"])
        elif seg["type"] == "jukugo":
            out.extend(b for b, _ in seg["items"])
    return "".join(out)


def _svg_open_print(w_pt, h_pt, w_cm, h_cm, dpi=TARGET_DPI, title=None):
    # Racine SVG : format physique en cm (width/height), viewBox en pt (1 unité = 1 pt
    # à l'impression), et dpi d'export Inkscape -> détection auto du format + résolution.
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
           f'width="{w_cm:g}cm" height="{h_cm:g}cm" '
           f'viewBox="0 0 {w_pt:g} {h_pt:g}" '
           f'inkscape:export-xdpi="{dpi}" inkscape:export-ydpi="{dpi}">']
    if title:
        plain = _title_plain(title)
        out.append('<metadata>')
        out.append('  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
                   'xmlns:dc="http://purl.org/dc/elements/1.1/">')
        out.append('    <rdf:Description rdf:about="">')
        out.append(f'      <dc:title>{escape(plain)}</dc:title>')
        out.append('      <dc:creator>kunkunshi_tools</dc:creator>')
        out.append('    </rdf:Description>')
        out.append('  </rdf:RDF>')
        out.append('</metadata>')
    out.append('<rect width="100%" height="100%" fill="white"/>')
    return out


def _tuto_svg_open(W, H):
    return ['<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">',
            '<rect width="100%" height="100%" fill="white"/>']


def _tuto_text_width(segs, fs):
    # Largeur estimée d'un texte à segments ruby, même convention que
    # _render_horizontal_ruby : _char_w par caractère (CJK = 1em, latin = 0.55em).
    w = 0.0
    for seg in segs:
        t = seg["type"]
        if t == "plain":
            w += sum(_char_w(ch, fs) for ch in seg["text"])
        elif t == "mono":
            w += _char_w(seg["base"], fs)
        elif t == "group":
            w += sum(_char_w(ch, fs) for ch in seg["base"])
        elif t == "jukugo":
            w += sum(_char_w(ch, fs) for base, _ in seg["items"] for ch in base)
    return w


def _tuto_title_page(song, W, H, opts=None, spec=None):
    spec = spec or TUTO
    md_sp = spec.u(spec.md_spacing)  # gap entre blocs de la page de titre (px)
    # Page a part : titre, accordage et autres infos, centres.
    out = _tuto_svg_open(W, H)
    _draw_frame(out, spec, opts)   # tracé seulement si frame_width > 0 (défaut 0)
    cx = W / 2
    y = H * 0.40
    title = song.meta.get("title", "")
    fs_t = max(12, int(H * 0.07))
    if title:
        segs = _parse_ruby(_link_free(title))
        if _has_ruby(segs):
            est = _tuto_text_width(segs, fs_t)
            _render_horizontal_text(out, title, cx - est / 2, y, fs_t, "black", links=True)
        else:
            _emit_centered_text(out, title, cx, y, fs_t, "black", links=True)
        y += md_sp
    st = _speed_text(song)
    if st:
        # tempo ♩=... : horizontal, centré sous le titre, au-dessus de @choshi ;
        # même fs (px) que la ligne @choshi de la page de titre
        fs_s = max(10, int(H * 0.035))
        _emit_centered_text(out, st, cx, y, fs_s, "#555")
        y += md_sp
    tuning = song.meta.get("choshi", "")
    if tuning and "choshi" in spec.meta_order:
        out.append(f'<text x="{cx:g}" y="{y:g}" text-anchor="middle" font-family="serif" '
                   f'font-size="{max(10, int(H * 0.035))}" fill="#555">{escape(tuning)}</text>')
        y += md_sp
    lines = []
    author = song.meta.get("author", "")
    for k in spec.meta_order:
        if k == "choshi":
            continue  # @choshi affiché plus haut, sous le tempo
        v = song.meta.get(k, "")
        if v and not (k == "genre" and v == author):
            lines.append(v)
    for ln in lines:
        _emit_centered_text(out, ln, cx, y, max(9, int(H * 0.028)), "#777", links=True)
        y += md_sp
    out.append("</svg>")
    return "\n".join(out)


def _tuto_tab_page(rows, vrows, W, H, ml, mt, cols, cell_w, cell_h, fs, opts, sec_title,
                   spec=None):
    # Une page = jusqu'à page_dans rows (dans) de cols cases, pleine largeur.
    # Pas de bande marker en tuto : les flèches de répétition ne sont pas
    # rendues (décision en attente sur la boucle vocale) ; les syllabes ::vocal
    # vont en bas de leur case (ligne marker virtuelle : centrées, au-dessus
    # de la bordure inférieure, sans chevaucher la note).
    out = _tuto_svg_open(W, H)
    o = opts or {}
    _draw_frame(out, spec, o)   # tracé seulement si frame_width > 0 (défaut 0)
    cs = o.get('cell_color') or '#999999'
    csw = o.get('cell_width') or 0.75
    y0 = mt
    if sec_title:
        out.append(f'<text x="{W - 16:g}" y="14" text-anchor="end" font-family="serif" '
                   f'font-size="12" fill="#999">{escape(_unescape(sec_title))}</text>')
        y0 += 10
    syl_fs = int(fs * 0.6)
    syl_pad = max(2, int(syl_fs * 0.28))  # marge sous la baseline (ne touche pas la bordure)
    for r, row in enumerate(rows):
        y = y0 + r * cell_h
        for idx in range(len(row)):
            x = ml + idx * cell_w
            out.append(f'<rect x="{x:g}" y="{y:g}" width="{cell_w:g}" '
                       f'height="{cell_h:g}" fill="none" stroke="{cs}" stroke-width="{csw:g}"/>')
        for idx, tok in enumerate(row):
            x = ml + idx * cell_w
            rs, base_tok, re_, vs, ve, koe = _strip_repeat_marks(tok)
            render_cell(out, base_tok, x + cell_w / 2, y + cell_h / 2, fs,
                        cell_w, cell_h, opts, orient="h")
            if vrows and r < len(vrows) and idx < len(vrows[r]):
                syl = vrows[r][idx]
                if syl and syl != "-":
                    # parenthèses de koedashi/koekiri = inline formatting :
                    # interprétées au parse, jamais rendues dans le layout
                    disp = syl.replace('(', '').replace(')', '')
                    if disp:
                        _draw_vocal_cell(out, _vocal_elements(syl), x, y,
                                         cell_w, cell_h, syl_fs, syl_pad,
                                         show_dots=bool(o.get('show_dots')))
    out.append("</svg>")
    return "\n".join(out)


def _render_tuto(song, sections, cols, page_dans, marker, opts, spec=None):
    # Layout tuto : horizontal, canvas WxH fixe (@tuto_block), 8 cases/dan et
    # 7 dans/page par défaut (calibré sur la vidéo exemple). Page 1 = titre/
    # accordage/infos seuls ; pages suivantes = tablature. Le bloc ::lyrics
    # n'est PAS rendu en tuto.
    W, H = _tuto_block_size(song)
    spec = spec or TUTO
    if cols is None:
        cols = spec.cells_per_dan
    if page_dans is None:
        page_dans = spec.dans_per_block
    ml = mt = mb = spec.u(spec.margin_l)
    # Marge droite renforée (16 + 1/4 de case) : les vocals placés sous le
    # straddle de la dernière colonne ne doivent pas toucher la bordure droite
    # du SVG. Marges haute/basse/gauche inchangées.
    cell_w = (W - ml - 16) / (cols + 0.25)   # car mr = 16 + cell_w/4
    mr = 16 + cell_w / 4
    cell_h = (H - mt - mb) / page_dans
    fs = max(spec.fs_min, int(cell_h * spec.fs_ratio))  # ratio fs/case ~0,38 (calibrage Portama)

    pages = [_tuto_title_page(song, W, H, opts, spec)]
    for sec_title, content, kind, vocal, lead in sections:
        if kind not in spec.render_sections:
            continue
        rows = _wrap_horizontal(content, cols)
        vrows = _wrap_horizontal(vocal, cols) if vocal else []
        for start in range(0, len(rows), page_dans):
            pages.append(_tuto_tab_page(rows[start:start + page_dans],
                                        vrows[start:start + page_dans],
                                        W, H, ml, mt, cols, cell_w, cell_h,
                                        fs, opts, sec_title, spec))
    return pages


def _wrap_horizontal(tokens, cols):
    return [tokens[i : i + cols] for i in range(0, len(tokens), cols)]


# --------------------------------------------------------------------------- #
# 3d. Rendu mega (page A3 paysage : deux blocs horizontaux de 32 dans x 12 cases)
# --------------------------------------------------------------------------- #
# Mise en page "mega" (demande utilisateur, exemple en PJ) : une page A3
# paysage (42 x 29,7 cm) tient DEUX blocs horizontaux empilés ; chaque bloc
# contient jusqu'à 32 blocs verticaux (dans) de 12 cases. Ordre de lecture :
# bloc du haut d'abord, de haut en bas et de droite à gauche dans chaque dan,
# puis bloc du bas idem. Colonne marker d'une DEMI-CASE à droite de chaque dan
# (comme en vertical). Medley : chaque chanson = une section (::part nom
# + ::tab) ; le nom de la chanson est imprimé au-dessus des colonnes concernées
# et la dernière colonne de chaque chanson est complétée par des cases VIDES
# (pas de tenuto, pas de cercle de repos) pour que la chanson suivante commence
# sur une colonne suivante. Titre global (@title) en colonne verticale en haut à
# droite, à droite de tous les blocs (dans la marge), répété sur chaque page.
# Paroles : la 1re page est RÉSERVÉE aux deux blocs de tablature, pleine
# largeur ; les paroles n'y restent que si elles sont très compactes
# (largeur réservée ≤ spec.lyr_inline_max_ratio de la largeur utile),
# sinon elles sont paginées sur des pages A3 dédiées APRÈS les pages de
# tablature, en colonnes verticales de droite à gauche. Pagination
# automatique : 64 dans par page A3 (@dans_per_page / -p peut réduire ce plafond).


def _mega_title_halfw(text, fs):
    """Largeur estimée d'un titre de section (CJK = fs, ASCII = 0.55 fs),
    ruby pris en compte via le plan ruby horizontal."""
    segments = _parse_ruby(text)
    if _has_ruby(segments):
        return _plan_horizontal_ruby(segments, fs)[1] / 2
    w = 0.0
    for ch in _unescape(text):
        w += fs if ord(ch) > 0x2E80 else fs * 0.55
    return w / 2


def _mega_span_arrow(out, x_from, x_to, y, color="#555"):
    """Flèche vectorielle horizontale de x_from vers x_to (pointe du côté de
    x_to). Trace la hampe à y, tête triangulaire de 4 pt. Utilisée pour
    associer un titre de section à son intervalle de dans (layout mega)."""
    if x_to == x_from:
        return
    dx = 4 if x_to > x_from else -4
    out.append(f'<line x1="{x_from:g}" y1="{y:g}" x2="{x_to - dx:g}" '
               f'y2="{y:g}" stroke="{color}" stroke-width="0.9"/>')
    out.append(f'<polygon points="{x_to:g},{y:g} {x_to - dx:g},{y - 2.4:g} '
               f'{x_to - dx:g},{y + 2.4:g}" fill="{color}"/>')

def _mega_song_header(out, text, xc, ty):
    """Nom de chanson en chapeau (layout mega, tablature comme paroles) :
    horizontal, 11 pt, #555, centré sur xc ; ruby éventuel (syntaxe 《》 et
    ｛｝《》) rendu au-dessus de la base, largeur réelle du plan ruby."""
    segments = _parse_ruby(text)
    if _has_ruby(segments):
        w = _plan_horizontal_ruby(segments, 11)[1]
        _render_horizontal_ruby(out, segments, xc - w / 2, ty, 11, "#555")
    else:
        out.append(f'<text x="{xc:g}" y="{ty:g}" text-anchor="middle" '
                   f'font-family="serif" font-size="11" fill="#555">'
                   f'{escape(_unescape(text))}</text>')


def _mega_paginate(stream, dans_per_block, blocks_per_page=2, per_page=None, rows=12):
    """Découpe le flux de dans en pages de `blocks_per_page` blocs de
    `dans_per_block` colonnes. Retourne une liste de pages, chaque page étant
    une liste de blocs (eux-mêmes des listes d'entrées du flux).

    Marqueurs dans le flux : ("__block__",) ferme le bloc courant en le
    complétant de dans VIDES jusqu'à `dans_per_block` colonnes ; ("__page__",)
    fait de même puis complète la page de blocs vides jusqu'à `blocks_per_page`
    — même si bloc/page n'étaient pas pleins (sauts volontaires ::block /
    ::page). `per_page` = plafond de colonnes par page (-p / @dans_per_page,
    défaut blocks_per_page * dans_per_block). `rows` = cases par dan (pour
    les dans vides)."""
    if per_page:
        per_page = max(1, min(per_page, blocks_per_page * dans_per_block))
    else:
        per_page = blocks_per_page * dans_per_block
    pages, cur_page, cur_blk = [], [], []

    def empty_dan():
        return ([EMPTY_TOKEN] * rows, None, None, -1)

    def page_cols():
        return sum(len(b) for b in cur_page) + len(cur_blk)

    def close_blk():
        nonlocal cur_blk
        if cur_blk:
            cur_page.append(cur_blk)
            cur_blk = []

    def close_page():
        nonlocal cur_page
        close_blk()
        if cur_page:
            pages.append(cur_page)
            cur_page = []

    for entry in stream:
        if entry[0] == "__block__":
            # le bloc courant est rempli de dans vides jusqu'à son nombre de
            # colonnes prévues, puis fermé
            while cur_blk and len(cur_blk) < dans_per_block:
                cur_blk.append(empty_dan())
            close_blk()
            if len(cur_page) >= blocks_per_page or page_cols() >= per_page:
                close_page()
            continue
        if entry[0] == "__page__":
            while cur_blk and len(cur_blk) < dans_per_block:
                cur_blk.append(empty_dan())
            close_blk()
            # la page est complétée de blocs vides jusqu'à blocks_per_page
            while 0 < len(cur_page) < blocks_per_page and page_cols() < per_page:
                cur_page.append([empty_dan() for _ in range(dans_per_block)])
            close_page()
            continue
        if page_cols() >= per_page:
            close_page()
        cur_blk.append(entry)
        if len(cur_blk) >= dans_per_block:
            close_blk()
            if len(cur_page) >= blocks_per_page:
                close_page()
    close_page()
    if not pages:
        pages = [[[]]]
    return pages


def _render_mega(song, sections, marker=False, opts=None, page_dans=None, spec=None):
    title = song.meta.get("title", "")
    tuning = song.meta.get("choshi", "本調子")

    # Syllabes vocales présentes -> colonne marker forcée (comme vertical)
    has_vocal = any(s[3] or s[2] == "vocal" for s in sections)
    marker = marker or has_vocal

    # Géométrie verticale : spec.blocks blocs de spec.cells_per_dan cases + gaps, marges
    spec = spec or MEGA
    # @mega_dans N : colonnes (dans) par bloc horizontal en mega (défaut : spec)
    dans_per_block = spec.dans_per_block
    if song.meta.get("mega_dans"):
        try:
            dans_per_block = max(1, int(song.meta["mega_dans"]))
        except ValueError:
            print(f"kkml2svg: WARNING: @mega_dans non entier ({song.meta['mega_dans']!r}), "
                  f"défaut {spec.dans_per_block} utilisé", file=sys.stderr)
    dans_per_page = spec.blocks * dans_per_block
    cell_h = ((spec.page_h - 2 * spec.margin_t - (spec.blocks - 1) * spec.block_gap)
              / (spec.blocks * spec.cells_per_dan))
    fs = max(spec.fs_min, int(cell_h * spec.fs_ratio))  # ratio fs/case ~0,38 (calibrage Portama)
    page_base = _meta_page_base(song.meta)
    grid_bottom = (spec.margin_t + spec.blocks * spec.cells_per_dan * cell_h
                   + (spec.blocks - 1) * spec.block_gap)

    # --- Colonne titre verticale (à droite de la grille, comme vertical) --- #
    TITLE_W = spec.u(spec.title_w)
    TITLE_GAP = spec.u(spec.title_gap)
    TITLE_SPACING = spec.u(spec.title_spacing)
    TUNING_SPACING = spec.u(spec.tuning_spacing)
    title_ruby_w = _ruby_needs_extra_width(title, 26) if title else 0
    title_offset = (TITLE_W + TITLE_GAP + title_ruby_w) if (title or tuning) else 0

    # --- Paroles verticales (à gauche de la 1re page) --- #
    lyrics_size = opts.get('lyrics_size', 'medium') if opts else 'medium'
    LYRICS_FS = int(fs * spec.lyr_size.get(lyrics_size, 0.75))
    LYRICS_SP = int(LYRICS_FS * spec.lyr_sp_ratio)
    LYRICS_COL_W = int(LYRICS_FS * spec.lyr_col_w_ratio)
    LYRICS_VERSE_GAP = int(LYRICS_COL_W * spec.lyr_verse_gap_ratio)
    lyrics_sections = [(s[0], s[1]) for s in sections if s[2] == "lyrics"]
    n_verses = 0
    max_ruby_w = 0
    for _, data in lyrics_sections:
        for verse in _split_verses(data):
            n_verses += len(_lyrics_columns(verse))
            for line in verse:
                for seg in line.split('|'):
                    if seg:
                        max_ruby_w = max(max_ruby_w, _ruby_needs_extra_width(seg, LYRICS_FS))
    if n_verses > 0:
        lyrics_total_w = n_verses * LYRICS_COL_W + (n_verses - 1) * LYRICS_VERSE_GAP
        lyrics_offset = lyrics_total_w + spec.u(spec.lyr_gap) + LYRICS_COL_W + max_ruby_w
    else:
        lyrics_total_w = 0
        lyrics_offset = 0
    # Page 1 réservée aux deux blocs de tablature, pleine largeur : les
    # paroles n'y restent que très compactes, sinon elles comprimeraient
    # cell_w. Elles passent alors sur des pages dédiées (voir plus bas).
    tab_avail_w = spec.page_w - 2 * spec.margin_l - title_offset
    inline_lyrics = (n_verses > 0
                     and lyrics_offset <= spec.lyr_inline_max_ratio * tab_avail_w)
    if not inline_lyrics:
        lyrics_offset = 0

    # Géométrie horizontale : la largeur restante est répartie sur
    # dans_per_block dans (cell_w + marker_w = 1,5 cell_w avec marker)
    avail_w = spec.page_w - 2 * spec.margin_l - title_offset - lyrics_offset
    if marker:
        cell_w = avail_w / (dans_per_block * 1.5)
        marker_w = cell_w * spec.marker_ratio   # PJ mega : marker ~11,5 pt pour case ~22 pt
    else:
        cell_w = avail_w / dans_per_block
        marker_w = 0
    group_w = cell_w + marker_w
    SYLLABLE_FS = (min(int(cell_h * spec.syl_cell_ratio), int(marker_w * spec.syl_marker_ratio))
                   if marker_w > 0 else int(fs * spec.syl_fs_ratio))

    # --- Flux de dans (colonnes de spec.cells_per_dan cases), vocal synchronisé --- #
    # Entrées : (col, vocal_col|None, sec_title|None, sec_id, lead|None) ou marqueur
    # ("__block__",) / ("__page__",) pour les sauts ::block / ::page
    stream = []
    sec_id = -1
    for sec_title, content, kind, vocal, lead in sections:
        if kind in ("block", "page"):
            stream.append(("__%s__" % kind,))
            continue
        if kind != "tab":
            continue
        sec_id += 1
        cols = _wrap_vertical(list(content), spec.cells_per_dan)
        vcols = _wrap_vertical(list(vocal), spec.cells_per_dan) if vocal else None
        # Fin de chanson : compléter la dernière colonne par des cases VIDES
        # (pas de tenuto) pour que la chanson suivante commence sur une
        # colonne suivante
        if cols and len(cols[-1]) < spec.cells_per_dan:
            pad = spec.cells_per_dan - len(cols[-1])
            # Case vide (pas de tenuto) : la chanson suivante commence sur
            # une colonne suivante, sans point ・ dans les cases de fin.
            cols[-1] = list(cols[-1]) + [EMPTY_TOKEN] * pad
            if vcols and len(vcols) == len(cols):
                vcols[-1] = list(vcols[-1]) + ["-"] * pad
        for ci, col in enumerate(cols):
            stream.append((col, vcols[ci] if vcols and ci < len(vcols) else None,
                           sec_title, sec_id, lead if ci == 0 else None))

    per_page = dans_per_page
    if page_dans:
        per_page = max(1, min(page_dans, dans_per_page))
    pages = _mega_paginate(stream, dans_per_block, spec.blocks, per_page, spec.cells_per_dan)

    result = []
    for pi, page_blocks in enumerate(pages):
        out = _svg_open_print(spec.page_w, spec.page_h, 42, 29.7, title=title)  # A3, 600 dpi
        _draw_frame(out, spec, opts)   # tracé seulement si frame_width > 0 (défaut 0)
        y0 = spec.margin_l
        for bdan in page_blocks:
            if not bdan:
                continue
            cols = [d[0] for d in bdan]
            vcols = [d[1] if d[1] is not None else ["-"] * spec.cells_per_dan for d in bdan]
            # Nom de chaque chanson (section) centré au-dessus de ses colonnes
            # dans ce bloc (runs contigus de même section)
            li = 0
            while li < len(bdan):
                lj = li
                while lj + 1 < len(bdan) and bdan[lj + 1][3] == bdan[li][3]:
                    lj += 1
                if bdan[li][2]:
                    x_right = spec.page_w - spec.margin_l - title_offset - li * group_w
                    x_left = spec.page_w - spec.margin_l - title_offset - (lj + 1) * group_w
                    xc = (x_right + x_left) / 2
                    ty = y0 - 6
                    # Nom de chanson, ruby éventuel compris
                    _mega_song_header(out, bdan[li][2], xc, ty)
                    # Flèches d'association : depuis chaque bord du titre vers
                    # le bord extérieur de l'intervalle de dans du morceau
                    # dans CE bloc (retrait 2 pt pour ne pas toucher le marker).
                    hw = _mega_title_halfw(bdan[li][2], 11)
                    ay = ty - 3.8  # milieu optique du texte fs 11
                    x_to_first = x_right - 2
                    x_to_last = x_left + 2
                    pad = 4
                    if x_to_first > xc + hw + pad + 8:
                        _mega_span_arrow(out, xc + hw + pad, x_to_first, ay)
                    if x_to_last < xc - hw - pad - 8:
                        _mega_span_arrow(out, xc - hw - pad, x_to_last, ay)
                lead = bdan[li][4] if len(bdan[li]) > 4 else None
                if lead:
                    x_first = spec.page_w - spec.margin_l - title_offset - (li + 1) * group_w
                    _draw_lead_straddle(out, lead, x_first + cell_w / 2, y0,
                                        cell_w, cell_h, fs, opts, orient="v")
                li = lj + 1
            _draw_vertical_tab(out, cols, spec.cells_per_dan, spec.margin_l, y0,
                               cell_w, cell_h, fs, spec.page_w, spec.margin_l,
                               marker_w, title_offset, opts, end_circle=False,
                               vocal_data=vcols if has_vocal else None,
                               syllable_fs=SYLLABLE_FS)
            y0 += spec.cells_per_dan * cell_h + spec.block_gap

        # Paroles verticales à gauche (1re page seulement, et uniquement si
        # assez compactes pour ne pas comprimer la grille ; la largeur est
        # réservée sur toutes les pages pour garder une géométrie constante)
        if pi == 0 and inline_lyrics:
            ly0 = spec.margin_l
            vi = 0
            for _, data in lyrics_sections:
                for verse in _split_verses(data):
                    layout = _lyrics_columns_layout(verse, _verse_indent_target(data))
                    for col_lines, verse_indent in layout:
                        vx = (spec.margin_l + lyrics_total_w
                              - vi * (LYRICS_COL_W + LYRICS_VERSE_GAP)
                              - LYRICS_COL_W / 2)
                        cy = ly0 + LYRICS_FS
                        if verse_indent > 0:
                            cy += verse_indent * LYRICS_SP
                        for li, line in enumerate(col_lines):
                            if li > 0:
                                cy += LYRICS_SP
                            cy = _render_vertical_text(out, line, vx, cy,
                                                       LYRICS_FS, "#333", LYRICS_SP)
                        vi += 1

        # --- Titre vertical à droite de la grille (répété sur chaque page) --- #
        _mega_meta_column(out, song, title, tuning, TITLE_W, TITLE_SPACING,
                          TUNING_SPACING, spec, grid_bottom)
        _draw_page_no(out, page_base + pi, spec.page_w / 2,
                      (grid_bottom + spec.page_h) / 2 + spec.page_no_fs * 0.35,
                      spec.page_no_fs)

        out.append("</svg>")
        result.append("\n".join(out))

    # --- Pages dédiées aux paroles (si trop larges pour la 1re page) :
    # mêmes pages A3, même structure que la tablature : DEUX blocs
    # horizontaux empilés de hauteur spec.cells_per_dan*cell_h, colonnes verticales
    # de droite à gauche, repli impératif à la hauteur du bloc, saut d'une
    # colonne entre deux chansons, TITRE de chaque chanson en colonne
    # verticale 「…」 en gras DEVANT ses paroles (remplace le chapeau
    # horizontal) ; bloc du haut consommé → bloc du bas ; les deux consommés →
    # page suivante ; colonne titre verticale répétée --- #
    if lyrics_sections and not inline_lyrics:
        blk_h = spec.cells_per_dan * cell_h
        usable_w = spec.page_w - 2 * spec.margin_l - title_offset
        col_step = LYRICS_COL_W + LYRICS_VERSE_GAP
        max_cols = max(1, int((usable_w + LYRICS_VERSE_GAP) / col_step))
        # Association chanson → paroles : remonter les blocs bruts (le
        # regroupement attache le titre au ::tab, pas aux ::lyrics qui le
        # suivent) ; chaque section de paroles doit connaître sa chanson.
        lyr_by_song = []
        cur_song = None
        for blk in song.blocks:
            if blk.kind == "part":
                cur_song = blk.label
            elif blk.kind == "lyrics":
                lyr_by_song.append((cur_song, blk.lines))
        # Slots de colonnes : (lines, indent, song_title, song_id), («T»,
        # song_title, song_id) pour la colonne titre, ou None pour la
        # colonne vide de séparation entre deux chansons. Chaque
        # colonne est repliée à la hauteur du bloc (l'indent de couplet ne
        # porte que sur le premier fragment).
        ly_cols = []
        for si, (song_title, data) in enumerate(lyr_by_song):
            scols = []   # colonnes de paroles de CETTE chanson
            base_indent = _verse_indent_target(data)
            for verse in _split_verses(data):
                for col_lines, indent in _lyrics_columns_layout(verse, base_indent):
                    # Niveau de continuation des fragments de REPLI : marqueur
                    # + 1 espace pleine chasse (un marqueur inline s'inter-
                    # prète comme « marqueur　», même règle que l'indent
                    # cible de la section) ; colonne de continuation : son
                    # indent.
                    if col_lines and _verse_indent_len(col_lines[0]) > 0:
                        wrap_ind = max(3, _verse_indent_len(col_lines[0]))
                    elif indent > 0:
                        wrap_ind = indent
                    else:
                        wrap_ind = 0
                    first = True
                    chunk = []
                    used = (indent * LYRICS_SP) + LYRICS_FS
                    for line in col_lines:
                        # repli impératif : hauteur réelle de la ligne
                        # (par caractère, ruby compris) + interligne
                        lh = (LYRICS_SP
                              + _vertical_text_height(line, LYRICS_FS, LYRICS_SP))
                        if chunk and used + lh > blk_h:
                            scols.append((chunk, indent if first else wrap_ind,
                                          song_title, si))
                            first = False
                            chunk = []
                            used = LYRICS_FS + wrap_ind * LYRICS_SP
                        chunk.append(line)
                        used += lh
                    if chunk:
                        scols.append((chunk, indent if first else wrap_ind,
                                      song_title, si))
            # Titre de chanson en COLONNE VERTICALE 「…」 en gras, placé
            # AVANT les paroles de la chanson (sens de lecture droite →
            # gauche : colonne la plus à droite du run). Il REMPLACE le
            # chapeau horizontal (nom + flèches) des pages dédiées.
            # Guillemets pivotés 90° par _vertical_char, comme toute
            # ponctuation verticale. Slot («T», titre, song_id).
            if scols:
                if ly_cols:
                    ly_cols.append(None)   # saut de colonne entre chansons
                if song_title:   # paroles sans ::song : pas de titre
                    ly_cols.append(("T", song_title, si))
                ly_cols.extend(scols)
        per_page = spec.blocks * max_cols
        ly_pages = [ly_cols[i:i + per_page]
                    for i in range(0, len(ly_cols), per_page)] or [[]]
        for lpi, page_cols in enumerate(ly_pages):
            out = _svg_open_print(spec.page_w, spec.page_h, 42, 29.7, title=title)
            _draw_frame(out, spec, opts)   # tracé seulement si frame_width > 0 (défaut 0)
            for b in range(spec.blocks):
                bcols = page_cols[b * max_cols:(b + 1) * max_cols]
                if not bcols:
                    break
                y0 = spec.margin_l + b * (blk_h + spec.block_gap)
                # (Plus de chapeau horizontal : le titre de chaque chanson
                # est rendu en colonne verticale 「…」 en gras, devant ses
                # paroles — cf. slot «T» ci-dessous.)
                # Colonnes du bloc, de droite à gauche
                for vi, col in enumerate(bcols):
                    if col is None:
                        continue
                    vx = (spec.page_w - spec.margin_l - title_offset
                          - LYRICS_COL_W / 2 - vi * col_step)
                    if col[0] == "T":
                        # Titre vertical en gras, PLUS GRAND que le texte
                        # des couplets (fs 11, taille des en-têtes de la
                        # tablature), encore remonté d'une position : le
                        # guillemet OUVRANT 「 pend au niveau du haut de
                        # bloc des colonnes (baseline y0 + fs, pivoté
                        # 90° par _vertical_char), le texte part une
                        # position plus bas (y0 + fs + 1·sp), 」 referme
                        # sous le dernier caractère. Garde anti-déborde-
                        # ment : fs réduit si le titre dépasse la hauteur
                        # du bloc.
                        tfs = 11
                        tsp = int(tfs * 1.2)
                        need = 2 * tsp + _vertical_text_height(col[1], tfs, tsp)
                        if need > blk_h:
                            tfs = max(5, int(tfs * (blk_h - 2 * tsp) / max(need - 2 * tsp, 1)))
                            tsp = int(tfs * 1.2)
                        out.append('<g font-weight="bold">')
                        # 「 au haut de bloc, une position au-dessus du texte
                        _vertical_char(out, "「", vx, y0 + tfs, tfs, "#000")
                        _render_vertical_text(out, col[1], vx, y0 + tfs + tsp,
                                              tfs, "#000", tsp)
                        _vertical_char(out, "」", vx, y0 + tfs + tsp
                                       + _vertical_text_height(col[1], tfs, tsp),
                                       tfs, "#000")
                        out.append('</g>')
                        continue
                    col_lines, indent = col[0], col[1]
                    cy = y0 + LYRICS_FS
                    if indent > 0:
                        cy += indent * LYRICS_SP
                    for lli, line in enumerate(col_lines):
                        if lli > 0:
                            cy += LYRICS_SP
                        cy = _render_vertical_text(out, line, vx, cy,
                                                   LYRICS_FS, "#333", LYRICS_SP)
            _mega_meta_column(out, song, title, tuning, TITLE_W, TITLE_SPACING,
                              TUNING_SPACING, spec, grid_bottom)
            _draw_page_no(out, page_base + len(pages) + lpi, spec.page_w / 2,
                          (grid_bottom + spec.page_h) / 2 + spec.page_no_fs * 0.35,
                          spec.page_no_fs)
            out.append("</svg>")
            result.append("\n".join(out))
    return result


def _mega_meta_column(out, song, title, tuning, TITLE_W, TITLE_SPACING,
                      TUNING_SPACING, spec, grid_bottom=0):
    """Colonne titre vertical à droite de la page mega (titre, accordage,
    genre, auteur) — répétée sur chaque page, tablature comme paroles."""
    md = spec.md_spacing  # avance avant chaque bloc de métadonnées
    if title or tuning:
        tx = spec.page_w - spec.margin_l - TITLE_W / 2
        ty = spec.margin_l
        if title:
            ty_end = _render_vertical_text(out, title, tx, ty + 20, 26, "black",
                                          TITLE_SPACING, links=True)
        else:
            ty_end = ty
        st = _speed_text(song)
        if st:
            # tempo ♩=... : horizontal, text-anchor=middle sur tx (centerline de
            # base du titre, hors ruby), sous le titre, au-dessus de genre/auteur
            _emit_centered_text(out, st, tx, ty_end + md + 12 * 0.88, 12, "#555")
            ty_end += md + 12
        author = song.meta.get("author", "")
        ty3 = ty_end
        for k in spec.meta_order:
            if k == "choshi":
                continue  # accordage ancré en bas de la colonne titre
            v = song.meta.get(k, "")
            if v and not (k == "genre" and v == author):
                for i, ch in enumerate(v):
                    _vertical_char(out, ch, tx, ty3 + i * TUNING_SPACING + md, 15, "#777")
                ty3 += len(v) * TUNING_SPACING + md
        if tuning and "choshi" in spec.meta_order:
            yb = grid_bottom - 4 - len(tuning) * TUNING_SPACING
            for i, ch in enumerate(tuning):
                _vertical_char(out, ch, tx, yb + i * TUNING_SPACING, 15, "#555")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _tech_char_pos(tech, cx, base_y, fs, note_fs, text_w=None, cell_h=None,
                   cell_cy=None, cell_w=None, orient="v", box_w=None, box_top=None):
    """Position (tx, ty, anchor) d'une marque de technique de type 'char'.

    base_y  : baseline de la note porteuse.
    note_fs : taille (font-size) de la note porteuse — pleine, petite
              (croche à cheval) ou réduite ('s'). Taille du glyphe ET tous les
              offsets (dx, dy, drop) sont des fractions de note_fs.
    text_w  : largeur rendue du token (textLength) ; défaut note_fs (caractère
              plein chasse). L'ancrage horizontal est le MÊME pour une note seule
              et pour un composite condensé (coin du token rendu).
    cell_w / cell_h / cell_cy : géométrie de la case (cell_cy = centre réel de la
              case, utile quand base_y est celui d'une note à cheval).
    orient  : 'v' (layouts verticaux) ou 'h' (horizontal/tuto) ; une marque peut
              définir 'pos_h' pour sa position en horizontal.

    'corner': 'top-right' (uchi/nuchi/kaki-utu) : ancré sur le coin haut-droit du
      rectangle englobant de la note rendue : tx = cx + box_w/2 + note_fs*dx,
      ty = box_top + note_fs*dy (box_w = largeur rendue : note_fs, ou text_w pour un
      composite condensé, ou largeur max du groupe d'accord ; box_top = base_y − note_fs,
      ou sommet du membre le plus haut pour un accord).

    Vertical (ty) :
      - 'anchor': 'cell-bottom' (aki-utu) : ty = bas de la case − note_fs*drop ;
      - 'anchor': 'note-center' (yubii) : ty = centerline de la note + 0,318*mark_fs,
        soit base_y − 0,318*note_fs + 0,318*mark_fs (mark_fs = fs du glyphe) ;
      - sinon : ty = base_y + note_fs*dy (dy propre à chaque marque).

    Horizontal (tx) :
      - 'left-third' (yubii, layouts verticaux) : centre du 1er tiers GAUCHE de la
        case, tx = cx − cell_w/3, ancre middle (indépendant du token) ;
      - 'bottom-third' (yubii, layout horizontal via 'pos_h') : tiers INFÉRIEUR de la
        case, sur la centerline de la note : tx = cx, ancre middle, et
        ty = cy + cell_h/3 + 0,318*mark_fs (centre du tiers inférieur) ;
      - sinon : coin du token rendu, tx = cx ± (text_w/2 + note_fs*(dx − 0,5)),
        ancre middle (top-right = bord droit, bottom-left = bord gauche).
    """
    dx = tech.get('dx', 0.22)
    dy = tech.get('dy', 0.05)
    scale = tech.get('scale', 1.0)
    mark_fs = int(note_fs * 1.1 * scale)
    pos = tech.get('pos_h') if (orient == "h" and tech.get('pos_h')) else tech['pos']
    top = pos == 'top-right'
    cy = cell_cy if cell_cy is not None else base_y - fs * 0.318
    anchor_kind = tech.get('anchor')
    if tech.get('corner') == 'top-right':
        bw = box_w if box_w is not None else (text_w if text_w is not None else note_fs)
        bt = box_top if box_top is not None else base_y - note_fs
        return cx + bw / 2 + note_fs * dx, bt + note_fs * dy, "middle"
    if anchor_kind == 'cell-bottom' and cell_h is not None:
        ty = cy + cell_h / 2 - note_fs * tech.get('drop', 0.1)
    elif anchor_kind == 'note-center':
        ty = base_y - 0.318 * note_fs + 0.318 * mark_fs
    else:
        ty = base_y + note_fs * dy
    if pos == 'left-third':
        tx = cx - cell_w / 3
        anchor = "middle"
    elif pos == 'bottom-third':
        tx = cx
        if cell_h is not None:
            ty = cy + cell_h / 3 + 0.318 * mark_fs
        anchor = "middle"
    else:
        if text_w is None:
            text_w = note_fs
        if top:
            tx = cx + text_w / 2 + note_fs * (dx - 0.5)
        else:
            tx = cx - text_w / 2 - note_fs * (dx - 0.5)
        anchor = "middle"
    return tx, ty, anchor


def _render_techniques(out, suffixes, cx, cy, cell_w, cell_h, fs, text_w=None,
                       tech_map=None, note_fs=None, cell_cy=None, orient="v",
                       box_w=None, box_top=None):
    """Dessine les marques de technique (souhou) autour de la cellule.

    Les marques de type 'char' sont rendues dans la même police (serif) et la
    même taille (fs) que la note, positionnées en haut-droite (ou bas-gauche)
    du caractère concerné.

    Règle : l'encre visible du signe ne doit pas chevaucher l'encre visible
    de la note. Chaque signe a ses propres offsets (dx, dy) pour respecter
    cette règle selon la forme de son glyphe.

    text_w : largeur du texte rendu (textLength). Quand fournie, la marque
    est positionnée par rapport au token multi-caractères (下老, positions
    hautes) au lieu du centre de la cellule.

    note_fs : taille réelle de la note porteuse quand elle diffère de fs
    (croche à cheval rendue à ss). Par défaut note_fs = fs. Taille du glyphe
    (tech_fs) et offsets de position (dx, dy, drop) sont tous relatifs à note_fs.
    """
    note_fs = fs if note_fs is None else note_fs
    base_y = cy + fs * 0.318
    for suffix in suffixes:
        tech = (tech_map or TECHNIQUE_SUFFIXES)[suffix]
        ttype = tech['type']
        if ttype == 'char':
            sym = tech['symbol']
            scale = tech.get('scale', 1.0)
            rotate = tech.get('rotate', 0)
            tech_fs = int(note_fs * 1.1 * scale)
            if tech['pos'] == 'inside-right':
                # ○/□ 声だし・声切り : petit glyphe DANS la case, côté
                # droit, centré verticalement (区画中右方, traité 野村流).
                out.append(f'<text x="{cx + cell_w * tech["dx"]}" '
                           f'y="{cy + fs * tech["dy"]}" '
                           f'text-anchor="middle" font-family="serif" '
                           f'font-size="{int(fs * scale)}" '
                           f'fill="black">{escape(sym)}</text>')
                continue
            tpos = tech.get('pos_h') if (orient == "h" and tech.get('pos_h')) else tech['pos']
            tx, ty, anchor = _tech_char_pos(tech, cx, base_y, fs, note_fs,
                                             text_w=text_w, cell_h=cell_h,
                                             cell_cy=cell_cy if cell_cy is not None else cy,
                                             cell_w=cell_w, orient=orient,
                                             box_w=box_w, box_top=box_top)
            if text_w is not None and tpos in ('top-right', 'bottom-left') and not tech.get('corner'):
                # token condensé (composite) : la marque reste DANS la case
                # (sauf ancrage 'corner' : ancrée au coin, peut déborder — nomura)
                half = tech_fs / 2
                if tpos == 'top-right':
                    tx = min(tx, cx + cell_w / 2 - half)
                else:
                    tx = max(tx, cx - cell_w / 2 + half)
            if rotate:
                anchor = {"start": "end", "end": "start",
                          "middle": "middle"}[anchor]
                out.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                           f'font-family="serif" font-size="{tech_fs}" '
                           f'fill="black" '
                           f'transform="rotate({rotate} {tx} {ty})">'
                           f'{escape(sym)}</text>')
            else:
                out.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                           f'font-family="serif" font-size="{tech_fs}" '
                           f'fill="black">{escape(sym)}</text>')


def _strip_repeat_marks(tok):
    """Détache |: (début), :| (fin), |( (début boucle vocale) et )| (fin
    boucle vocale) d'un token.
    Retourne (repeat_start, base_tok, repeat_end, vrep_start, vrep_end) :
    des booléens et le token sans les marqueurs. Le rendu des kanjis de
    notes n'est PAS décalé — les marqueurs |( / )| vivent dans la colonne
    marker, comme les flèches de |: / :|."""
    rs = False
    re_ = False
    vs = False
    ve = False
    koe = False
    # Bornes de chant ( et ) : peuvent précéder/suivre les marqueurs de
    # répétition (ex. "(|:合", "上:)|") — on les dépile dans n'importe quel
    # ordre pour ne garder que le contenu de la case.
    while True:
        if tok.startswith('(:'):
            vs = True
            tok = tok[2:]
        elif tok.endswith(':)') and not tok.endswith('(:'):  # garde (: seul
            ve = True
            tok = tok[:-2]
        elif tok.startswith('('):
            koe = True
            tok = tok[1:]
        elif tok.startswith(REPEAT_START):
            rs = True
            tok = tok[len(REPEAT_START):]
        elif tok.startswith(VREPEAT_START):
            vs = True
            _warn_once("'|(' DÉPRÉCIÉ : boucle vocale à écrire (: ... :) dans ::vocal")
            tok = tok[len(VREPEAT_START):]
        elif tok.endswith(')'):
            koe = True
            tok = tok[:-1]
        elif tok.endswith(REPEAT_END):
            re_ = True
            tok = tok[:-len(REPEAT_END)]
        elif tok.endswith(VREPEAT_END):
            ve = True
            _warn_once("')|' DÉPRÉCIÉ : boucle vocale à écrire (: ... :) dans ::vocal")
            tok = tok[:-len(VREPEAT_END)]
        else:
            break
    return rs, tok, re_, vs, ve, koe


def _render_repeat_arrow(out, x_left, cy, cell_h, marker_w, arrow_type,
                         stroke="#bbbbbb", sw=0.75, filled=False):
    """Dessine une flèche de répétition en graphiques vectoriels SVG.

    La flèche part de la bordure gauche de la colonne marker (x_left),
    va horizontalement vers la droite sur 66% de marker_w, puis descend
    (ou monte) verticalement, et se termine par un triangle creux.
    Le coude horizontal/vertical est UN SEUL path (pas deux <line>
    superposées) ; trait de même largeur et couleur que la grille
    (stroke/sw passés par le layout appelant, défaut = cases vertical).

    arrow_type: 'start' = flèche descendante (~80% haut), 'end' = flèche montante (~80% bas).
    x_left = bordure gauche de la colonne marker. cy = position verticale du haut de la case.
    La queue (path en L) porte toujours fill="none" : même avec un <g> rempli (flèche pleine), elle n’est jamais remplie — un path ouvert serait fermé implicitement au remplissage, créant un triangle rectangle rempli au coude ; seule la tête (polygon) hérite du fill du groupe."""
    out.append(f'<g class="repeat-arrow" fill="{stroke if filled else "none"}" stroke="{stroke}" stroke-width="{sw:g}">')
    h_len = marker_w * 0.66  # longueur du trait horizontal
    v_len = h_len  # trait vertical au moins aussi long que l'horizontal
    tri_size = marker_w * 0.22  # demi-largeur du triangle
    tri_h = 3 ** 0.5 * tri_size  # hauteur triangle équilatéral

    if arrow_type == 'start':
        # Part à ~20% du haut : trait horizontal à cell_h * 0.20
        hy = cy + cell_h * 0.20
        # Coude propre : horizontal puis vertical descendant, un seul path
        hx = x_left + h_len
        vy = hy + v_len
        out.append(f'<path d="M {x_left:g} {hy:g} L {hx:g} {hy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        # Triangle creux pointant vers le bas, sommet à (hx, vy + tri_h)
        tip_y = vy + tri_h
        out.append(f'<polygon points="{hx - tri_size:g},{vy:g} '
                   f'{hx + tri_size:g},{vy:g} {hx:g},{tip_y:g}"/>')
    else:
        # Part à ~80% du bas : trait horizontal à cell_h * 0.80
        hy = cy + cell_h * 0.80
        hx = x_left + h_len
        # Coude propre : horizontal puis vertical montant, un seul path
        vy = hy - v_len
        out.append(f'<path d="M {x_left:g} {hy:g} L {hx:g} {hy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        # Triangle creux pointant vers le haut, sommet à (hx, vy - tri_h)
        tip_y = vy - tri_h
        out.append(f'<polygon points="{hx - tri_size:g},{vy:g} '
                   f'{hx + tri_size:g},{vy:g} {hx:g},{tip_y:g}"/>')
    out.append('</g>')
def _render_vrep_marker(out, x_left, cy, cell_h, marker_w, marker_type,
                        stroke="#bbbbbb", sw=0.75, filled=False):
    """Symbole de répétition du chant dans la colonne marker — même
    géométrie et même taille que l'ancien marqueur @end_circle
    (_render_end_circle) : barre horizontale sur 66% de marker_w, montant
    vertical, disque creux (rayon 22% de marker_w).
    Le coude barre/montant est UN SEUL path (pas deux <line> superposées) ;
    trait de même largeur et couleur que la grille (stroke/sw passés par
    le layout appelant, défaut = cases vertical).

    marker_type: 'end' = )| → ┘● (barre à ~80% du bas, montant vers le
    haut, disque au-dessus) ; 'start' = |( → image spéculaire par rapport
    à l'axe HORIZONTAL : barre à ~20% du haut, montant vers le bas,
    disque en dessous.
    x_left = bordure gauche de la colonne marker. cy = haut de la case.
    La queue (path en L) porte toujours fill="none" : même avec un <g> rempli (flèche pleine), elle n’est jamais remplie — un path ouvert serait fermé implicitement au remplissage, créant un triangle rectangle rempli au coude ; seule la tête (cercle) hérite du fill du groupe."""
    out.append(f'<g class="vocal-rep" fill="{stroke if filled else "none"}" stroke="{stroke}" stroke-width="{sw:g}">')
    h_len = marker_w * 0.66
    v_len = h_len
    r = marker_w * 0.22

    hx = x_left + h_len
    if marker_type == 'end':
        hy = cy + cell_h * 0.80
        # Coude propre : barre horizontale puis montant vers le haut
        vy = hy - v_len
        out.append(f'<path d="M {x_left:g} {hy:g} L {hx:g} {hy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        out.append(f'<circle cx="{hx:g}" cy="{vy - r:g}" r="{r:g}"/>')
    else:  # 'start' : miroir horizontal — barre en haut, montant descendant
        hy = cy + cell_h * 0.20
        vy = hy + v_len
        out.append(f'<path d="M {x_left:g} {hy:g} L {hx:g} {hy:g} '
                   f'L {hx:g} {vy:g}" fill="none"/>')
        out.append(f'<circle cx="{hx:g}" cy="{vy + r:g}" r="{r:g}"/>')
    out.append('</g>')
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
        if opts is not None and not opts.get('shaku_sharp', False):
            return escape("尺")
        return (f'{escape("尺")}'
                f'<tspan font-size="{int(font_size * 0.65)}" '
                f'dx="0" dy="0">♯</tspan>')
    return escape(note)


_WARNED_TOKENS = set()
_WARNED_MISC = set()


def _warn_once(msg):
    if msg not in _WARNED_MISC:
        _WARNED_MISC.add(msg)
        print(f"kkml2svg: WARNING: {msg}", file=sys.stderr)


def _info_input_variant(orig, canon):
    """INFO stderr (une seule fois par paire) : une variante de saisie
    pleine chasse a été normalisée vers la forme canonique."""
    key = (orig, canon)
    if key not in _INFO_INPUT_SEEN:
        _INFO_INPUT_SEEN.add(key)
        print(f"kkml2svg: INFO: entrée '{orig}' normalisée en '{canon}' "
              f"(variante de saisie acceptée)",
              file=sys.stderr)


_INFO_INPUT_SEEN = set()


_WARNED_MISC = set()


def _warn_once(msg):
    if msg not in _WARNED_MISC:
        _WARNED_MISC.add(msg)
        print(f"kkml2svg: WARNING: {msg}", file=sys.stderr)


def _warn_unknown_token(tok):
    """Alerte stderr une seule fois par token non reconnu (anti-spam)."""
    if tok not in _WARNED_TOKENS:
        _WARNED_TOKENS.add(tok)
        print(f"kkml2svg: WARNING: token non reconnu {tok!r} "
              f"(rendu dégradé : 3 premiers caractères condensés)",
              file=sys.stderr)


def _avg_tech_map():
    # Historique : ' et ^ partageaient une position moyenne. Le calibrage
    # Inkscape de nov. 2026 a montré des réglages distincts : chaque marque
    # garde ses propres dx/dy. La map reste une copie (uniformise l'accès),
    # sans moyennage.
    return dict(TECHNIQUE_SUFFIXES)


def render_cell(out, tok, cx, cy, fs, cell_w=52, cell_h=58, opts=None, orient="v"):
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
      '  → uchi-utu  (｀ en haut-droite, même police et taille que la note)
               alias : ｀ (pleine chasse), * / ＊ (dépréciés)
      ^  → kaki-utu  (⌝ en haut-droite)
      v  → aki-utu   (V en bas-gauche, même police et taille que la note)
      <  → kachi-utu (⌞ en bas-gauche, même police et taille que la note)
      s  → kuubanchi (rendre le kanji plus petit, jeu faible)


    Les marques diacritiques (', *, ^, v, <) sont rendues dans la même police
    (serif) et la même taille (effective_fs) que la note. Elles ne modifient
    ni le centrage ni la taille de la note (sauf 's' qui réduit la taille).

    Positions étendues :
      尺♯       → décomposé au rendu (note 尺 + marque ♯ standard) ; @shaku_sharp off
               masque le ♯ (rendu en 尺 simple) ; jamais entouré par @shaku_circled
      下尺      → 尺 entouré d'un cercle
      下老      → deux caractères condensés via textLength (CONDENSE_W)
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
    circle_w = opts.get('circle_width', 1)  # épaisseur du cercle de 尺 (@shaku_circled)
    tmap = _avg_tech_map()  # copie des positions propres à chaque marque
    def _rt(out, suffixes, cx, cy, cw, ch, fs, text_w=None, note_fs=None,
            cell_cy=None, box_w=None, box_top=None):
        _render_techniques(out, suffixes, cx, cy, cw, ch, fs, text_w=text_w,
                           tech_map=tmap, note_fs=note_fs, cell_cy=cell_cy,
                           orient=orient, box_w=box_w, box_top=box_top)

    if tok in (EMPTY_TOKEN, "", None):
        return

    if tok == SUSTAIN_TOKEN:
        out.append(f'<text x="{cx}" y="{cy + fs * 0.227}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="#888">・</text>')
        return

    # Repos (cercle)
    if tok == REST_TOKEN:
        out.append(f'<text x="{cx}" y="{cy + fs * 0.318}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="black">'
                   f'{escape(REST_TOKEN)}</text>')
        return

    # Marques de répétition
    # ○/□ de répétition du chant (vocalRep Portama) : occupent la case
    # entière, taille note — distincts des petits ○/□ des suffixes ( )
    # et du repos ◯ (U+25EF, grand cercle centré).
    if tok == REPEAT_START:
        out.append(f'<text x="{cx}" y="{cy + fs * 0.364}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="black">'
                   f'↓</text>')
        return
    if tok == REPEAT_END:
        out.append(f'<text x="{cx}" y="{cy + fs * 0.364}" text-anchor="middle" '
                   f'font-family="serif" font-size="{fs}" fill="black">'
                   f'↑</text>')
        return

    # Extraire le préfixe 声だし ( (le chant s'ouvre AVANT la note),
    # puis les suffixes de technique depuis la fin du token.
    # (中) = 声だし + 中 + 声切り : les deux bornes peuvent cohabiter.
    koe_prefix = tok.startswith('(')
    koe_suffix = tok.endswith(')')
    base_tok = tok[1:] if koe_prefix else tok
    # Le shuffle ':' peut précéder/suivre la borne (ex. "(:合", "上:)") :
    # on ne touche PAS à base_tok ici — la branche shuffle gère ':' quelle que
    # soit sa position, et la note garde sa taille pleine (effective_fs = fs).
    tech_suffixes = []
    # Le token 尺♯ reste indivisible au FORMAT, mais il est décomposé au RENDU comme
    # toute note altérée : la note 尺 garde sa position et sa taille, le ♯ est la marque
    # d'altération standard (haut-droite). Sémantique conservée : @shaku_sharp off masque le ♯
    # (rendu en 尺 simple) ; un shaku altéré n'est JAMAIS cerclé par @shaku_circled.
    while len(base_tok) > 1 and base_tok[-1] in TECHNIQUE_CHARS:
        tech_suffixes.insert(0, base_tok[-1])
        base_tok = base_tok[:-1]
    shaku_sharp = base_tok == "尺" and "♯" in tech_suffixes
    if shaku_sharp and not opts.get("shaku_sharp", False):
        tech_suffixes = [t for t in tech_suffixes if t != "♯"]
    # Doigtés (yubii) : un token composé UNIQUEMENT de ㊀-㊃ n'est pas une
    # note (les ㊀-㊃ ne sont jamais des positions autonomes : confusion avec
    # le silence ◯) — avertissement, rien n'est rendu.
    if base_tok and all(ch in YUBII_CHARS for ch in base_tok):
        _warn_once("yubii ㊀-㊃ sans note : suffixe attendu sur une note de ::tab "
                   "(ex. 合㊀), jamais une position autonome")
        return
    if not opts.get('render_koe', True):
        # koekiri non affiché (ex. layout tuto) : on garde l'interprétation
        # mais on ne rend pas le symbole □
        tech_suffixes = [s for s in tech_suffixes if s != ')']
    if not opts.get('render_yubii', True):
        # yubii non affichés (ex. layout tuto : collision avec les vocals)
        tech_suffixes = [s for s in tech_suffixes if s not in YUBII_CHARS]

    # Bornes de chant (声だし/声切り) sur un repos ◯ : légitime, PAS
    # d'avertissement. Les bornes s'adressent à la VOIX, et la ligne
    # vocale ne suit pas nécessairement celle du sanshin — le chant peut
    # démarrer ou s'arrêter pendant un silence de l'instrument.
    # (Ligne de voix distincte : non implémentée ; 野村流 la pratique.)

    # ○ 声だし en préfixe : même position que le □ 声切り suffixe —
    # dans la case, côté droit (区画中右方, traité 野村流 p. 9).
    # Le kanji du kandokoro garde sa taille pleine : le cercle est petit et
    # ancré au bord droit de la case, il ne rétrécit pas la note.
    if koe_prefix and opts.get('render_koe', True):
        out.append(f'<text x="{cx + cell_w * 0.36}" y="{cy + fs * 0.318}" '
                   f'text-anchor="middle" font-family="serif" '
                   f'font-size="{int(fs * 0.42)}" fill="black">○</text>')

    is_small = 's' in tech_suffixes
    effective_fs = int(fs * KUUBANCHI_RATIO) if is_small else fs
    # Centrage vertical relatif (retour visuel PR #98) : la baseline d'un glyphe
    # est cy + 0,318 × SA PROPRE fs (effective_fs / sh / ss), pas cy + 0,318 × fs
    # de case — sinon kuubanchi/shuffle/straddle seraient trop bas quand la fs diminue.

    # 下尺 → 尺 entouré d'un cercle
    if base_tok == "下尺":
        r = effective_fs * 0.6325
        # cercle centré sur le glyphe du 尺 (calibrage Inkscape nov. 2026 :
        # centre = baseline − fs·0.318 = cy ; l'ancien cy+2 décentrait vers le bas)
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                   f'fill="none" stroke="black" stroke-width="{circle_w:g}"/>')
        out.append(f'<text x="{cx}" y="{cy + effective_fs * 0.318}" text-anchor="middle" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black">{escape("尺")}</text>')
        _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # 下老 → deux caractères condensés via textLength (règle CONDENSE_W, comme toute position étendue)
    if base_tok == "下老":
        target_w = effective_fs * CONDENSE_W[2]
        y_text = cy + effective_fs * 0.318
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape("下老")}</text>')
        _rt(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=target_w)
        return

    # 下八 → kandokoro propre (女絃 sous 八, octave de 中) : deux caractères
    # condensés via textLength (règle CONDENSE_W, comme 下老), SANS cercle.
    if base_tok == "下八":
        target_w = effective_fs * CONDENSE_W[2]
        y_text = cy + effective_fs * 0.318
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape("下八")}</text>')
        _rt(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=target_w)
        return

    # Positions hautes : イ尺, ロ五, イ工, etc. (préfixe + kanji condensés)
    # Deux caractères dans un seul <text> avec textLength selon CONDENSE_W (120% de fs).
    # lengthAdjust="spacingAndGlyphs" compresse légèrement les glyphes ; la déformation reste minime et lisible.
    if (len(base_tok) == 2
            and base_tok[0] in HIGH_PREFIXES
            and base_tok[1] in HIGH_POS_KANJI):
        target_w = effective_fs * CONDENSE_W[2]
        y_text = cy + effective_fs * 0.318
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape(base_tok)}</text>')
        _rt(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=target_w)
        return

    # Position haute 3 caractères : イ下尺 (préfixe + 下尺)
    # 3 caractères condensés via textLength. Pas de cercle autour du 尺
    # dans ce composé (décision du 16 sept. 2026) : le 下 reste visible,
    # le rendu suit le patron de 下老 élargi à 3 caractères.
    if (len(base_tok) == 3
            and base_tok[0] in HIGH_PREFIXES
            and base_tok[1:] == "下尺"):
        target_w = effective_fs * CONDENSE_W[3]
        y_text = cy + effective_fs * 0.318
        out.append(f'<text x="{cx - target_w/2}" y="{y_text}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">'
                   f'{escape(base_tok)}</text>')
        _rt(out, tech_suffixes, cx, cy, cell_w, cell_h,
                           effective_fs, text_w=target_w)
        return

    # Accords (jusqu'à 3 notes simultanées) : note+note[+note]
    # Rendu : notes empilées verticalement, taille 72% ; un membre composite est condensé
    # via CONDENSE_W à cette fs réduite (et non à la fs de case).
    if any(sep in base_tok for sep in ("+", "=", "-")) and len(base_tok) > 1:
        chord_notes = [n for n in re.split(r"[+=\-]", base_tok) if n]
        if len(chord_notes) >= 2:
            n = len(chord_notes)
            step = effective_fs * 0.82
            start = cy - (n - 1) * step / 2
            small = int(effective_fs * CHORD_RATIO)
            for j, c in enumerate(chord_notes):
                out.append(f'<text x="{cx}" y="{start + j*step + small/3}" '
                           f'text-anchor="middle" font-family="serif" '
                           f'font-size="{small}" fill="black"{_condensed_attrs(c, small)}>'
                           f'{escape(c)}</text>')
            # rectangle englobant du GROUPE d'accord (règle corner 2026-11-23) :
            # largeur = max des largeurs rendues des membres (condensés si composites),
            # sommet em = baseline du membre le plus haut − small
            box_w = max(small if len(c) == 1 else small * CONDENSE_W.get(min(len(c), 3), 1.8)
                        for c in chord_notes)
            box_top = start + small / 3 - small
            _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs,
                box_w=box_w, box_top=box_top)
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
        main_sharp = main_note == "尺" and "♯" in main_tech
        if main_sharp and not opts.get("shaku_sharp", False):
            main_tech = [t for t in main_tech if t != "♯"]

        # Cercle autour du shaku principal si @shaku_circled on (jamais si altéré)
        if main_note == "尺" and opts.get('shaku_circled') and not main_sharp:
            r = effective_fs * 0.6325
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                       f'fill="none" stroke="black" stroke-width="{circle_w:g}"/>')
        out.append(f'<text x="{cx}" y="{cy + effective_fs * 0.318}" text-anchor="middle" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black">{_note_svg(main_note, effective_fs, opts)}</text>')
        # Techniques de la note principale
        if main_tech:
            _rt(out, main_tech, cx, cy, cell_w, cell_h, effective_fs)

        if straddle_note:
            ss_pos = int(fs * STRADDLE_RATIO)
            ss = int(effective_fs * STRADDLE_RATIO)
            if orient == "h":
                # horizontal : la note à cheval chevauche la bordure DROITE (verticale)
                # le kanji à cheval est CENTRÉ sur la bordure droite (verticale) ;
                # l’ornement suit (positionné depuis straddle_x)
                straddle_x = cx + cell_w * 0.50
                # centré VERTICALEMENT avec la note principale : chaque glyphe
                # est centré sur cy avec sa propre taille (baseline = cy + taille*0.318)
                straddle_y = cy + ss * 0.318
            else:
                # vertical : chevauche la bordure INFÉRIEURE (horizontale)
                straddle_x = cx
                straddle_y = cy + cell_h * 0.50 + ss_pos / 3
            if straddle_note == "尺" and not opts.get("shaku_sharp", False):
                tech_suffixes = [t for t in tech_suffixes if t != "♯"]
            # Cercle autour du shaku à cheval si @shaku_circled on (jamais si altéré)
            if straddle_note == "尺" and opts.get('shaku_circled') and "♯" not in tech_suffixes:
                r = ss * 0.713
                ccx, ccy = (straddle_x, cy + 2) if orient == "h" else (cx, straddle_y - ss * 0.35)
                out.append(f'<circle cx="{ccx}" cy="{ccy}" r="{r}" '
                           f'fill="none" stroke="black" stroke-width="0.8"/>')
            out.append(f'<text x="{straddle_x}" y="{straddle_y}" '
                       f'text-anchor="middle" font-family="serif" '
                       f'font-size="{ss}" fill="black">'
                       f'{_note_svg(straddle_note, ss, opts)}</text>')
            # Les techniques de fin de token s'appliquent à la note à cheval :
            if tech_suffixes:
                if orient == "h":
                    # techniques du straddle : positionnées depuis le straddle
                    # (bordure droite), avec sa propre taille ss
                    _rt(out, tech_suffixes, straddle_x, cy,
                                       cell_w, cell_h, ss)
                else:
                    # note_fs = ss : la marque se cale sur la petite note
                    # à cheval (taille réelle du kanji porteur)
                    _rt(out, tech_suffixes, cx, straddle_y - fs * 0.318,
                                       cell_w, cell_h, effective_fs,
                                       note_fs=ss, cell_cy=cy)
        else:
            # Pas de note à cheval : les techniques s'appliquent à la note principale
            _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # --- shuffle 早弾き : A:B (deux notes égales, empilées) --- #
    if ":" in base_tok:
        parts = base_tok.split(":", 1)
        # Token ":X" ou "X:" (une seule note, ex. "(:X" / "X:)" après strip des
        # parenthèses au parsing) : la note est rendue CENTRÉE, taille pleine
        # (comme une noire) — pas décalée dans le slot "lower" du shuffle.
        if len(parts) == 2 and (not parts[0] or not parts[1]):
            lone = parts[0] or parts[1]
            if lone:
                out.append(f'<text x="{cx}" y="{cy + fs * 0.318}" text-anchor="middle" '
                           f'font-family="serif" font-size="{fs}" fill="black"{_condensed_attrs(lone, fs)}>'
                           f'{_note_svg(lone, fs, opts)}</text>')
                _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
                return
        # Shuffle à N notes (A:B:C..., N >= 3, ex. 老:四:◯) : notes égales
        # empilées, généralisation du shuffle 2 notes (早弾き à 3 coups).
        notes = base_tok.split(':')
        if len(notes) >= 3 and all(notes):
            n = len(notes)
            sh = int(effective_fs * (0.60 if n == 3 else 0.52))
            if orient == "h":
                # horizontal : côte à côte, réparties sur la largeur
                xs = [cx - fs * 0.42 + i * (fs * 0.84 / (n - 1)) for i in range(n)]
                ys = [cy + sh * 0.318] * n
            else:
                # vertical : empilées de haut en bas, réparties sur la hauteur
                ys = [cy - fs * 0.30 + i * (fs * 0.68 / (n - 1)) for i in range(n)]
                xs = [cx] * n
            for xnote, ynote, note in zip(xs, ys, notes):
                out.append(f'<text x="{xnote:g}" y="{ynote:g}" '
                           f'text-anchor="middle" font-family="serif" '
                           f'font-size="{sh}" fill="black"{_condensed_attrs(note, sh)}>'
                           f'{_note_svg(note, sh, opts)}</text>')
            _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
            return
        # La borne de chant ○/□ est un petit glyphe à part (côté droit de la
        # case) : elle ne change PAS la géométrie des notes du shuffle.
        koe = False
        sh_pos = int(fs * 0.72)
        # Taille : 80% d'une note seule (noire) — nettement plus grand
        # qu'une note à cheval (72%), sans atteindre la taille pleine.
        # Clamp : la case doit tenir 2 glyphes + 3 marges (m ~ 0.45 sh).
        sh = effective_fs * SHUFFLE_RATIO
        if orient == "h":
            sh = min(sh, cell_w / 2.9)
        else:
            sh = min(sh, cell_h / 2.9)
        # En présence d'une borne de chant, la note reste centrée comme une
        # noire (pas de décalage vers le haut). Si le ':' est en tête (ex.
        # "(:合"), la note est parts[1] et parts[0] est vide.
        if koe and not parts[0] and parts[1]:
            parts = (parts[1], "")
        if orient == "h":
            # horizontal : deux notes côte à côte, réparties sur la largeur
            # avec des marges égales (bord − m − note − m − note − m − bord).
            if koe:
                y_main = y_lower = cy + sh * 0.318
                x_main = cx
                x_lower = cx + fs * 0.42 + sh_pos / 3
            else:
                y_main = y_lower = cy + sh * 0.318
                x_left = cx - cell_w / 2
                m = (cell_w - 2 * sh) / 3
                x_main = x_left + m + sh / 2
                x_lower = x_left + cell_w - m - sh / 2
        else:
            x_main = x_lower = cx
            if koe:
                y_main = cy + sh * 0.318
                y_lower = cy + fs * 0.42 + sh_pos / 3
            else:
                # Distribution verticale à marges égales :
                # bord haut − m − note − m − note − m − bord bas.
                # bbox CJK ≈ [baseline − 0.88 em, baseline + 0.12 em].
                cell_top = cy - cell_h / 2
                m = (cell_h - 2 * sh) / 3
                y_main = cell_top + m + sh * 0.88
                y_lower = cell_top + cell_h - m - sh * 0.12
        out.append(f'<text x="{x_main:g}" y="{y_main:g}" '
                   f'text-anchor="middle" font-family="serif" '
                   f'font-size="{sh:g}" fill="black"{_condensed_attrs(parts[0], sh)}>{_note_svg(parts[0], sh, opts)}</text>')
        lower = parts[1] if len(parts) > 1 else ""
        if lower:
            out.append(f'<text x="{x_lower:g}" y="{y_lower:g}" '
                       f'text-anchor="middle" font-family="serif" '
                       f'font-size="{sh:g}" fill="black"{_condensed_attrs(lower, sh)}>'
                       f'{_note_svg(lower, sh, opts)}</text>')
        _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)
        return

    # --- note simple (noire) --- #
    if len(base_tok) == 1:
        if base_tok == "尺" and opts.get('shaku_circled') and not shaku_sharp:
            r = effective_fs * 0.6325
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                       f'fill="none" stroke="black" stroke-width="{circle_w:g}"/>')
        out.append(f'<text x="{cx}" y="{cy + effective_fs * 0.318}" text-anchor="middle" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black">{escape(base_tok)}</text>')
    else:
        # Token non reconnu (ni position simple, ni étendue, ni séparateur).
        # Repli dégradé assumé : premiers caractères (3 max) rendus condensés
        # via textLength (patron イ中 à 120% pour 2 car., イ下尺 à 180% pour 3),
        # et alerte stderr (une seule fois par token unique).
        _warn_unknown_token(base_tok)
        shown = base_tok[:3]
        target_w = effective_fs * CONDENSE_W[len(shown)]
        out.append(f'<text x="{cx - target_w/2}" y="{cy + effective_fs * 0.318}" '
                   f'font-family="serif" font-size="{effective_fs}" '
                   f'fill="black" textLength="{target_w}" '
                   f'lengthAdjust="spacingAndGlyphs">{escape(shown)}</text>')

    _rt(out, tech_suffixes, cx, cy, cell_w, cell_h, effective_fs)


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
VERTICAL_ROTATE_CHARS = set("（）()「」『』《》ー"
    + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")  # + yamakakko 《》 (échapés = littéraux pivotés)
#   + romaji/chiffres half-width (2026-11-25, JLREQ texte vertical : le latin demi-chasse
#   est pivoté de 90° ; le latin PLEINE chasse ＡＢＣ U+FF21+ reste droit, idem tiret ASCII '-')

# Vraies métriques des lettres/chiffres latins half-width : largeurs d'avance WX
# (en em) de Times-Roman, AFM Adobe standard (em = 1000) — la police de référence
# des serif occidentales. En écriture verticale, un RUN de latins pivotés est émis
# en UN SEUL bloc <text> rotatif (voir _vertical_rotated_run) : c'est le moteur qui
# fait avancer les glyphes avec ces vraies largeurs ; la table ne sert qu'à l'avance
# du run entier (frontière avec le caractère suivant), d'où une erreur minime.
LATIN_WIDTH_EM = {
    **{c: 0.5 for c in "0123456789"},
    "a": 0.444, "b": 0.5, "c": 0.444, "d": 0.5, "e": 0.444, "f": 0.333, "g": 0.5,
    "h": 0.5, "i": 0.278, "j": 0.278, "k": 0.5, "l": 0.278, "m": 0.778, "n": 0.5,
    "o": 0.5, "p": 0.5, "q": 0.5, "r": 0.333, "s": 0.389, "t": 0.278, "u": 0.5,
    "v": 0.5, "w": 0.722, "x": 0.5, "y": 0.5, "z": 0.444,
    "A": 0.722, "B": 0.667, "C": 0.667, "D": 0.722, "E": 0.611, "F": 0.556, "G": 0.722,
    "H": 0.722, "I": 0.333, "J": 0.389, "K": 0.722, "L": 0.611, "M": 0.889, "N": 0.722,
    "O": 0.722, "P": 0.556, "Q": 0.722, "R": 0.667, "S": 0.556, "T": 0.611, "U": 0.722,
    "V": 0.722, "W": 0.944, "X": 0.722, "Y": 0.722, "Z": 0.611,
}


def _latin_run_char(ch):
    """Vrai si ch fait partie d'un run de latins half-width pivotés en bloc."""
    return ch in VERTICAL_ROTATE_CHARS and ch.isascii() and ch.isalnum()


def _vstep(ch, fs, sp):
    """Avance verticale d'un caractère en texte vertical : chasse du glyphe
    (fs x chasse em) pour un latin half-width pivoté, pas fixe sp sinon."""
    if _latin_run_char(ch):
        return fs * LATIN_WIDTH_EM.get(ch, 0.5)
    return sp


def _vertical_rotated_run(out, run, x, y, fs, fill, family="serif"):
    """Émet un RUN de latins half-width pivotés en UN SEUL bloc <text> avec un
    unique transform="rotate(90 x cy)" : le moteur de rendu fait alors avancer les
    glyphes avec leurs VRAIES largeurs (+ crénage), exactement comme à l'horizontal
    (mesuré le 2026-11-25 sur « composites » en Times : le pivotage lettre par lettre
    à chasses approchées décalait les centres jusqu'à 8,7 pt à fs 26 et élargissait
    le run de +7,6 %). y = baseline du 1er caractère (convention _vertical_char)."""
    cy = y - fs * 0.35
    out.append(f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{fs:g}" '
               f'fill="{fill}" transform="rotate(90 {x:g} {cy:g})">'
               f'{escape("".join(run))}</text>')


def _emit_vertical_sequence(out, items, x, fs, fill, family="serif", group=True):
    """Émet une séquence de (caractère, baseline) en texte vertical : les runs de
    latins half-width pivotés en UN bloc rotatif (_vertical_rotated_run), les autres
    caractères pivotés pleine chasse individuellement (_vertical_char), le reste en
    UN bloc <text> groupé (group=True) ou caractère par caractère (group=False)."""
    gchars, gys = [], []

    def flush():
        if gchars:
            xs = " ".join(f"{x:g}" for _ in gchars)
            out.append(f'<text x="{xs}" y="{" ".join(f"{v:g}" for v in gys)}" '
                       f'text-anchor="middle" font-family="{family}" '
                       f'font-size="{fs:g}" fill="{fill}">'
                       f'{escape("".join(gchars))}</text>')
            gchars.clear()
            gys.clear()

    i, n = 0, len(items)
    while i < n:
        ch, yy = items[i]
        if _latin_run_char(ch):
            flush()
            run = []
            while i < n and _latin_run_char(items[i][0]):
                run.append(items[i][0])
                i += 1
            _vertical_rotated_run(out, run, x, yy, fs, fill, family)
        elif ch in VERTICAL_ROTATE_CHARS:
            flush()
            _vertical_char(out, ch, x, yy, fs, fill, family)
            i += 1
        elif group:
            gchars.append(ch)
            gys.append(yy)
            i += 1
        else:
            _vertical_char(out, ch, x, yy, fs, fill, family)
            i += 1
    flush()



def _vertical_char(out, ch, x, y, fs, fill, family="serif"):
    """Rend un caractère en texte vertical.

    Les parenthèses （）() et guillemets 「」『』 sont pivotées de 90° dans
    le sens horaire, comme l'exige la typographie japonaise verticale.
    Le signe ー (chōonpu, U+30FC) est également pivoté de 90° : barre
    horizontale en horizontal, verticale en écriture verticale.
    (Pas de pivot pour le tiret ASCII '-' ni pour 一, qui reste droit ;
    idem pour le latin/chiffres PLEINE chasse ＡＢＣ... — seuls les caractères half-width A-Za-z0-9 sont pivotés,
    règle JLREQ du texte vertical appliquée au romaji, 2026-11-25.)
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
# Échappement : \《 \》 \｛ \｝ = délimiteur littéral (antislash retiré).

RUBY_OPEN  = "｛"   # U+FF5B
RUBY_CLOSE = "｝"   # U+FF5D
ANNOT_OPEN = "《"   # U+300A
ANNOT_CLOSE = "》"  # U+300B
ESCAPE = "\\"
ESCAPABLE = RUBY_OPEN + RUBY_CLOSE + ANNOT_OPEN + ANNOT_CLOSE  # ｛｝《》


def _unescape(s):
    """Retire l'antislash des délimiteurs échappés (\《 \》 \｛ \｝ -> 《 》 ｛ ｝).
    Un antislash devant tout autre caractère reste littéral."""
    if ESCAPE not in s:
        return s
    out = []
    i = 0
    while i < len(s):
        if s[i] == ESCAPE and i + 1 < len(s) and s[i + 1] in ESCAPABLE:
            out.append(s[i + 1])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _escape(s):
    """Échappe les délimiteurs ruby — ré-émission en syntaxe KKML depuis du
    texte déjà analysé (ex. _h_lyrics_atoms)."""
    if not any(c in ESCAPABLE for c in s):
        return s
    return "".join(ESCAPE + c if c in ESCAPABLE else c for c in s)


def _find_unescaped(s, ch, start):
    """Prochaine occurrence de ch non échappée (non précédée d'un antislash)."""
    j = s.find(ch, start)
    while j > 0 and s[j - 1] == ESCAPE:
        j = s.find(ch, j + 1)
    return j


# --------------------------------------------------------------------------- #
# Liens hypertexte dans les métadonnées : [label](url), style Markdown.
# Le label peut contenir du ruby (syntaxe 《》 ｛｝) ; l'url n'est pas affichée.
# Un antislash devant [ ou ] rend le crochet littéral (\(). Les paires ruby
# échappées (\《 etc.) sont conservées telles quelles dans les segments.
# --------------------------------------------------------------------------- #
_LINK_RE = re.compile(r"\[([^\[\]]*)\]\(([^()]*)\)")


def _split_links(text):
    """Découpe en segments ('text', s) ou ('link', label, url)."""
    segs, buf = [], []
    i, n = 0, len(text)
    def flush():
        if buf:
            segs.append(("text", "".join(buf)))
            buf.clear()
    while i < n:
        c = text[i]
        if c == ESCAPE and i + 1 < n and text[i + 1] in ESCAPABLE:
            buf.append(text[i:i + 2])  # paire ruby échappée : gardée pour _parse_ruby
            i += 2
        elif c == ESCAPE and i + 1 < n and text[i + 1] in "[]":
            buf.append(text[i + 1])     # crochet littéral
            i += 2
        elif c == "[":
            m = _LINK_RE.match(text, i)
            if m and m.group(2).strip():
                flush()
                segs.append(("link", m.group(1), m.group(2)))
                i = m.end()
            else:
                buf.append(c)
                i += 1
        else:
            buf.append(c)
            i += 1
    flush()
    return segs


def _link_free(text):
    """Texte sans la syntaxe des liens (labels conservés) — pour les mesures."""
    return "".join(seg[1] for seg in _split_links(text))


def _link_open(url):
    return (f'<a xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'xlink:href="{escape(url).replace(chr(34), "&quot;")}">')


def _emit_centered_text(out, text, cx, y, fs, fill, family="serif", links=False):
    """Émet un <text> centré en cx ; avec links=True, les [label](url) sont
    enveloppés dans un <a xlink:href> (seul le label est affiché)."""
    segs = _split_links(text) if links else [("text", text)]
    if len(segs) == 1 and segs[0][0] == "text":
        out.append(f'<text x="{cx:g}" y="{y:g}" text-anchor="middle" font-family="{family}" '
                   f'font-size="{fs}" fill="{fill}">{escape(_unescape(segs[0][1]))}</text>')
        return
    w = _h_text_w(_link_free(text), fs)
    xcur = cx - w / 2
    for seg in segs:
        body = (f'<text x="{xcur:g}" y="{y:g}" font-family="{family}" '
                f'font-size="{fs}" fill="{fill}">{escape(_unescape(seg[1]))}</text>')
        if seg[0] == "link":
            out.append(_link_open(seg[2]))
            out.append(body)
            out.append("</a>")
        else:
            out.append(body)
        xcur += _h_text_w(seg[1], fs)


def _parse_ruby(text):
    """Découpe une chaîne en segments avec ou sans ruby.
    Retourne une liste de dicts : plain, mono, group, jukugo.
    Les délimiteurs échappés (\《 \》 \｛ \｝) sont des caractères littéraux :
    l'antislash est retiré et ils ne structurent pas le texte."""
    segments = []
    i = 0
    n = len(text)
    plain_start = i

    while i < n:
        if text[i] == ESCAPE and i + 1 < n and text[i + 1] in ESCAPABLE:
            i += 2  # délimiteur échappé : caractère littéral du texte clair
            continue
        # Groupe ｛...｝
        if text[i] == RUBY_OPEN:
            if i > plain_start:
                segments.append({"type": "plain", "text": _unescape(text[plain_start:i])})
            i += 1  # skip ｛
            group_start = i
            depth = 1
            while i < n and depth > 0:
                if text[i] == ESCAPE and i + 1 < n and text[i + 1] in ESCAPABLE:
                    i += 2
                    continue
                if text[i] == RUBY_OPEN:
                    depth += 1
                elif text[i] == RUBY_CLOSE:
                    depth -= 1
                if depth > 0:
                    i += 1
            group_content = text[group_start:i]
            i += 1  # skip ｝
            plain_start = i

            if _find_unescaped(group_content, ANNOT_OPEN, 0) != -1:
                # Jukugo-ruby : annotations individuelles dans le groupe
                items = []
                ji = 0
                base_start = ji
                while ji < len(group_content):
                    if (group_content[ji] == ESCAPE and ji + 1 < len(group_content)
                            and group_content[ji + 1] in ESCAPABLE):
                        ji += 2
                        continue
                    if group_content[ji] == ANNOT_OPEN:
                        close_idx = _find_unescaped(group_content, ANNOT_CLOSE, ji)
                        if close_idx == -1:
                            raise ValueError(f"annotation ruby sans {ANNOT_CLOSE} : {group_content!r}")
                        if ji > base_start:
                            base_chars = _unescape(group_content[base_start:ji])
                            ruby_text = _unescape(group_content[ji+1:close_idx])
                            items.append((base_chars, ruby_text))
                        ji = close_idx + 1
                        base_start = ji
                    else:
                        ji += 1
                if base_start < len(group_content):
                    rest = group_content[base_start:]
                    ri = 0
                    while ri < len(rest):
                        if rest[ri] == ESCAPE and ri + 1 < len(rest) and rest[ri + 1] in ESCAPABLE:
                            items.append((rest[ri + 1], None))
                            ri += 2
                        else:
                            items.append((rest[ri], None))
                            ri += 1
                segments.append({"type": "jukugo", "items": items})
            else:
                # Group-ruby simple : ｛base｝《ruby》
                if i < n and text[i:i+1] == ANNOT_OPEN:
                    close_idx = _find_unescaped(text, ANNOT_CLOSE, i)
                    if close_idx == -1:
                        raise ValueError(f"annotation ruby sans {ANNOT_CLOSE} : {text!r}")
                    ruby_text = _unescape(text[i+1:close_idx])
                    segments.append({"type": "group",
                                     "base": _unescape(group_content), "ruby": ruby_text})
                    i = close_idx + 1
                    plain_start = i
                else:
                    # Groupe sans annotation -> plain
                    segments.append({"type": "plain", "text": _unescape(group_content)})

        elif text[i:i+1] == ANNOT_OPEN:
            # Mono-ruby : base = dernier caractère du texte précédent
            base_text = _unescape(text[plain_start:i])
            close_idx = _find_unescaped(text, ANNOT_CLOSE, i)
            if close_idx == -1:
                raise ValueError(f"annotation ruby sans {ANNOT_CLOSE} : {text!r}")
            ruby_text = _unescape(text[i+1:close_idx])
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
        segments.append({"type": "plain", "text": _unescape(text[plain_start:])})

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


def _plan_vertical_ruby(segments, fs, sp):
    """Planifie la disposition verticale d'une suite de segments ruby.

    Règle générique (comme les traiteurs de texte Word/LibreOffice) :
    JAMAIS d'écartement des caractères AU SEIN d'un groupe rubyé —
    ce sont les GROUPES (bases groupées) qui s'écartent, de manière à ce
    que les blocs ruby se suivent en flux continu (haut du bloc ruby n+1
    = bas du bloc ruby n + gap constant), sans à-coups. Le bloc ruby est
    centré sur sa base quand le flux le permet ; sinon le groupe de base
    est poussé vers le bas pour que son ruby prenne la suite du flux.
    (Le ruby vivant dans sa propre colonne à droite, seuls les blocs ruby
    peuvent se chevaucher entre eux.)

    Retourne (plan, hauteur) où plan est une liste de
    {'base': [(car, y), …], 'ruby': [(car, y), …]} — y RELATIFS au départ,
    cumulés segment après segment. hauteur = y final du flux de base.
    """
    ruby_fs = int(fs * RUBY_SCALE)
    ruby_sp = sp * 0.55
    # Les glyphes sont rendus horizontaux empilés (baseline en y, encre de
    # y-0.88em à y+0.12em) : le centre d'encre d'un glyphe est à y-0.38em.
    # Pour centrer le bloc ruby sur l'ENCRE de sa base (et pas sur les
    # baselines), on compense l'écart 0.38em x (fs - ruby_fs).
    adj = 0.38 * (fs - ruby_fs)
    # flux ruby continu : l'intervalle entre blocs suit le rythme intra-bloc
    # (ruby_sp entre baselines), avec garde-fou minimal (boîte + interstice).
    gap = ruby_fs * 0.4
    step = max(ruby_sp, ruby_fs + gap)

    def keep(ch):
        return not (ch.isspace() or unicodedata.combining(ch)
                    or ch in VARIATION_SELECTORS)

    y = 0.0        # curseur du flux de base (next baseline)
    ry_cur = None  # bas du dernier bloc ruby posé (flux ruby continu)
    plan = []

    def annotated(base, ruby):
        """Pose un groupe rubyé : bases à sp (jamais écartées entre elles),
        ruby centré sur sa base ou poussé à la suite du flux ruby."""
        nonlocal y, ry_cur
        n = len(base)
        # positions cumulées : chasse variable des latins pivotés (2026-11-25)
        bpos = []
        yy = y
        for ch in base:
            bpos.append((ch, yy))
            yy += _vstep(ch, fs, sp)
        H_b = bpos[-1][1] - bpos[0][1] if n > 1 else 0.0
        if not ruby:
            plan.append({'base': bpos, 'ruby': []})
            y = yy
            return
        H_r = (len(ruby) - 1) * ruby_sp
        # centrage sur les centres d'ENCRE (glyphe : encre de y-0.88em à
        # y+0.12em, centre à y-0.38em) : le bloc ruby paraît sinon trop bas.
        centered_ry = y + H_b / 2 - H_r / 2 - adj
        if ry_cur is None:
            ry = centered_ry
        else:
            ry = max(ry_cur + step, centered_ry)
        b0 = ry + H_r / 2 - H_b / 2 + adj
        if b0 < y:  # garde-fou (arrondis) : la base ne remonte jamais
            b0 = y
            ry = max(ry, y + H_b / 2 - adj - H_r / 2)
        rpos = []
        rr = ry
        for rc in ruby:
            rpos.append((rc, rr))
            rr += _vstep(rc, ruby_fs, ruby_sp)
        plan.append({'base': [(ch, b0 + (bp - bpos[0][1])) for ch, bp in bpos],
                     'ruby': rpos})
        ry_cur = rpos[-1][1]
        y = b0 + H_b + _vstep(base[-1], fs, sp)   # le flux de base continue après la dernière base (rebasé sur b0)

    for seg in segments:
        if seg["type"] == "plain":
            base = []
            for ch in seg["text"]:
                if ch.isspace():
                    y += sp
                    continue
                if keep(ch):
                    base.append((ch, y))
                y += _vstep(ch, fs, sp)   # chasse variable des latins pivotés (2026-11-25)
            plan.append({'base': base, 'ruby': []})
        elif seg["type"] == "mono":
            annotated(seg["base"], seg["ruby"] or "")
        elif seg["type"] == "group":
            annotated(seg["base"], seg["ruby"] or "")
        elif seg["type"] == "jukugo":
            for base, ruby in seg["items"]:
                annotated(base, ruby or "")
    return plan, y


def _render_vertical_ruby(out, segments, x, y, fs, fill, sp, family="serif"):
    """Rend des segments ruby en mode vertical (ruby à droite),
    caractère par caractère, selon le plan de _plan_vertical_ruby
    (écartement générique des bases quand les blocs ruby sont trop longs).
    x = position horizontale du texte de base
    y = position verticale de départ (baseline du 1er caractère)
    fs = taille de base, sp = espacement vertical entre caractères de base
    Retourne le y après le dernier segment."""
    ruby_fs = int(fs * RUBY_SCALE)
    ruby_x = x + fs * 0.75  # ruby à droite, espacé de la base
    plan, h = _plan_vertical_ruby(segments, fs, sp)
    for e in plan:
        _emit_vertical_sequence(out, [(ch, y + cy) for ch, cy in e['base']],
                                x, fs, fill, family, group=False)
        _emit_vertical_sequence(out, [(rc, y + ry) for rc, ry in e['ruby']],
                                ruby_x, ruby_fs, fill, family, group=False)
    return y + h


def _vertical_grouped_text(out, text, x, y, fs, fill, sp, family="serif", links=False):
    """Rend un texte vertical en BLOCS <text> groupés (SVG 1.1, listes
    links=True : les liens [label](url) des métadonnées sont enveloppés
    dans un <a xlink:href> (label seul affiché).
    x/y par glyphe) :
      <text x="x x x …" y="y1 y2 …" …>caractères</text>
    (liste x répétée : indispensable, sinon chaque glyphe conserve l'avance
    naturelle du précédent et le texte part en escalier)

    - Les caractères de BASE (tous segments confondus) sont regroupés en
      UN SEUL bloc ; chaque annotation ruby est un bloc <text> indépendant
      à droite de sa base (« les ruby vivent leur vie »), positions
      calculées par _plan_vertical_ruby (écartement générique des bases
      quand les blocs ruby sont trop longs).
    - Rotation (ー, parenthèses, guillemets) : ces glyphes sortent du bloc
      et sont rendus en éléments <text> individuels avec
      transform="rotate(90 x cy)" (le pivot par glyphe de l'attribut rotate
      étant dépendant du moteur de rendu).
    Retourne le y après le dernier caractère (comme _render_vertical_text).
    """
    if links:
        for seg in _split_links(text):
            if seg[0] == "text":
                y = _vertical_grouped_text(out, seg[1], x, y, fs, fill, sp, family)
            else:
                sub = []
                y2 = _vertical_grouped_text(sub, seg[1], x, y, fs, fill, sp, family)
                out.append(_link_open(seg[2]))
                out.extend(sub)
                out.append("</a>")
                y = y2
        return y
    def _emit_group(chars, ys, gfs, gx):
        # Runs de latins half-width pivotés en UN bloc rotatif (2026-11-25),
        # autres pivotés pleine chasse en éléments individuels, le reste en bloc groupé.
        _emit_vertical_sequence(out, list(zip(chars, ys)), gx, gfs, fill, family, group=True)

    segments = _parse_ruby(text)
    plan, h = _plan_vertical_ruby(segments, fs, sp)
    ruby_fs = int(fs * RUBY_SCALE)
    ruby_x = x + fs * 0.75  # ruby à droite, espacé de la base
    base_chars, base_ys = [], []   # bloc unique des caractères de base
    for e in plan:
        for ch, cy in e['base']:
            base_chars.append(ch)
            base_ys.append(y + cy)   # le plan donne des y RELATIFS
        if e['ruby']:
            _emit_group([c for c, _ in e['ruby']],
                        [y + cy for _, cy in e['ruby']], ruby_fs, ruby_x)
    _emit_group(base_chars, base_ys, fs, x)
    return y + h


def _render_vertical_text(out, text, x, y, fs, fill, sp, family="serif", links=False):
    """Rend un texte en mode vertical, avec ou sans ruby.
    Sans ruby : rendu caractère par caractère (compatibilité ascendante).
    Avec ruby : utilise _render_vertical_ruby.
    links=True : liens [label](url) enveloppés dans un <a xlink:href>."""
    if links:
        for seg in _split_links(text):
            if seg[0] == "text":
                y = _render_vertical_text(out, seg[1], x, y, fs, fill, sp, family)
            else:
                sub = []
                y2 = _render_vertical_text(sub, seg[1], x, y, fs, fill, sp, family)
                out.append(_link_open(seg[2]))
                out.extend(sub)
                out.append("</a>")
                y = y2
        return y
    segments = _parse_ruby(text)
    if not _has_ruby(segments):
        items = []
        for ch in _unescape(text):
            if ch.isspace():
                y += sp
                continue
            if unicodedata.combining(ch) or ch in VARIATION_SELECTORS:
                continue
            items.append((ch, y))
            y += _vstep(ch, fs, sp)   # avance du run de latins pivotés (2026-11-25)
        _emit_vertical_sequence(out, items, x, fs, fill, family, group=False)
        return y
    return _render_vertical_ruby(out, segments, x, y, fs, fill, sp, family)


def _vertical_text_height(text, fs, sp):
    """Hauteur réellement consommée par _render_vertical_text(text, …, sp) :
    avance par caractère (espaces compris), caractères combinants ignorés ;
    avec ruby, hauteur du plan ruby vertical (l'écartement ruby allonge le
    flux). Utilisée pour le repli des colonnes de paroles en blocs de
    hauteur fixée (layout mega)."""
    segments = _parse_ruby(text)
    if _has_ruby(segments):
        return _plan_vertical_ruby(segments, fs, sp)[1]
    h = 0.0
    for ch in _unescape(text):
        if ch.isspace():
            h += sp
            continue
        if unicodedata.combining(ch) or ch in VARIATION_SELECTORS:
            continue
        h += sp
    return h


def _char_w(ch, fs):
    # Largeur approximative d'un glyphe : pleine chasse (CJK/kana/kanji >= U+2E80)
    # = 1em ; latin (romaji) = 0.55em. L'élément <text> SVG se rend à la largeur
    # naturelle du glyphe : l'avance entre segments ruby doit suivre cette
    # largeur, sinon les segments se chevauchent (ex. le mono 花 tombait sur
    # les kana さぐぬ d'un titre てぃんさぐぬ花『はな』).
    return fs if ord(ch) >= 0x2E80 else fs * 0.55


def _plan_horizontal_ruby(segments, fs):
    """Planifie la disposition horizontale d'une suite de segments ruby.

    Même règle Word/LibreOffice qu'en vertical (_plan_vertical_ruby) :
    JAMAIS d'écartement des caractères au sein d'un groupe rubyé — ce sont
    les GROUPES qui s'écartent, pour que les blocs ruby (au-dessus de la
    base) se suivent en flux continu : bord gauche du bloc ruby n+1 >= bord
    droit du bloc n + gap (0,4 x ruby_fs). Chaque bloc ruby est centré sur
    sa base quand le flux le permet ; sinon le groupe de base est poussé
    vers la droite. En horizontal, les avances (_char_w : CJK 1em, latin
    0,55em) tiennent lieu de boîtes : le centrage sur les avances équivaut
    au centrage sur l'encre.

    Retourne (plan, largeur) où plan est une liste de
    {'base': (texte, x), 'ruby': (texte, x) ou None} — x RELATIFS au départ,
    cumulés segment après segment. largeur = x final du flux de base.
    """
    ruby_fs = int(fs * RUBY_SCALE)
    gap = ruby_fs * 0.4   # interstice constant entre blocs ruby voisins

    x = 0.0        # curseur du flux de base (bord gauche du prochain groupe)
    rx_end = None  # bord droit du dernier bloc ruby posé (flux continu)
    plan = []

    def annotated(base, ruby):
        nonlocal x, rx_end
        base_w = sum(_char_w(c, fs) for c in base)
        if not ruby:
            plan.append({'base': (base, x), 'ruby': None})
            x += base_w
            return
        ruby_w = sum(_char_w(c, ruby_fs) for c in ruby)
        centered_rx = x + (base_w - ruby_w) / 2
        if rx_end is None:
            rx = centered_rx
        else:
            rx = max(rx_end + gap, centered_rx)
        b0 = rx + ruby_w / 2 - base_w / 2
        if b0 < x:  # garde-fou (arrondis) : la base ne remonte jamais
            b0 = x
            rx = max(rx, b0 + (base_w - ruby_w) / 2)
        plan.append({'base': (base, b0), 'ruby': (ruby, rx)})
        rx_end = rx + ruby_w
        x = b0 + base_w   # le flux de base continue après la dernière base

    for seg in segments:
        if seg["type"] == "plain":
            plan.append({'base': (seg["text"], x), 'ruby': None})
            x += sum(_char_w(c, fs) for c in seg["text"])
        elif seg["type"] == "mono":
            annotated(seg["base"], seg["ruby"] or "")
        elif seg["type"] == "group":
            annotated(seg["base"], seg["ruby"] or "")
        elif seg["type"] == "jukugo":
            for base, ruby in seg["items"]:
                annotated(base, ruby or "")
    return plan, x


def _render_horizontal_ruby(out, segments, x, y, fs, fill, family="serif"):
    """Rend des segments ruby en mode horizontal (ruby au-dessus de la base),
    selon le plan de _plan_horizontal_ruby (règle d'écartement générique).
    x = position horizontale de départ
    y = position verticale du texte de base (baseline)
    Retourne le x après le dernier segment."""
    ruby_fs = int(fs * RUBY_SCALE)
    # ruby bien AU-DESSUS du glyphe de base : un CJK monte ~0.88em au-dessus
    # de la baseline ; à 0.55em le ruby chevauchait le haut du caractère (ex. 花)
    ruby_y = y - fs * 0.95

    plan, w = _plan_horizontal_ruby(segments, fs)
    for e in plan:
        base, bx = e['base']
        out.append(f'<text x="{x + bx:g}" y="{y}" font-family="{family}" '
                   f'font-size="{fs}" fill="{fill}">{escape(base)}</text>')
        if e['ruby']:
            ruby, rx = e['ruby']
            out.append(f'<text x="{x + rx:g}" y="{ruby_y}" '
                       f'font-family="{family}" font-size="{ruby_fs}" '
                       f'fill="{fill}">{escape(ruby)}</text>')
    return x + w


def _h_text_w(text, fs):
    """Largeur avancée d'un texte horizontal (ruby pris en compte via le
    plan, sinon somme des largeurs de glyphes)."""
    if not text:
        return 0.0
    segments = _parse_ruby(text)
    if _has_ruby(segments):
        return _plan_horizontal_ruby(segments, fs)[1]
    return sum(_char_w(c, fs) for c in _unescape(text))


def _render_horizontal_text(out, text, x, y, fs, fill, family="serif", links=False):
    """Rend un texte en mode horizontal, avec ou sans ruby.
    Sans ruby : un seul élément <text> (compatibilité ascendante).
    Avec ruby : utilise _render_horizontal_ruby.
    links=True : liens [label](url) enveloppés dans un <a xlink:href>."""
    if links:
        for seg in _split_links(text):
            if seg[0] == "text":
                x = _render_horizontal_text(out, seg[1], x, y, fs, fill, family)
            else:
                sub = []
                x2 = _render_horizontal_text(sub, seg[1], x, y, fs, fill, family)
                out.append(_link_open(seg[2]))
                out.extend(sub)
                out.append("</a>")
                x = x2
        return x
    segments = _parse_ruby(text)
    if not _has_ruby(segments):
        out.append(f'<text x="{x:g}" y="{y:g}" font-family="{family}" '
                   f'font-size="{fs:g}" fill="{fill}">{escape(_unescape(text))}</text>')
        return x + sum(_char_w(ch, fs) for ch in _unescape(text))
    return _render_horizontal_ruby(out, segments, x, y, fs, fill, family)


# --------------------------------------------------------------------------- #
# 4. CLI
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="KKML -> 工工四 SVG converter")
    ap.add_argument("input", help="fichier .kkml ou '-' pour stdin")
    ap.add_argument("-o", "--output", help="fichier SVG de sortie")
    ap.add_argument("-c", "--cells-per-dan", dest="cols", type=int,
                    help="cellules par dan : lignes par colonne (vertical) ou colonnes par rangée (horizontal)")
    ap.add_argument("-l", "--layout", choices=["vertical", "horizontal", "nomura", "chindami", "tuto", "mega"],
                    help="force le layout (surcharge @layout)")
    ap.add_argument("-p", "--dans-per-page", "--page-dans", type=int, dest="page_dans",
                    help="nombre max de dans par page (pagination multipage, surcharge @dans_per_page)")
    ap.add_argument("--kinsoku", choices=["simple", "strict", "off"], default=None,
                    help="kinsoku JLREQ au repli des paroles ::lyrics (surcharge @kinsoku)")
    args = ap.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
        out_path = args.output or "output.svg"
    else:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
        out_path = args.output or (args.input.rsplit(".", 1)[0] + ".svg")

    song = parse_kkml(text)
    svgs = render_svg(song, cols=args.cols, layout=args.layout,
                       page_dans=args.page_dans, kinsoku=args.kinsoku)
    if len(svgs) == 1:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svgs[0])
        print(f"OK: {out_path}  ({len(svgs[0])} octets)", file=sys.stderr)
    else:
        base, dot, ext = out_path.rpartition(".")
        stem = base if dot else out_path
        ext = ("." + ext) if dot else ""
        for i, svg in enumerate(svgs, 1):
            page_path = f"{stem}-{i}{ext}"
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"OK: {page_path}  ({len(svg)} octets)", file=sys.stderr)
        print(f"{len(svgs)} pages générées", file=sys.stderr)


if __name__ == "__main__":
    main()
