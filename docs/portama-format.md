# Format Portama JSON (portama.com/kunkun4)

Portama est un éditeur de kunkunshi en ligne ([portama.com/kunkun4](https://portama.com/kunkun4/)) qui génère des tablatures de sanshin. Il peut exporter le résultat au format JSON et PDF. Le format JSON peut servir de source d'import pour le convertisseur KKML.

## Structure du JSON

```json
{
  "version": "2.2",
  "musicno": 5168,
  "numDans": 19,
  "cellsPerDan": 24,
  "score": [[...], [...], ...],
  "title": "かぎやで風節",
  "choshi": "hon",
  "chogen": "5",
  "speed": "68",
  "rhythm": "0",
  "rhythmMode": "0",
  "orientation": "landscape",
  "allRubyData": {...},
  "allLyricsData": {...},
  "lyricsWritingMode": "vertical",
  "lyricsFontFamily": "mincho",
  "lyricsFontSize": "10pt"
}
```

## Description des champs

| Champ | Type | Description |
|-------|------|-------------|
| `version` | string | Numéro de version du JSON Portama |
| `numDans` | int | Nombre de dans (段). |
| `cellsPerDan` | int | Toujours 24 (12 notes × 2 cellules : main + straddle). |
| `musicno` | int | Inconnu, probablement identifiant unique du morceau sur l'éditeur Kunkunshi Portama |
| `score` | `Array<Array<Cell>>` | 2D : `[dan][cell]`. Chaque dan a 24 cellules (12 paires main+straddle). |
| `title` | string | Titre de la chanson. |
| `choshi` | string | Accordage : `"hon"` = 本調子. |
| `chogen` | string | Génération/clé (4 ou 5 observé). Signification exacte inconnue. |
| `speed` | string | Tempo (BPM). Ex : "180". |
| `rhythm` | string | Mode rythmique. "0" = ?, "100" = ?. |
| `rhythmMode` | string | "0" ou "100". |
| `orientation` | string | Toujours `"landscape"`. |
| `allRubyData` | inconnu | Voir section dédiée ci-dessous. |
| `allLyricsData` | inconnu | Cadres de paroles avec `id`, `content`, `x`, `y`, `width`, `height`, `fontSize`. Content = "歌詞を入力" si non renseigné. |
| `lyricsWritingMode` | string | inconnu. Ex : "vertical". |
| `lyricsFontFamily` | string | inconnu. Ex : "mincho". |
| `lyricsFontSize` | string | inconnu. Ex : "10pt". |

## Structure des cellules (`score[dan][cell]`)

Chaque cellule est un objet avec :

| Champ | Type | Description |
|-------|------|-------------|
| `note` | string | Caractère PUA Unicode (U+E000–U+E030) ou chaîne vide. |
| `isSmall` | bool | `true` = petite note (straddle), `false` = note standard. Sur une note principale, indique un shuffle (deux notes égales). |
| `acc` | string | Altération : `"sharp"` = dièse (observé uniquement sur 尺 → 尺♯). |
| `orn` | string | Ornement/souhou : `"u"` = uchi-utu. Autres valeurs non confirmées. |
| `repeatStart` | bool | Début de répétition. |
| `repeatEnd` | bool | Fin de répétition. |

### Organisation des 24 cellules par dan

Les cellules sont organisées en 12 paires consécutives :

- Index pair (0, 2, 4, ...) = note principale
- Index impair (1, 3, 5, ...) = note à cheval (straddle)

| Main | Straddle | Mode KKML | Token |
|------|----------|----------|-------|
| note | vide | Noire | `A` |
| note (isSmall=false) | note | Croche | `A/B` |
| note (isSmall=true) | note | Shuffle 早弾き | `A:B` |
| note (isSmall=true) | vide | Kuubanchi | `As` |
| vide | vide | Case vide | `-` |

## Correspondance PUA → kanji

Confirmée par recoupement entre les fichiers JSON et les corrigés KKML manuels de だんじゅかりゆし et 国頭ジントヨー (12 septembre 2026). Le 3e octet UTF-8 de chaque caractère PUA est extrait via `jq` + `explode[2]`, puis converti : `byte3 & 0x3F` = offset PUA (U+E0xx).

| 3e octet (décimal) | Codepoint PUA | Kanji | Fichiers confirmants |
|-------------------|---------------|-------|----------------------|
| 128 | U+E000 | 合 | だんじゅ, 国頭, かぎや |
| 129 | U+E001 | 乙 | だんじゅ, 国頭, かぎや |
| 130 | U+E002 | 老 | だんじゅ, 国頭, かぎや |
| 144 | U+E010 | 四 | だんじゅ, 国頭, かぎや |
| 145 | U+E011 | 上 | だんじゅ, 国頭, かぎや |
| 146 | U+E012 | 中 | だんじゅ, 国頭 |
| 147 | U+E013 | 尺 | だんじゅ, かぎや |
| 160 | U+E020 | 工 | les 3 |
| 161 | U+E021 | 五 | 国頭, かぎや |
| 162 | U+E022 | 六 | だんじゅ |
| 163 | U+E023 | 七 | だんじゅ, 国頭, かぎや |
| 164 | U+E024 | 八 | かぎや (1 occurrence, validé par cohérence séquentielle avec l'utilisateur) |
| 165 | U+E025 | 九 | Non observé (inféré par séquence) |
| 176 | U+E030 | ◯ (silence) | les 3 |

Structure : trois blocs séquentiels — E000–E002 (registre grave : 合 乙 老), E010–E013 (registre médian : 四 上 中 尺), E020–E025 (registre aigu : 工 五 六 七 八 九), E030 (silence). Les intervalles E003–E00F et E014–E01F sont inutilisés. L'ordre interne de chaque bloc suit l'ordre traditionnel du kunkunshi (grave → aigu). U+E024=八 et U+E025=九 sont confirmés par cohérence séquentielle avec l'utilisateur ; U+E025 n'a pas encore été observé dans un fichier Portama.

## Ornements (souhou)

Seul `"u"` (uchi-utu → suffixe `*` en KKML) est confirmé dans les fichiers analysés.

Hypothèses non confirmées (à vérifier avec d'autres fichiers) :
- `"k"` → kaki-utu → `^`
- `"a"` → aki-utu → `v`
- `"c"` → kachi-utu → `<`
- `"t"` → taachi → `=`

## Encodage

Le fichier JSON est en UTF-8.

## Colonne marker et données vocales (`allRubyData`)

`allRubyData` contient le texte vocal affiché dans la colonne marker (sous-colonne droite de chaque pile). Clé = numéro de page en string, valeur = tableau de lignes, 1 ligne par dan (19 lignes pour かぎやで風節 = 19 dans).

Structure du positionnement (validée exactement contre le PDF rendu) :

- U+3000 (espace pleine largeur) = 1 unité ; espace ASCII = 0,5 unité.
- Champ de saisie d'environ 36 unités pour 12 cases = exactement 3 unités monospace par case (longueurs de ligne observées 14–36 unités).
- Le rendu PDF est une application STRICTEMENT LINÉAIRE des unités source : `top_caractère = 36,9 + 2,74 + 14,646 × unités` (mesuré sur かぎやで風節.pdf, 58 caractères, résidu max 0,00 pt). L'unité = hauteur_case/3 = 43,94/3 = 14,646 pt.
- La conclusion initiale « pas de système de slots strict (33/54) » est à remplacer par : il existe une grille stricte de 3 lignes ruby par case (fractions de case 0,06 / 0,40 / 0,73 pour les unités entières mod 3), mais AUCUN arrimage des syllabes aux notes — l'auteur place librement les syllabes à la demi-unité près (fractions observées 0,06–0,90). C'est un champ texte vertical libre, pas un modèle syllabe↔note.

Rendu des caractères (mesuré sur かぎやで風節.pdf) :

- Police IPAexMincho 11 pt (ratio vs note fs 17 = 0,65 ; ratio vs hauteur de case = 0,25). Le JSON dit `lyricsFontSize: "10pt"` mais le ruby rendu est à 11 pt.
- Colonne marker : sous-colonne de 24,1 pt à droite de chaque pile (largeur pile 52,4 = 28,3 notes + 24,1 marker, séparées par un trait vertical). Ruby dessiné à +3,7 pt du bord gauche de la sous-colonne marker (boîte de 11 pt, léger biais gauche).
- Chaque caractère pleine largeur = 1 ligne à l'avance de 14,646 pt (1,33 × fs ruby), quelle que soit son appartenance à un token.
- Petits kana (ぁぃぅぇぉゃゅょゎ) : rendus à +12,99 pt sous le caractère précédent (vs 14,646 sur la grille — tuck optique de 1,65 pt) et +1,12 pt à droite ; le caractère suivant reprend sa position de grille. Mesuré sur 17 instances, valeurs identiques au centième.
- Caractères pleine taille dans un token multi-caractères (きゆ, やう) : avance pleine de 14,646 pt, pas de tuck. Donc Portama ne tuck que les petits kana, sans notion de syllabe.
- ー (chōonpu) absent de ce fichier : comportement non mesuré.
- Syllabes multi-caractères dans la source : caractères adjacents sans séparateur (てぃ, でぃ, をぅ, つぃ, とぅ, ちゃ, しゃ, やう, きゆ, et un token de 3 caractères つぃぶ). Confirme la règle KKML « 1 token = 1 syllabe ». Incohérence de saisie auteur : dan 3 utilise を+う (う pleine taille) alors que dans 6/11/14 c'est を+ぅ (petit).

Implication pour notre convertisseur : l'alignement strict de `::vocal` (syllabe i ↔ note i, par padding) reste plus rigoureux que le positionnement libre de Portama — mais la convention Portama montre la tolérance de la tradition : 3 lignes ruby par case, placement à la demi-unité. Les constantes mesurées pour un éventuel calibrage : ruby_fs/note_fs = 0,65 ; avance ligne = cell_h/3 ; tuck petit kana = 1,18 × fs sous le haut du caractère précédent (notre espacement actuel : syllable_fs × 0,85).

Un seul échantillon contient des données ruby : かぎやで風節.json (allRubyData vide pour 国頭ジントヨー et だんじゅかりゆし).

## Géométrie du PDF Portama (だんじゅかりゆし.pdf et かぎやで風節.pdf, A4 paysage)

Les deux PDF partagent la même grille :

- Cadre extérieur 28,3–819,2 × 28,3–575,4 pt. Piles au pas de 60,9 pt, cadre de pile 52,4 pt de large = sous-colonne notes 28,3 pt (gauche) + sous-colonne marker 24,1 pt (droite), séparées par un trait vertical. Jusqu'à 12 piles par page ; だんじゅかりゆし (7 dans) = 1 page, かぎやで風節 (19 dans) = 12 piles page 1 + 7 piles page 2 (dans 13–19, demi-page gauche vide). Ordre de lecture des piles : droite → gauche (dan 1 = pile la plus à droite).
- 12 cases par pile, hauteur 43,94 pt (grille y 36,9–564,1). Notes fs=17 pt centrées dans la sous-colonne notes, police custom embarquée (PUA Portama). Croches (straddle) fs=13, dièses fs=14 (10 sur straddle), uchi-utu fs=14 (10 sur straddle).
- Flèches de répétition rendues DANS la sous-colonne marker (ligne verticale vers le bord droit de la sous-colonne + pointes horizontales, hauteur ~28 pt) — confirme notre design `_render_repeat_arrow`.
- Ratios Portama vs notre convertisseur : marker/note_subcol = 24,1/28,3 = 0,85 (nous 0,5) ; cell_h/note_subcol = 43,94/28,3 = 1,55 (nous 1,12) ; fs/cell_h = 17/43,94 = 0,39 (nous 0,38) ; titre vertical fs=20 espacé 22 pt ; accordage fs=14.
- だんじゅかりゆし.pdf : aucun texte vocal rendu (allLyricsData = placeholder « 歌詞を入力 »). かぎやで風節.pdf : ruby rendu (voir section allRubyData).

## Autres champs

| Champ | Description |
|-------|-------------|
| `allRubyData` | Voir section dédiée ci-dessus. |
| `allLyricsData` | Cadres de paroles avec `id`, `content`, `x`, `y`, `width`, `height`, `fontSize`. Content = "歌詞を入力" si non renseigné. |
| `lyricsWritingMode` | `"vertical"` (toujours). |
| `lyricsFontFamily` | `"mincho"` (toujours). |
| `lyricsFontSize` | `"10pt"`. |
| `lyricsPageBreak` | `"auto"`. |
| `lyricsDisplayNumber` | `"yes"`. |
| `rubyPrintMode` | `"current"`. |
| `print_duration` | `"yes"` ou `"no"`. |
| `viewsize` | 100. |
| `trackCount` | 1. |
| `currentTrack` | 1. |
| `price` | 0. |
| `isPublished` | 0. |
| `findname` | Nom de recherche (romanisation, peut être vide). |

## Limitations de Portama vs KKML

Portama ne connaît pas 九, 下老, ni les positions en イ (上半老, 上老, etc.). Son alphabet PUA s'arrête à 八 (U+E024) + ◯ (U+E030). KKML est strictement plus expressif.

- Portama → KKML : sans perte (tout ce que Portama encode existe en KKML).
- KKML → Portama : impossible pour les pièces utilisant 九, 下老, positions en イ, ou tout kanji hors du sous-ensemble Portama.

## Conversion Portama → KKML

Le convertisseur se trouve dans le canvas `portama-to-kkml`. Il mappe :
- PUA → kanji
- Paires (main, straddle) → noires, croches (A/B) ou shuffles (A:B)
- `acc: "sharp"` → 尺♯
- `orn: "u"` → suffixe `*`
- `repeatStart/repeatEnd` → `|:` / `:|`
- `choshi` → `@tuning`
- `cellsPerDan / 2` → `@cols`

## Capacités audio

Portama peut jouer l'audio des tablatures en interprétant chaque note PUA comme une hauteur sonore basée sur l'accordage (`choshi`). Les fichiers audio correspondants pourraient servir à vérifier la correspondance hauteur → note, mais ne sont pas nécessaires pour la conversion visuelle.

## Fichiers analysés

| Fichier | Dans | numDans | Notes spéciales |
|---------|------|---------|-----------------|
| かぎやで風節 | `/home/user/uploads/` | 19 | `orn:"u"` (7 occurrences), `acc:"sharp"` (fréquent), `repeatStart/End` |
| 国頭[くんじゃん]ジントヨー | `/home/user/uploads/` | 9 | `repeatStart/End`, aucun ornement, aucune altération |
| だんじゅかりゆし | `/home/user/uploads/` | 7 | `repeatStart/End`, aucun ornement, aucune altération |
