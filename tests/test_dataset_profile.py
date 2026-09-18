import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from config import CONFIG, PROFILE, derive_config, load_profile
from inspect_excel import inspect
from site_builder import render_index

ACCEPTANCE = json.loads((ROOT / "dataset" / "acceptance.json").read_text(encoding="utf-8"))


class DatasetProfileTests(unittest.TestCase):
    def test_profile_is_valid_and_roles_are_derived_by_name(self):
        self.assertEqual(load_profile(), PROFILE)
        names = [field["name"] for field in PROFILE["fields"]]
        self.assertEqual(CONFIG["key"], names.index(PROFILE["roles"]["key"]))
        self.assertEqual(CONFIG["text"], names.index(PROFILE["roles"]["fullText"]))
        self.assertEqual(CONFIG["facets"], [names.index(name) for name in PROFILE["roles"]["metadataFacets"]])

    def test_reordering_fields_recalculates_indexes(self):
        profile = copy.deepcopy(PROFILE)
        profile["fields"] = list(reversed(profile["fields"]))
        config = derive_config(profile)
        names = [field["name"] for field in profile["fields"]]
        self.assertEqual(config["titleField"], names.index(profile["roles"]["title"]))
        self.assertEqual(config["tieBreak"], names.index(profile["roles"]["sort"]["tieBreaker"]))

    def test_site_metadata_renders_from_profile(self):
        source = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        rendered = render_index(source)
        self.assertIn(f'<title>{PROFILE["site"]["title"]}</title>', rendered)
        self.assertIn(PROFILE["site"]["description"], rendered)
        self.assertIn(PROFILE["site"]["canonicalUrl"], rendered)

    def test_excel_inspection_exposes_adaptation_evidence(self):
        report = inspect(ROOT / ACCEPTANCE["sources"]["marked"], example_limit=1)
        self.assertEqual(report["rowCount"], ACCEPTANCE["expected"]["recordCount"])
        self.assertEqual(report["columnCount"], ACCEPTANCE["expected"]["columnCount"])
        self.assertEqual(report["blockingIssues"], [])
        self.assertIn(PROFILE["roles"]["key"], report["candidates"]["uniqueKeys"])
        full_text = next(field for field in report["fields"] if field["name"] == PROFILE["roles"]["fullText"])
        self.assertGreater(full_text["averageCharacters"], 0)
        self.assertGreaterEqual(full_text["maxCharacters"], full_text["averageCharacters"])


if __name__ == "__main__":
    unittest.main()
