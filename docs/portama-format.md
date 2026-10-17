# Référence du format JSON Portama

Portama est un éditeur en ligne ([portama.com/kunkun4](https://portama.com/kunkun4/)) créé et maintenu par Rafael López García, qui permet de générer et stocker des tablatures kunknshi pour le sanshin. Son format de stockage natif est JSON.

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

| Champ               | Type.   | Description |
|---------------------|---------|-------------|
| `version`           | string  | Numéro de version du JSON Portama. (2.2 = version courante au 26/09/2026). |
| `musicno`           | int     | Identifiant du morceau sur Portama. Défaut : 0. |
| `userId`            | int     | Identifiant de l'utilisateur sur Portama. Défaut : 0. |
| `numDans`           | int     | Nombre de dans (段) déclaré. |
| `cellsPerDan`       | int     | Nombre de cellules par dan (`24` ou `36`). |
| `score`             | array   | 2D : `[dan][cell]`. Contenu de la tablature en dans et cellules (12 paires main+straddle) ; le dernier dan peut être plus court. |
| `allRubyData`       | array   | Paroles en phonétique avec alignement sur le rythme. Voir section dédiée ci-dessous. |
| `price`             | int     | Prix en Yen pour les morceaux publiés sur la plateforme. Défaut : 0 |
| `isPublished`       | int     | Indique si le morceau est publié sur la plateforme. Défaut : 0 |
| `viewSize`          | int     | Inconnu (présumé : niveau de zoom de la visualisation). Défaut : 100 |
| `trackCount`        | int     | Inconnu (présumé : nombre de répétitions de boucle vocale à faire). Défaut : 1 |
| `currentTrack`      | int     | Inconnu (présumé : nombre de répétitions actuel). Défaut : 1 |
| `title`             | string  | Titre du morceau. |
| `findName`          | string  | Inconnu (présumé : alias du titre pour les recherches). |
| `speed`             | string  | Tempo. Ex : "180". |
| `chogen`            | string  | Ajustement par rapport à l'accordage nominal, en demi-tons. Défaut : 5 (nominal) |
| `choshi`            | string  | Accordage : `hon` (本調子), `niage` (二揚げ), `sansage` (三下げ), `ichiage` (一揚げ), `ichiniage` (一二揚げ). |
| `rhythm`            | string  | Rythme. "0" = ?, "100" = ?. |
| `rhythmMode`        | string  | Mode rythmique. "0" = ?, "100" = ?. |
| `orientation`       | string  | `\"landscape\"` : paysage, `\"portrait\"` : portrait. |
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
| `note`            | string | Caractère PUA Unicode (entre U+E000 et U+E044) représentant la position à jouer, ou chaîne vide. |
| `isSmall`         | bool   | Taille de note : `false` = note standard, `true` = petite note. Défaut : `false` |
| `acc`             | string | Altération : `\"sharp\"` = Dièse (♯), `\"flat\"` = bémol (♭).|
| `orn`             | string | Ornement/souhou : `\"k\"` (kaki-utu), `\"u\"` (uchi-utu), `\"nu\"` (nuki-utu). Seules ces trois valeurs sont supportées. k et u s'excluent mutuellement dans l'éditeur. Portama ignore silencieusement `orn` sur une case vide.|
| `yubii`           | int    | 指位記号 (doigté de main gauche) : `1` = 人差指, `2` = 中指, `3` = 無名指, `4` = 小指.|
| `repeatStart`     | bool   | Début de répétition.                           |
| `repeatEnd`       | bool   | Fin de répétition.                             |
| `vocalRepStart`   | bool   | Début de boucle vocale.                        |
| `vocalRepEnd`     | bool   | Fin de boucle vocale.                          |
| `vocalPosMarkers` | array  | 1D : vocalStart = ○ (声だし), vocalEnd = □ (声切り), pos = ?? : ??; pos = "mid" : milieu de cellule, pos = ?? : ??  |
| `note2`           | string | Deuxième note par case        |
| `acc2`            | string | Deuxième altération par case  |
| `orn2`            | string | Deuxième ornement par case    |
| `isChiribichi`    | bool   | `true` : un chiribichi (チリ弾き) est joué sur ce temps, `false` : pas de chiribichi | 
| `isOsaikudashi`   | bool   | `true` : un osaikudachi (押さい下ち) est joué sur ce temps, `false` : pas de osaikudachi.    |

## Structure du tableau allRubyData

1 array par page ; 1 ligne par dan ; 3 unités de double largeur par cellule. Description détaillée à compléter.

| Champ      | Type   | Description |
|------------|--------|-------------|
| `1`        | array  | 1D: Liste de rubys ; 1 ligne par dan ; 3 double largeur par cellule |
| `2`        | array  | idem        |
| etc.       | array  | idem        |

## Structure du tableau allLyricsData

Champs : `id`, `content`, `x`, `y`, `width`, `height`, `fontSize`. Description détaillée à compléter.

| Champ      | Type   | Description                              |
|------------|--------|------------------------------------------|
| `id`       | int    | Identifiant du bloc                      |
| `content`  | string | Paroles du couplet. Défaut : \"歌詞を入力\" |
| `x`        | real   | Position x du bloc dans la mise en page  |
| `y`        | real   | Position y du bloc dans la mise en page  |
| `width`    | real   | Largeur du bloc dans la mise en page     |
| `height`   | real   | Hauteur du bloc dans la mise en page     |
| `fontSize` | int    | Taille de police du bloc.                |

### Organisation des cellules par dan

Portama autorise deux réglages :

- `cellsPerDan` = `24` : 12 paires de cellules (24 cellules) par dan : utilisation indiquée pour le layout au format paysage
- `cellsPerDan` = `32` : 16 paires de cellules (32 cellules) par dan : utilisation indiquée pour le layout au format portrait

Les cellules sont organisées comme suit :

- Index pair (0, 2, 4, ...) = note principale
- Index impair (1, 3, 5, ...) = note à cheval sur deux cases (straddle)

La combinaison d'une cellule paire et d'une cellule impaire donne les figures rythmiques suivantes.

| Paire                | Impaire  | Equivalent KKML | Ecriture en KKML |
|----------------------|----------|-----------------|------------------|
| note                 | vide     | Noire           | `A`              |
| note (isSmall=false) | note     | Croche          | `A/B`            |
| note (isSmall=true)  | note     | Shuffle (早弾き) | `A:B`            |
| note (isSmall=true)  | vide     | Kuubanchi       | `As`             |
| vide                 | vide     | Case vide       | `-`              |

## Correspondance PUA → symboles

| PUA    | Symbole  | Commentaire            |
|--------|----------|------------------------|
| U+E000 | 合       |                        |
| U+E001 | 乙       |                        |
| U+E002 | 老       |                        |
| U+E003 | 下老      | glyphe composite 下+老 |
| U+E004 | ロ上.     | glyphe composite ロ+上 |
| U+E005 | ロ中      | glyphe composite ロ+中 |
| U+E006 | ロ尺      | glyphe composite ロ+尺 |
| U+E007 | イ合      | glyphe composite イ+合 |
| U+E008 | イ乙      | glyphe composite イ+乙 |
| U+E010 | 四       |                       |
| U+E011 | 上       |                       |
| U+E012 | 中       |                       |
| U+E013 | 尺       |                       |
| U+E014 | 下尺      | glyphe composite 下+尺 |
| U+E015 | ロ五.     | glyphe composite ロ+五 |
| U+E016 | イ老.     | glyphe composite イ+老 |
| U+E017 | イ四      | glyphe composite イ+四 |
| U+E018 | イ上      | glyphe composite イ+上 |
| U+E020 | 工       |                       |
| U+E021 | 五       |                       |
| U+E022 | 六       |                       |
| U+E023 | 七       |                       |
| U+E024 | 八       |                       |
| U+E025 | 九       |                       |
| U+E026 | イ尺      | glyphe composite イ+尺 |
| U+E027 | イ工      | glyphe composite イ+工 |
| U+E028 | イ五      | glyphe composite イ+五 |
| U+E030 | ○        | silence               |
| U+E031 | kaki-utu | glyphe d'ornement     |
| U+E032 | uchi-utu | glyphe d'ornement     |
| U+E033 | nuki-utu | glyphe d'ornement     |
| U+E041 | ㊀       | yubii-1 (index)        |
| U+E042 | ㊁       | yubii-2 (majeur)       |
| U+E043 | ㊂       | yubii-3 (non spécifié) |
| U+E044 | ㊃       | yubii-4 (auriculaire)  |

Notes :

- Les PUA U+E009, U+E019, U+E029, et U+E034 à U+E040 ne sont pas utilisés. La liste s'arrête à U+E044.
- Portama utilise les webfonts [kk4font1.ttf](https://www.portama.com/editor/fonts/kk4font1.ttf) (mincho) et [kk4font2.ttf](https://www.portama.com/editor/fonts/kk4font2.ttf) (gothic) pour représenter ces symboles à l'écran et dans les PDF exportés. Ces fontes semblent avoir été composées sur mesure pour les besoins du kunkunshi. Elles sont marquées "Copyright (c) 2026, feava" et ne sont pas assorties d'une licence explicite, donc soumises au règles standard du droit d'auteur.

## Ornements (souhou)

Valeurs de `orn` possibles :

| orn   | PUA     | Correspondance en KKML | Description |
|-------|---------|------------------------|-------------|
| `k`   | U+E031  | `^`                    | kaki-utu    |
| `u`   | U+E032  | `*`                    | uchi-utu    |
| `nu`  | U+E033  | `n`                    | nuchi-utu   |

Note : les ornements "nuchi-utu" et "uchi-nuuchi-utu" de KKML ne sont pas supportés par Portama.

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
