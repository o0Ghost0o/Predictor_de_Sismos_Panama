import streamlit as st, pandas as pd, requests, datetime

API = "http://localhost:8001"
st.set_page_config(page_title="Sismos Panamá", layout="wide")
st.title("Sismos Panamá — Nivel de actividad (escala 3–6)")

st.info("Nivel 3 = tranquilo · 4 = leve posible · 5 = intermedio posible · 6 = fuerte posible. "
        "Niveles 7–10 no se pronostican: solo hubo 5 sismos M7+ en 56 años. Investigación, no alerta oficial.")

try:
    zones_info = requests.get(f"{API}/zones", timeout=5).json()
except Exception as e:
    st.error(f"API no disponible en {API} — arranca: uvicorn src.serve.app:app --port 8001. ({e})")
    st.stop()

tab1, tab2 = st.tabs(["Pronóstico", "Pronóstico vs Realidad"])

with tab1:
    zmin = pd.to_datetime(zones_info["date_min"]).date()
    zmax = pd.to_datetime(zones_info["date_max"]).date()
    d = st.date_input("Fecha de prueba", value=datetime.date(2025, 6, 15),
                      min_value=zmin, max_value=zmax)
    data = requests.get(f"{API}/risk", params={"date": str(d)}, timeout=10).json()
    df = pd.DataFrame(data).sort_values("nivel", ascending=False)
    cols = st.columns(len(df))
    for c, (_, r) in zip(cols, df.iterrows()):
        c.metric(r["zone"], f"Nivel {r['nivel']}", f"M4:{r['p_M4_7d']:.0%} M5:{r['p_M5_7d']:.0%} M6:{r['p_M6_7d']:.0%}")
        c.caption(r["mensaje"])
    st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("Comparativa en años no vistos por el modelo")
    bt = requests.get(f"{API}/backtest", timeout=30).json()
    st.caption(f"Periodo: {bt['periodo']} · {bt['umbral_alerta']}")
    zdf = pd.DataFrame(bt["por_zona"]).set_index("zone")
    st.dataframe(zdf, use_container_width=True)
    st.bar_chart(zdf[["aciertos", "falsas_alarmas", "omitidos"]])
    st.subheader("Eventos reales recientes: ¿qué decía el modelo 7 días antes?")
    st.dataframe(pd.DataFrame(bt["ultimos_eventos_acertar"]), use_container_width=True)
    st.caption("Lectura honesta: CHIRIQUI detecta casi todo pero dispara muchas falsas alarmas; "
               "CENTRAL/AZUERO/BOCAS son débiles; el M7.7 de Azuero (oct-2026) fue omitido (Nivel 3).")
