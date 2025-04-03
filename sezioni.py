# DEBUG PATCH — mostra header del foglio 'riferimenti'
import streamlit as st
import pandas as pd
from datetime import date

def mostra_nuovo_movimento(utente, client, SHEET_URL, SHEET_NAME):
    st.subheader("➕ Nuovo Movimento")
    if utente["ruolo"] not in ["superadmin", "tesoriere"]:
        st.warning("Sezione riservata ai tesorieri e al superadmin.")
        return

    try:
        worksheet = client.open_by_url(SHEET_URL).worksheet("riferimenti")
        headers = worksheet.row_values(1)
        st.info(f"🧪 Header rilevato nella riga 1: {headers}")
        riferimenti_raw = worksheet.get_all_records()
        riferimenti = pd.DataFrame(riferimenti_raw)
    except Exception as e:
        st.error("❌ Errore nel caricamento del foglio 'riferimenti'.")
        st.exception(e)
        st.stop()

    st.success("✅ Il foglio è stato caricato correttamente.")
