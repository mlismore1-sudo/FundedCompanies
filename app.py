import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from db import get_client, recent_screening

load_dotenv()

st.set_page_config(page_title="Companies House Monitor", layout="wide")
st.title("Companies House Investment Monitor")
st.caption("SH01, PSC and RLE-related changes detected from Companies House data")

try:
    client = get_client()
    rows = recent_screening(client)
except Exception as exc:
    st.error(f"Database connection failed: {exc}")
    st.stop()

if not rows:
    st.info("No screening events have been stored yet. Start the local worker and wait for events.")
    st.stop()

df = pd.DataFrame(rows)

with st.sidebar:
    st.header("Filters")
    nature_options = sorted(df["nature_of_change"].dropna().unique().tolist())
    selected_natures = st.multiselect("Nature of change", nature_options, default=nature_options)
    search = st.text_input("Company or PSC name")
    min_confidence = st.slider("Minimum confidence", 0, 100, 0)

filtered = df[df["nature_of_change"].isin(selected_natures)]
filtered = filtered[filtered["confidence_score"].fillna(0) >= min_confidence]
if search:
    mask = (
        filtered["company_name"].fillna("").str.contains(search, case=False, na=False)
        | filtered["new_psc_name"].fillna("").str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

columns = [
    "company_name",
    "nature_of_change",
    "new_psc_name",
    "sic_codes",
    "date_of_incorporation",
    "sh01_date",
    "psc_date",
    "confidence_score",
    "detected_at",
    "explanation",
]
columns = [x for x in columns if x in filtered.columns]
st.dataframe(filtered[columns], use_container_width=True, hide_index=True)
st.caption(f"Showing {len(filtered)} of {len(df)} stored events")
