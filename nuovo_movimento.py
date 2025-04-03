import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(credentials)

@st.cache_data
def carica_riferimenti():
    sheet = client.open("Prima Nota 2024").worksheet("riferimenti")
    df = pd.DataFrame(sheet.get_all_records())
    return df

riferimenti = carica_riferimenti()
causali = riferimenti['Causale'].dropna().unique().tolist()
centri = riferimenti['Centro di costo'].dropna().unique().tolist()
casse = riferimenti['Cassa'].dropna().unique().tolist()

with st.form("nuovo_movimento"):
    data = st.date_input("Data")
    causale = st.selectbox("Causale", causali)
    centro = st.selectbox("Centro di Costo", centri)
    importo = st.number_input("Importo", step=0.01)
    descrizione = st.text_input("Descrizione")
    cassa = st.selectbox("Cassa", casse)
    note = st.text_input("Note")
    submitted = st.form_submit_button("Aggiungi Movimento")

    if submitted:
        nuova_riga = [str(data), causale, centro, importo, descrizione, cassa, note]
        prima_nota = client.open("Prima Nota 2024").worksheet("Prima Nota")
        prima_nota.append_row(nuova_riga)
        st.success("Movimento aggiunto correttamente!")
