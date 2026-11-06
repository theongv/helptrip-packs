#!/usr/bin/env python3
"""Tests de la validation des phrases de publish.py : python3 -B test_publish.py

Les packs de test sont écrits dans un dossier temporaire, hors du dépôt.
"""

import json
import tempfile
import unittest
from pathlib import Path

from publish import PublishError, validate_pack


def pack(language, **changes):
    content = {
        "format": 1,
        "countryCode": "LU",
        "version": "2026-11-06",
        "languageCode": language,
        "currency": {},
        "countryInfo": {},
        "phrases": [],
    }
    content.update(changes)
    return content


class ValidatePhrases(unittest.TestCase):
    def validate(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lu.json"
            path.write_text(json.dumps(content), encoding="utf-8")
            return validate_pack(path)

    def test_a_francais_sans_phrases_accepte(self):
        self.assertEqual(self.validate(pack("fr-LU"))["phrases"], [])

    def test_b_autre_langue_sans_phrases_refuse(self):
        with self.assertRaisesRegex(PublishError, "aucune phrase"):
            self.validate(pack("es-MX"))

    def test_c_phrases_non_vides_accepte(self):
        phrases = [{"category": "emergency", "french": "Au secours !", "translation": "Ayuda"}]
        self.assertEqual(self.validate(pack("es-MX", phrases=phrases))["phrases"], phrases)

    def test_d_cle_phrases_absente_refuse(self):
        content = pack("fr-LU")
        del content["phrases"]
        with self.assertRaisesRegex(PublishError, r"champs manquants \['phrases'\]"):
            self.validate(content)

    def test_e_francais_phrases_pas_une_liste_refuse(self):
        with self.assertRaisesRegex(PublishError, "aucune phrase"):
            self.validate(pack("fr-LU", phrases="abc"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
