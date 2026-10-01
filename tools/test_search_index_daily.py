import datetime as dt
import unittest
from search_index_daily import needs_build


class DailyGateTests(unittest.TestCase):
    def test_same_beijing_day_skips_even_if_utc_dates_differ(self):
        now = dt.datetime.fromisoformat("2026-10-01T10:00:00+00:00")
        self.assertFalse(needs_build({"built": "2026-09-30T17:00:00Z"}, now))

    def test_new_beijing_day_allows_build(self):
        now = dt.datetime.fromisoformat("2026-10-01T16:00:00+00:00")
        self.assertTrue(needs_build({"built": "2026-10-01T15:59:59Z"}, now))

    def test_first_publication_today_skips_the_evening_repeat(self):
        now = dt.datetime.fromisoformat("2026-10-01T15:20:00+00:00")
        self.assertFalse(needs_build({"built": "2026-10-01T06:20:00Z"}, now))

    def test_invalid_timestamp_fails_closed(self):
        with self.assertRaises(ValueError):
            needs_build({"built": "not-a-date"})
        with self.assertRaises(ValueError):
            needs_build({"built": "2026-10-01T06:20:00"})


if __name__ == "__main__":
    unittest.main()
