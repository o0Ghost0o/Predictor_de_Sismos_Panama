"""METAR horario IEM (Iowa State) para 3 aeropuertos: MPBO=Bocas, MPDA=David(Chiriqui+Azuero), MPMG=Tocumen(Central+Darien).
Features diarias: medias, rango termico, tendencia de presion (proxy de carga atmosferica)."""
import argparse
import pandas as pd
import requests

ST = {"MPBO": "BOCAS", "MPDA": "CHIRIQUI", "MPMG": "CENTRAL"}
EXTRA = {"AZUERO": "MPDA", "DARIEN": "MPMG"}  # mas cercano disponible (limitacion documentada)
BASE = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

def fetch(st: str, start: str, end: str) -> pd.DataFrame:
    y1, m1, d1 = start.split("-"); y2, m2, d2 = end.split("-")
    p = {"station": st, "data": ["tmpc", "relh", "alti"], "year1": y1, "month1": m1, "day1": d1,
         "year2": y2, "month2": m2, "day2": d2, "tz": "Etc/UTC", "format": "onlycomma",
         "latlon": "yes", "missing": "empty", "trace": "T", "direct": "no",
         "report_type": ["3", "4"]}
    r = requests.get(BASE, params=p, timeout=180)
    r.raise_for_status()
    import io
    df = pd.read_csv(io.StringIO(r.text))
    df["valid"] = pd.to_datetime(df["valid"], utc=True)
    df["date"] = df.valid.dt.normalize()
    g = df.groupby("date").agg(t_tmp=("tmpc", "mean"), t_rh=("relh", "mean"),
                               t_alti=("alti", "mean"), t_alti_range=("alti", lambda s: s.max() - s.min()),
                               t_alti_tend=("alti", lambda s: s.iloc[-1] - s.iloc[0] if len(s) > 1 else 0),
                               t_trange=("tmpc", lambda s: s.max() - s.min()), nobs=("tmpc", "size")).reset_index()
    g["station"] = st
    return g

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--out", default="data/raw/metar_daily.parquet")
    a = ap.parse_args()
    import os; os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    dfs = []
    for st in ST:
        d = fetch(st, a.start, a.end)
        print(st, len(d), "dias", flush=True)
        dfs.append(d)
    pd.concat(dfs, ignore_index=True).to_parquet(a.out, index=False)
    print("saved", a.out)
