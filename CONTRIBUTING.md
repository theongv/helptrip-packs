# Contribuer aux packs HelpTrip

## Règle n° 1 : ne jamais toucher au manifeste public pour un test

`versions.json` sur la branche `main` est lu par **toutes les installations de l'app**
(raw.githubusercontent.com le sert en quelques secondes à quelques minutes). Le modifier,
même « juste le temps d'un test », change ce que reçoivent les vrais utilisateurs :
un pack plus ancien peut leur être installé, ou une mise à jour légitime masquée.

Interdit sur `main` :
- éditer `versions.json` à la main ;
- pointer un pays vers un ancien commit pour forcer un écart de version ;
- lancer `publish.py` pour autre chose qu'une vraie publication.

`versions.json` sur `main` ne change **que** via `python3 publish.py`, pour publier une
vraie correction ou un nouveau pack.

Incident à l'origine de cette règle (06/10/2026) : pour tester la mise à jour, le manifeste
public a été pointé sur l'ancienne version du pack Espagne (commit `2a220b8`), puis annulé
(`d954dd0`). Pendant ce temps, tout nouvel utilisateur de l'Espagne recevait l'ancien pack.

## Tester avec une ancienne version d'un pack

Choisir l'une des deux méthodes. Aucune ne modifie `main`.

### A. Manifeste local (recommandé)

Récupérer l'ancien pack depuis l'historique et le servir depuis le Mac :

    mkdir -p /tmp/packs-test/aaaaaaa /tmp/packs-test/main
    git show <ancien_commit>:es.json > /tmp/packs-test/aaaaaaa/es.json
    cp *.json /tmp/packs-test/main/        # repli @main pour les autres pays
    # manifeste de test qui annonce l'ancienne version, au faux commit "aaaaaaa"
    cat > /tmp/packs-test/versions.json <<'JSON'
    {"format": 1, "packs": {"ES": {"version": "<ancienne_version>", "commit": "aaaaaaa"}}}
    JSON
    python3 -m http.server 8787 --directory /tmp/packs-test

Le champ `commit` doit être un hash de 7 à 40 caractères hexadécimaux, sinon l'app ignore
l'entrée : d'où le nom de dossier `aaaaaaa`, qui en a la forme.

Puis lancer l'app sur ce serveur (10.0.2.2 = le Mac vu depuis l'émulateur) :

    flutter run --dart-define=PACK_MANIFEST_URL=http://10.0.2.2:8787/versions.json \
                --dart-define=PACK_BASE_URL=http://10.0.2.2:8787/main/ \
                --dart-define='PACK_PINNED_URL=http://10.0.2.2:8787/{commit}/{file}'

Pour simuler la publication d'une version plus récente, remplacer le `versions.json` local.
Pour simuler un échec réseau, arrêter le serveur ou passer l'émulateur en mode avion.

### B. Branche de test séparée

    git switch -c test-rollback
    # modifier versions.json sur cette branche uniquement, puis :
    git push origin test-rollback

et lancer l'app avec
`--dart-define=PACK_MANIFEST_URL=https://raw.githubusercontent.com/theongv/helptrip-packs/test-rollback/versions.json`.

Après le test : supprimer la branche (`git push origin --delete test-rollback` puis
`git branch -D test-rollback`) et revenir sur `main` sans y fusionner quoi que ce soit.

## Publier

Voir l'en-tête de `publish.py` et le README. Toujours `python3 publish.py --dry-run` d'abord.
