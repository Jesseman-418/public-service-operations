from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NYC 311 Response Times",layout="wide")
st.title("NYC 311 Response-Time Explorer")
path=st.sidebar.text_input("311 CSV", "data/nyc_311.csv")
sla=st.sidebar.number_input("Descriptive SLA threshold (hours)",min_value=1,value=72)
minimum=st.sidebar.number_input("Minimum group size",min_value=1,value=30)
if not Path(path).exists():
    st.info("Fetch an open sample: `python src/fetch_311.py --start-date 2026-01-01 --rows 50000`.")
    st.stop()
from analyze import analyze
result=analyze(pd.read_csv(path),sla_hours=sla,min_group=minimum)
data=result["prepared"]; c1,c2,c3=st.columns(3); c1.metric("Closed valid requests",f"{len(data):,}"); c2.metric("Median response",f"{data.response_hours.median():.1f} h"); c3.metric(f"Closed within {sla:g} h",f"{data.closed_within_sla.mean():.1%}")
st.subheader("Median response by borough (95% bootstrap interval)")
st.dataframe(result["borough"],hide_index=True,use_container_width=True)
if not result["borough"].empty: st.bar_chart(result["borough"].set_index("borough")["median_response_hours"])
st.subheader("Complaint types with the longest median response")
st.dataframe(result["complaints"].head(20),hide_index=True,use_container_width=True)
st.info(result["report"]["decision_note"]+" This is a follow-up hypothesis, not a causal conclusion.")
st.caption("Open administrative records; open/invalid timestamps excluded. Complaint mix and agency differences can confound comparisons.")
