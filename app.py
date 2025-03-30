import streamlit as st
import pandas as pd

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📒 Prima Nota - Contabilità 2024 (da Google Sheets)")

@st.cache_data
def carica_dati_da_google_sheet():
    url = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/export?format=csv"
    df = pd.read_csv(url)

    # Pulizia campi
    df.columns = df.columns.str.strip()
    df['Importo'] = (
        df['Importo']
        .astype(str)
        .str.replace('€', '', regex=False)
        .str.replace(',', '.', regex=False)
        .str.strip()
    )
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce')

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data', 'Importo'])

    return df

df = carica_dati_da_google_sheet()

# UI Filtri
col1, col2 = st.columns(2)
mesi = df['data'].dt.strftime('%Y-%m').sort_values().unique()
centri = df['Centro di Costo'].dropna().unique()

mese_selezionato = col1.selectbox("📆 Seleziona mese:", mesi)
centro_selezionato = col2.selectbox("🏷️ Seleziona centro di costo:", ["Tutti"] + list(centri))

df_filt = df[df['data'].dt.strftime('%Y-%m') == mese_selezionato]
if centro_selezionato != "Tutti":
    df_filt = df_filt[df_filt['Centro di Costo'] == centro_selezionato]

# Output
st.subheader("📋 Movimenti")
st.dataframe(df_filt, use_container_width=True)

entrate = df_filt[df_filt['Importo'] > 0]['Importo'].sum()
uscite = df_filt[df_filt['Importo'] < 0]['Importo'].sum()
saldo = entrate + uscite

st.markdown(f"**Totale entrate:** {entrate:.2f} €")
st.markdown(f"**Totale uscite:** {uscite:.2f} €")
st.markdown(f"**Saldo del mese:** {saldo:.2f} €")
