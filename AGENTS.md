# AGENTS.md — contexte agent pour kunkunshi_tools

Ce fichier contient la connaissance **machine/projet** destinée aux agents IA (et contributeurs techniques) : roadmap, statuts, points ouverts, mesures de calibrage, architecture du code. La documentation **humaine** (notation musicale, formats, layout) est dans `docs/` et le README — ne pas y mélanger de suivi de tâches.

Règles :
- Tout ajout de statut, TODO, mesure ou point ouvert va ici, jamais dans `docs/`.
- `docs/` reste la référence du format KKML et de la notation ; le code est la source de vérité du comportement.
- Tests : `python3 tests/run_tests.py`. Python 3 stdlib uniquement, aucune dépendance.

---
# Feuille de route

Dernière mise à jour : 23 novembre 2026

Pipeline : Portama JSON → KKML → SVG / PDF. Ce document est la référence unique pour
les priorités du projet. Statuts : ✅ fait · 🚧 en cours · ⬜ à faire · ❓ décision à trancher.

## 0. Syntaxe KKML — points à trancher (personne n'utilise encore KKML, il y a le temps)
- ✅ (2026-11-22) `kkml2pdf.py` : validation des PDF de page produits par le moteur SVG→PDF — `_pdf_complet()` attend (jusqu'à `_PDF_TIMEOUT` = 10 s) que le fichier commence par `%PDF-` et contienne `%%EOF` dans son dernier tampon, sinon `RuntimeError` explicite. Cause d'un crash utilisateur (inkscape sur macOS rend la main avant d'avoir tout écrit → PDF tronqué → pypdf : « EOF marker not found » + `PdfStreamError: Stream has ended unexpectedly` au merge ; reproduit avec pypdf 3.9). Test n°9 `tests/test_kkml2pdf.py` (tronqué détecté, écriture différée attendue).

- ✅ (2026-11-22) Renommage `kkml_cleaner.py` → `kkml_clean.py` (objet → verbe d'action) : fichier renommé, imports (`import kkml_clean as c` dans `kkml_beautify.py` et les tests), tests renommés (`tests/test_kkml_clean.py`, `test_clean_meta.py`, `test_clean_medley.py`), références README/`docs/kkml-format.md`/`.github/workflows/tests.yml` mises à jour, préfixes stderr `kkml_clean: ...`. Shim `kkml_cleaner.py` ajouté pour la transition (AVERTISSEMENT + délégation vers `kkml_clean.py`) — supprimé aussitôt après (voir entrée ci-dessous). Comportement inchangé : sorties du cleaner byte-identiques à l'ancien cleaner sur les samples ; toute la suite de tests passe.
- ✅ (2026-11-22) `@tuning` → `@choshi` (le champ JSON Portama s'appelle `choshi`) : alias `@tuning` accepté au parsing (info stderr, stocké sous la clé canonique `choshi` dans `song.meta`, forme collée `@tuningValeur` comprise — `META_ALIASES = {"tuning": "choshi"}` dans kkml2svg.py, `tuning` reste dans `META_KEYS`), rectifié en `@choshi` par kkml_clean (info « renommé en @choshi ») ; `META_ORDER`/`_meta_blocks` et tous les rendus lisent `choshi` ; `portama2kkml.py` émet `@choshi` (CHOSHI_MAP) ; samples, README et `docs/kkml-format.md` en forme canonique. Rendus 60/60 byte-identiques vs main ; rendu `@tuning` == rendu `@choshi` (test). Tests : `tests/test_source.py` (alias + META_ORDER), `tests/test_clean_meta.py` n°10 (rectification), `tests/test_portama_meta.py` (émission `@choshi`) — en CI.
- ✅ (2026-11-22) Suppression du shim `kkml_cleaner.py` : la transition du renommage (PR #80) est terminée — l'ancien nom n'est plus délégué, utiliser `python3 kkml_clean.py ...`. README mis à jour ; aucun test ne passait par le shim ; `python3 tests/run_tests.py` + les 19 `tests/test_*.py` passent.
- ✅ (2026-11-22) Niveaux stderr en **majuscules** : `INFO` / `WARNING` / `ERROR`, format `<script>: LEVEL: message` dans les 5 scripts (kkml2svg, kkml_clean, kkml_beautify, kkml2pdf, portama2kkml) — avant : `kkml_clean: info:/AVERTISSEMENT:/ERREUR:`, `AVERTISSEMENT :` / `ERREUR :` sans préfixe (kkml2svg, kkml2pdf), `portama2kkml: msg` sans niveau. Textes des messages inchangés (français). `tests/run_tests.py` (détection `WARNING`) et les tests matchant `AVERTISSEMENT`/`ERREUR`/`"info"` mis à jour (`WARNING`/`ERROR`/`INFO`). Suite complète OK ; smoke : `kkml_clean: INFO:`/`WARNING:`/`ERROR:`, `kkml2svg: INFO:`/`WARNING:`, `kkml2pdf: ERROR:`.
- ✅ (2026-11-22) Numéros de page `–n–` auto-incrémentés en nomura/chindami/mega, avec `@page_base >= 1` (défaut 1 ; invalide → WARNING + 1 ; forme collée comprise via META_KEYS) : **nomura** = hors du cadre en haut (baseline fy0−8, ne touche pas le filet ; tiret demi-cadratin – U+2013, classe JLREQ cl-03 demi-em — le choonpu ー U+30FC n'est pas un tiret et porte un serif en mincho), n pair → aligné à gauche du cadre (fx0), n impair → à droite (fx1) — remplace l'ancien numéro nomura (bas, centré, `{pi+1}`) ; **chindami** = centré (page_w/2), mi-hauteur entre le bas de la grille et le bas de la page ; **mega** = centré, mi-distance entre le bas du 2e bloc et le bord bas de la feuille, même hauteur sur une page paroles seules. `page_no_fs` (LayoutSpec) : 13 en nomura (même valeur que la méta accordage 13 pt, champ indépendant), 11 ailleurs, helpers `_meta_page_base` / `_draw_page_no` ; vertical/horizontal/tuto inchangés (pas de numéro). Tests `tests/test_page_numbers.py` (en CI). Docs : `docs/kkml-format.md` (`@page_base`), `docs/svg-layout.md` (3 layouts), README.
- ✅ (2026-11-22) `@choshi` aligné en bas de la colonne titre en mega et nomura (chindami le faisait déjà) : première baseline à `grid_bottom − 4 − len(choshi)·espacement`, même règle qu'en chindami (`fy1 − 4 − len·16`) — mega : `grid_bottom` = bas du 2e bloc, répété sur chaque page (tablature ET paroles), genre/auteur restent sous le titre ; nomura : `grid_y0 + grid_h`, page 1 (colonne titre). vertical/horizontal inchangés (sous le titre). Tests `tests/test_choshi_align.py` (en CI). Docs `docs/svg-layout.md` (3 sections), `docs/kkml-format.md`.
- ✅ (2026-11-22) `@speed` rendu `♩=120` en horizontal, fs 12 (10 en chindami), sans espace, dans les 6 layouts : layouts horizontaux sauf tuto = dans le flux des métadonnées à droite du titre, avant `@choshi` (`_meta_blocks(song, speed_h=True)`) ; layouts verticaux (vertical, chindami, nomura, mega) = sous le titre, `text-anchor="middle"` exactement sur la centerline de base du titre (hors ruby), au-dessus de `@choshi` (mega : répété sur chaque page comme la colonne titre) ; tuto = page de titre, sous le titre, centré, au-dessus de `@choshi`, même fs en px que la ligne `@choshi` (max(10, int(H*0.035)) = 25 px à H=720). Helper `_speed_text` (forme collée `@speed120` comprise via META_KEYS) ; toujours horizontal : `<text>` sans `transform` même en vertical. Tests `tests/test_speed.py` (en CI). Régression 60 rendus : seuls les 3 samples avec `@speed` (テスト節, テスト節-2, 安波節) changent (ajout de la ligne ♩=). Docs `docs/kkml-format.md` (`@speed`), `docs/svg-layout.md` (6 sections), README.
- ✅ (2026-11-22) Bornes de chant koedashi/koekiri en layout `horizontal` alignées sur la centerline du **tiers inférieur de la case** (avant : centerline de la case) : `yk = y_top − cell_h/6 + ss·0,318` dans `_draw_marker_line_vocal` (les symboles ○/□ sont rendus dans la case, pas dans la ligne marker). Autres layouts inchangés (alignement sur la sous-partie de case du élément vocal rattaché en vertical ; `tuto` : `render_koe off`). Test `tests/test_koe_lower_third.py` (en CI). Docs `docs/svg-layout.md`, `docs/kkml-format.md`.
- ✅ (2026-11-22) Constante `md_spacing` par layout (champ `LayoutSpec`, en pt, converti via `spec.u()`) : espacement **homogène** entre le titre et la 1re métadonnée et entre chaque bloc de métadonnées, dans les 6 layouts (vertical 15 px, horizontal 20 px, nomura 8 pt, chindami 6 pt, tuto 43,2 px = H×0,06 à H=720, mega 15 pt). Exception : `@choshi` quand il est ancré en bas de la colonne titre (chindami/nomura/mega) garde son ancrage. Test `tests/test_md_spacing.py` (en CI). Doc `docs/svg-layout.md` (6 sections).
- ✅ (2026-11-22) Taille ET position des caractères de technique (souhou) entièrement relatives à `note_fs`, homogènes entre les 6 layouts (mêmes constantes globales `TECHNIQUE_SUFFIXES`, offsets propres à chaque glyphe) : `tech_fs = int(note_fs·1,1·scale)`, `tx = cx ± note_fs·dx`, `ty = baseline + note_fs·dy` (idem drop, retrait 0,34) dans `_tech_char_pos`/`_render_techniques` — avant, `dy`/taille étaient × fs de case en vertical/nomura/mega/chindami et × ss en horizontal/tuto (mélange absolu/relatif). Recalibrage kaki-utu `^` (`⌝`) d'après correction Inkscape (Hiragino Mincho ProN, nomura 十九の春, −3/+3 pt à ss=18) : `dx` 0,63 → 0,4633, `dy` −0,42 → −0,44 — reproduit exactement en nomura, et en em de note_fs partout. Tests `tests/test_kaki_utu.py` (en CI). Doc `docs/svg-layout.md` (souhou).
- ✅ (2026-11-22) Repli des paroles en nomura : une colonne de couplet plus haute que le hanmen est repliée en sous-colonnes via `_cap_lyr_column` (`max_lyr_u = int((grid_h − LYRICS_FS) // LYRICS_SP) + 1`, kinsoku défaut `off` en nomura), comme en chindami ; les sous-colonnes comptent dans la pagination (dans virtuels) et plus rien ne déborde du cadre (avant : 十九の春 nomura p.2 débordait jusqu'à y=1034 pour un cadre bas à 793,9). Test `tests/test_nomura_lyrics_wrap.py` (en CI). Doc `docs/svg-layout.md` (section nomura).
- ✅ (2026-11-22) Samples KKML en **forme canonique** : les 11 fichiers de `samples/kkml/` ont été passés au cleaner (10 modifiés — méta regroupées en haut avec `@format KKML` ajouté si absent, une seule ligne vide entre le bloc méta et les sections et entre sections, sections `::vocal`/`::lyrics` vides créées si manquantes, `@tuning`→`@choshi`, `－`→`-`, `口`→`ロ`, fermetures `::` de medley supprimées ; `かぎやで風節.kkml` était déjà propre byte-identique). Versions « sales » d'origine conservées en fixtures `tests/fixtures/dirty/` (11 fichiers). Garde-fou : test n°45 de `tests/test_kkml_clean.py` (`clean(x)==x` pour chaque sample) ; `test_clean_medley.py` lit désormais la fixture dirty et assert que le sample est clean ; `test_beautify.py` teste l'idempotence sur samples + fixtures. Rendus 60 (11 samples × 6 layouts) : seuls `テスト節.kkml`/`テスト節-2.kkml` changent (section `::lyrics` vide ajoutée → horizontal 504→551 px, mega 1→2 pages). Les WARNING `::vocal désaligné` restent (le cleaner ne réaligne pas quand le total ne boucle pas) : PSC-eisa-medley 132/120 + 73/72, medley-samples 216/225, かぎやで風節 216/225, テスト節-2 54/51, 国仲節ジョー 52/51. README + `samples/README.md` mis à jour.
- ✅ (2026-11-23) Samples KKML **synthétiques** déplacés en fixtures : `テスト節.kkml`, `テスト節-2.kkml`, `medley-samples.kkml` (et les rendus mega de référence `medley-samples-mega-p1/p2.svg`) quittent `samples/kkml/`/`samples/svg/` pour `tests/fixtures/synthetic/` — `samples/kkml/` ne contient plus que des chansons/medleys réels (8 fichiers, tous clean). Références mises à jour : `test_testbushi.py` (KKML_PATH/KKML2), `test_song.py`, `test_page_numbers.py`, `test_beautify.py`, `test_clean_medley.py` (assert clean sur la fixture synthetic), `test_kkml_clean.py` n°45 (garde-fou `clean(x)==x` sur `samples/kkml` + `tests/fixtures/synthetic`). `run_tests.py` couvre désormais 8 homologues kkml (les JSON/PDF `テスト節*` restent dans `samples/`, affichés « pas de .kkml : ignoré »). Régression 48 rendus (8 samples × 6 layouts) byte-identiques vs main. README + `samples/README.md` mis à jour.
- ⬜ (2026-11-22) Idées utilisateur pour la roadmap, à trier/implémenter :
  - ✅ (2026-11-23) `::song <nom>` renommé en **`::part <nom>`** (forme canonique ; la fermeture `::` inchangée) : `::song`, `::songs`, `::parts` et `::section` restent des alias acceptés au parsing (info stderr, `SECTION_ALIASES` kkml2svg.py) et rectifiés en `::part` par kkml_clean ; rendu mega des titres identique octet par octet (vérifié vs HEAD). Impact : kkml2svg (`SECTION_ALIASES`, `blk.kind == "part"` ×2), kkml_clean (runs/marqueurs), tests renommés (`test_song.py` → `test_part.py`, test_clean_medley, test_kkml_clean n°44, test_lead_straddle), CI, `docs/kkml-format.md`/`docs/svg-layout.md`, medleys canoniques (`samples/kkml/PSC-eisa-medley.kkml`, fixture synthetic medley-samples) ; les fixtures dirty gardent `::song` (test de rectification).
  - **Constantes par modèle de mise en page** déterminant, pour chaque métadonnée, si elle est représentée ou non (ex. table « méta affichée » dans chaque `LayoutSpec` : `@source`/`@comment` non affichés partout aujourd'hui, `@choshi` dans la colonne titre, etc.) — rendre explicite et surchargeable ce que chaque layout rend.
  - ⬜ (2026-11-23) Constantes de modèle de layout indiquant quels **types de sections** sont pris en compte (ex. table « sections rendues » dans chaque `LayoutSpec` : `::lyrics` exclu du layout tuto, `::vocal` non supporté en horizontal) — pendant « sections » de la table « méta affichée » ci-dessus.
  - ✅ (2026-11-22) `@choshi` en bas de la colonne titre en chindami (déjà en place), mega et nomura (fait, voir entrée ✅ de la section 0) ; **vertical** reste à faire.
  - ✅ (2026-11-22) Représenter `@speed` sous la forme `♩=120` (fs 12, sans espace), **toujours à l'horizontal, même en mise en page verticale** — fait (voir entrée ✅ de la section 0) : `<text>` sans `transform`.
  - ✅ (2026-11-22) Position de kaki-utu `^` (`⌝`) revue : tout passé en relatif de `note_fs`, homogène entre layouts — fait (voir entrée ✅ de la section 0).
  - ⬜ (2026-11-23) Nouvelle section `::melody` (optionnelle), alignée sur `::vocal`, pour représenter la hauteur de chant — compatibilité avec les manuels nomura-ryu (sous-colonne « hauteur » de la colonne marker nomura, voir P3 `::声楽譜`).
  - ⬜ (2026-11-23) Blocs de lyrics multiples dans les layouts : pouvoir déclarer plusieurs blocs `::lyrics` et les rendre dans la mise en page (plusieurs blocs/colonnes de paroles), au-delà du flux unique rendu à la suite aujourd'hui (voir aussi `@lyrics_variant`, section 2).
  - ⬜ (2026-11-23) Amélioration de l'indentation des couplets (pas encore parfaite — cf. déviation JLREQ notée section 6 : indent à 3 chasses pleines vs 字下げ 1 em).
- ⬜ (2026-11-22) Autres idées utilisateur :
  - ✅ (2026-11-22) `@tuning` remplacé par `@choshi` — fait (voir entrée ✅ de la section 0) : alias `@tuning` accepté au parsing avec info stderr, rectifié en `@choshi` par le cleaner.
  - ✅ (2026-11-22) Numéros de page auto-incrémentés en nomura/chindami/mega — fait (voir entrée ✅ de la section 0) : `–n–`, n = `@page_base` (>= 1) + index de page.
  - Supprimer les `::` de fin de section superflus dans les medleys (semblent ne servir à rien) — le cleaner les supprime automatiquement.
  - ✅ (2026-11-22) Niveaux stderr en majuscules — fait (voir entrée ✅ de la section 0) : `INFO`/`WARNING`/`ERROR`, format `<script>: LEVEL: message` dans tous les scripts.
  - Les scripts Python communiquent en **anglais**, pas en français (messages stderr, docstrings CLI) — voir l'entrée i18n ⬜ de la section 4 « Long terme » (bascule du projet en anglais).

- ✅ (2026-11-22) Choonpu littéral échappé `\ー` dans `::vocal` : un `ー`/`ｰ`/`－` ISOLÉ reste case vide (historique), mais `\ー` (antislash + choonpu) = choonpu littéral seul dans la case (voyelle longue isolée, ex. 唐船ドーイ) — rendu ー (tourné 90° en vertical, à plat en horizontal), case NON vide. Parsing conserve l'échappement (variantes normalisées en `\ー`), `_vocal_elements` le dé-échappe au rendu, le cleaner le préserve tel quel (idempotent). Koedashi/koekiri : rendus ○/□ DANS la case (bord droit) sur tous les layouts sauf tuto (`render_koe off`) — y compris mega (avant : plus aucun layout ne les rendait, les parenthèses étant retirées de `::tab` au parsing). Rendu depuis la ligne vocale (`_draw_vertical_vocal` pour vertical/mega/chindami, boucle inline de `_render_nomura`, `_draw_marker_line_vocal` pour horizontal) via le helper `_vocal_paren_slots` : `(` = élément juste après, `)` = élément juste avant ; la borne est alignée sur le slot de cet élément (syllabe ou point `.` — l'alignement suit l'emplacement théorique du point même masqué par `@show_dots off`). La géométrie des notes ne change pas. 38/60 rendus samples diffèrent de main, diffs = ajouts de lignes ○/□ uniquement. Tests `tests/test_vocal_choonpu_koe.py` (en CI). Doc `docs/kkml-format.md` (section Vocal).
- ⬜ (2026-11-22) Normaliser `::tab` et `::vocal` en **pleine chasse** : les alignements en chasse fixe sont quasi impossibles avec un mélange pleine/demie chasse (seule la police Osaka fait le job), ce qui rend `kkml_beautify.py` vain. Piste : le cleaner émet les tokens de `::tab`/`::vocal` en forme canonique pleine chasse (compléter `FULLWIDTH_MAP` : kana/katakana demi-largeur ｱ→ア, chiffres, ponctuation…). Points à trancher : impact sur les rendus SVG (`disp_width` change → re-vérifier les 60 rendus samples × 6 layouts), sur `kkml_beautify.py` (qui deviendrait alors réellement utile), et sur le parsing (accepter les deux formes en entrée, comme aujourd'hui).
- ✅ (2026-11-22) `@show_dots on|off` (défaut `off`) : affiche/masque les points ・ (U+30FB) de positionnement des syllabes `::vocal` dans la colonne/ligne marker de toutes les mises en page (4 sites de rendu : `_render_nomura`, `_draw_vertical_vocal` [vertical/mega/chindami/nomura], `_draw_marker_line_vocal` [horizontal], `_draw_vocal_cell` [tuto] — nouveau paramètre `show_dots`). Le point occupe toujours sa sous-partie de case dans le calcul : masquer les points ne déplace JAMAIS les syllabes. `kkml2pdf.py` hérite via `render_svg`. `META_KEYS` += `show_dots` (cleaner la conserve). Défaut off = changement de rendu : 49/60 rendus samples diffèrent de main, toutes les diffs = suppressions de lignes `<text>・</text>` uniquement ; avec `@show_dots on` les 60 rendus sont byte-identiques à main. Tests `tests/test_show_dots.py` (en CI) ; tests 23/26/35/36/38 de `test_kkml_cleaner.py` passent désormais avec `@show_dots on` explicite. Doc `docs/kkml-format.md` (table des métadonnées), README, docstring CLI de kkml2svg.
- ✅ (2026-11-22) Outils lenients sur les noms de sections mal écrits : `SECTION_ALIASES` dans `kkml2svg.py` (`::tabs`→`::tab`, `::vocals`→`::vocal`, `::lyric`→`::lyrics`, `::songs`→`::song`, plus l'ancien `::section`→`::song`) — acceptés au parsing avec info stderr, `kkml_cleaner.py` les rectifie en nom canonique (il rémet `::`+kind canonique), `kkml_beautify.py` aligne aussi les corps de `::tabs`/`::vocals` (SECTION_RE élargi, en-tête émis tel quel). 60 rendus samples × 6 layouts byte-identiques vs main ; cleaner byte-identique sur les 10 samples. Tests : n°44 `tests/test_kkml_cleaner.py`, n°8 `tests/test_beautify.py` (en CI). Doc `docs/kkml-format.md`.
- ✅ (2026-11-21) Faille « ⚪ laissé passer dans ::tab » : la normalisation des variantes de repos ne matchait que le token EXACT (`tk in REST_VARIANTS`) — les tokens composites (`|:⚪`, `⚪:|`, `(:○`) et le straddle de tête `/⚪` y échappaient. Fix : helper `_normalize_rest_token` (kkml2svg) qui canonicalise la base quand les marqueurs `|: :| (| )| ( )` sont retirés, utilisé au parse (tokens + `leading_straddle`) et dans le cleaner. `○/工` (straddle note/note) préservé. 102/114 rendus identiques vs main ; 12 diffs = un seul glyphe `○`→`◯` dans `(○` (medley-samples, 安波節). Test 43 dans `tests/test_kkml_cleaner.py` (en CI).
- ✅ (2026-11-21) `kkml_beautify.py` : le straddle de tête `/B` (1er token de la 1re ligne de `::tab`) sort de la grille d'alignement — émis tel quel + 1 espace, les colonnes sont calculées sur la note suivante (test 7 de `tests/test_beautify.py`) ; 114 rendus raw vs beautifié identiques, idempotent.
- ✅ (2026-11-21) Cleaner : trim des fins de lignes — espaces/tabulations supprimés sur toutes les lignes émises (`rstrip(" \t")` à l'assemblage) ; idempotent ; aucune différence de sortie sur les 19 samples (leurs espaces finaux étaient déjà dans des lignes re-jointes), test 42 dans `tests/test_kkml_cleaner.py` (en CI).
- ✅ (2026-11-21) Nouveau `kkml_beautify.py` : alignement des débuts de cellules dans `::tab`/`::vocal` pour l'édition en chasse fixe — tokens normalisés (comme le cleaner) puis complétés d'espaces simples selon la largeur d'affichage par colonne (CJK pleine chasse = 2, combinant = 0, `disp_width`), pas d'espace en fin de ligne, reste du fichier inchangé octet par octet. Idempotent ; 114 rendus samples × 6 layouts identiques raw vs beautifié. Tests `tests/test_beautify.py` (étape CI), README, docstring CLI.
- ✅ (2026-11-21) `tests/test_kkml_cleaner.py` réparé et ajouté au CI : l'assert `base41 == 4` (ligne 443) était périmé depuis `8dcd87c` — la règle d'indentation uniforme est `max(3, plus long marqueur)` (en-têtes de couplet = 3 caractères pleine chasse), le test attendait l'ancien `max+1`. Le fichier passe entièrement (rc=0) et tourne désormais dans `.github/workflows/tests.yml`.
- ✅ (2026-11-21) Cleaner : plus de vrac sur les medleys — découpage en « runs » (blocs de contenu entre marqueurs `::song`/`::block`/`::page`) : chaque run réémis en ordre canonique `::tab ::vocal ::lyrics`, marqueurs à leur place dans le flux (avant : tous les `::tab` puis tous les `::vocal` puis tous les `::lyrics`, `::song` à la fin). Réalignement `::vocal` PAR RUN (chaque `::song` comparé à son propre `::tab`, plus au premier `::tab` global). Blocs `::vocal`/`::lyrics` manquants créés dans le run du premier `::tab`. Idempotent ; 18/19 samples nettoyés byte-identiques à l'ancien cleaner, medley-samples.kkml correctement regroupé et rendu mega avec noms de chansons. Tests `tests/test_cleaner_medley.py` (étape CI ajoutée).
- ✅ (2026-11-21) Cadre générique pour tous les layouts (`LayoutSpec`) : `margin_t/b/l/r` écartent le **cadre** du bord de feuille (`frame_rect()`), `pad_t/b/l/r` définissent le **hanmen** à l'intérieur (`hanmen_rect()`) ; `frame_width = 0` (défaut hors nomura) = cadre **non tracé**, le cadre virtuel se confond alors avec le hanmen (padding 0). Champs supprimés : `frame_w/frame_h/frame_margin_x/frame_margin_y/grid_top/grid_bottom`. Tracé via `_draw_frame()` dans les layouts à page imposée (nomura 1,5 pt `#333333` ; chindami/tuto/mega si `@frame_width > 0`) ; page libre (vertical/horizontal) : hanmen = marges + padding, cadre non tracé. `@frame_width 0` accepté (0 = off, `_meta_pt(zero_ok=True)`), négatif/non numérique → AVERTISSEMENT. nomura : marges dérivées du cadre nominal 559,3×745,9, `pad_* = dan_gap = 14,5` ; chindami : marges = mesures scans, pad 0. Rendus : 114 samples × 6 layouts identiques à main sauf nomura (bruit float 1 ulp sur cell_h, sémantiquement identique à 1e-9 — l'ancien code mixait 745,9 nominal et 745,8999999999999 calculé). Tests `tests/test_layout_attrs.py` §10-14 ; figures `docs/svg/` régénérées ; doc `docs/svg-layout.md` (section « Cadre et hanmen »).
- ✅ (2026-11-21) Attributs de design par mise en page, surchargeables par métadonnées : 8 nouveaux champs `LayoutSpec` (`text_color` "#000000", `frame_color` "#333333", `frame_width` 1.5, `cell_color` "#bbbbbb", `cell_width` 0.75, `arrow_color` "#bbbbbb", `arrow_width` 0.75, `arrow_fill` False — surchargés par layout : horizontal/tuto cases `#999999`, nomura cases/flèches `#333333`+`0.6` + cadre `#333333`/`1.5`, chindami `0.6`) + métadonnées KKML `@text_color @frame_color @frame_width @cell_color @cell_width @arrow_color @arrow_width @arrow_fill on|off` (couleurs format HTML #rgb/#rrggbb/nom CSS, épaisseurs pt > 0 ; valeur invalide → AVERTISSEMENT + défaut du layout). Résolution dans `render_svg` (méta > spec) passée via `opts` aux renderers ; `@text_color` ≠ noir (#000000) appliqué en post-traitement (`_apply_text_color` : fill sur la racine `<svg>`, fill retirés des `<text>`) — rendu historique inchangé octet par octet sinon (114 rendus samples × 6 layouts identiques vs main). `META_KEYS` += les 8 clés (cleaner les conserve). `@arrow_fill on` = têtes de flèches remplies. Tests `tests/test_layout_attrs.py`. Doc `docs/kkml-format.md` (table des métadonnées).
- ✅ (2026-11-21) Marqueurs de couplet ①-⑳ (U+2460-U+2473, `、` facultatif après) reconnus en début de ligne de `::lyrics`, comme les numéros CJK `一、` (nouvelle regex `VERSE_CIRCLED_RE`, branchée dans `_verse_indent_len`, `_verse_indent_target`, `_pad_inline_marker`) — tests `tests/test_verse_markers.py`.
- ✅ (2026-11-21) SVG : chaque marqueur de répétition est un groupe `<g>` — `_render_repeat_arrow`/`_h_repeat_arrow` (`class="repeat-arrow"`), `_render_vrep_marker`/`_h_vrep_marker` (`class="vocal-rep"`) ; `fill`/`stroke`/`stroke-width` sur le `<g>`, enfants = géométrie seule (héritage). Vérifié : 114 rendus, diff sémantique nul (attributs effectifs identiques). Tests `tests/test_svg_groups.py`.
- ✅ (2026-11-21) Straddle de tête `/B` (rang -1, hors spec Portama mais observé sur PDF) : token `/B` en tout premier token d'un bloc `::tab` = note à cheval sur le bord précédent de la 1re case (haut en vertical, gauche en horizontal) ; ne consomme pas de case. Parsing : stocké sur `Block.leading_straddle`, retiré des lignes ; token `/X` ailleurs → AVERTISSEMENT + ignoré. Rendu vertical/horizontal/mega via `_draw_lead_straddle` (miroir du straddle A/B) ; autres layouts → AVERTISSEMENT. Cleaner le réémet en tête de bloc (idempotent). Tests `tests/test_lead_straddle.py`.
- ✅ (2026-11-21) `::song <nom>` = forme canonique de nom de chanson dans une compilation (medley) ; `::section <nom>` n'est plus qu'un alias accepté, renommé avec info stderr (`::section` était trop générique : `::tab` est déjà une section). Le sample medley l'utilisait déjà en `::song`, les noms de chansons étaient perdus au rendu mega tant que ce n'était pas câblé. Tests `tests/test_song.py`.
- ✅ (2026-11-21) Layout mega adaptable : `@mega_dans N` = dans (colonnes) par bloc horizontal (défaut 32 ; cell_w et pagination s'adaptent — note : 31+33 = 64 = 2×32, le défaut couvre déjà un document à blocs de 31/33) ; marqueurs `::block` (saut au bloc suivant, le bloc sauté étant rempli de dans vides jusqu'à `@mega_dans`) et `::page` (idem + page complétée de blocs vides), sans contenu, ignorés hors mega — pagination factorisée dans `_mega_paginate` (sans marqueur = comportement historique identique). Tests `tests/test_mega_breaks.py`.
- ✅ (2026-11-20) Délimiteurs ruby `《》` / `｛｝` conservés définitivement (TODO de `docs/kkml-format.md` fermé, pas de passage aux yamakakko `〈〉`) ; échappement par antislash `\《 \》 \｛ \｝` implémenté dans `kkml2svg.py` (`_parse_ruby` et `_lyr_line_segments` échappement-conscients, `_cap_lyr_column` ne coupe jamais une paire `\X`, `_h_lyrics_atoms` ré-échappe à la ré-émission KKML) — tests `tests/test_escape.py`.
- ✅ (2026-11-21) Nouvelle métadonnée `@source` (texte libre sourçant la version du morceau : chindami, nomura, site web, production perso…) — **non affichée dans les SVG** (information KKML uniquement, comme `@comment`) : reconnue par le parser (`META_KEYS`, tolérance `@sourceValeur` collé) et conservée par le cleaner, mais retirée de `META_ORDER` et de la page titre tuto. Liens hypertexte `[label](url)` style Markdown dans les métadonnées affichées uniquement (`@title`, `@author`, `@composer`, `@lyricist`, `@origin`, `@genre`), rendus en `<a xlink:href>` dans le SVG (paramètre `links=True` des renderers texte `_render_vertical_text`/`_render_horizontal_text`/`_vertical_grouped_text`, helper `_emit_centered_text` pour les textes centrés ; mesures via `_link_free`) ; `\[` `\]` = crochet littéral. Pas de lien dans `::lyrics`/`::tab`/`::vocal`. Tests `tests/test_source.py`.
- ✅ (2026-11-01) `|( )|` DÉPRÉCIÉ dans `::tab` (AVERTISSEMENT, encore accepté) ; boucle vocale = `(: ... :)` dans `::tab` (jamais dans `::vocal`).
- ❓ Marqueurs de boucle dans `::tab` : `|: :|` actuels (boucle vocale `(: :)` dans `::tab`) entrent en conflit avec
  le shuffle `A:B` (double point) et `|` est aussi saut de ligne de couplet / séparateur
  de case ailleurs. Pistes : `[ ]` et `( )` dans `::tab` ; ou retirer `|` carrément.
- ❓ `::vocal` : meilleurs symboles pour koedashi/koekiri (idéalement ronds/carrés
  côté WYSIWYG, mais saisie texte difficile même pour des Japonais) vs `( )` ASCII.
- ❓ Kuubanchi (Portama isSmall sans straddle) : suffixe `s` actuel — aucun romaji de
  ROMAJI_TO_KANJI ne finit par `s`, donc pas de collision avérée aujourd'hui, mais à
  surveiller si la table romaji s'enrichit. La position rythmique (2e note d'un temps
  petite) est déjà couverte par croche/shuffle.
- ✅ (2026-11-04) Nuchi-utu (Portama orn `nu`, PUA U+E033) : suffixe `"` (U+0022),
  jumeau de `'` (uchi-utu tenu) ; glyphe rendu ゜ (U+309C, « apostrophe vide ») ;
  ＂ (U+FF02) normalisé en `"` via FULLWIDTH_MAP ; mapping Portama `nu` → `"`.
  `n` reste EXCLU (collision romaji : yon, bon…).
- ✅ (2026-11-23) Koedashi/koekiri attenant à un point `.` (ex. `.)`, `(.`) : résolu — la borne se rattache au point via `_vocal_paren_slots` (kkml2svg.py:3243) et ○/□ est rendu DANS la case aligné sur le slot du point, même masqué par `@show_dots off` (vérifié : `.)` en vertical → □ à la hauteur du ・ avec `@show_dots on`, position inchangée avec `off`). Les parenthèses ne changent PAS le nombre de sous-positions vocales de la case (corrigé 2026-11-10, commit 5d4838a — cas ahabushi case 44 : 3 points dans le KKML = 3 positions, plus de point fantôme).
- ⬜ (2026-11-23) Affichage des koedashi/koekiri (○/□) piloté par une **constante de layout** (champ `LayoutSpec`, ex. `render_koe on|off`, surchargeable par méta) au lieu du `render_koe = layout != "tuto"` en dur (kkml2svg.py:1051) — aujourd'hui le layout tuto ne rend pas ○/□ ; même esprit que les tables « méta affichée » / « sections rendues » (entrées ci-dessus).
- ❓ Notes entre parenthèses dans certaines tablatures (notes à sauter au 1er passage,
  jouées en revenant de boucle) : syntaxe à prévoir, risque de collision avec koedashi/koekiri.

## 1. Validations en attente (bloquantes ou quasi)

- ✅ (2026-11-01, PR #12) marqueur de couplet en début de ligne dans `::lyrics` force le changement de couplet (même sans ligne vide) → saut de colonne en layout vertical. Cas jukunoharu. `_split_verses` modifié.

- ✅ (2026-11-23) Validation かぎやで風節 (KKML `samples/kkml/かぎやで風節.kkml`) vs PDF Portama (`samples/portama-pdf/かぎやで風節.pdf`, 2 p.) — **mapping PUA U+E024 = 八 confirmé** : une seule occurrence dans le JSON (`score[4][2].note`), dessinée p.1 colonne x=469 en 2e case du dan 5 (y=485,8), lue « 八 » à l'OCR de la page et à la même position dans le SVG vertical régénéré (dan 5 `七 八 七 五…`, 八 unique dans le rendu). Silences ◯/尺♯ (dan 14) OK : 13 ◯ (U+25EF) dans le SVG, 尺♯ rendu 尺 (U+5C3A) + ♯ (U+266F) séparé — les ♯ du PDF sont des runs F3@10pt aux mêmes positions. Ornements ' OK : 7 × orn "u" dans le JSON (dans 3, 5, 10, 12×2, 18×2) = 7 suffixes ' dans le KKML = 7 × U+FF40 dans le SVG, coin haut-droite de la note porteuse (dx ≈ +0,58·fs, dy ≈ −2) ; le PDF dessine l'ornement en petit glyphe (U+E032, F3@10pt) près de la note. Méthodo : extraction texte du PDF (ToUnicode Identity-H, fontes F2/F3) + OCR des 2 pages + SVG vertical/nomura régénérés, comparaison colonne par colonne.
- 🚧 (2026-11-23) Régénérer et valider le SVG de test des souhou (uchi-utu `'` (alias `*`), kaki-utu `^`, aki-utu `v`, kachi-utu `<`, kuubanchi `s`, taachi `=`, nuchi-utu `"`) ; ajuster dx/dy/scale/rotate selon retours visuels. **Grille régénérée** : `tests/fixtures/synthetic/テスト節{,-2}-{vertical,horizontal,nomura,chindami,tuto,mega}*.svg` (6 layouts, rc=0 sans WARNING) — à valider visuellement (Inkscape / aperçu GitHub) ; constantes actuelles dans `TECHNIQUE_SUFFIXES` (kkml2svg.py:239+, relatives à `note_fs`). Note : `テスト節-2` n'apporte rien côté souhou (seul `::vocal` diffère : bornes `( )` et points `.`). **Jeu de test composites ajouté** : `tests/fixtures/synthetic/テスト節-composites{,-gothic}.kkml` + rendus × 6 layouts (0 WARNING) — couvre positions hautes イX/ロX, 下老/下八/下尺, イ下尺, accords de composites, kuubanchi/techniques/altérations/yubii sur composites, @shaku_sharp+@shaku_circled on, @font_style gothic.
- ✅ (2026-11-23) Retours visuels grille souhou (PR #98) : (1) ~~yubii~~ FAIT (règle revue après retour utilisateur) : layouts VERTICAUX = centre du 1er tiers GAUCHE de la case (`tx = cx − cell_w/3`, `'pos': 'left-third'`), ancré verticalement sur la CENTERLINE de la note porteuse (`'anchor': 'note-center'`, main + straddle) ; layout HORIZONTAL = tiers INFÉRIEUR de la case sur la centerline de la note (`'pos_h': 'bottom-third'`, `tx = cx`, `ty = cy + cell_h/3 + 0,318*mark_fs`) ; TUTO = non affichés (`opts 'render_yubii' = layout != "tuto"`, comme 'render_koe' — collision avec la ligne vocale). Test 2b de `tests/test_yubii.py`. ⚠ Ajustements ultérieurs du placement yubii à prévoir (roadmap). Reste : (2) cercle shaku en `stroke-width="1"` en dur ; (3) nomura contraignant ; (2) **cercle shaku en `stroke-width="1"` en dur** (kkml2svg.py:2699 et :4226) → paraît plus gras en chindami/mega (unités px, fs plus petit) — rendre le trait relatif à fs ; (3) **nomura très contraignant** : réduire la taille de police des notes OU déroger aux règles générales de placement des annotations/altérations (décision à prendre).
- ⬜ (2026-11-23) Positions composites non reconnues (trouvé par le test テスト節-composites : WARNING + rendu dégradé « 3 premiers caractères condensés ») : tout `下X` hors {下老 (U+4E0B U+8001 — le commentaire « 下乙 » de kkml2svg.py:4450 compare en fait U+8001 « 老 », à clarifier), 下八, 下尺}, ex. 下乙/下中 ; `イ下老`/`イ下八` documentés (docs/notation.md:113) mais seul `イ下尺` est implémenté ; positions hautes limitées à `HIGH_POS_KANJI` = {合,乙,老,四,上,尺,工,五,中} — イ六/イ七 attestés nomura-ryū (docs/notation.md:106) non rendus. Yubii : codepoints U+3280-U+3283 (U+2460+ = marqueurs de couplet,jamais des yubii).
- ⬜ (2026-11-23) Revue de la grille composites (PR #98, retour visuel) : (1) ~~centrage du cercle shaku incohérent~~ FAIT (voir ✅ ci-dessous) : — `下尺` cercle en (cx, cy) (kkml2svg.py:4441) mais `尺` cerclé en (cx, cy+2) (:4689), croches :4543/:4571 — unifier sur (cx, cy), le recalibrage nov. 2026 n'a été appliqué qu'à `下尺` ; (2) ~~`尺♯` = token indivisible,~~ FAIT (décomposé au rendu, voir ✅ ci-dessous) ; ♯ en tspan inline à 65% (la note n'est PAS déplacée), jamais cerclé ; `#`/`＃` → `♯` normalisés au parsing (FULLWIDTH_MAP), `b`→`♭` seulement sur tokens 2 car. (`_normalize_tab_token`) ; altération sur note simple = marque séparée haut-droite vs tspan inline sur `尺♯` — à uniformiser ou documenter ; (3) ~~accords/shuffle à membre composite~~ FAIT : membre composite condensé via `CONDENSE_W` à sa fs RÉELLE (72% accord, 80% shuffle) grâce à `_condensed_attrs` (avant : rendu brut, plus large en relatif) ; test 7c. ; (4) ~~condensation 2 car. incohérente~~ FAITE (CONDENSE_W, voir ✅ ci-dessus) : : `下老`/`下八` à 100% de fs, `イX`/`ロX` à 120%, `イ下尺` à 180% — unifier la règle ; (5) yubii U+3280-U+3283 OK sur composites.
- ✅ (2026-11-23) Grille souhou (PR #98) : **`尺♯` décomposé au RENDU** comme toute note altérée — la note 尺 garde exactement sa position/taille (test : élément identique à 尺 seul), le ♯ est la marque d'altération standard haut-droite (identique à 合♯), plus de tspan inline. Le token reste indivisible au FORMAT (portama2kkml inchangé) et la sémantique est conservée : `@shaku_sharp off` masque le ♯ (rendu 尺 simple), un shaku altéré n'est JAMAIS cerclé par `@shaku_circled`. **Cercles shaku unifiés en (cx, cy)** (plus de cy+2) et **codepoint corrigé 尖 U+5C16 → 尺 U+5C3A (= 尺 ; jamais 尻 U+5C3B ni 尖 U+5C16 en KKML)** aux 3 sites croches/straddles (kkml2svg.py:2696/:4541/:4568 — les cercles y étaient morts, jamais dessinés). **aki-utu `v` : glyphe V → ∨ U+2228** (chevron sans serif) **avec `scale: 0.80`** (test visuel PR #98 : tech_fs = int(note_fs×1,1×0,80), ex. 45 à fs 52 au lieu de 57). **Condensation unifiée** : `CONDENSE_W = {2: 1.2, 3: 1.8}` — 2 car. → 120% de fs pour TOUS les préfixes (下/イ/ロ, 下老 et 下八 passent de 100% à 120%), 3 car. → 180% ; repli dégradé aligné. Tests 7b/7c dans test_testbushi.py (condensation unifiée ; membres composites d'accord/shuffle condensés à leur fs réelle via `_condensed_attrs`). Tests : `tests/test_testbushi.py` §7 réécrit (position identique, marque identique, masquage, cerclage, croches). Docs `docs/notation.md`/`docs/kkml-format.md` mises à jour. Rendus `samples/svg/` non regénérés (déjà non byte-sync avec main avant ce changement).
- ✅ (2026-11-23) **Règle KKML : jamais de 尻 U+5C3B ni de 尖 U+5C16** — le kandokoro shaku s'écrit 尺 U+5C3A ; 尻/尖 sont des alias normalisés en 尺 au parsing (`FULLWIDTH_MAP`, kkml2svg.py) et par le cleaner (via `_normalize_tab_token`), suffixes compris (尻♯ = 尺♯). Test §6 de `tests/test_testbushi.py` étendu.
- ✅ (2026-11-23) Retours visuels grille souhou/composites (PR #98) appliqués : (a) **marques top-right ancrées au bord DROIT du token rendu** (`_tech_char_pos` : `tx = cx ± (text_w/2 + note_fs*(dx-0,5))`, ancre middle, clampé dans la case) — une altération sur composite (bémols cases 20/33) n'est plus centrée sur la case mais au même coin haut-droite qu'une note seule ; règle identique pour bottom-left ; (b) **aki-utu `v` ancré au BAS de la case** (nouvel ancrage `'cell-bottom'`, `drop: 0.12` : `ty = cell_cy + cell_h/2 - note_fs*drop`, presque au bas de la case, aussi sur straddle via `cell_cy`) ; (c) **constantes de taux séparées alignées deux à deux** : `KUUBANCHI_RATIO = STRADDLE_RATIO = 0.713`, `CHORD_RATIO = SHUFFLE_RATIO = 0.8` (kuubanchi×straddle se multiplient). Tests 7d/7e dans `tests/test_testbushi.py`. Grille `tests/fixtures/synthetic/テスト節*` régénérée (6 layouts × 2 variantes).
- ✅ (2026-11-23) **Ancrage coin du rectangle englobant** pour uchi-utu `'`, nuchi-utu `"`, kaki-utu `^` (`'corner': 'top-right'` dans `TECHNIQUE_SUFFIXES`) : `tx = cx + box_w/2 + note_fs*dx`, `ty = box_top + note_fs*dy`, avec `box_w` = largeur RENDUE de la note (note_fs seule, textLength du composite condensé, ou largeur max des membres d'un accord) et `box_top` = sommet em (base_y − note_fs, ou membre le plus haut d'un accord). Taille : `tech_fs = int(note_fs*1,1*scale)` — proportionnelle à la fs de rattachement, facteur propre à l'ornement, indépendante de la condensation. dx/dy mesurés depuis le coin (valeurs = anciennes − 0,5 en x, depuis le sommet em en y) : positions note seule/composite/straddle PRÉSERVÉES octet par octet (grille non modifiée hors accords) ; seuls les accords changent (ancrage sur le groupe). Paramètres `box_w`/`box_top` transmis via `_rt`/`_render_techniques`/`_tech_char_pos` ; branche accord calcule la box du groupe. Tests : `test_kaki_utu.py` §5 (accords), §§1-4 mis à jour, test_kkml_clean n°29/33. Grille composites : accords ornés ajoutés (`合-乙+老^`, `尺=ロ合'`) pour validation visuelle. Ancien ancrage 'note-top' supprimé.
- ✅ (2026-11-23) **Centrage vertical relatif** (retour visuel PR #98, horizontal) : la baseline d'un glyphe de note est
  `cy + 0,318 × SA PROPRE fs` (`effective_fs` kuubanchi, `sh` shuffle, `ss` straddle), jamais `cy + 0,318 × fs` de case
  (ratio 1,0) — avant, kuubanchi/shuffle/straddle étaient trop bas quand la fs diminuait. Sites : note simple, composites
  (下老/下八/下尺/positions hautes), note principale de straddle, shuffle 2 et N en horizontal (+ cas koe en vertical).
  Inchangé quand fs pleine (effective_fs == fs). Test 7f dans `tests/test_testbushi.py`. Grille régénérée.
- ⬜ Valider le rendu vocal multi-caractères (うちなぐち) : empilement petits kana, ー vertical,
  chevauchement bord inférieur. Support vocal en mode horizontal non implémenté (priorité verticale).
- ⬜ Valider visuellement les accords (`四-五`, `+`) et le rendu condensé イ下尺 / ロ下尺 sans cercle.

## 2. Phases fonctionnelles (séquencement P0 → P4)

### P0 — Référence 野村流 dans la documentation — ⬜
- Section « Référence 野村流 » dans `docs/notation.md` : modèle à 4 positions/case,
  inventaires techniques instrumentales et vocales, code couleur rouge (haut) / noir (bas).
- Enrichir les positions vocales : 才 凡 勺.
- Table d'alias de normalisation des tokens.
- Relecture des scans sources pour la fidélité des formes (pré requis de P3).

### P1 — Techniques instrumentales étendues — 🚧
- ✅ Position 下八 (kandokoro propre, octave de 中) — commit `8b4d683`.
- ⬜ Suffixes techniques supplémentaires dans `TECHNIQUE_SUFFIXES` : 打抜音, 抑下し, 開音, 掻音,
  小字 (~70 %). Patron rodé, effort faible.
- Non couvert volontairement : イ下八 / ロ下八 (non attestés, repli dégradé).

### P2 — Section positionnée (ruby vocal) : nombre de positions variable, règles de layouting — ✅ décidé le 2026-11-01
- DÉCISION TRANCHÉE : **pas de nombre de positions fixe dans KKML**. Le nombre de
  positions par case est libre (constaté à la saisie, peut dépasser 4). La question
  grille 3 (Portama) vs 4 (Nomura-ryu) est caduque : l'import Portama produit
  naturellement 3 positions/case, le layout nomura impose ses propres seuils.
- `::vocal` (mot = syllabe, points `.` = subdivision du temps en parts égales) reste
  la syntaxe de saisie ; incompatible avec 声楽譜 ; la section positionnée (futur
  `::ruby`) sera le substrat commun à P3.
- **Règles de layouting** (seuils appliqués au rendu, pas au format). Chaque règle a
  un défaut par layout et une méta KKML d'override (CLI prioritaire sur méta, comme
  `@cells_per_dan`/`-c`, `@layout`/`-l`, `@dans_per_page`/`-p`) :
  - `@overflow allow|shrink|truncate|error` — syllabes/caractères qui dépassent la
    case. Défaut vertical : `allow` (chevauchement bord inférieur accepté, comportement
    historique). Défaut nomura : `error` (fidélité stricte à la grille traditionnelle).
  - `@text_shrink on|off` — réduction de la taille de police jusqu'à un plancher quand
    la colonne marker est trop chargée. Défaut : `on` en vertical, `off` en nomura.
  - `@truncate on|off` — troncature avec `…` au-delà d'un seuil de positions/case.
    Défaut : `off` partout.
  - `@strict on|off` — toute situation anormale (figure non reconnue, positions
    au-delà du seuil du layout) devient une erreur (exit non-zéro) au lieu d'un
    avertissement. Défaut : `off`. Utile en CI : `tests/run_tests.py` échoue déjà sur
    tout `AVERTISSEMENT` ; `@strict on` renforce.
- Seuils par layout paramétrés, pas en dur : la colonne marker nomura est plus étroite
  que celle du vertical, les planchers de taille et seuils de troncature diffèrent.
- Round-trip Portama : export KKML → Portama arrondit à la grille 3 unités/case de
  `allRubyData` (perte admise) ou refuse si une case dépasse 3 positions.
- Constantes mesurées disponibles (かぐやで風節, PDF vectoriel) : ruby fs = 0,65 × note fs,
  avance ligne = cell_h/3, tuck petit kana +1,18 × fs, offset x +0,1 × fs.
- ⬜ Mesurer le rendu du chōonpu ー si un PDF ruby avec voyelles longues est disponible.

### P3 — Section 聲楽譜 (notation vocale) — ⬜ (dépend de P0 et P2)
- Section paire à `::tab`, grammaire type `発声法:hauteur[:上|平|下]`.
- Table de rendu des ~20 発声法記号 (上吟/下吟/次第上/次第下/押切/直吟/呑み/掛/大掛/当/
  ネーキ/クダミ/ユルシ/振い/廻い/振上げ/内グヰ/突吟/スクヰ…).
- Rendu : glyphes Unicode (▲○●□↑) ou formes SVG dessinées ; rouge/noir via `fill` SVG.
- 勺 凡 才 acceptés comme hauteurs ; 声だし / 声切り en colonne marker.

### Variantes phonétiques des paroles — ✅
- Blocs `::lyrics-kanji` / `::lyrics-ruby` / `::lyrics-kana` / `::lyrics-romaji` (alias `::lyrics` = `::lyrics-ruby`). Grammaire et rendu identiques à `::lyrics` ; la variante est conservée sur `Block.variant`. Permet de distinguer plusieurs versions phonétiques d'une même chanson (japonais vs étrangers).
- ⬜ Sélection de la version rendue (méta `@lyrics_variant` ou option CLI) — actuellement toutes les variantes sont rendues à la suite.

### P4 — Annotations de marge et de tempo — ⬜
- 指位記号 (doigtés) : numéraux encerclés ㊀㊁㊂㊃ (野村流), colonne/marge dédiée,
  (2026-11-19) encodage KKML en place : suffixe ㊀㊁㊂㊃ (U+3280-U+3283) sur la note dans `::tab` (ex. `合㊀`), jamais position autonome (garde-fou + AVERTISSEMENT si seul) ; variantes ㈠㈡㈢㈣ (U+3220-U+3223) normalisées. Rendu : glyphe à gauche de la note, même baseline, fs ≈ 0,735×fs (`TECHNIQUE_SUFFIXES` pos 'left', calibré sur samples/portama-pdf/テスト節.pdf). portama2kkml : cell.yubii 1-4 et note PUA U+E041-E044 → suffixe. Reste : rendu en marge dédiée Nomura (P4) et extraction inverse dans kkml2portama.
  jamais dans la grille (collision avec la normalisation REST_VARIANTS → ◯).
- 撥記号 (coups de plectre).
- Annotations de tempo : 五分拍子 (「此間X分Y厘脉」), 少緩弾 / 少早弾.

## 3. Backlog Portama (conversion JSON → KKML)

- ⬜ Compléter le mapping des ornements (`orn` au-delà de `"u"`).
- ⬜ Comprendre la sémantique audio de `chogen` (4 vs 5), `rhythm`, `rhythmMode` — passthrough verbatim en place depuis le 2026-11-19 (`@chogen`/`@rythm`/`@rythm_mode`), la déduction `@base_note` ↔ `chogen` reste à définir.
- ⬜ Recenser les autres accordages (`choshi` : ni, san…) et leur mapping PUA.
- ⬜ Round-trip Portama : variante « raw » de `::ruby` (ligne allRubyData littérale, sans perte).
- ⬜ Contrepartie `::vocal` : règle note = floor(unités/3), validée sans collision sur かぎやで風節.
- ❓ (2026-11-19) Granularité `::vocal` vs round-trip Portama (remontée utilisateur) : une case KKML = paire Portama = 2 cellules × 3 positions vocales (top/mid/bot) = **6 sous-positions** ; idem côté ruby (`allRubyData` = 3 unités/cellule Portama = 6/case KKML). Encodage actuel (1 token `::vocal` par paire) : cellule principale → `(`/`)` nu (**position perdue**), cellule à cheval seule → points de tête (top = nu, mid = 1, bot = 2 — position OK), les deux combinés → token nu (`()` / `)(`, **positions perdues**). Pour un réexport Portama fidèle, il faudra soit coder la position des deux côtés dans le même token (ex. principale = parenthèse + points de queue, à cheval = points de tête + parenthèse), soit diviser chaque case en 6 sous-positions. À trancher avant d'écrire `kkml2portama.py`.
  **Proposition de résolution (2026-11-19)** : champ `::vocal` de 6 sous-positions par case (0=principale top, 1=mid, 2=bot, 3=à cheval top, 4=mid, 5=bot) ; un marqueur koedashi/koekiri = la parenthèse placée à l'index N du champ, les autres slots en points `.` — ex. koedashi seul : `(.....` `.(....` `..(...` `...(..` `....(.` `.....(`. La parenthèse reste du formatage inline (0 unité, déjà le cas dans `_vocal_elements`) : son slot = nombre d'unités AVANT elle, un caractère pleine chasse (kanji) comptant 2 unités et étant atomique (pas de borne à l'intérieur). Avec du chant : ex. `字..(.` = kanji (2 unités) + 2 points → parenthèse au slot 4. Cas limite « case pleine de chant » (6 unités) : pas de débordement puisque la parenthèse est gratuite — koedashi en `(字字字` (borne 0) ou `字字字(` (borne 6 = fin de case) ; un slot demandé à l'intérieur d'un caractère pleine chasse est rabattu sur la borne suivante. À valider avant implémentation.

## 4. Long terme

- ❓ (2026-11-23) Remplacer les notations `A/B` (croche), `A:B` (shuffle), `A//B/C`… de `::tab` par un système de points analogue à celui de `::vocal` — **long terme, soumis à un vote préalable des utilisateurs**, car cela remet en cause le caractère intuitif du KKML.
- ⬜ Conversion KKML -> Portama JSON
- ⬜ Pipeline de publication LaTeX : collaboration avec éditeurs et communauté large.
  Pas de LilyPond / portée standard.
- ⬜ GUI : combler l'écart avec Portama (avantage GUI).
- ⬜ Internationalisation (non prioritaire) : basculer le projet en anglais, ou en multilingue
  français / anglais / japonais (README, `docs/`, messages et diagnostics des scripts Python,
  commentaires du code). À trancher le moment venu : anglais seul vs i18n complète.
- ✅ `kkml_cleaner.py` (2026-11-01, PR #10) : normaliser un KKML sur sa forme canonique (formes pleine chasse → demi-largeur, romaji/chiffres → kanji kandokoro, kanji composites → katakana+kanji, `::tab-lyrics`/`::tab-vocals` → `::vocal`, ordre des sections `::tab` `::vocal` `::lyrics`). Réutilise les tables de normalisation de `kkml2svg.py` ; sortie : KKML canonique, idempotent (cleaner(cleaner(x)) == cleaner(x)). Règles de complétion structurelle :
  - `::vocal` manquante → la créer, remplie de cases vides (`-`) alignées sur `::tab` (même nombre de cases par ligne) ;
  - `::vocal` désalignée de `::tab` (cases/ligne différentes) mais total de cases identique → réaligner ligne à ligne sur `::tab` ; si le total ne boucle pas → avertissement stderr, PAS de réalignement ;
  - `::lyrics` manquante → la créer, vide ;
  - `::tab` implicite (lignes hors section) → rendre la section explicite (info) ;
  - `::tab` manquante → la créer, vide (peu de risques).
- ✅ (2026-11-21) Ordre des métadonnées du cleaner : toutes regroupées en haut du fichier, `@format`/`@version`/`@title` toujours en premier (si présents), puis les autres dans leur ordre d'apparition dans le fichier (l'ancien ordre canonique `meta_order` est supprimé) ; `@layout` n'est plus perdu à la réécriture ; dédup première occurrence. Séparateurs : une et une seule ligne vide entre le bloc des métadonnées et la première section, et entre chaque section (aucune ligne vide en tête si pas de métadonnées, aucune en fin de fichier). `@format KKML` ajouté s'il est absent (épinglé en première ligne). Tests `tests/test_cleaner_meta.py`.
Mode test (`--dry-run` / `-n`) : affiche le KKML nettoyé sur stdout (ou écrit dans un fichier distinct) sans écraser le KKML d'origine, pour voir le résultat avant application.
`@cells_per_dan` comme indice de repli (jamais de valeur par défaut) : si `@cells_per_dan n` est présent, le cleaner replie `::tab` à n cellules/ligne (dernier dan partiel conservé tel quel, info) puis aligne `::vocal` dessus ; si absent, les sauts de ligne de l'utilisateur sont conservés tels quels. Ancien nom `@cols` renommé par le cleaner (info). (Portama : `cellsPerDan`). Terminologie retenue : **cellule** = unité sémantique de temps dans `::tab`/`::vocal` ; **case** = cellule rendue graphiquement (tableau du layout SVG) ; **dan** (段) = groupe de cellules, ligne horizontale dans le fichier KKML, colonne dans le layout vertical. La bibliographie anglaise parle de « column » (Kunkunshi Editor : « 12 columns per page, 12 cells per column ») ; dans le gojūon japonais 段 [dan] = colonne, 行 [gyō] = ligne. Même rigueur pour le marker : **marker** = concept sémantique (marques de répétition `|:`/`:|`, bornes de chant `(`/`)`, syllabes vocales, hauteur de chant), rendu dans le layout comme **colonne marker** (vertical) ou **ligne marker** (horizontal), largeur `marker_w`. `@marker on|off` pilote le concept ; `marker_w` la représentation. Terminologie officielle : **section** = bloc `::...` du KKML (`::tab`, `::vocal`, `::lyrics`…) ; le mot **bloc** est réservé aux éventuels blocs de texte du layout. Terminologie : **syllabe** réservé aux syllabes japonaises / langues ryukyu ; dans le contexte général de `::tab`/`::vocal` (token vocal quelconque, y compris romaji ou kana non japonais), parler de **token vocal** (code : `vocal_data`, `syllable_fs` renommables en `vocal_fs` à l'occasion).
Diagnostics : le cleaner émet info / avertissement / erreur sur stderr selon la gravité (ex. normalisation appliquée = info, réalignement refusé = avertissement, KKML malformé et inutilisable par le parser = erreur fatale, exit non nul).
- ✅ (2026-11-22) `kkml_cleaner.py` renommé en `kkml_clean.py` (objet → verbe d'action) — fait : fichier + imports + tests renommés, références README/`docs/`/CI mises à jour, shim `kkml_cleaner.py` ajouté pour la transition puis supprimé. Voir l'entrée ✅ de la section 0.
- ⬜ (2026-11-22) Gestion de medleys (compilations) — trois chantiers liés :
  - `kkml-append.py` : créer un medley KKML à partir de plusieurs chansons (fichiers KKML individuels) — chaque chanson devient un run `::song <nom>` + son contenu (`::tab`/`::vocal`/`::lyrics`), métadonnées communes du medley en tête de fichier.
  - `kkml-split.py` : découper un medley en chansons KKML indépendantes — réattribuer à chaque fichier sorti les métadonnées communes du medley (ex. `@title` global) plus les métadonnées spécifiques de la chanson.
  - Métadonnées spécifiques à une chanson dans un medley : autoriser des lignes `@clé valeur` À L'INTÉRIEUR du bloc `::song <nom>` (ex. `@choshi`, `@source`, `@chogen` — appliquées à cette chanson uniquement). À parser dans `parse_kkml` (champ dédié sur le bloc song), à préserver/réémettre par le cleaner, à réécrire en tête du fichier par `kkml-split.py`, et éventuellement à prendre en compte au rendu mega (surcharge des méta globales pour les colonnes de cette chanson).

## 5. Positionnement

Le convertisseur est plus avancé que threedaymonk/kunkunshi et Kunkunshi Editor
(accords, positions composées, souhou, vocal, répétitions). Portama reste en avance
sur l'interface. La priorité est la fidélité notationnelle (P0 → P3) avant la
publication (LaTeX) et l'ergonomie (GUI).

## 6. Conformité typographie japonaise (JLREQ) — ⬜

Référence : [Requirements for Japanese Text Layout 日本語組版処理の要件（日本語版）](https://www.w3.org/TR/jlreq/) (W3C) —
annexe A (classes de caractères cl-01…cl-30), §3.2.6 (espacement inter-caractères, quart de
cadratin), règles de retour à la ligne (kinsoku 行頭禁則 / 行末禁則, base JIS X 4051),
écriture verticale (formes de présentation U+FE30–FE4F / UAX #50 Vertical_Orientation).
Propositions discutées le 2026-11-20.

Déjà conforme : rotation 90° de ー （）()「」『』 en vertical
(`VERTICAL_ROTATE_CHARS`, `kkml2svg.py`) appliquée au titre, métadonnées et paroles ;
ruby mono/group/jukugo avec segments atomiques au repli (`_lyr_line_segments`) ;
petits kana tassés dans la colonne marker (`_draw_vertical_vocal`).

- 🚧 P0 Kinsoku au repli des paroles — `::lyrics` uniquement (2026-11-20, PR #42) : seul
  `_cap_lyr_column` (chindami) coupe les lignes de paroles au caractère ; vertical/mega ne
  repliquent qu'aux `|` explicites, horizontal ne replie pas (règle alignée). Tables JLREQ
  annexe A (`KINSOKU_NO_LINE_START` / `_STRICT` / `KINSOKU_NO_LINE_END`) + `_kinsoku_adjust_cut`
  : 行頭禁則 (cl-02/05/06/07/09/10/11/29) avec追い出し, 行末禁則 (cl-01) ; méta
  `@kinsoku simple|strict|off` + CLI `--kinsoku` (défaut `simple`, `off` en nomura) ;
  tests `tests/test_kinsoku.py`. Corrigé au passage : boucle infinie préexistante de
  `_cap_lyr_column` quand un segment plaine coupé voyait son reste entièrement placé
  (`u` non recalé sur `len(text)` après la coupe). Reste : lien ぶら下げ ↔ `@overflow`
  (cl-06 seules en fin de colonne), repli horizontal si activé un jour.
- ⬜ P0 Yakumono en vertical : 、。，． placés dans le quart supérieur droit de la chasse
  (formes verticales U+FE11/FE12) au lieu du centrage de `_vertical_char` ; étendre
  `VERTICAL_ROTATE_CHARS` avec ― – ‥ … ′ ″ et les formes U+FE30–FE4F.
- ✅ (2026-11-22) Petits kana tassés dans la colonne marker verticale (`_draw_vertical_vocal` : layouts
  vertical/chindami/mega ; syllabe 2 parties grand+petit → petit à droite (+0,25 fs, +0,60 fs — avance ~0,6 em, conforme JLREQ cl-11), MÊME taille de police
  (le glyphe petit kana est nativement plus petit : グヮ vs グワ), comme les PDF Nomura/Portama — JLREQ cl-11 ; nomura/horizontal/tuto inchangés).
- ⬜ P1 Petits kana (cl-11) tassés (avance ~0,6 em + décalage haut-droite) dans TOUTES les
  colonnes verticales (paroles/titre via `_render_vertical_text`), pas seulement la colonne
  marker ; inclus dans 行頭禁則.
- ⬜ P1 Quart de cadratin (四分アキ) CJK↔latin (JLREQ §3.2.6 : 1/4 em entre cl-15/16/19
  et cl-27, aucun en début/fin de ligne) : fonction d'avance par classes de caractères
  pour le flux horizontal et l'espacement vertical (étendre/remplacer `_char_w`).
- ⬜ P1 Normalisations `kkml_clean.py` : katakana demi-chasse U+FF61–FF9F → pleine chasse
  (le rendu suppose des chasses carrées 1 em), tirets ‐‑‒–—― → canonique
  (ー réservé au kana), ‥ vs … selon orientation, quotes occidentales “”‘’ →
  「」『』 ; diagnostic info comme les règles existantes.
- ⬜ P2 Séquences insécables (分割禁止 : `100%`, `¥100`, paires de parenthèses)
  en segments atomiques dans `_lyr_line_segments`, au-delà des groupes ruby.
- ⬜ P2 Écriture verticale native `writing-mode="vertical-rl"` + `text-orientation: mixed`
  (UAX #50) en option, rendu manuel actuel en repli (rsvg-convert/inkscape pour le PDF).
- ⬜ P2 Documentation + tests : section « conformité typographie japonaise » dans
  `docs/svg-layout.md` avec le lien JLREQ et les déviations volontaires (indent de couplet
  à 3 chasses pleines vs 字下げ 1 em du JLREQ, propre aux recueils 工工四) ; tests golden
  (colonne finissant par 、, repli devant ）, petit kana / ー en tête de colonne, texte
  mixte kanji/romaji).

# Références de calibrage externes (hors dépôt)

Les constantes mesurées (NOMURA_*, CHINDAMI_*) figurent dans le code et
dans ce fichier. Les scans de recueils servant au calibrage ne sont pas
dans le dépôt (droits d'auteur) ; leur provenance et leur emplacement
privés ne sont pas référencés ici.

- ✅ (2026-11-23) `calibration/left-1200.png` / `right-1200.png` **purgés de tout l'historique git** (données personnelles accidentelles dans `left-1200.png`) : réécriture `git filter-branch --index-filter 'git rm -r --cached --ignore-unmatch calibration/left-1200.png calibration/right-1200.png' --prune-empty` (le commit d'upload ne contenait que les 2 PNG → commit vide éliminé), force-push de `main` (`4c3ce57` → `5848a64`, 1175 commits), gc local (pack promisor du partial clone supprimé). Plus aucun objet PNG atteignable depuis `main`, localement comme sur le serveur. **Reste à faire** : les refs internes `refs/pull/*` (~95 refs GitHub) et les vues en cache conservent encore les anciens objets côté serveur — purge définitive à demander au **Support GitHub** (suppression de données sensibles / cached views). Ne jamais réuploader de scans ou PNG de calibrage dans le dépôt.

# Architecture des convertisseurs Python

> Contenu déplacé depuis `docs/converter-architecture.md`. Documentation agent : structure interne du code, pour la navigation lors des modifications. La documentation utilisateur reste dans `docs/`.

## `kkml2svg.py`

Python 3 autonome, ~4400 lignes (4403 au 2026-11-15). Ce dépôt est la source de vérité du code.

### Constantes de mise en page : `LayoutSpec` (2026-11-20, PR #44)

Toutes les constantes partagées des 6 layouts vivent dans un dataclass figé
`LayoutSpec` (champs en **pt**, `PX = 0,75`), une instance par layout :
`VERTICAL`, `HORIZONTAL`, `NOMURA`, `CHINDAMI`, `TUTO`, `MEGA` + dict
`LAYOUTS`. `spec.u(v)` convertit en unité native du layout (`px = pt / PX`,
exact pour nos valeurs). Champs : marges (`margin_t/b/l/r`), cadre
(`frame_w/h`, 0 = pas de cadre, `frame_margin_x/y`), titre (`title_w`,
`title_gap`, `title_spacing`, `tuning_spacing`, `title_fs`, `meta_fs`),
`gap_header`, `header_h`/`header_h_title`, `cell_w/cell_h` (0 = dérivé de la
page), `fs` (0 = `max(fs_min, fs_ratio × cell_h)`), `cells_per_dan`
(ex-`rows_per_col`/`cols_per_row`), `marker_ratio` (+ `marker_w` absolu si
> 0, chindami), `pile_w`, `lyr_gap`, `lyr_size` (ex-`lyrics_size`),
`lyr_fs` (fs paroles ABSOLUE en pt, 0 = dérivée de `lyr_size` × `fs` ;
chindami 10,8), ratios paroles (`lyr_sp_ratio`, `lyr_col_w_ratio`,
`lyr_verse_gap_ratio`), ratios syllabes
(`syl_cell_ratio`, `syl_marker_ratio`, `syl_fs_ratio`), structure de blocs
(`blocks` = 1 partout sauf mega 2, `block_gap` = 0 sauf mega 30,
`dans_per_block` = `max_dans` hors mega — nomura 7, chindami 15, tuto 7 —
0 = illimité en vertical/horizontal, 32 en mega ; `lyr_inline_max_ratio` =
seuil paroles inline 1re page, mega), `dan_gap`/`max_dans` (nomura, chindami,
tuto).
✅ (2026-11-21) unification des champs de bloc : `blocks`/`block_gap`/
`dans_per_block` présents dans TOUS les layouts (hors mega : bloc unique,
`dans_per_block = max_dans`) ; `rows_per_col`+`cols_per_row` fondus en
`cells_per_dan` (le « 7 dans/page » de tuto, ex-`rows_per_col`, est porté
par `dans_per_block`) ; `lyrics_size` → `lyr_size` ; `lyr_fs_ratio` →
`lyr_fs` (valeur absolue). Vérifié : rendus SVG byte-identiques
(114 échantillons × 6 layouts).
✅ (2026-11-21) les alias de module `NOMURA_*`/`CHINDAMI_*`/`MEGA_*`/
`TUTO_DEFAULT_*` ont été SUPPRIMÉS : les renderers lisent `spec.*`
directement (`spec` passé en paramètre, y compris à `_mega_meta_column` ;
`cell_w/h` nomura dérivés du spec dans `_render_nomura`). Seuls `PX` et
`CM` restent des constantes de module (conversion d'unités).
`render_svg` choisit `spec = LAYOUTS[layout]` et le passe à chaque renderer
(paramètre `spec=None`). Vérifié : rendus SVG byte-identiques avant/après
(114 échantillons × 6 layouts). Le générateur de figures
`docs/svg/make_svg_layout_figures.py` (PR #43) lit les specs (`k.MEGA.page_w`…)
et ses libellés utilisent les noms de champs du spec en minuscules
(`margin_l`, `title_w`, `block_gap`, `dans_per_block`, `dan_gap`, `grid_top`,
`lyr_gap`, `spec.fs`…) — figures `docs/svg/*.svg` régénérées (diff = libellés
uniquement, 2026-11-21). Les noms en MAJUSCULES restants dans les libellés
(`LYRICS_FS`, `SYLLABLE_SP`…) sont des variables locales des renderers, pas des
paramètres de mise en page.

### CLI

```bash
python3 kkml2svg.py chanson.kkml -o chanson.svg
python3 kkml2svg.py chanson.kkml            # -> chanson.svg
cat chanson.kkml | python3 kkml2svg.py -     # stdin -> stdout
```

Options : `-o output`, `-c cells_per_dan`, `-l vertical|horizontal|nomura|chindami|tuto|mega`, `-p/--dans-per-page N`

### Structure du code

### 0. Rendu multipage (`render_svg`)

- `render_svg(...)` retourne désormais une **liste de SVG** (un par page).
- Pagination : `@dans_per_page N` (méta ; `@page_dans` accepté comme ancien nom) ou `-p/--dans-per-page N` (CLI ; `--page-dans` reste accepté en alias). Défaut : None = une seule page (comportement historique).
- `_render_vertical` découpe les sections tab en pages de N dans ; les colonnes vocales (`vocal_data`) sont tranchées en synchronisation avec les colonnes de tab (même slice).
- Sections lyrics et titre vertical : répétés sur chaque page.
- `main()` : 1 page → sortie simple ; n pages → `stem-1.svg` … `stem-n.svg`.

### 1. Parseur KKML (`parse_kkml`, lignes ~129-210)

- Classes `Song` (meta, blocks, cols, layout) et `Block` (kind, label, lines)
- Lit ligne par ligne : commentaires `#`, métadonnées `@`, sections `::kind`, fermeture `::`
- Sections supportées : `tab`, `lyrics`, `vocal`, `section` (`::tab-lyrics` et `::tab-vocals` sont des alias dépréciés de `::vocal`)
- `::vocal` se paire à la section `::tab` précédente : chaque ligne vocale est aplatie avec padding par ligne (`-`) sur la structure de la ligne de tab de même index ; l'excédent est tronqué. La syllabe i reste alignée sur la note i.

#### 2. Rendu SVG (`render_svg`, ~212-308)

- Regroupe les sections en 4-uplets `(section_title, content, kind, vocal_data)`
- `has_vocal = any(s[3] or s[2] == "vocal")` → active automatiquement la colonne marker
- Constantes de rendu vocal : `SYLLABLE_FS = min(int(cell_h * 0.26), int(marker_w * 0.8))`
- Route vers `_render_vertical`, `_render_horizontal`, `_render_nomura`, `_render_chindami`, `_render_tuto` ou `_render_mega` selon le layout

#### 3a. Rendu vertical (`_render_vertical`, ~309-580)

- Offsets `title_offset`, `lyrics_offset`, `marker_w = cell_w // 2` si marker
- Helpers : `_wrap_vertical` (découpage en colonnes de N), `_split_verses` (couplets)
- Titre vertical à droite, paroles verticales à gauche

#### 3b. Rendu vocal (`_draw_vertical_vocal`, ~613 + `SMALL_KANA`)

- Un token = une syllabe, rendu dans la colonne marker centré sur la note
- Token multi-caractères empilé : caractère principal aligné sur la note, caractères combinants dessous (espacement `int(syllable_fs * 1.15)` entre caractères combinants ; `SYLLABLE_SP = int(SYLLABLE_FS * 0.9)` entre syllabes d'une même case), ー pivoté 90°
- Chevauchement du bord inférieur de case accepté

#### 3c-nomura. Rendu Nomura-ryu (`_render_nomura`)
- **`nomura` est une FLAVEUR, pas seulement un layout** : elle modifie substantiellement le rendu du KKML, au-delà de la géométrie — options forcées (`@marker on`, `@shaku_sharp off`, `@shaku_circled off`), pagination propre (titre/couplets en dans virtuels, excédent sur page suivante), colonne marker à droite en 3 sous-colonnes. Toute nouvelle contrainte Nomura-ryu doit être forcée dans `_render_nomura`, pas laissée aux méta KKML.
- Layout `nomura` (`@layout nomura` / `-l nomura`) : page A4 portrait 21 × 29,7 cm = 595,28 × 841,89 pt (via la constante CM = 28,3465 pt/cm, partagée avec chindami), cadre filet, 12 cases/dan, marker = largeur d'une case à DROITE des notes (filets vertical ×2 + haut/bas), jusqu'à 7 dans/page, titre = 1 dan complet en colonne droite p.1, paroles en colonnes verticales, multipage automatique (1 SVG/page). `@marker on` forcé (cosubstantiel).
- **3 constantes primaires** (tout le reste est dérivé) : `NOMURA_FRAME_W = 559,3` (largeur cadre, médiane 12 pages), `NOMURA_FRAME_H = 745,9` (hauteur cadre), `NOMURA_DAN_GAP = 14,5` (marge de dans M unique). Dérivés : `FRAME_MARGIN_X = (595,28 − 559,3)/2 ≈ 18` ; `FRAME_MARGIN = (841,89 − 745,9)/2 ≈ 48` ; `CELL_W = (FRAME_W − 8M)/14 ≈ 31,7` ; `CELL_H = (FRAME_H − 2M)/12 ≈ 59,7` ; `group_w = 2×CELL_W`.
- **Marge M unique partout** : haut cadre→grille, droite cadre→1er dan (marker), entre dans, gauche 7e dan→gauche cadre, bas grille→bas cadre. Géométrie : `grid_y0 = frame_y0 + M` ; `x_right = frame_x1 − M` ; chaque dan décrémente `x_right −= (group_w + M)`. Vérifié : boucle au pt près.
- **Taille des notes : 26 pt** (validée visuellement, cf7f524). Mesure scan : encre kanji ≈ 0,43 × case → fs ≈ 29 pt, trop gros avec une police mincho moderne ; 26 pt retenu. Valeur explicite dans `_render_nomura`.
- Titre : centré exactement entre le filet droit de la première colonne marker et le filet droit de page (`tx = x_right − group_w/2`) ; taille `cell_h × 0,43` ; indentation `cell_h × 1,8` sous le haut de grille. Le centrage porte sur la colonne de base uniquement ; le ruby du titre (mono `安《あ》`, group `｛…｝《…》`, RUBY_SCALE 50 %) se colle à droite de la base (`ruby_x = x + fs × 0,75`) **sans déplacer ni le centrage ni la base** — comportement standard de `_render_vertical_ruby`, ne pas régresser.
- Couplets (`::lyrics`, préfixés ⚪︎, `||` = saut sans colonne blanche) : **3 colonnes max par dan virtuel** calées pile sur la largeur d'un dan (`LYRICS_COL_W = group_w/3`) ; au-delà de 3 colonnes → dan virtuel supplémentaire espacé de M.
- **Pagination couplets** : la musique remplit les pages normalement (p.1 = 7 − 1 si titre, puis 7 dans ; jamais réduite, jamais de dan de musique perdu). Les couplets occupent les dans LIBRES de la dernière page de musique ; l'excédent de dans virtuels passe sur des pages suivantes dédiées couplets (7 dans virtuels max/page). **Jamais de débordement du cadre.** Tuple de page : `(cols, vocal_cols, is_last, lyr_dans_here, lyr_col_offset)`.
- **Colonne marker = 3 sous-colonnes virtuelles** (spec Nomura-ryu, non encore implémentées) :
  1. **droite** : hauteur de chant — petits kanjis dérivés des kandokoro du sanshin (avec variantes vocales) ;
  2. **milieu** : instructions de chant — points de positionnement exact des notes, lignes de glissando, etc. ;
  3. **gauche** : texte du chant en syllabique (`::vocal`).
  Implémentation actuelle : syllabes centrées dans la bande marker (à déplacer vers la sous-colonne gauche) ; sous-colonnes hauteur/milieu à créer avec P3 声楽譜.
- **尺♯ en nomura-ryu** : `@shaku_sharp off` **et** `@shaku_circled off` systématiques — les 尺♯ sont rendus en 尺 simples, jamais encerclés ; c'est au lecteur de deviner la hauteur exacte des shaku à jouer. Le layout nomura doit forcer ces deux options (comme `@marker on`), indépendamment des méta KKML.
- Aplatit les sections tab en flux de colonnes de 12 ; les syllabes `::vocal` vont dans le marker. Sélecteurs de variante (U+FE00–FE0F) non rendus (éviter l'« espace doublée » en tête de couplet).

#### 3c. Rendu horizontal (`_render_horizontal`, ~794)

- Mode songbook : gauche→droite, haut→bas. Vocal horizontal non implémenté (priorité au vertical)

#### Fonctions de dessin

- `_draw_vertical_tab` — grille verticale, deux passes (rectangles puis notes) ; rend aussi les données vocales pairées
- `render_cell` (~1147) — rend un token (voir ci-dessous)
- `_note_svg` — rendu d'une note unique
- `_render_techniques` — souhou autour de la cellule ; suffixes avec `dx/dy/scale/rotate` individuels, paramètre `text_w` pour multi-caractères
- `_strip_repeat_marks` + `_render_repeat_arrow` — marques `|:`/`:|` détachées des tokens, flèches ↓/↑ rendues dans la colonne marker
- `_render_end_circle` — cercle de fin
- `_render_vertical_ruby` / `_render_vertical_text` / `_render_horizontal_ruby` / `_render_horizontal_text` — texte vertical/horizontal (titres, paroles, ruby)

#### Tokens gérés par `render_cell` (ordre de traitement)

1. Marques de répétition détachées avant traitement (`_strip_repeat_marks`)
2. Cas spéciaux : EMPTY (`-`), SUSTAIN (`.` → ・), REST (◯/variants)
3. Suffixes de technique extraits de la fin du token
4. 尺♯ selon `@shaku_sharp` (jamais entouré)
5. Accords `A-B` / `A-B-C` (séparateur `-`, max 3 notes) : notes empilées à 72%
6. 下老 et positions hautes `イX`/`ロX` : un seul `<text>` avec `textLength` + `lengthAdjust="spacingAndGlyphs"` (下老 demi-largeur, positions hautes 120%)
7. イ下尺 : 3 caractères condensés (イ下尺), textLength 180%, sans cercle
8. Croche `A/B` (note principale + à cheval), shuffle `A:B` (deux notes empilées)
9. Note simple centrée ; ornement multi-caractères empilé

#### Constantes notables

- `POSITION_CHARS`, `REST_VARIANTS`, `TECHNIQUE_SUFFIXES` (uchi-utu `'` (alias `*`, `｀`), kaki-utu `^`, aki-utu `v`, kachi-utu `<`, kuubanchi `s`, taachi `=`)
- `HIGH_PREFIX_I` / `HIGH_PREFIX_RO` (positions hautes イ/ロ + kanji compatibles)
- `FONT_STYLES` : mincho (défaut), gothic, serif (`@font_style`)
- `VERSE_*` : regex de numéros de couplet, puces, genre (男/女)

### Paramètres par défaut

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| cell_w | 52 | largeur de case |
| cell_h | 58 | hauteur de case |
| font_size | 22 | taille police notes |
| cells_per_dan | 12 | cellules par dan, lignes par colonne (vertical) — défaut depuis le 14 sept. 2026 (avant : 9) |
| marker_w | cell_w // 2 | colonne marker (auto si ::vocal) |

## `kkml2pdf.py`

Python 3 autonome (stdlib) **plus** dépendances externes optionnelles détectées à l'exécution : un moteur SVG→PDF et un outil de fusion PDF. Ce dépôt est la source de vérité du code.

### CLI

```bash
python3 kkml2pdf.py chanson.kkml -o chanson.pdf
python3 kkml2pdf.py chanson.kkml            # -> chanson.pdf
cat chanson.kkml | python3 kkml2pdf.py -     # stdin -> output.pdf
```

Options : `-o output`, `-c cells_per_dan`, `-l layout`, `-p/--dans-per-page N` (passés à `render_svg`), `--engine auto|rsvg-convert|inkscape|cairosvg`, `--merger auto|pypdf|pdfunite|gs`, `--keep-temp DIR`.

### Chaîne

- `render_pages(text, layout, cols, page_dans)` : `parse_kkml` + garde + `kkml2svg.render_svg(...)` → `(layout_effectif, [svg, ...])`. Garde : seuls `chindami`/`nomura`/`mega` (`LAYOUTS_CM`) sont acceptés — les seuls layouts dont kkml2svg émet la racine SVG en cm (`_svg_open_print`) ; les layouts libres (page en pt/px selon le contenu) lèvent `UnsupportedLayout` → exit 2.
- `page_size_cm(svg)` : lit `width`/`height` en cm sur la racine `<svg>` (log par page ; `None` → AVERTISSEMENT).
- `produce_pdf(svgs, out, engine, merger, workdir)` : écrit `page-N.svg` dans un répertoire temporaire (`--keep-temp DIR` les conserve), convertit chaque page en `page-N.pdf` via `convert_page`, fusionne dans l'ordre via `merge_pdfs`.
- `convert_page(engine, svg, pdf)` : `rsvg-convert -f pdf -o`, `inkscape --export-type=pdf --export-filename=`, ou `cairosvg.svg2pdf(url=..., write_to=...)`. La taille de page PDF vient du cm du SVG (MediaBox en pt = cm × 28,3465).
- `merge_pdfs(merger, pdfs, out)` : `pypdf.PdfWriter.append` page par page, ou CLI `pdfunite` / `gs -sDEVICE=pdfwrite`.
- Détection : `detect_engine`/`detect_merger` (`auto` = premier disponible ; `--engine`/`--merger` pour forcer). `cairosvg` n'est retenu que si son import réussit (sinon OSError libcairo). Aucun disponible → ERREUR + exit 1 avec la liste des installables.
- `engine`/`merger` acceptent aussi une fonction appelable — utilisé par `tests/test_kkml2pdf.py`.

## `portama2kkml.py`

Python 3 autonome. Ce dépôt est la source de vérité du code.

- Mapping PUA → kanji (voir [format Portama](docs/portama-format.md))
- Paires (main, straddle) → noires, croches (A/B) ou shuffles (A:B) selon `isSmall`
- `acc: "sharp"` → 尺♯, `orn: "u"` → suffixe `'`
- `repeatStart/repeatEnd` → `|:` / `:|`
- `choshi` → `@choshi`, `cellsPerDan / 2` → `@cells_per_dan`
- N'exporte pas encore `allRubyData` (proposition `::ruby` / conversion `::vocal`, voir `docs/kkml-format.md`)

## Séparation documentation humaine / agent

- `AGENTS.md` (racine) : contexte agent — roadmap, priorités, points ouverts, mesures, architecture du code. Ne pas déplacer vers `docs/`.
- `docs/` : documentation humaine uniquement (notation musicale, formats KKML et Portama, layout SVG). Ne pas y ajouter de statuts de tâche, TODO, mesures de calibrage ou références de commits.
- Mettre à jour la section « Validations en attente » et les statuts de phase lors de chaque changement fonctionnel.


## Détails de rendu (fonction render_cell) — déplacés depuis docs/notation.md

- Noire : `font-size = fs` (ou `int(fs*0.67)` si kuubanchi), baseline `y = cy + fs * 0.318` (depuis 2026-11-10 : le +7 en dur ne scalait pas hors fs=22), `text-anchor = middle`
- Croche, note principale : `font-size = effective_fs`, `y = cy + fs * 0.318`
- Croche, note à cheval : `font-size = int(effective_fs * 0.713)` (+15%), position `straddle_y` calculée sur `fs` de base (inchangée par `s`) ; horizontal : straddle centré sur la bordure droite (`straddle_x = cx + cell_w/2`, `straddle_y = cy + ss*0.318`) ; vertical : chevauche la bordure inférieure (`straddle_y = cy + cell_h/2 + ss_pos/3`) ; `y = straddle_y`
- Shuffle A:B (2 notes) : `sh = effective_fs * 0.8` (fs pleine si borne de chant `(`/`)`), clamp `min(sh, cell/2.9)` ; vertical : empilées à marges égales sur la hauteur de case (bbox CJK baseline−0,88em … baseline+0,12em) ; horizontal : côte à côte à marges égales. Shuffle N≥3 notes (A:B:C…) : `sh = 0,60` (n=3) / `0,52` (n>3) × effective_fs, même distribution
- 尺 entouré (noire, `@shaku_circled on`) : cercle SVG `r = effective_fs * 0.6325`, centre `(cx, cy+2)`, `stroke-width=1`
- 尺 entouré (croche, note principale) : même cercle `(cx, cy+2)`, dessiné avant le texte
- 尺 entouré (croche, note à cheval) : cercle `r = ss * 0.713`, centre `(straddle_x, cy+2)` en horizontal, `(cx, straddle_y - ss*0.35)` en vertical
- 下尺 : TOUJOURS entouré (indépendamment de `@shaku_circled`) : cercle `r = effective_fs * 0.6325`, centre `(cx, cy)` — recentré sur le glyphe au calibrage nov. 2026 (l'ancien `cy+2` décentrait vers le bas)
- Marques diacritiques : police serif, `font-size = int(effective_fs * 1.1)` (+10%). Positionnement : voir les deux modes ci-dessus (notes simples vs tokens multi-caractères avec text_w)
- uchi-utu : caractère ｀ (accent grave, U+FF40) en haut-droite
- 下老 : un seul `<text>` avec `textLength = effective_fs * 1.0`, `lengthAdjust="spacingAndGlyphs"`, `text-anchor` non spécifié (left). Techniques passées avec `text_w=effective_fs * 1.0`
- Positions hautes (イ尺, イ五, etc.) : un seul `<text>` avec `textLength = effective_fs * 1.2`, `lengthAdjust="spacingAndGlyphs"`. Techniques passées avec `text_w=effective_fs * 1.2`
- fs (font_size) par défaut = 22, cell_w = 52, cell_h = 58

## Offsets des marques diacritiques (TECHNIQUE_SUFFIXES) — déplacés depuis docs/notation.md

Calibrage Inkscape nov. 2026 (grille de test + こぐやで風節, てぃんさぐぬ花, 十九の春). Formules dans `_tech_char_pos` (kkml2svg.py) ; `_render_techniques` accepte `note_fs` = taille réelle de la note porteuse (pleine, croche à cheval `ss`, ou réduite par `s`). Baseline de la note : `base_y = cy + fs * 0.318`. Taille du glyphe : `tech_fs = int(fs * 1.1 * scale)`. Règle : l'encre du signe ne chevauche pas l'encre de la note.

- uchi-utu (`'`, alias `*`, glyphe ｀ U+FF40) : top-right, `tx = cx + 0.58·note_fs`, ancré sur le sommet de la note (`anchor: note-top`) : `ty = base_y − note_fs + 0.91·fs` — la marque descend chevaucher le coin haut-droit du kanji ; `scale=1.21`
- nuchi-utu (`"`, glyphe ゜ U+309C) : à droite de la note, mi-hauteur du kanji : `tx = cx + 1.125·note_fs`, `ty = base_y + 0.02·fs` ; `scale=1.21`
- kaki-utu (`^`, glyphe ⌝ U+231D natif, sans rotation) : top-right en retrait au-dessus de la note : `tx = cx + 0.63·note_fs`, `ty = base_y − 0.42·fs` ; `scale=0.91`
- aki-utu (`v`, glyphe V) et kachi-utu (`<`, glyphe ⌞ U+231E — plus ┗ U+2517) : bottom-left au contact du kanji : `tx = cx − 0.57·note_fs`, `ty = base_y + 0.44·fs`
- Token multi-caractères (`text_w` fourni, ex. 下老 / positions hautes) : top-right → ancre `start` en `cx` (la marque surplombe le caractère de droite) ; bottom-left → ancre `end` en `cx − 0.34·fs`

`'` et `^` ne partagent plus de position moyenne (calibrage nov. 2026 : ｀ descend chevaucher la note, ⌝ reste en retrait au-dessus). Les offsets horizontaux sont des fractions de `note_fs` : la marque suit le coin du kanji quelle que soit sa taille. Aucun souhou ne modifie les coordonnées de la note, sauf `s` qui réduit la taille à 67% sans déplacer le centre.

## Positionnement des syllabes vocales — déplacé depuis docs/notation.md

- Taille de police : SYLLABLE_FS = min(int(cell_h * 0.26), int(marker_w * 0.8)) ≈ 15px avec les valeurs par défaut (cell_w=52, cell_h=58, marker_w=26)
- Position x : centre de la colonne marker = `x + cell_w + marker_w / 2`
- Position y : `cy + cell_h/2 + cell_h*(j/n) + syllable_fs/3` (j = indice de la sous-partie dans la case, n = nombre d'éléments du token ; 1er élément au centre de la case)
- Couleur : gris foncé (#333)
- Police : serif (même que les notes)


## Sections de `docs/portama-format.md` à documenter (TODO déplacés)

- Structure du tableau `allRubyData` : 1 array par page, 1 ligne par dan, 3 unités double largeur par cellule. Description détaillée à documenter.
- Structure du tableau `allLyricsData` : `id`, `content`, `x`, `y`, `width`, `height`, `fontSize` — description détaillée à documenter.
- Mapping conversion restant à définir : orn `nu` → suffixe `n` (proposition ; `"` en place depuis 2026-11-04). ✅ yubii et vocalPosMarkers encodés depuis le 2026-11-19 (vocalPosMarkers : seules les cellules isSmall mid → `::vocal`, le reste ignoré avec info stderr).
- `choshi` + `chogen` → `@choshi` (chogen − 5 = demi-tons ; pas encore implémenté).
- Point ouvert : `repeatStart`/`repeatEnd`/`vocalRepStart`/`vocalRepEnd` ne rendent RIEN dans テスト節.pdf (dan 1, cases 13–19 : aucun graphique ni flèche), alors que d'autres pièces rendent des flèches dans la colonne marker. Le déclencheur exact du rendu des flèches reste à élucider.
- ✅ `kkml2pdf.py` (2026-11-19) : KKML → PDF multipage pour les layouts à format cm prédéfini (chindami/nomura/mega) — voir la section architecture `kkml2pdf.py` ci-dessous.
## Modèles de page — état (2026-11-15)

- ✅ SVG multipage (2026-10-02) : `@dans_per_page` / `-p` implémentés ; contrainte Portama 12 dans/page vérifiée sur かぎやで風節.pdf.
- ✅ Layout Nomura-ryu (2026-10-03) : portrait A4, cadre filet, 12 cases/dan, 7 dans/page — mesuré sur les scans Nomura-ryu (retirés du dépôt, droits d'auteur — voir `samples/nomura-ryu-pdf/README.md`), validé sur かぎやで風節 (3 pages : titre+6 / 7 / 6+couplets).
- ✅ Géométrie Nomura (2026-10-03) : 3 constantes primaires (cadre 559,3 × 745,9 pt, marge de dans M = 14,5 unique partout), tout dérivé — boucle vérifiée au pt près (e288f91…).
- ✅ Couplets nomura (2026-10-03) : 3 colonnes/dan virtuel calées sur la largeur de dan (eebf527, 1bbf95c) ; excédent sur pages suivantes dédiées (7 dans virtuels max/page), jamais de débordement du cadre, jamais de dan de musique perdu (3ec6aca). Validé sur cas limite 6 couplets (4 pages, p.4 couplets seuls).
- ✅ Ruby du titre (2026-10-03) : かぎやで風節.kkml titre phonétisé か《カ》｛ぎや｝《ヂャ》で《ディ》風《フウ》節《ブシ》 — base à tx inchangée, ruby collé à droite, centrage du dan virtuel préservé (42d6699).
- 🚧 (2026-11-10) Layout `tuto` (POC) : horizontal, canvas WxH fixe (`@tuto_block`, défaut 1280x720), 8 cases/dan et 7 dans/page (calibré sur la vidéo exemple https://www.youtube.com/watch?v=GvcZoeCbIPQ), page 1 = titre/accordage/infos seuls, ligne marker au-dessus de chaque dan si `::vocal` + `@marker on`. Reste : calage visuel fin (fs, marges) et SVG de référence d'un échantillon.
- 🚧 (2026-11-15) Layout `mega` (POC, demande utilisateur avec exemple PJ) : page A3 paysage (42 × 29,7 cm), **2 blocs horizontaux empilés** de chacun **32 dans × 12 cases** (64 dans/page, 768 cases, pagination auto `fichier-N.svg`). Ordre de lecture : bloc du haut d'abord, haut→bas et droite→gauche dans chaque dan, puis bloc du bas idem. Colonne marker = **1/2 case** à droite de chaque dan (`marker_w = cell_w/2`, forcée par `::vocal`, sinon `@marker`). **Medley** : chaque chanson = `::song <nom>` + `::tab` ; le nom est imprimé en 11 pt centré au-dessus des colonnes de la chanson dans chaque bloc (avec flèches d'association), et la dernière colonne de chaque chanson est complétée par des **cases vides (`-`, pas de tenuto)** pour que la chanson suivante commence sur une colonne suivante. **Titre global `@title` en colonne verticale en haut à droite, à droite de tous les blocs (marge droite)**, répété sur chaque page ; paroles verticales à gauche de la 1re page (largeur réservée partout). Géométrie dérivée de la page : `cell_h = (page_h − 2×MEGA_MARGIN − MEGA_BLOCK_GAP)/24`, `cell_w = largeur dispo/(32×1,5)`, `fs = 0,38×cell_h` (constantes MEGA_* dans `kkml2svg.py`, fonction `_render_mega`, rendu des dans repris de `_draw_vertical_tab`). Dans la PJ (A3 = 2 A4 assemblés, couture imparfaite au milieu, **31 colonnes visibles par bloc** dans le scan) : case ≈ 22 × 32,5 pt, marker ≈ 11,5 pt. Suites 26-42 (2026-11-15) : paroles paginées sur des **pages A3 dédiées** après les pages de tablature quand la largeur réservée dépasse 15 % de la grille (`MEGA_LYRICS_INLINE_MAX_RATIO`), avec la même structure de 2 blocs, repli obligatoire à la hauteur de bloc et **titre de chaque chanson en colonne verticale 「…」 gras fs 11 remonté au haut de bloc** ; hayashi ; en-têtes de couplets toujours 3 caractères pleine chasse, matérialisés par `_pad_inline_marker` ; marqueur ⚪︎ (U+26AA, +U+FE0E) reconnu comme marqueur de couplet. Reste : validation visuelle contre la PJ et calage fin (marges, gap, taille des noms de chansons).
- ✅ (2026-11-15) Layout `chindami` complet : page 23 × 15 cm paysage imposée (viewBox en pt), piles de 12 cases lues haut→bas droite→gauche, colonne marker ~1/2 case à droite de chaque pile, 15 piles/page (14 en p.1 quand le titre occupe sa colonne), `@musicno` écrit en HORIZONTAL fs 11 au sommet de la colonne titre et repoussant le titre de `fs + 8` pt (n° > 999 tronqué mod 1000, 0 non écrit), repli des paroles en sous-colonnes de hauteur de grille, pages dédiées paroles, textes verticaux en blocs `<text>` groupés (constantes `CHINDAMI_*`, fonction `_render_chindami`).
- ✅ (2026-11-19) Métadonnées de compatibilité Portama câblées de bout en bout : `@musicno @chogen @speed @rythm @rythm_mode` ajoutées à `META_KEYS` (tolérance `@cléValeur` collé — fix préfixe le plus long d'abord, `@rythm_mode0` ne matche plus `@rythm`), émises telles quelles par `portama2kkml.py` quand le champ JSON est présent (présence/absence préservée), et reconstruites par `portama_fields_from_meta()` (musicno → int, autres → chaînes) pour le futur `kkml2portama.py`. Round-trip vérifié sur les 8 échantillons (`tests/test_portama_meta.py`) ; `@musicno` reste affiché en chindami (mod 1000) ; le cleaner les conserve (ordre canonique, idempotent).
- ✅ (2026-11-19) `kkml2pdf.py` : PDF multipage pour les layouts à format cm prédéfini uniquement (chindami 23×15, nomura A4 21×29,7, mega A3 42×29,7) — chaîne `kkml2svg.render_svg` (liste de pages SVG en cm) → conversion page par page (moteur auto : rsvg-convert, inkscape, cairosvg) → fusion (auto : pypdf, pdfunite, gs) ; layouts libres refusés (exit 2, message explicite), MediaBox = taille cm du SVG. Tests : `tests/test_kkml2pdf.py` (garde layout, tailles cm, multipage, pipeline avec faux moteur + fusion pypdf, CLI). Bac à sable : ratios de page rendus 0,707 / 1,533 / 1,414 conformes (A4 portrait / 23×15 / A3 paysage).
- ⚪︎ (2026-11-19) Blocage pré-existant dans `kkml2svg` : `kkml2svg.py -l chindami` sur `samples/kkml/かぎやで風節.kkml` ne termine pas (> 60 s ; `安波節.kkml` en chindami : 0,00 s, 2 pages). À investiguer dans `_render_chindami` (repli/pagination des paroles ?). Indépendant de `kkml2pdf.py`.
- ✅ (2026-11-19) Assemblage PDF : `kkml2pdf.py` — kkml2svg (`render_svg`, liste de pages SVG en cm) → moteur SVG→PDF page à page (auto : rsvg-convert, inkscape, cairosvg) → fusion multipage (auto : pypdf, pdfunite, gs). L'embed des polices CJK reste du ressort du moteur SVG→PDF.
- ✅ (2026-11-19) Codage des doigtés (yubii) en KKML : suffixe ㊀㊁㊂㊃ (U+3280-U+3283) sur la note dans `::tab` (ex. `合㊀`) — jamais une position autonome (garde-fou + AVERTISSEMENT si token seul) ; variantes ㈠㈡㈢㈣ (U+3220-U+3223) normalisées. Rendu kkml2svg : glyphe à GAUCHE de la note dans la case, même baseline, fs ≈ 0,735 × fs note (`TECHNIQUE_SUFFIXES`, pos 'left', dx 0,91 — calibrage samples/portama-pdf/テスト節.pdf : note fs 17 à x=652, yubii fs 12,5 à x=636,5). portama2kkml : `cell.yubii` 1-4 et note PUA U+E041-E044 → suffixe en fin de token. Tests : `tests/test_yubii.py` (rendu, garde-fou, normalisation, mapping Portama, non-régression 7 échantillons).
- ✅ (2026-11-19) Conversion テスト節 (test bushi) fidèle à la correction manuelle de l'utilisateur (`samples/kkml/テスト節.kkml`, ajoutée au dépôt) : portama2kkml — PUA composites complétés selon docs/portama-format.md (E003 下老, E004 ロ上, E005 ロ中, E006 ロ尺, E007 イ合, E008 イ乙, E014 下尺, E015 ロ五, E016 イ老, E017 イ四, E018 イ上, E025 九, E026 イ尺, E027 イ工, E028 イ五) ; `acc` sharp/flat sur TOUTE note → suffixe ♯/♭ (cas spécial 尺♯ préservé) ; `vocalRepStart/End` → `(:` / `:)` ; paire à cheval seule (main vide) → `-/B` ; cellule terminale impaire conservée ; `vocalPosMarkers` → section `::vocal` (lignes paddées à `-`) : cellule principale → `(`/`)` nu, cellule à cheval mid seule → `.( `/`.)`, combinés en token nu (`()`) si les deux cellules de la paire ont un marqueur. Paires vides terminales retirées de `::tab` (restent dans `::vocal`). Échantillon テスト節-2 ajouté (dan 5 à 11 cellules : paires vides terminales avec marqueurs vocaux). Clés `vocalPosMarkers` observées : `top`/`mid`/`bot` (`bot`, pas `bottom` — テスト節-3.json dan 5 cellules 11/15, échantillon ajouté en portama-json) ; encodage ::vocal : top → `(`/`)` nu, mid → `.( `/`.)`, bot → `..(` /`..)` (nb de points = hauteur), combinés en token nu si la paire a aussi un marqueur principal. NB : l'éditeur graphique semblait ne placer que `mid`, mais des fichiers avec `top`/`bot` existent (observation utilisateur 2026-11-19). kkml2svg — ♯/♭ en suffixe sur toute note (`TECHNIQUE_SUFFIXES` pos 'top-right', dx 0,87, dy −0,2, scale 0,48 — calibrage テスト節.pdf), variantes 口+kanji → ロ+kanji, `⚪︎` (U+26AA+U+FE0E) → repos ◯, sélecteurs U+FE00-FE0F retirés, `#`→♯, `b`→♭. Tests : `tests/test_testbushi.py`. Correction manuelle révisée par l'utilisateur (2026-11-19) : E014 = 下尺 et E028 = イ五 confirmés (la doc avait raison), E030 = silence ◯, et les marqueurs vocaux des cellules principales (dan 1 cellules 21/23, dan 2 cellule 1) sont bien encodés en `(`/`)` dans `::vocal` — la correction révisée `samples/kkml/テスト節.kkml` correspond au convertisseur à l'identique après normalisation.
- ⚪︎ Raffinements nomura en réserve : marqueur ⚪︎ de couplet, taille/espacement des paroles, calligraphie du titre.
- ⚪︎ Raffinements supplémentaires de la mise en page nomura à définir plus tard (retours visuels utilisateur sur かぎやで風節 et 安波節 ; typiquement : ajustement fin du placement des couplets sur page dédiée, sous-colonnes marker, etc.).
- ⚪︎ Tester le rendu d'安波節 (6 couplets = 2 dans virtuels) pour valider la pagination multi-dans virtuels.
- ✅ Scans Nomura-ryu retirés du dépôt (droits d’auteur) : les 4 PDF de `samples/nomura-ryu-pdf/` supprimés ; les constantes mesurées restent consignées ci-dessous.

## Constantes de calibrage mesurées sur les PDF Portama (recherche)

**Pagination vérifiée (かぎやで風節.pdf, 2 pages)** : maximum 12 piles (dans) par page — page 1 = 12 séparateurs verticaux au pas de 60,9 pt, page 2 = 7 piles (12+7 = 19 dans). A4 paysage (841,89 × 595,28 pt), 12 cases/pile de 43,94 pt. Le titre vertical (fs 20) et l'accordage (fs 14) sont répétés sur chaque page.

Ces mesures (かぎやで風節.pdf, テスト節.pdf) servent au calibrage du rendu ; elles ne sont pas des spécifications utilisateur.

- Rendu PDF ruby STRICTEMENT LINÉAIRE : `top_caractère = 36,9 + 2,74 + 14,646 × unités` (58 caractères, résidu max 0,00 pt). Unité = hauteur_case/3 = 43,94/3 = 14,646 pt.
- Grille stricte de 3 lignes ruby par case (fractions 0,06 / 0,40 / 0,73), aucun arrimage syllabe↔note — champ texte vertical libre, placement à la demi-unité près (fractions 0,06–0,90).
- Ruby : police IPAexMincho 11 pt (ratio vs note fs 17 = 0,65 ; ratio vs hauteur de case = 0,25). Le JSON dit `lyricsFontSize: "10pt"` mais le ruby rendu est à 11 pt.
- Colonne marker : sous-colonne de 24,1 pt à droite de chaque pile (largeur pile 52,4 = 28,3 notes + 24,1 marker). Ruby dessiné à +3,7 pt du bord gauche de la sous-colonne marker.
- Avance par caractère pleine largeur : 14,646 pt (1,33 × fs ruby), quelle que soit l'appartenance au token.
- Petits kana : +12,99 pt sous le caractère précédent (tuck optique de 1,65 pt) et +1,12 pt à droite ; le caractère suivant reprend sa position de grille. Mesuré sur 17 instances, identique au centième. Portama ne tuck que les petits kana, sans notion de syllabe.
- ー (chōonpu) absent du corpus : comportement non mesuré.
- Géométrie du PDF (A4 paysage, TCPDF) : cadre 28,3–819,2 × 28,3–575,4 pt ; piles au pas de 60,9 pt, cadre 52,4 pt (notes 28,3 + marker 24,1) ; 12 piles/page, 12 cases/pile, hauteur 43,94 pt ; notes fs=17, straddle fs=13 ; ratios marker/notes 0,85 (nous 0,5), cell_h/notes 1,55 (nous 1,12), fs/cell_h 0,39 (nous 0,38).
- Géométrie fine des marques (テスト節.pdf) : orn fs 14 (dx +6,16, dy +4,03 ; isSmall 10, dx +8,07) ; acc fs 14 (dx −2,84, dy +4,02 ; isSmall 10, dx −4,84) ; yubii fs 12,5 (dx −15,46, dy +0,93, colonne dédiée à gauche) ; ○/□ fs 9 (marker +14,8 pt, dy +3,3).
- Polices embarquées : Untitled1 (Type0, Identity-H, upem 1024 ; CID = codepoint PUA) pour les notes, IPAexMincho pour le texte. Contours des glyphes de テスト節.pdf extraits (chemins SVG upem 1024) — disponibles pour la rénovation du rendu des ornements.
- Constantes pour une éventuelle section `::ruby` : ruby_fs/note_fs = 0,65 ; avance ligne = cell_h/3 ; tuck petit kana = 1,18 × fs (chez nous : `SYLLABLE_SP` = 0,9 × syllable_fs entre syllabes, `step` = 1,15 × syllable_fs entre caractères combinants).

## Constantes de calibrage mesurées sur les scans Nomura-ryu (recherche)

Sources : scans du recueil « 琉球流工工四上巡り » — かぎゃでゅ風節 (3 pages), 後にゆく (2 pages), 恩納節 (2 pages) — rééditions scannées de planches calligraphiées (~1930), conservés hors du dépôt (droits d’auteur).

- Page physique : A4 portrait, **5 dan/page** (largeur de bande ~119,5–121,8 pt, la dernière parfois réduite).
- Grille de cases **dans chaque dan** : cases empilées le long de la direction de lecture (haut→bas), séparateurs au pas très stable de **245 px ≈ 60,6 pt** (mesuré sur 50+ intervalles, dispersion 244–247 px). Cases pleines : ~12 par dan courant (max observé 12, souvent moins en fin de morceau), séparées de filets pleine largeur de dan.
- Case : hauteur 245 px ≈ **60,6 pt**, largeur ~128 px ≈ **31,7 pt** — plus haute que large (ratio ≈ 1,9). Le dan contient une sous-colonne **notes** + une sous-colonne **marker** de même largeur (~128 px), séparées par un filet vertical court (voir filets internes détectés à ~135/260/317/381/451 px dans 後に屋節-2) ; groupes de cases + marker séparés par des **marges blanches** entre dans.
- Titre : vertical, en haut à droite de la **première page** de chaque morceau (position à mesurer finement ; non détectée automatiquement sur ces scans).
- Paroles : sur la **dernière page**, à gauche des dernières notes, dans la bande marker (phonétique, boucles, indications de chant spécifiques Nomura-ryu) — bandes marker très chargées.
- Ordre de lecture : droite→gauche (dan 1 = colonne la plus à droite), cases haut→bas dans chaque dan.
- Implications modèle de page : pagination par **nombre de cases par dan** (12 par dan, systématique), **jusqu'à 7 dan/page** ; lorsque nécessaire un dan est retiré (décalé) pour placer le titre et/ou les paroles. Structure différente de Portama (paysage, piles horizontales de cases).
- Spécification utilisateur (à considérer comme la règle, les mesures ci-dessus n'étant que 3 exemples) : chaque page est encadrée par un **filet** (seul le numéro de page est à l'extérieur) — utiliser ce filet comme origine pour le placement relatif de tous les objets. Page toujours portrait. Dans toujours à 12 cases. Composition manuelle (~1930) d'une régularité exceptionnelle.
**Structures exactes vérifiées (description de droite à gauche, haut→bas = ordre de lecture japonais)** :
- かぎやで風節 (3 pages) : p1 = titre + 6 dans ; p2 = 7 dans ; p3 = 6 dans (les 3 dernières cases du 6e dan sont vides mais présentes) + paroles.
- 恩納節 (2 pages) : p1 = titre + 6 dans ; p2 = 6 dans + paroles.
- 後に屋節 (2 pages) : p1 = titre + 6 dans ; p2 = 4 dans (5 cases vides à la fin du 4e dan) + couplets + titre de la chanson suivante (équivalent 1 dan, à ignorer) + couplets suivants (équivalent 1 dan, à ignorer).

En conséquence : le titre occupe l'équivalent d'**1 dan de large** en haut à droite (colonne la plus à droite) ; les paroles occupent l'équivalent d'**1 colonne de dan** en bas à gauche de la dernière page ; une page pleine = 7 dans ; page avec titre ou paroles = 6 dans utiles ; les deux = 5 dans utiles. Cases vides en fin de morceau : présentes mais non remplies.
- Couplets : débutent par un marqueur générique ⚪︎ (un par couplet) ; coût variable — 1 dan en général, jusqu'à 2 dans si les couplets sont très longs.
- Variations d'éditeur : quelques libéralités possibles par rapport à la structure ; le modèle de page doit s'en tenir aux basiques communs à tous les morceaux et ignorer les rares variantes.
**Vérification sur les pages supplémentaires (野村流工工四上巻, fichier temporaire « glissés », 11 pages)** : assemblage des 5 bandes par page en portrait confirme — filet de cadre page (top/bottom ~189 et ~3260 px ≈ 48 pt des bords), grille de cases **12 par dan** (13 filets au pas 245 px, ex. dan complet : 261→507→752→997→1241→1486→1731→1976→2221→2466→2711→2956→3201), sous-colonne marker à droite de chaque dan, plusieurs dans par page (5-7 détectés selon pages, cohérent avec titre/paroles/couplets consommant des colonnes). L'assemblage des bandes JPEG par page PDF est nécessaire pour la mesure : chaque bande PDF (~841,8 × ~121 pt) est une **tranche horizontale** de la page portrait, pas un dan complet (correction de l'interprétation initiale).
