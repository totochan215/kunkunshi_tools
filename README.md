# kunkunshi_tools

Outils d'édition de tablatures 工工四 (kunkunshi) pour le sanshin d'Okinawa.
Python 3 autonome, aucune dépendance hors stdlib.
En bref, un outil pour sanshin 🪕 ... sous python ! 🐍 😂

Réalisé en partie par intelligence artificielle (https://chat.mistral.ai/)

- Pipeline 1 : saisie dans l'éditeur Portama → JSON Portama → KKML → retouche manuelle en KKML → SVG
- Pipeline 2 : saisie manuelle en KKML → SVG

## Scripts

### portama2kkml.py

Convertit un fichier JSON de [Portama](https://portama.com/) en KKML.

    python3 portama2kkml.py input.json -o output.kkml
    cat input.json | python3 portama2kkml.py - > output.kkml

Gère : notes, ornements (uchi-utu, kaki-utu, nuchi-utu), altérations (dièse, bémol), figures rythmiques (noire, deux croches, shuffle, silence),
repères de répétition `|:` `:|` `|(` `)|`, repères de début et fin du chant (`(` `)`), accordages (`本調子`, `二揚げ`, `三下げ`, `一揚げ`, `一二揚げ`), autres métadonnées, paroles, etc.

### kkml2svg.py

Rend un fichier KKML sous forme de tablature SVG, en appliquant les options de mise en page stockées dans les métadonnées ou forcées en ligne de commande.

    python3 kkml2svg.py chanson.kkml -o chanson.svg
    python3 kkml2svg.py chanson.kkml                  # -> chanson.svg
    cat chanson.kkml | python3 kkml2svg.py -          # stdin -> stdout

Options CLI : `-o/--output`, `-c/--cols`, `-l/--layout vertical|horizontal`.

### kkml2pdf.py

Conversion KKML → PDF : script non écrit à ce jour.

## Le format KKML

Format texte permettant de saisir et mettre en forme des tablatures 工工四 (kunkunshi) sous une forme simple et intuitive. KKML pour KunKunshi Markup Language. Et si ça marche pas, c'est 💩

Exemple :

    @title かぎやで風節
    @tuning 本調子
    @cols 12

    ::tab
    |:工 五 四 工 四 乙 四 合/尺:| 工 ◯ 工 五
    工 尺♯ 工 合/尺♯ 工 五 工 尺♯ 工 合/尺♯ 工 五
    工 尺♯/工 上 尺* 上 老/四 上 尺♯ 上 老 四 老
    ::

    ::vocal
    - - - - - - - - きゆ - ぬ -
    - ふ - - - - く - - - ら -
    しゃ - - - - - - - や - - -
    ::

    ::lyrics
    一、｛今日｝《きゆ》の《ぬ》誇《ふく》らしゃや　何をにぎやなたてる　莟で居る花の　露行逢たごと
    ::

(Extrait de かぎやで風節 (Kajadifu bushi))

- Métadonnées : `@title`, `@tuning`, `@cols`, `@layout`, `@marker`, `@author`,
  `@shaku_circled`, `@shaku_sharp`, `@lyrics_size`, etc.
- Sections :
    - `::tab` — tablature, une ligne par dan, 1 token par temps. `A` = 1 noire, `A/B` = 2 croches, `A:B` = shuffle (croche pointée + double croche),
      `|:` `:|` = répétition de l'intro, `|(` `)|` = répétition du chant, suffixes de technique `* ^ v < s =`.
    - `::vocal` — paroles en phonétique, alignement approximatif sur la musique, une ligne par dan, 1 token par temps,
    - `::lyrics` — paroles complètes avec support du guide phonétique (ruby), sans alignement sur la musique.

Détail complet : [docs/notation.md](docs/notation.md) et [docs/kkml-format.md](docs/kkml-format.md).

## Documentation

- [docs/kkml-format.md](docs/kkml-format.md) — syntaxe et règles du format KKML
- [docs/notation.md](docs/notation.md) — notation musicale (positions, modes rythmiques, souhou, vocal etc.)
- [docs/portama-format.md](docs/portama-format.md) — description du format JSON Portama sur la base de sa rétro-ingénierie
- [docs/svg-layout.md](docs/svg-layout.md) — layout SVG (dimensions, constantes, colonne marker)

La roadmap du projet et le contexte technique pour contributeurs/agents IA sont dans [AGENTS.md](AGENTS.md).

## Echantillons de fichiers

### Matériel disponible

- [samples/kkml/](samples/kkml/) — fichiers KKML de référence
- [samples/portama-json/](samples/portama-json/) — fichiers Portama bruts en JSON
- [samples/portama-pdf/](samples/portama-pdf/) — fichiers Portama rendus au format PDF
- [samples/svg/](samples/svg/) — rendus SVG de référence produits par kkml2svg.py

### Homologues et tests

- Les fichiers échantillons portant le même nom de base (sans suffixe) à travers `samples/kkml`,
`samples/portama-json`, `samples/portama-pdf` et `samples/svg` sont des
homologues : ils représentent la même chanson et peuvent donc être utilisés pour des tests.
- Un suffixe de variante après
`-` distingue des variantes (ex. `かぎやで風節-vocal.kkml`). Les segments ruby
entre crochets éventuels sont ignorés dans l'appariement (`国頭[くんじゃん]ジントヨー.pdf`
correspond à `国頭ジントヨー.kkml`).
