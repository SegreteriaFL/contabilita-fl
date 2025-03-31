import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📊 Gestionale Contabilità ETS 2024")

# === Simulazione Login Utente ===
utenti = [
    {"nome": "Mario Rossi", "email": "mario@fl.org", "ruolo": "superadmin", "provincia": "Tutte"},
    {"nome": "Lucia Bianchi", "email": "lucia@fl.org", "ruolo": "supervisore", "provincia": "Tutte"},
    {"nome": "Paolo Verdi", "email": "paolo.siena@fl.org", "ruolo": "tesoriere", "provincia": "Siena"},
    {"nome": "Anna Neri", "email": "anna.firenze@fl.org", "ruolo": "tesoriere", "provincia": "Firenze"},
    {"nome": "Franca Gialli", "email": "franca@fl.org", "ruolo": "lettore", "provincia": "Pisa"},
]

nominativi = [f"{u['nome']} ({u['ruolo']})" for u in utenti]
utente_sel = st.sidebar.selectbox("👤 Seleziona utente:", nominativi)
utente = next(u for u in utenti if f"{u['nome']} ({u['ruolo']})" == utente_sel)

st.sidebar.markdown(f"**Ruolo:** {utente['ruolo']}")
if utente['provincia'] != "Tutte":
    st.sidebar.markdown(f"**Provincia:** {utente['provincia']}")

# === Connessione sicura a Google Sheets ===
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/edit#gid=0"
SHEET_NAME = "prima_nota_2024"

# === Funzioni ===
def carica_movimenti():
    sh = client.open_by_url(SHEET_URL)
    worksheet = sh.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df

def scrivi_movimento(riga):
    sh = client.open_by_url(SHEET_URL)
    worksheet = sh.worksheet(SHEET_NAME)
    worksheet.append_row(riga)

# === Sezione Nuovo Movimento ===
if utente["ruolo"] in ["superadmin", "tesoriere"]:
    st.subheader("➕ Inserisci un nuovo movimento")
    with st.form("nuovo_movimento"):
        data_mov = st.date_input("Data", value=date.today())
        causale = st.selectbox("Causale", ["Donazione", "Spesa", "Quota associativa", "Altro"])
        centro = st.text_input("Centro di costo / progetto")
        importo = st.number_input("Importo (€)", min_value=0.01, step=0.01)
        descrizione = st.text_input("Descrizione")
        cassa = st.selectbox("Cassa", ["Banca", "Contanti"])
        note = st.text_input("Note (facoltative)")
        conferma = st.form_submit_button("Salva movimento")

    if conferma:
        nuova_riga = [
            data_mov.strftime("%Y-%m-%d"), causale, centro, importo,
            descrizione, cassa, utente["provincia"], note
        ]
        scrivi_movimento(nuova_riga)
        st.success("✅ Movimento salvato correttamente!")

# === Visualizzazione dati (placeholder) ===
st.subheader("📄 Prima Nota")
df = carica_movimenti()
st.dataframe(df)

# Altre sezioni (Dashboard, Rendiconto, ecc.) possono essere reintegrate qui