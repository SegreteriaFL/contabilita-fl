
import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📊 Gestionale Contabilità ETS 2024")

# === Autenticazione Google Sheets da secrets ===
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# === Config ===
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/edit#gid=0"
SHEET_NAME = "Foglio1"

# === Lettura dati ===
def carica_movimenti():
    sh = client.open_by_url(SHEET_URL)
    worksheet = sh.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
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
    return df, worksheet

# === Scrittura nuovo movimento ===
def aggiungi_movimento(worksheet, data, causale, centro, importo, descrizione, cassa, note):
    nuova_riga = [str(data.date()), causale, centro, importo, descrizione, cassa, note]
    worksheet.append_row(nuova_riga, value_input_option="USER_ENTERED")

# === Interfaccia ===
df, ws = carica_movimenti()

menu = st.sidebar.radio("📁 Sezioni", ["Visualizza movimenti", "➕ Nuovo movimento"])

if menu == "Visualizza movimenti":
    st.header("📋 Movimenti registrati")
    st.dataframe(df, use_container_width=True)

elif menu == "➕ Nuovo movimento":
    st.header("➕ Aggiungi nuovo movimento contabile")

    with st.form("nuovo_movimento"):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        importo = col2.number_input("Importo (€)", step=0.01, format="%.2f")
        causale = st.text_input("Causale")
        centro = st.text_input("Centro di Costo")
        descrizione = st.text_area("Descrizione", height=60)
        cassa = st.selectbox("Cassa", ["Cassa", "Bonifico", "Altro"])
        note = st.text_area("Note", height=40)

        submitted = st.form_submit_button("📤 Salva movimento")
        if submitted:
            try:
                aggiungi_movimento(ws, data, causale, centro, importo, descrizione, cassa, note)
                st.success("✅ Movimento aggiunto con successo!")
                st.balloons()
                # Ricarica i dati aggiornati
                df, ws = carica_movimenti()
                st.header("📋 Movimenti registrati (aggiornati)")
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Errore durante il salvataggio: {e}")
