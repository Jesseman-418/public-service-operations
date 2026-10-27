import sys,unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from analyze import prepare,analyze,bootstrap_median_ci

def sample():
    return pd.DataFrame([
      {"created_date":"2026-01-01T00:00:00","closed_date":"2026-01-02T00:00:00","complaint_type":"Noise","borough":"QUEENS"},
      {"created_date":"2026-01-02T00:00:00","closed_date":"2026-01-05T00:00:00","complaint_type":"Heat","borough":"QUEENS"},
      {"created_date":"2026-01-03T00:00:00","closed_date":"2026-01-03T12:00:00","complaint_type":"Noise","borough":"BROOKLYN"},
      {"created_date":"2026-01-03T00:00:00","closed_date":None,"complaint_type":"Heat","borough":"BROOKLYN"},
    ])

class AnalysisTests(unittest.TestCase):
    def test_open_and_invalid_rows_are_excluded(self):
        d=prepare(sample()); self.assertEqual(len(d),3); self.assertTrue((d.response_hours>=0).all())
    def test_bootstrap_interval_contains_median(self):
        x=[1,2,3,4,5]; lo,hi=bootstrap_median_ci(x,iterations=200); self.assertLessEqual(lo,3); self.assertGreaterEqual(hi,3)
    def test_groups_and_caveats_returned(self):
        r=analyze(sample(),min_group=1,iterations=100)
        self.assertIn("caveats",r["report"]); self.assertIn("median_ci_low",r["borough"].columns)
    def test_missing_schema_rejected(self):
        with self.assertRaises(ValueError): prepare(pd.DataFrame({"created_date":[]}))

if __name__=="__main__": unittest.main()
