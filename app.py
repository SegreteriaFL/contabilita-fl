
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📒 Prima Nota - Contabilità 2024")

# Link pubblico del foglio Google in formato CSV (da export -> file ID)
google_sheet_url = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/export?format=csv"

@st.cache_data
def carica_dati():
    df = pd.read_csv(google_sheet_url)
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    return df

df = carica_dati()

# Filtro per mese e centro di costo
col1, col2 = st.columns(2)
mesi = df['data'].dt.to_period('M').astype(str).unique()
centri = df['Centro di Costo'].dropna().unique()

mese = col1.selectbox("📆 Mese", mesi)
centro = col2.selectbox("🏷️ Centro di costo", ["Tutti"] + list(centri))

df_filt = df[df['data'].dt.to_period('M').astype(str) == mese]
if centro != "Tutti":
    df_filt = df_filt[df_filt['Centro di Costo'] == centro]

st.subheader("📋 Movimenti")
st.dataframe(df_filt, use_container_width=True)

entrate = df_filt[df_filt['Importo'] > 0]['Importo'].sum()
uscite = df_filt[df_filt['Importo'] < 0]['Importo'].sum()
saldo = entrate + uscite

st.markdown(f"**Entrate:** {entrate:.2f} €")
st.markdown(f"**Uscite:** {uscite:.2f} €")
st.markdown(f"**Saldo netto:** {saldo:.2f} €")
