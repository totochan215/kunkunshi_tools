# kunkunshi_tools

Outils d'édition de tablatures 工工四 (kunkunshi) pour le sanshin d'Okinawa.
Python 3 autonome, aucune dépendance hors stdlib.
En bref, un outil pour sanshin 🪕 ... sous python ! 🐍 😂

- Pipeline 1 : Saisie graphique dans l'éditeur Portama → JSON Portama → KKML
- Pipeline 2 : Saisie/mise à jour texte en KKML → SVG / PDF → Impression ou finalisation dans un logiciel d'édition
- Pipeline 3 (à l'étude) : Saisie texte en KKML → JSON Portama → Finalisation dans l'éditeur Portama

Etat d'avancement : `Proof of Concept`. Le but est de parvenir à une spécification cohérente et englobante du format KKML et de ses outils.

Projet réalisé en partie par intelligence artificielle (https://chat.mistral.ai/code/)

## Scripts

### portama2kkml.py

Convertit un fichier JSON [Portama](https://portama.com/) en KKML.

    python3 portama2kkml.py chanson.json -o chanson.kkml
    python3 portama2kkml.py chanson.json                        # -> chanson.kkml
    cat chanson.json | python3 portama2kkml.py - > chanson.kkml

Options CLI : `-o/--output`

Gère : notes, ornements (uchi-utu, kaki-utu, nuchi-utu), altérations (dièse, bémol), figures rythmiques (noire, deux croches, croche pointée + double croche, silence), styles rythmiques (standard, hayabichi), repères de répétition (instrumental, chant), repères de respiration (koedashi, koekiri), accordages (`本調子`, `二揚げ`, `三下げ`, `一揚げ`, `一二揚げ`), hauteur de base, tempo, autres métadonnées, paroles, etc.

### kkml2svg.py

Rend un fichier KKML sous forme de mise en page SVG, en appliquant les options de mise en page stockées dans les métadonnées ou forcées en ligne de commande.

    python3 kkml2svg.py chanson.kkml -o chanson.svg
    python3 kkml2svg.py chanson.kkml                  # -> chanson.svg
    cat chanson.kkml | python3 kkml2svg.py -          # stdin -> stdout

Options CLI : `-o/--output`, `-c/--cells-per-dan`, `-l/--layout vertical|horizontal|nomura|chindami|tuto|mega`, `-p/--dans-per-page`.

### kkml_cleaner.py

Normalise un fichier KKML sous sa forme canonique. 
(idempotent : `cleaner(cleaner(x)) == cleaner(x)`) :

    python3 kkml_cleaner.py dirty.kkml                  # réécrit le fichier en place
    python3 kkml_cleaner.py -n dirty.kkml               # mode test (dry run)
    python3 kkml_cleaner.py -n -o clean.kkml dirty.kkml # écrit dans un autre morceau

Options CLI : `-n/--dry-run`, `-o/--output`

### kkml2pdf.py

Convertit un fichier KKML en **PDF multipage**, en appelant `kkml2svg` (chaîne
`render_svg` → une page SVG autonome en cm → conversion page par page en PDF
1 page → fusion en un seul PDF). Réservé à ce stade aux layouts dont le
format de page est prédéfini en cm : `chindami` (23 × 15 cm), `nomura`
(A4 portrait 21 × 29,7 cm), `mega` (A3 paysage 42 × 29,7 cm). Les layouts
libres (page à taille variable) sont refusés : utiliser `kkml2svg.py` puis
l'export du logiciel d'édition.

    python3 kkml2pdf.py chanson.kkml -o chanson.pdf
    python3 kkml2pdf.py chanson.kkml                  # -> chanson.pdf
    cat chanson.kkml | python3 kkml2pdf.py -          # stdin -> output.pdf

Options CLI : `-o/--output`, `-c/--cells-per-dan`, `-l/--layout nomura|chindami|mega`, `-p/--dans-per-page`, `--engine auto|rsvg-convert|inkscape|cairosvg`, `--merger auto|pypdf|pdfunite|gs`, `--keep-temp DIR` (conserve les SVG/PDF intermédiaires).

La taille de page PDF (MediaBox) est celle du SVG en cm. Dépendances externes
optionnelles (hors stdlib) : un moteur SVG→PDF détecté automatiquement
(`rsvg-convert`, `inkscape`, ou module python `cairosvg`) et un outil de fusion
(`pypdf`, `pdfunite` ou `gs`) — l'embed des polices CJK est du ressort du moteur.

### kkml2portama.py

Conversion KKML → JSON Portama : script non écrit à ce jour.

## Le format KKML

Format texte permettant de saisir et mettre en forme des tablatures 工工四 (kunkunshi) sous une forme simple et intuitive. KKML pour KunKunshi Markup Language. Et si ça marche pas, c'est 💩

Exemple :

    @title かぎやで風節
    @tuning 本調子
    @cells_per_dan 12

    ::tab
    |:工 五 四 工 四 乙 四 合/尺:| 工 ◯ 工 五
    工 尺# 工 合/尺# 工 五 工 尺# 工 合/尺# 工 五
    工 尺#/工 上 尺* 上 老/四 上 尺# 上 老 四 老
    ::

    ::vocal
    - - - - - - - - きゆ - ぬ -
    - ふ - - - - く - - - ら -
    しゃ - - - - - - - や - - -
    ::

    ::lyrics
    一、｛今日｝《きゆ》の《ぬ》誇《ふく》らしゃや　何をにぎやなたてる　莟で居る花の　露行逢たごと
    ::

*Extrait de かぎやで風節 (Kajadifu bushi)*

- Métadonnées : `@title`, `@tuning`, `@cells_per_dan`, `@layout`, `@marker`, `@author`,
  `@shaku_circled`, `@shaku_sharp`, `@lyrics_size`, etc.
- Sections :
    - `::tab` — tablature, 1 figure par temps. `A` = 1 noire, `A/B` = 2 croches, `A:B` = 1 croche pointée + 1 double croche,
      `|:` `:|` = boucle instrumentale, `(:` `:)` = boucle vocale, `' " ^ v < s` = ornements (technique de jeu),
    - `::vocal` — paroles en phonétique alignées sur la tablature,
    - `::lyrics` — paroles complètes avec support éventuel du guide phonétique (ruby), sans alignement sur la tablature.
      Variantes : `::lyrics-kanji`, `::lyrics-ruby`, `::lyrics-kana`, `::lyrics-romaji`. `::lyrics` est un alias de `::lyrics-ruby` (kanji + rubys).

Détail complet : [docs/notation.md](docs/notation.md) et [docs/kkml-format.md](docs/kkml-format.md).

## Documentation

- [docs/kkml-format.md](docs/kkml-format.md) — syntaxe et règles du format KKML
- [docs/notation.md](docs/notation.md) — notation musicale kunkunshi (positions, modes rythmiques, technique, vocal etc.)
- [docs/portama-format.md](docs/portama-format.md) — description du format JSON Portama
- [docs/svg-layout.md](docs/svg-layout.md) — description des mises en page SVG (dimensions, constantes, etc.)

La roadmap du projet et le contexte technique pour contributeurs/agents IA sont dans [AGENTS.md](AGENTS.md). Les agents IA écrivent exclusivement dans ce fichier.

## Echantillons de fichiers

### Matériel disponible

- [samples/kkml/](samples/kkml/) — fichiers KKML de référence
- [samples/portama-json/](samples/portama-json/) — fichiers Portama bruts en JSON
- [samples/portama-pdf/](samples/portama-pdf/) — fichiers Portama rendus au format PDF
- [samples/svg/](samples/svg/) — rendus SVG de référence
