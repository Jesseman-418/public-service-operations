"""Response-time analysis with transparent filters and bootstrap intervals."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED={"created_date","closed_date","complaint_type","borough"}

def prepare(requests:pd.DataFrame)->pd.DataFrame:
    missing=REQUIRED-set(requests.columns)
    if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
    d=requests.copy()
    d["created"]=pd.to_datetime(d.created_date,utc=True,errors="coerce")
    d["closed"]=pd.to_datetime(d.closed_date,utc=True,errors="coerce")
    d["response_hours"]=(d.closed-d.created).dt.total_seconds()/3600
    d["borough"]=d.borough.fillna("Unknown").astype(str).str.title()
    d["complaint_type"]=d.complaint_type.fillna("Unknown").astype(str)
    return d.dropna(subset=["created","closed"]).query("response_hours >= 0").copy()

def bootstrap_median_ci(values,iterations=1000,seed=42):
    x=np.asarray(values,dtype=float); x=x[np.isfinite(x)]
    if len(x)==0: return (None,None)
    rng=np.random.default_rng(seed); medians=np.empty(iterations,dtype=float)
    for i in range(iterations): medians[i]=np.median(rng.choice(x,size=len(x),replace=True))
    return (float(np.quantile(medians,.025)),float(np.quantile(medians,.975)))

def analyze(requests:pd.DataFrame,sla_hours:float=72,min_group:int=30,iterations:int=1000)->dict:
    d=prepare(requests)
    if d.empty: raise ValueError("No requests have valid, nonnegative creation-to-closure intervals")
    d["closed_within_sla"]=d.response_hours<=sla_hours
    borough=[]
    for name,g in d.groupby("borough"):
        if len(g)<min_group: continue
        lo,hi=bootstrap_median_ci(g.response_hours,iterations,seed=42)
        borough.append({"borough":name,"requests":int(len(g)),"median_response_hours":float(g.response_hours.median()),
                        "p90_response_hours":float(g.response_hours.quantile(.9)),"sla_rate":float(g.closed_within_sla.mean()),
                        "median_ci_low":lo,"median_ci_high":hi})
    by_complaint=(d.groupby("complaint_type").agg(requests=("response_hours","size"),median_response_hours=("response_hours","median"),p90_response_hours=("response_hours",lambda x:x.quantile(.9)),sla_rate=("closed_within_sla","mean"))
                  .query("requests >= @min_group").sort_values("median_response_hours",ascending=False).reset_index())
    borough=sorted(borough,key=lambda x:x["median_response_hours"],reverse=True)
    leading=borough[0]["borough"] if borough else None
    report={"valid_closed_requests":int(len(d)),"invalid_or_open_rows_excluded":int(len(requests)-len(d)),"sla_hours":sla_hours,
            "borough_metrics":borough,"slowest_eligible_borough":leading,
            "decision_note":f"Review staffing, case mix, and process for {leading} as a follow-up hypothesis." if leading else "No borough met the minimum group size.",
            "caveats":["Only requests with valid creation and closure timestamps are included.","SLA is a descriptive 72-hour threshold, not an official NYC service guarantee.","Differences are observational and may reflect complaint mix, agency, or reporting delays.","Bootstrap intervals describe sampling variability, not all sources of measurement bias."]}
    return {"prepared":d,"borough":pd.DataFrame(borough),"complaints":by_complaint,"report":report}

def write_outputs(data:pd.DataFrame,out_dir:str|Path,**kwargs):
    result=analyze(data,**kwargs); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    result["borough"].to_csv(out/"borough_metrics.csv",index=False); result["complaints"].to_csv(out/"complaint_metrics.csv",index=False)
    (out/"decision_memo.json").write_text(json.dumps(result["report"],indent=2)); return result

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("csv"); p.add_argument("--output",default="outputs"); p.add_argument("--sla-hours",type=float,default=72); a=p.parse_args()
    res=write_outputs(pd.read_csv(a.csv),a.output,sla_hours=a.sla_hours); print(json.dumps(res["report"],indent=2))
