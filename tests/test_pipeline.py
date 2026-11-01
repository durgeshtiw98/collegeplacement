import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from pipeline import analyze, load_data, percent, ROOT


class MetricsTest(unittest.TestCase):
    def test_zero_denominator(self):
        self.assertIsNone(percent(0, 0))

    def test_duplicate_application_does_not_double_count_student_placement(self):
        data, issues, errors = load_data(ROOT/'data/raw')
        original = analyze(data, issues, errors)
        data['Applications'] += data['Applications']
        duplicate = analyze(data, [], [])
        self.assertEqual(original['placed_eligible_students'], duplicate['placed_eligible_students'])
        self.assertEqual(original['placement_percentage'], duplicate['placement_percentage'])

    def test_orphan_reference_blocks_publication(self):
        data, issues, errors = load_data(ROOT/'data/raw')
        data['Applications'][0]['Student_ID'] = 'NONEXISTENT'
        analyze(data, issues, errors)
        self.assertTrue(any('unresolved Student_ID' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
