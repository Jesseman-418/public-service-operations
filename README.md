# Public Service Operations Analysis

Measure NYC 311 closure times by borough and complaint type, quantify median uncertainty with bootstrap intervals, and explore patterns in an interactive dashboard.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/fetch_311.py --start-date 2026-01-01 --rows 50000 --output data/nyc_311.csv
python src/analyze.py data/nyc_311.csv --output outputs
streamlit run src/dashboard.py
python -m unittest discover -s tests -v
```

Source: [NYC 311 Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests/erm2-nwe9). The downloader uses the public Socrata endpoint and supports a date/row limit. Results exclude open requests and invalid or negative durations. The dashboard displays a configurable 72-hour descriptive threshold; it is not an official service-level guarantee.

`outputs/decision_memo.json` includes the observed slowest eligible borough and follow-up hypothesis with caveats. Bootstrap intervals quantify sampling variability, not confounding from agency, issue mix, reporting delay, or other sources. This analysis is descriptive and does not establish causal bottlenecks.
