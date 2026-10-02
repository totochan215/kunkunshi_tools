# Référence du format JSON Portama

Portama est un éditeur en ligne ([portama.com/kunkun4](https://portama.com/kunkun4/)) qui permet de générer et stocker des tablatures kunknshi pour le sanshin. Son format de stockage natif est JSON.

## Source du document

Source principale pour la sémantique : `main.js` de l'éditeur ([portama.com/editor/js/main.js?V=2.55](https://www.portama.com/editor/js/main.js?V=2.55)), recoupé avec le corpus de fichiers JSON/PDF et la pièce de test テスト節.json / テスト節.pdf.

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
| `version`     | string | Numéro de version du JSON Portama. (2.2 = version courante au 26/09/2026). |
| `musicno`     | int    | Identifiant du morceau sur Portama. Défaut 0. |
| `userId`      | int    | Identifiant de l'utilisateur sur Portama. Défaut 0. |
| `numDans`     | int    | Nombre de dans (段) déclaré. |
| `cellsPerDan` | int    | Nombre de cellules par dan (`24` ou `36`). |
| `score`       | array  | 2D : `[dan][cell]`. Contenu de la tablature en dans et cellules (12 paires main+straddle) ; le dernier dan peut être plus court. |
| `allRubyData` | array  | Paroles en phonétique avec alignement sur le rythme. Voir section dédiée ci-dessous. |
| `price`       | int    | Prix en Yen pour les morceaux publiés sur la plateforme. Défaut : 0 |
| `isPublished` | int    | Indique si le morceau est publié sur la plateforme. Défaut : 0 |
| `viewSize`    | int    | Inconnu (présumé : niveau de zoom de la visualisation). Défaut : 100 |
| `trackCount`  | int    | Inconnu (présumé : nombre de répétitions de boucle vocale à faire). Défaut : 1 |
| `currentTrack`| int    | Inconnu (présumé : nombre de répétitions actuel). Défaut : 1 |
| `title`       | string | Titre du morceau. |
| `findName`    | string | Inconnu (présumé : alias du titre pour les recherches). |
| `speed`       | string | Tempo. Ex : "180". |
| `chogen`      | string | Ajustement par rapport à l'accordage nominal, en demi-tons. Défaut : 5 (nominal) |
| `choshi`      | string | Accordage : `hon` (本調子), `niage` (二揚げ), `sansage` (三下げ), `ichiage` (一揚げ), `ichiniage` (一二揚げ). |
| `rhythm`      | string | Rythme. "0" = ?, "100" = ?. |
| `rhythmMode`  | string | Mode rythmique. "0" = ?, "100" = ?. |
| `orientation` | string | `\"landscape\"` : paysage, `\"portrait\"` : portrait. |
| `allLyricsData`     | array   | 2D. Paroles organisées par cadres. Voir ci-dessous |
| `lyricsWritingMode` | string  | inconnu.|
| `lyricsFontSize`    | string  | Taille de police.|
| `lyricsFontFamily`  | string  | Famille de police : `mincho` : mincho (serif), `gothic` : gothique (sans-serif), .|
| `lyricsWritingMode` | string  | inconnu.|
| `rubyPrintMode `    | string  | inconnu.|
| `print_duration`    | string  | inconnu.|

## Structure du tableau score

Tableau 2D ([dan][cell]).
Chaque cellule est un objet avec :

| Champ             | Type   | Description |
|-------------------|--------|-------------|
| `note`            | string | Caractère PUA Unicode (U+E000–U+E044) représentant la position à jouer, ou chaîne vide. |
| `isSmall`         | bool   | Taille de note : `false` = note standard, `true` = petite note (straddle). Défaut : `false` |
| `acc`             | string | Altération : `\"sharp\"` = Dièse (♯), `\"flat\"` = bémol (♭).|
| `orn`             | string | Ornement/souhou : `\"k\"` (kaki-utu), `\"u\"` (uchi-utu), `\"nu\"` (nuki-utu). Seules ces trois valeurs sont supportées. k et u s'excluent mutuellement dans l'éditeur. Portama ignore silencieusement `orn` sur une case vide.|
| `yubii`           | int    | 指位記号 (doigté de main gauche) : `1` = 人差指, `2` = 中指, `3` = 無名指, `4` = 小指.|
| `repeatStart`     | bool   | Début de répétition.                           |
| `repeatEnd`       | bool   | Fin de répétition.                             |
| `vocalRepStart`   | bool   | Début de boucle vocale.                        |
| `vocalRepEnd`     | bool   | Fin de boucle vocale.                          |
| `vocalPosMarkers` | array  | 1D : vocalStart = ○ (声だし), vocalEnd = □ (声切り), pos = ?? : ??; pos = "mid" : milieu de cellule, pos = ?? : ??  |
| `note2`           | string | Deuxième note par case (rôle à préciser)       |
| `acc2`            | string | Deuxième altération par case (rôle à préciser) |
| `orn2`            | string | Deuxième ornement par case (rôle à préciser)   |
| `isChiribichi`    | bool   | Cas où un chiribichi (チリ弾き) est joué sur ce temps   | 
| `isOsaikudashi`   | bool   | Cas où un osaikudachi (押さい下ち) est joué sur ce temps    |

## Structure du tableau allRubyData

1 array par page ; 1 ligne par dan ; 3 unités de double largeur par cellule. Description détaillée à compléter.

| Champ      | Type   | Description |
|------------|--------|-------------|
| 1          | array  | 1D: Liste de rubys ; 1 ligne par dan ; 3 double largeur par cellule |
| 2          | array  | idem        |
| etc.       | array  | idem        |

## Structure du tableau allLyricsData

Champs : `id`, `content`, `x`, `y`, `width`, `height`, `fontSize`. Description détaillée à compléter.

| Champ      | Type   | Description |
|------------|--------|-------------|
| `id`       | int    | Identifiant du bloc                      |
| `content`  | string | Paroles du couplet. Défaut : \"歌詞を入力\" |
| `x`        | real   | Position x du bloc dans la mise en page  |
| `y`        | real   | Position y du bloc dans la mise en page  |
| `width`    | real   | Largeur du bloc dans la mise en page     |
| `height`   | real   | Hauteur du bloc dans la mise en page     |
| `fontSize` | int    | Taille de police du bloc.                |

### Organisation des cellules par dan

Portama autorise deux réglages :

- 12 paires de cellules (24 cellules) par dan : utilisation indiquée pour le layout au format paysage
- 16 paires de cellules (32 cellules) par dan : utilisation indiquée pour le layout au format portrait

Les cellules sont organisées comme suit :

- Index pair (0, 2, 4, ...) = note principale
- Index impair (1, 3, 5, ...) = note à cheval (straddle)

| Main                 | Straddle | Equivalent KKML | Token KKML |
|----------------------|----------|-----------------|------------|
| note                 | vide     | Noire           | `A`        |
| note (isSmall=false) | note     | Croche          | `A/B`      |
| note (isSmall=true)  | note     | Shuffle 早弾き   | `A:B`      |
| note (isSmall=true)  | vide     | Kuubanchi       | `As`       |
| vide                 | vide     | Case vide       | `-`        |

## Correspondance PUA → symboles

| PUA    | Kanji           | Position audio  | Corde | Commentaire |
|--------|-----------------|-----------------|-------|--------------
| U+E000 | 合   | C01 | 男弦 | |
| U+E001 | 乙   | C03 | 男弦 | |
| U+E002 | 老   | C05 | 男弦 | |
| U+E003 | 下老  | C06 | 男弦 | glyphe composite 下+老 |
| U+E004 | ロ上 | C08 | 男弦 | glyphe composite ロ+上 |
| U+E005 | ロ中 | C10 | 男弦 | glyphe composite ロ+中 |
| U+E006 | ロ尺 | C12 | 男弦 | glyphe composite ロ+尺 |
| U+E007 | イ合 | C13 | 男弦 | glyphe composite イ+合 |
| U+E008 | イ乙 | C15 | 男弦 | glyphe composite イ+乙 |
| U+E010 | 四   | B01 | 中弦 | |
| U+E011 | 上   | B03 | 中弦 | |
| U+E012 | 中   | B05 | 中弦 | |
| U+E013 | 尺          | B06 | 中弦 | |
| U+E014 | 下尺        | B08 | 中弦 | glyphe composite 下+尺 |
| U+E015 | ロ五 | B10 | 中弦 | glyphe composite ロ+五 |
| U+E016 | イ老 | B12 | 中弦 | glyphe composite イ+老 |
| U+E017 | イ四 | B13 | 中弦 | glyphe composite イ+四 |
| U+E018 | イ上 | B15 | 中弦 | glyphe composite イ+上 |
| U+E020 | 工          | A03 | 女弦 | |
| U+E021 | 五          | A05 | 女弦 | |
| U+E022 | 六          | A07 | 女弦 | |
| U+E023 | 七          | A08 | 女弦 | |
| U+E024 | 八          | A10 | 女弦 | |
| U+E025 | 九          | A12 | 女弦 | |
| U+E026 | イ尺 | A14 | 女弦 | glyphe composite イ+尺 |
| U+E027 | イ工 | A15 | 女弦 | glyphe composite イ+工 |
| U+E028 | イ五 | A17 | 女弦 | glyphe composite イ+五 |
| U+E030 | ○      | —  | —                 | silence |
| U+E031 | kaki-utu    | —  | — | glyphe d'ornement |
| U+E032 | uchi-utu    | —  | — | glyphe d'ornement |
| U+E033 | nuki-utu    | —  | — | glyphe d'ornement |
| U+E041 | ㊀     | —  | — | yubii-1 (index) |
| U+E042 | ㊁     | —  | — | yubii-2 (majeur) |
| U+E043 | ㊂     | —  | — | yubii-3 (non spécifié) |
| U+E044 | ㊃     | —  | — | yubii-4 (auriculaire) |

Notes :

- Les PUA U+E009, U+E019, U+E029, et U+E034 à U+E040 ne sont pas utilisés. La liste s'arrête à U+E044.
- Portama utilise les webfonts [kk4font1.ttf](https://www.portama.com/editor/fonts/kk4font1.ttf) (mincho) et [kk4font2.ttf](https://www.portama.com/editor/fonts/kk4font2.ttf) (gothic) pour représenter ces symboles à l'écran et dans les PDF exportés. Ces fontes semblent avoir été composées sur mesure pour les besoins du kunkunshi. Elles sont marquées "Copyright (c) 2026, feava" et ne sont pas assorties d'une licence explicite, donc soumises au règles standard du droit d'auteur.

## Ornements (souhou)

Valeurs de `orn` possibles :

| `orn` | PUA     | Suffixe KKML | Description |
|-------|---------|--------------|-------------|
| `k`   | U+E031  | `^`          | kaki-utu    |
| `u`   | U+E032  | `*`          | uchi-utu    |
| `nu`  | U+E033  | `n`          | nuchi-utu   |

## Encodage

Le fichier JSON est en UTF-8. Les positions, ornements et yubii sont codés par des caractères PUA à 3 octets.

## Colonne marker et données vocales (`allRubyData`)

`allRubyData` contient le texte vocal affiché dans la colonne marker (sous-colonne droite de chaque pile). Clé = numéro de page en string, valeur = tableau de lignes, 1 ligne par dan (19 lignes pour かぎやで風節 = 19 dans).

## Limitations de Portama vs KKML

L'alphabet Portama est plus riche que ce qui était documenté initialement : 下老 (E003), positions ロ (E004–E006, E015) et positions イ une octave au-dessus (E007–E008, E016–E018, E026–E028) existent. Portama ne connaît en revanche ni les positions イ non cartographiées (上半老, 上老, イ六, イ七, etc.) ni les kanji hors de sa carte PUA.

- Portama → KKML : sans perte (tout ce que Portama encode existe en KKML). Mapping requis : orn `nu` → suffixe `n`, yubii 1–4, acc ♯/♭ sur toute note, vocalPosMarkers, chogen → @tuning (décalage en demi-tons), notes E003–E028.
- KKML → Portama : impossible pour les pièces utilisant des positions en イ hors carte Portama ou tout kanji hors du sous-ensemble Portama.

## Conversion Portama → KKML

Le convertisseur (`portama2kkml.py`) mappe :
- PUA → kanji (carte complète E000–E044, cf. ci-dessus)
- Paires (main, straddle) → noires, croches (A/B) ou shuffles (A:B)
- `acc: "sharp"/"flat"` → ♯/♭
- `orn: "k"/"u"/"nu"` → `^` / `*` / `n`
- `repeatStart/repeatEnd` → `|:` / `:|`
- `choshi` + `chogen` → `@tuning` (chogen − 5 = demi-tons)
- Nombre de dans : déduit de `score`, jamais de `numDans`
- `cellsPerDan / 2` → `@cols`

## Capacités audio

Portama peut jouer l'audio des tablatures en interprétant chaque note PUA comme une hauteur sonore basée sur `choshi` (décalages par corde) et `chogen` (décalage global en demi-tons, `chogen - 5`). `puaAudioMap` de main.js donne les positions exactes par corde.
