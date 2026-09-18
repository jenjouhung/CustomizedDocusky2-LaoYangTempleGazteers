import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from markup import parse_text
import packages

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = json.loads((PROJECT_ROOT / 'dataset' / 'acceptance.json').read_text(encoding='utf-8'))


class MarkupTests(unittest.TestCase):
    def test_text_offsets_entities_and_alias(self):
        parsed = parse_text('𠮷比丘<person Term="揚法師" RefId="A1">道揚</person>&amp;後', {'person'})
        self.assertEqual(parsed['text'], '𠮷比丘道揚&後')
        tag = parsed['tags'][0]
        self.assertEqual(parsed['text'][tag['start']:tag['end']], '道揚')
        self.assertEqual(tag['term'], '揚法師')
        self.assertEqual(parse_text('A&B', {})['text'], 'A&B')

    def test_invalid_markup(self):
        for raw in ['<person>甲</person>', '<person term=" ">甲</person>',
                    '<person term="甲" Term="乙">甲</person>', '<person term="甲">',
                    '<person term="甲"><person term="乙">乙</person></person>',
                    '<unknown term="甲">甲</unknown>', '<!DOCTYPE x><person term="甲">甲</person>',
                    '<person term="甲"/>']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_text(raw, {'person'})

    def test_real_version_and_document_counts(self):
        original = packages.DATA
        source = packages.ROOT / ACCEPTANCE['sources']['marked']
        with tempfile.TemporaryDirectory() as tmp:
            packages.DATA = Path(tmp) / 'data'
            try:
                meta = packages.import_file(source)
                base = packages.DATA / meta['id']
                self.assertEqual(meta['count'], ACCEPTANCE['expected']['recordCount'])
                facets = packages.read(base / 'facets.json')
                expected = ACCEPTANCE['expected']['tagFacets']
                for name, values_expected in expected.items():
                    values = facets['tag:'+name]
                    self.assertEqual(len(values), values_expected['termCount'])
                    self.assertEqual(len(set(n for ids in values.values() for n in ids)), values_expected['documentCount'])
                    self.assertTrue(all(len(ids)==len(set(ids)) for ids in values.values()))
                # Independent oracle: reconstruct every indexed character from the plain text.
                oracle = {}
                for n in range(ACCEPTANCE['expected']['recordCount']):
                    text = packages.read(base/'texts'/f'{n}.json')['text']
                    for pos, char in enumerate(text):
                        oracle.setdefault(char, {}).setdefault(str(n), []).append(pos)
                self.assertEqual(packages.read(base/'index.json'), oracle)
                packages.verify(packages.DATA)
            finally:
                packages.DATA = original
