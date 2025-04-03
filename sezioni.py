# ✅ sezioni.py — con gestione errori sul foglio "riferimenti"
import streamlit as st
import plotly.express as px
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# Tutte le funzioni precedenti (mostra_prima_nota, mostra_dashboard, mostra_rendiconto, mostra_donazioni, mostra_quote)
# sono identiche alla versione precedente e quindi omesse qui per brevità

def mostra_nuovo_movimento(utente, client, SHEET_URL, SHEET_NAME):
    st.subheader("➕ Nuovo Movimento")
    if utente["ruolo"] not in ["superadmin", "tesoriere"]:
        st.warning("Sezione riservata ai tesorieri e al superadmin.")
        return

    try:
        riferimenti_raw = client.open_by_url(SHEET_URL).worksheet("riferimenti").get_all_records()
        riferimenti = pd.DataFrame(riferimenti_raw)
    except Exception as e:
        st.error("❌ Errore nel caricamento del foglio 'riferimenti'. Verifica che esista e che sia condiviso con il service account.")
        st.exception(e)
        st.stop()

    causali = riferimenti['Causale'].dropna().unique().tolist() if 'Causale' in riferimenti else []
    centri = riferimenti['Centro di costo'].dropna().unique().tolist() if 'Centro di costo' in riferimenti else []
    casse = riferimenti['Cassa'].dropna().unique().tolist() if 'Cassa' in riferimenti else []

    if not (causali and centri and casse):
        st.warning("⚠️ Attenzione: alcuni campi nel foglio 'riferimenti' potrebbero essere vuoti o mancanti.")

    with st.form("nuovo_movimento"):
        data_mov = st.date_input("Data", value=date.today())
        causale = st.selectbox("Causale", causali)
        centro = st.selectbox("Centro di costo", centri)
        importo = st.number_input("Importo", step=0.01, format="%.2f")
        descrizione = st.text_area("Descrizione")
        cassa = st.selectbox("Metodo di pagamento", casse)
        note = st.text_input("Note")
        submitted = st.form_submit_button("💾 Salva movimento")

        if submitted:
            if not causale or importo == 0:
                st.error("Causale e importo sono obbligatori!")
            else:
                try:
                    ws = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
                    nuova_riga = [
                        str(data_mov), causale, centro, importo,
                        descrizione, cassa, note, utente["provincia"]
                    ]
                    ws.append_row(nuova_riga)
                    st.success("Movimento inserito correttamente!")
                except Exception as e:
                    st.error("❌ Errore durante l'inserimento del movimento.")
                    st.exception(e)
