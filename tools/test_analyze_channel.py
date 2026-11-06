import csv
import json
from pathlib import Path
import tempfile
import unittest
from analyze_channel import metric, normalize, safe_cell, write_results


class AcquisitionFormattingTests(unittest.TestCase):
    def test_missing_metrics_are_not_zero(self):
        item = normalize({'id': 'P337IKPsixQ', 'view_count': 0, 'duration': 14.5})
        self.assertEqual(item['views'], 0)
        self.assertIsNone(item['likes'])
        self.assertEqual(item['duration_seconds'], 14.5)
        for invalid in [True, -1, float('nan'), 1.5, '1000']:
            self.assertIsNone(metric(invalid))

    def test_csv_cannot_execute_untrusted_title_as_formula(self):
        self.assertEqual(safe_cell(' =HYPERLINK("x")'), '\' =HYPERLINK("x")')
        self.assertEqual(safe_cell('Curiosidade'), 'Curiosidade')

    def test_only_allowlisted_metadata_persists(self):
        item = normalize({'id': 'P337IKPsixQ', 'title': '=malicious()', 'url': 'https://signed.example/token',
                          'subtitles': {'pt': [{'url': 'https://signed.example/secret'}]}, 'transcript': 'private'})
        payload = {'source': 'fixture', 'collected_at_utc': '2026-11-05T00:00:00+00:00', 'videos': [item], 'attempts': []}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_results(root, payload)
            saved = (root / 'metadata.json').read_text()
            self.assertNotIn('signed.example', saved)
            self.assertNotIn('transcript', saved)
            self.assertEqual(json.loads(saved)['videos'][0]['caption_languages'], ['pt'])
            with (root / 'metrics.csv').open(encoding='utf-8-sig', newline='') as f:
                row = next(csv.DictReader(f))
            self.assertEqual(row['likes'], '')
            self.assertTrue(row['title'].startswith("'="))
            self.assertIn('FIXTURE LOCAL', (root / 'report.md').read_text())


if __name__ == '__main__':
    unittest.main()
