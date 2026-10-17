import csv
import tempfile
import unittest
from pathlib import Path
from scripts.validate_data import SCHEDULE, MOVIES, validate, valid_time


class ValidationTests(unittest.TestCase):
    def check_rows(self, header, rows, kind='schedule'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            with path.open('w', encoding='utf-8-sig', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerows(rows)
            return validate(path, kind)

    def test_overnight_time(self):
        self.assertTrue(valid_time('~26:38', end=True))
        self.assertFalse(valid_time('26:60', end=True))
        self.assertFalse(valid_time('~10:00'))

    def test_seats_and_index_independent_duplicates(self):
        row = ['서울', '강남', '23:00', '~25:00', '2D', '1관', '0', '100']
        count, errors, warnings = self.check_rows(['', *SCHEDULE], [['0', *row], ['1', *row]])
        self.assertEqual(count, 2)
        self.assertFalse(errors)
        self.assertTrue(any('동일' in w for w in warnings))
        row[-2] = '101'
        self.assertTrue(self.check_rows(SCHEDULE, [row])[1])

    def test_empty_wrong_header_and_ragged(self):
        self.assertTrue(self.check_rows(SCHEDULE, [])[1])
        self.assertTrue(self.check_rows(['wrong'], [])[1])
        self.assertTrue(self.check_rows(SCHEDULE, [['서울']])[1])

    def test_movie_flags(self):
        row = [''] * len(MOVIES)
        row[MOVIES.index('title')] = '테스트'
        for name in ['mx4d', 'dolby', 'atmos', 'mega_only']:
            row[MOVIES.index(name)] = '0'
        self.assertFalse(self.check_rows(MOVIES, [row], 'movies')[1])
        row[MOVIES.index('dolby')] = '2'
        self.assertTrue(self.check_rows(MOVIES, [row], 'movies')[1])


if __name__ == '__main__':
    unittest.main()
