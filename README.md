# HelpTrip — packs pays

Contenu hors ligne de l'application HelpTrip : un fichier JSON par pays
(devise, numéros d'urgence, ambassade, pourboire, douane, phrases essentielles).

Pays disponibles : Japon (`jp`), Italie (`it`), Thaïlande (`th`), Espagne (`es`), Portugal (`pt`).

Les phrases ont été écrites puis relues par l'IA, et n'ont pas encore été relues par des locuteurs natifs.

Fichiers servis par jsDelivr, par exemple :
https://cdn.jsdelivr.net/gh/theongv/helptrip-packs@main/jp.json

Format : voir `lib/models/pack_content.dart` dans le code de l'application.
Les informations pratiques sont données à titre indicatif : vérifiez-les
auprès des sources officielles (France Diplomatie, douane.gouv.fr) avant de partir.

## Tester sans toucher au manifeste public

Ne jamais modifier `versions.json` sur `main` pour un test : il est lu par tous les
utilisateurs. Voir `CONTRIBUTING.md` (manifeste local ou branche de test séparée).

## Publier

Ne jamais pousser les packs à la main : utiliser le script, qui vérifie les packs,
refuse un contenu modifié sans nouvelle version, puis écrit `versions.json` (le manifeste
lu par l'app) avec le hash du commit des packs.

    python3 publish.py --dry-run     # vérifier
    python3 publish.py -m "Pack JP : …"   # publier

Détails en tête de `publish.py`.

