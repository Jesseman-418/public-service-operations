"""Fetch a bounded sample of NYC 311 service requests from the public SODA API."""
from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
import requests
import pandas as pd

ENDPOINT="https://data.cityofnewyork.us/resource/erm2-nwe9.json"
FIELDS=["created_date","closed_date","complaint_type","borough","agency","status"]

def fetch(start_date:str,rows:int,output:str)->pd.DataFrame:
    if rows<1 or rows>250_000: raise ValueError("rows must be between 1 and 250000")
    where=f"created_date >= '{start_date}T00:00:00'"
    collected=[]; offset=0
    while len(collected)<rows:
        size=min(50_000,rows-len(collected))
        response=requests.get(ENDPOINT,params={"$select":",".join(FIELDS),"$where":where,"$limit":size,"$offset":offset,"$order":"created_date ASC"},timeout=60)
        response.raise_for_status(); batch=response.json()
        if not batch: break
        collected.extend(batch); offset+=len(batch)
    if not collected: raise RuntimeError("The API returned no rows for this date range")
    df=pd.DataFrame(collected); Path(output).parent.mkdir(parents=True,exist_ok=True); df.to_csv(output,index=False)
    return df

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--start-date",default="2026-01-01"); p.add_argument("--rows",type=int,default=50000); p.add_argument("--output",default="data/nyc_311.csv"); a=p.parse_args()
    d=fetch(a.start_date,a.rows,a.output); print({"rows":len(d),"file":a.output})
