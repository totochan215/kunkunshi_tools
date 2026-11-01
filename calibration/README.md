# Références de calibrage (HORS du dépôt public — droits d'auteur)

Les scans de recueils imprimés (chindami-kunkunshi, nomura-ryu, songbook
Paris Sanshin Club) ne figurent PAS dans ce dépôt. Ils servent uniquement à
calibrer les constantes des layouts (mesures consignées dans AGENTS.md).

Emplacement privé : Google Drive de thomas.kochert@gmail.com

- Dossier « chindami-kunkunshi » :
  https://drive.google.com/drive/folders/1-hx9uiqK3gIGtgPyQqqXnqTMaJ2nRmhq
  (工工四百選集(茶色)-p08…p15.pdf — pages extraites du recueil, morceaux n°1-3)
- Dossier « nomura-ryu » :
  https://drive.google.com/drive/folders/1Kbhv5rDXGLeslFqz8uuAexQP-FtKS7Jl
  (野村流工工四上巻-かぐやで風節.pdf, -後に屋節.pdf, -意綺節.pdf, -misc.pdf ;
   + scan complet 野村流工工四上巻.pdf de Paris Sanshin Club, 90 Mo)
- Dossier « songbook-paris-sanshin-club » (dossier parent id 1_bT0Sci9Bv6nFadxzFPi9N9shlc_raYO) :
  SONGBOOK PARIS SANSHIN CLUB 202202252300-p4…p7.pdf (pages scannées du songbook)

Sources amont (Paris Sanshin Club, paris.sanshin.club@gmail.com) :
- 工工四百選集(茶色).pdf / (緑).pdf : dossier 1EHL1e3a5qsM_-j9eAr9DMZ6SrKGHBVZ3
  https://drive.google.com/drive/folders/1EHL1e3a5qsM_-j9eAr9DMZ6SrKGHBVZ3

## Split des PDF complets en pages

Script : `calibration/split_pdf.py` (dépendance perso `pypdf`, hors pipeline).

    python3 calibration/split_pdf.py /chemin/工工四百選集(茶色).pdf /sortie/chindami/ -p chindami-tea

Produit `<prefix>-pNNN.pdf` (N = page PDF, 1-based) + `<prefix>-manifest.json`
avec deux champs clés : `page_pdf` (automatique) et `page_imprimee` (à
corriger à la main — la page imprimée peut différer de la page PDF).

Workflow index : déposer le PDF complet dans le dossier Drive idoine, splitter
en local, uploader les pages dans le même dossier, puis indiquer ici les
`page_pdf` portant l'index de chaque recueil ; seules ces pages seront OCRisées
pour construire l'index (champ `titre_ocr` à ajouter au manifeste).
