#!/usr/bin/env python3
"""Publication des packs HelpTrip (à lancer depuis la racine du dépôt helptrip-packs).

Usage :
    python3 publish.py --dry-run       # vérifie tout, n'écrit et ne pousse rien
    python3 publish.py                 # vérifie, committe, écrit le manifeste, pousse
    python3 publish.py -m "Pack JP : nouvelle astreinte"   # message du commit des packs

Ce que fait le script, dans l'ordre :
  1. Valide chaque pack (xx.json) : JSON lisible, champs obligatoires, code pays
     identique au nom du fichier, version au format AAAA-MM-JJ ou AAAA-MM-JJ.N.
  2. Compare chaque pack à la version publiée dans versions.json. ÉCHEC si le contenu
     a changé sans que "version" soit augmentée : l'app ne proposerait jamais la
     correction aux utilisateurs. Échec aussi si la version a baissé.
  3. Committe les packs modifiés, puis écrit versions.json avec le hash de ce commit
     (adresse jsDelivr immuable @<hash>), le committe, et pousse la branche courante.

Pour augmenter une version : "2026-10-05.2" → "2026-10-05.3" le même jour,
ou "2026-10-06" un autre jour. La révision est comparée comme un nombre (.9 < .10).

L'app lit le manifeste sur raw.githubusercontent.com/theongv/helptrip-packs/main/
versions.json et télécharge chaque pack sur
cdn.jsdelivr.net/gh/theongv/helptrip-packs@<commit>/<code>.json.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = Path("versions.json")
PACK_FILE = re.compile(r"^[a-z]{2}\.json$")
VERSION = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:\.(\d{1,6}))?$")
REQUIRED = ["format", "countryCode", "version", "languageCode", "currency",
            "countryInfo", "phrases"]


class PublishError(Exception):
    pass


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise PublishError(f"git {' '.join(args)} : {result.stderr.strip()}")
    return result


def parse_version(text):
    """(date, révision) comparable, ou None si illisible (comme PackVersion dans l'app)."""
    match = VERSION.match(text.strip()) if isinstance(text, str) else None
    if not match:
        return None
    year, month, day = (int(match.group(i)) for i in (1, 2, 3))
    try:
        date = datetime.date(year, month, day)
    except ValueError:
        return None
    return (date, int(match.group(4) or 0))


def validate_pack(path):
    """Renvoie le pack lu, ou lève PublishError avec la raison."""
    try:
        pack = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PublishError(f"{path} : JSON invalide ({error})")
    if not isinstance(pack, dict):
        raise PublishError(f"{path} : objet JSON attendu")
    missing = [key for key in REQUIRED if key not in pack]
    if missing:
        raise PublishError(f"{path} : champs manquants {missing}")
    if pack["format"] != 1:
        raise PublishError(f"{path} : format {pack['format']} inconnu")
    expected = path.stem.upper()
    if pack["countryCode"] != expected:
        raise PublishError(f"{path} : countryCode {pack['countryCode']} au lieu de {expected}")
    if parse_version(pack["version"]) is None:
        raise PublishError(f"{path} : version illisible « {pack['version']} »")
    if not isinstance(pack["phrases"], list) or not pack["phrases"]:
        raise PublishError(f"{path} : aucune phrase")
    return pack


def load_manifest():
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("packs", {})
    except json.JSONDecodeError as error:
        raise PublishError(f"{MANIFEST} illisible ({error})")


def published_content(commit, path):
    result = git("show", f"{commit}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser(description="Publie les packs HelpTrip.")
    parser.add_argument("--dry-run", action="store_true", help="vérifier sans rien écrire")
    parser.add_argument("-m", "--message", default="Mise à jour des packs")
    args = parser.parse_args()

    packs = sorted(p for p in Path(".").iterdir() if PACK_FILE.match(p.name))
    if not packs:
        raise PublishError("aucun pack (xx.json) dans ce dossier")
    manifest = load_manifest()

    # 1 et 2 : validation et contrôle des versions
    changed, entries = [], {}
    for path in packs:
        pack = validate_pack(path)
        code, version = pack["countryCode"], pack["version"]
        published = manifest.get(code)
        if published is None:
            print(f"  {code} {version} : nouveau pack")
            changed.append(path)
            entries[code] = {"version": version}
            continue

        old_version = parse_version(published.get("version"))
        new_version = parse_version(version)
        old_content = published_content(published.get("commit", ""), path.name)
        same_content = old_content == path.read_text(encoding="utf-8")

        if same_content:
            if version != published["version"]:
                raise PublishError(f"{code} : contenu identique mais version modifiée")
            entries[code] = published  # inchangé : on garde son commit
            continue
        if old_version is not None and new_version <= old_version:
            raise PublishError(
                f"{code} : contenu modifié sans augmenter la version "
                f"({version}, déjà publiée : {published['version']}). "
                "Les utilisateurs ne recevraient jamais la correction."
            )
        print(f"  {code} : {published['version']} → {version}")
        changed.append(path)
        entries[code] = {"version": version}

    if not changed and set(manifest) == set(entries):
        print("Rien à publier : packs et manifeste sont à jour.")
        return
    if args.dry_run:
        print(f"Vérification réussie ({len(changed)} pack(s) à publier). Rien n'a été écrit.")
        return

    # 3 : commit des packs, manifeste avec le hash de ce commit, push
    git("add", *[p.name for p in changed])
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-q", "-m", args.message)
    commit = git("rev-parse", "HEAD").stdout.strip()
    for path in changed:
        # Le commit référencé doit contenir exactement ce contenu
        if published_content(commit, path.name) != path.read_text(encoding="utf-8"):
            raise PublishError(f"{path} : contenu différent dans le commit {commit[:7]}")
        entries[path.stem.upper()]["commit"] = commit

    MANIFEST.write_text(
        json.dumps({"format": 1, "packs": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    git("add", MANIFEST.name)
    git("commit", "-q", "-m", f"Manifeste : packs au commit {commit[:7]}")
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    git("push", "-q", "origin", branch)
    print(f"Publié sur {branch} : {len(changed)} pack(s), commit {commit[:7]}.")


if __name__ == "__main__":
    try:
        main()
    except PublishError as error:
        print(f"ÉCHEC : {error}", file=sys.stderr)
        sys.exit(1)
