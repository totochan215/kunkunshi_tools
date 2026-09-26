# Format Portama JSON (portama.com/kunkun4)

Portama est un éditeur de kunkunshi en ligne ([portama.com/kunkun4](https://portama.com/kunkun4/)) qui génère des tablatures de sanshin. Son format de stockage natif est JSON. L'éditeur peut également exporter un rendu au format PDF (généré par TCPDF, polices sous-ensemblées et embarquées).

Source principale pour la sémantique : `main.js` de l'éditeur ([portama.com/editor/js/main.js?V=2.55](https://www.portama.com/editor/js/main.js?V=2.55)), recoupé avec le corpus de fichiers JSON/PDF et la pièce de test テスト節 (qui exerce presque tout l'inventaire Portama, 26 septembre 2026).

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
| `version` | string | Numéro de version du JSON Portama (2.2 observé). |
| `numDans` | int | Nombre de dans (段). ATTENTION : peut être périmé — テスト節 déclare 7 alors que `score` contient 5 dans (le dernier tronqué à 5 cases). Toujours déduire du `score` lui-même. |
| `cellsPerDan` | int | Toujours 24 (12 notes × 2 cellules : main + straddle). |
| `musicno` | int | Identifiant du morceau sur Portama (0 pour une création locale). |
| `score` | `Array<Array<Cell>>` | 2D : `[dan][cell]`. Chaque dan a 24 cellules (12 paires main+straddle) ; le dernier dan peut être plus court. |
| `title` | string | Titre de la chanson. |
| `choshi` | string | Accordage : `hon`, `niage` (二揚げ), `sansage` (三下げ), `ichiage` (一揚げ), `ichiniage` (一二揚げ). Décale les hauteurs audio des cordes (ex. niage : 中弦 +2 demi-tons ; ichiniage : 男弦 +2, 中弦 +2, 女弦 0). |
| `chogen` | string | DÉCODÉ : demi-tons ajoutés à l'accordage nominal. Formule de main.js : `tuningOffset = chogen - 5`. Corpus : 十九の春=5 (base), てぃんさぐぬ花=4 (−1), 国頭ジントヨー=4, テスト節=7 (+2). Rendu dans le PDF comme label 本調子 fs14 (indépendant de chogen). |
| `speed` | string | Tempo (BPM). Ex : "180". |
| `rhythm` | string | Mode rythmique. "0" = ?, "100" = ?. |
| `rhythmMode` | string | "0" ou "100". |
| `orientation` | string | Toujours `\"landscape\"`. |
| `allRubyData` | inconnu | Voir section dédiée ci-dessous. |
| `allLyricsData` | inconnu | Cadres de paroles avec `id`, `content`, `x`, `y`, `width`, `height`, `fontSize`. Content = \"歌詞を入力\" si non renseigné. |
| `lyricsWritingMode` | string | inconnu. Ex : \"vertical\". |
| `lyricsFontFamily` | string | inconnu. Ex : \"mincho\". |
| `lyricsFontSize` | string | inconnu. Ex : \"10pt\". |

## Structure des cellules (`score[dan][cell]`)

Chaque cellule est un objet avec :

| Champ | Type | Description |
|-------|------|-------------|
| `note` | string | Caractère PUA Unicode (U+E000–U+E044) ou chaîne vide. |
| `isSmall` | bool | `true` = petite note (straddle), `false` = note standard. Sur une note principale, indique un shuffle (deux notes égales). |
| `acc` | string | Altération : `\"sharp\"` (♯) ou `\"flat\"` (♭). Rendu en fs14 à gauche de la note (dx −2,84 pt) ; fs10/dx −4,84 sur case isSmall. |
| `orn` | string | Ornement/souhou : `\"k\"` (kaki-utu), `\"u\"` (uchi-utu), `\"nu\"` (nuki 抜音). Seules ces trois valeurs existent. k et u s'excluent mutuellement dans l'éditeur. Portama ignore silencieusement `orn` sur une case vide. Rendu en fs14 à l'épaule droite (dx +6,16, dy +4,03) ; fs10/dx +8,07 sur isSmall. |
| `yubii` | int | 指位記号 (doigté de main gauche) : 1 = 人差指, 2 = 中指, 3 = 無名指, 4 = 小指. Rendu fs12,5 dans une colonne à gauche de la note (dx −15,46 pt). |
| `repeatStart` | bool | Début de répétition. |
| `repeatEnd` | bool | Fin de répétition. |
| `vocalRepStart` | bool | Début de boucle vocale `|(...)`. |
| `vocalRepEnd` | bool | Fin de boucle vocale. |
| `vocalPosMarkers` | dict | `{top: null|\"vocalStart\"|\"vocalEnd\", mid: ..., bot: ...}` — placement de 声だし/声切り à un tiers de case. vocalStart rend ○ (U+25CB), vocalEnd rend □ (U+25A1), fs9 dans la colonne marker (+14,8 pt de la sous-colonne notes). Distinct de `vocalRepStart/End`. |
| `note2`, `acc2`, `orn2` | — | Deuxième note/altération/ornement par case : présents dans le modèle de l'éditeur (main.js), non observés dans les fichiers du corpus. |
| `isChiribichi`, `isOsaikudashi` | bool | Présents dans le modèle de l'éditeur (main.js), non observés dans le corpus. |

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

## Correspondance PUA → positions (carte complète)

Confirmée par trois sources croisées : corrigés KKML manuels (だんじゅかりゆし, 国頭ジントヨー), `puaToKanji` + `puaAudioMap` de main.js v2.55, et テスト節 (qui parcourt tout l'inventaire). Les positions sont notées corde/demi-tons (C = 男弦, B = 中弦, A = 女弦).

| PUA | Kanji (main.js) | Position audio | Corde |
|-----|-----------------|-----------------|-------|
| U+E000 | 合 | C01 | 男弦 |
| U+E001 | 乙 | C03 | 男弦 |
| U+E002 | 老 | C05 | 男弦 |
| U+E003 | 下老 | C06 | 男弦 |
| U+E004 | 四 | C08 | 男弦 (octave haute) |
| U+E005 | 上 | C10 | 男弦 |
| U+E006 | 中 | C12 | 男弦 |
| U+E007 | 尺 | C13 | 男弦 |
| U+E008 | 工 | C15 | 男弦 |
| U+E010 | 四 | B01 | 中弦 |
| U+E011 | 上 | B03 | 中弦 |
| U+E012 | 中 | B05 | 中弦 |
| U+E013 | 尺 | B06 | 中弦 |
| U+E014 | 下尺 | B08 | 中弦 |
| U+E015 | (sans nom JS) | B10 | 中弦 |
| U+E016 | (sans nom JS) | B12 | 中弦 |
| U+E017 | (sans nom JS) | B13 | 中弦 |
| U+E018 | (sans nom JS) | B15 | 中弦 |
| U+E020 | 工 | A03 | 女弦 |
| U+E021 | 五 | A05 | 女弦 |
| U+E022 | 六 | A07 | 女弦 |
| U+E023 | 七 | A08 | 女弦 |
| U+E024 | 八 | A10 | 女弦 |
| U+E025 | 九 | A12 | 女弦 |
| U+E026 | 十 | A14 | 女弦 |
| U+E027 | 斗 | A15 | 女弦 |
| U+E028 | 為 | A17 | 女弦 |
| U+E030 | ○ (silence) | — | — |
| U+E031 | kaki-utu | — | glyphe d'ornement |
| U+E032 | uchi-utu | — | glyphe d'ornement |
| U+E033 | (nuki) | — | glyphe d'ornement : croissant d'uchi-utu avec contre-trou (anneau partiel) |
| U+E041–E044 | yubii 1–4 | — | 指位記号 |

Notes :

- La nomenclature E004–E008 (四上中尺工 sur 男弦) et E015–E018 (中弦 hautes) vient de main.js ; ces positions n'ont pas de kanji propre dans la tradition écrite. Dans la police embarquée du PDF, les positions hautes 男弦/中弦 sont rendues avec des kanji-variantes homophones (cf. 対音表 : 吐=上, 呎=尺, 亿=五, 佬=六, 仝=八) — glyphes visuellement distincts des kanji des registres nominaux.
- U+E029, E019, E034–E040, E045+ : non définis. U+E033 est référencé par le JS ; identifié comme glyphe nuki par テスト節 (orn `nu` → E033 dans le flux texte du PDF).
- 十 (E026), 斗 (E027), 為 (E028) identifiés via les positions koto du traité (recoupement puaAudioMap).

## Ornements (souhou)

Valeurs de `orn` confirmées (テスト節, main.js) :

| `orn` | Glyphe PUA | Suffixe KKML | Description |
|-------|------------|--------------|-------------|
| `k` | U+E031 | `^` | kaki-utu (┛ en coin, trait uniforme ~0,065 em) |
| `u` | U+E032 | `*` | uchi-utu (croissant de pinceau, tête épaisse en bas-gauche, queue fine en haut) |
| `nu` | U+E033 | `n` (proposition) | nuki 抜音 — croissant d'uchi-utu avec contre-trou (anneau partiel) |

Exclusion mutuelle k/u dans l'éditeur. `nu` est composable avec les autres (à confirmer par l'UI). Hypothèses antérieures (`a`, `c`, `t`) : invalidées, elles n'existent pas dans Portama.

## Encodage

Le fichier JSON est en UTF-8. Les notes sont des caractères PUA à 3 octets UTF-8 (EE 80 xx pour E00x, EE 81 xx pour E01x, EE 82 xx pour E02x, EE 83/84 xx pour E03x/E04x) ; le 3e octet se convertit en `byte3 & 0x3F` = offset bas du codepoint.

## Colonne marker et données vocales (`allRubyData`)

`allRubyData` contient le texte vocal affiché dans la colonne marker (sous-colonne droite de chaque pile). Clé = numéro de page en string, valeur = tableau de lignes, 1 ligne par dan (19 lignes pour かぎやで風節 = 19 dans).

Structure du positionnement (validée exactement contre le PDF rendu) :

- U+3000 (espace pleine largeur) = 1 unité ; espace ASCII = 0,5 unité.
- Champ de saisie d'environ 36 unités pour 12 cases = exactement 3 unités monospace par case (longueurs de ligne observées 14–36 unités).
- Le rendu PDF est une application STRICTEMENT LINÉAIRE des unités source : `top_caractère = 36,9 + 2,74 + 14,646 × unités` (mesuré sur かぎやで風節.pdf, 58 caractères, résidu max 0,00 pt). L'unité = hauteur_case/3 = 43,94/3 = 14,646 pt.
- Il existe une grille stricte de 3 lignes ruby par case (fractions de case 0,06 / 0,40 / 0,73 pour les unités entières mod 3), mais AUCUN arrimage des syllabes aux notes — l'auteur place librement les syllabes à la demi-unité près (fractions observées 0,06–0,90). C'est un champ texte vertical libre, pas un modèle syllabe↔note.

Rendu des caractères (mesuré sur かぎやで風節.pdf) :

- Police IPAexMincho 11 pt (ratio vs note fs 17 = 0,65 ; ratio vs hauteur de case = 0,25). Le JSON dit `lyricsFontSize: \"10pt\"` mais le ruby rendu est à 11 pt.
- Colonne marker : sous-colonne de 24,1 pt à droite de chaque pile (largeur pile 52,4 = 28,3 notes + 24,1 marker, séparées par un trait vertical). Ruby dessiné à +3,7 pt du bord gauche de la sous-colonne marker (boîte de 11 pt, léger biais gauche).
- Chaque caractère pleine largeur = 1 ligne à l'avance de 14,646 pt (1,33 × fs ruby), quelle que soit son appartenance à un token.
- Petits kana (ぁぃぅぇぉゃゅょゎ) : rendus à +12,99 pt sous le caractère précédent (vs 14,646 sur la grille — tuck optique de 1,65 pt) et +1,12 pt à droite ; le caractère suivant reprend sa position de grille. Mesuré sur 17 instances, valeurs identiques au centième.
- Caractères pleine taille dans un token multi-caractères (きゆ, やう) : avance pleine de 14,646 pt, pas de tuck. Donc Portama ne tuck que les petits kana, sans notion de syllabe.
- ー (chōonpu) absent de ce fichier : comportement non mesuré.
- Syllabes multi-caractères dans la source : caractères adjacents sans séparateur (てぃ, でぃ, をぅ, つぃ, とぅ, ちゃ, しゃ, やう, きゆ, et un token de 3 caractères つぃぶ). Confirme la règle KKML « 1 token = 1 syllabe ». Incohérence de saisie auteur : dan 3 utilise を+う (う pleine taille) alors que dans 6/11/14 c'est を+ぅ (petit).

Implication pour notre convertisseur : l'alignement strict de `::vocal` (syllabe i ↔ note i, par padding) reste plus rigoureux que le positionnement libre de Portama — mais la convention Portama montre la tolérance de la tradition : 3 lignes ruby par case, placement à la demi-unité. Les constantes mesurées pour un éventuel calibrage : ruby_fs/note_fs = 0,65 ; avance ligne = cell_h/3 ; tuck petit kana = 1,18 × fs sous le haut du caractère précédent (notre espacement actuel : syllable_fs × 0,85).

Un seul échantillon contient des données ruby : かぎやで風節.json (allRubyData vide pour les autres).

## Géométrie du PDF Portama (A4 paysage, TCPDF)

Grille commune à tous les PDF analysés (だんじゅかりゆし, かぎやで風節, テスト節) :

- Cadre extérieur 28,3–819,2 × 28,3–575,4 pt. Piles au pas de 60,9 pt, cadre de pile 52,4 pt de large = sous-colonne notes 28,3 pt (gauche) + sous-colonne marker 24,1 pt (droite), séparées par un trait vertical. Jusqu'à 12 piles par page. Ordre de lecture des piles : droite → gauche (dan 1 = pile la plus à droite).
- 12 cases par pile, hauteur 43,94 pt (grille y 36,9–564,1). Notes principales fs=17 pt centrées dans la sous-colonne notes. Straddle/isSmall fs=13.
- Flèches de répétition rendues DANS la sous-colonne marker (ligne verticale vers le bord droit + pointes horizontales, hauteur ~28 pt) — confirme notre design `_render_repeat_arrow`.
- Titre vertical fs20 en marge droite ; label d'accordage fs14 vertical en bas à droite.
- Ratios Portama vs notre convertisseur : marker/note_subcol = 24,1/28,3 = 0,85 (nous 0,5) ; cell_h/note_subcol = 43,94/28,3 = 1,55 (nous 1,12) ; fs/cell_h = 17/43,94 = 0,39 (nous 0,38).

Géométrie fine des marques (mesurée sur テスト節.pdf, positions Td absolues) :

| Marque | fs (case main) | Position | fs (isSmall) |
|--------|----------------|----------|--------------|
| note principale | 17 | centre sous-colonne notes | 13 |
| orn (k/u/nu) | 14 | dx +6,16, dy +4,03 pt (épaule droite) | 10, dx +8,07 |
| acc (♯/♭) | 14 | dx −2,84, dy +4,02 pt (gauche de la note) | 10, dx −4,84 |
| yubii 1–4 | 12,5 | dx −15,46, dy +0,93 pt (colonne dédiée à gauche) | — |
| ○/□ (vocalPosMarkers) | 9 | colonne marker à +14,8 pt, dy +3,3 pt | +1,7 pt |

La colonne isSmall d'une paire est décalée ~+2 pt à droite de la colonne principale du même dan.

Point ouvert : `repeatStart`/`repeatEnd`/`vocalRepStart`/`vocalRepEnd` ne rendent RIEN dans テスト節.pdf (dan 1, cases 13–19 : aucun graphique ni flèche), alors que d'autres pièces rendent des flèches dans la colonne marker. Le déclencheur exact du rendu des flèches reste à élucider.

## Polices embarquées du PDF

Deux polices sous-ensemblées par TCPDF :

- Notes/kanji de tablature : Untitled1 (Type0, Identity-H, upem 1024, 40 glyphes dans テスト節). CIDToGIDMap intégré ; CID = codepoint PUA (ex. CID E033 → GID 35). TCPDF ne sous-ensemble que les glyphes utilisés : E026 (十) et E043 (yubii 3) sont vides dans テスト節.pdf car la pièce ne les emploie pas.
- Texte (titre, ruby, ○/□, paroles) : IPAexMincho (Type0, Identity-H).
- ♭ = U+266D, ♯ = U+266F rendus dans la police de tablature (GID 30/31 dans テスト節).

Les contours (chemins SVG en unités upem 1024) de tous les glyphes de テスト節.pdf ont été extraits — disponibles pour la rénovation du rendu des ornements.

## Limitations de Portama vs KKML

L'alphabet Portama est plus riche que ce qui était documenté initialement (下老 E003 et les positions hautes E004–E008/E015–E018 existent), mais Portama ne connaît toujours pas les positions en イ (上半老, 上老, etc.) ni les kanji hors de sa carte PUA.

- Portama → KKML : sans perte (tout ce que Portama encode existe en KKML). Mapping requis : orn `nu` → suffixe `n` (proposition), yubii 1–4, acc ♯/♭ sur toute note, vocalPosMarkers, chogen → @tuning (décalage en demi-tons).
- KKML → Portama : impossible pour les pièces utilisant les positions en イ ou tout kanji hors du sous-ensemble Portama.

## Conversion Portama → KKML

Le convertisseur (`portama2kkml.py`) mappe :
- PUA → kanji (carte complète E000–E033, cf. ci-dessus)
- Paires (main, straddle) → noires, croches (A/B) ou shuffles (A:B)
- `acc: "sharp"/"flat"` → ♯/♭
- `orn: "k"/"u"/"nu"` → `^` / `*` / `n` (proposition)
- `yubii: 1-4` → à définir
- `vocalPosMarkers` → à définir
- `repeatStart/repeatEnd` → `|:` / `:|`
- `choshi` + `chogen` → `@tuning` (chogen − 5 = demi-tons ; pas encore implémenté)
- Nombre de dans : déduit de `score`, jamais de `numDans`
- `cellsPerDan / 2` → `@cols`

## Capacités audio

Portama peut jouer l'audio des tablatures en interprétant chaque note PUA comme une hauteur sonore basée sur `choshi` (décalages par corde) et `chogen` (décalage global en demi-tons, `chogen - 5`). `puaAudioMap` de main.js donne les positions exactes par corde.

## Fichiers analysés

| Fichier | Dans | numDans | Notes spéciales |
|---------|------|---------|-----------------|
| かぎやで風節 | `./samples/` | 19 | `orn:\"u\"` (7 occurrences), `acc:\"sharp\"` (fréquent), `repeatStart/End`, ruby |
| 国頭[くんじゃん]ジントヨー | `./samples/` | 9 | `repeatStart/End`, chogen=4 |
| だんじゅかりゆし | `./samples/` | 7 | `repeatStart/End` |
| テスト節 | `./samples/` | 7 (réel : 5) | Pièce de test exhaustive : tous les ornements (k/u/nu), acc ♯/♭, yubii 1/2/4, vocalPosMarkers, repeatStart/End, vocalRep, tout l'inventaire PUA E000–E033 ; chogen=7 ; dan5 tronqué (5 cases) |
