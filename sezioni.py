# ✅ sezioni.py — con placeholder "Seleziona..." nei menu a tendina
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
        expected = ["Causale", "Centro di costo", "Cassa"]
        riferimenti_raw = worksheet.get_all_records(expected_headers=expected)
        riferimenti = pd.DataFrame(riferimenti_raw)
    except Exception as e:
        st.error("❌ Errore nel caricamento del foglio 'riferimenti'.")
        st.exception(e)
        st.stop()

    # Pulizia per campo isolato
    causali = riferimenti[
        (riferimenti["Causale"].notna()) & (riferimenti["Causale"] != "") &
        (riferimenti["Centro di costo"] == "") & (riferimenti["Cassa"] == "")
    ]["Causale"].unique().tolist()

    centri = riferimenti[
        (riferimenti["Centro di costo"].notna()) & (riferimenti["Centro di costo"] != "") &
        (riferimenti["Causale"] == "") & (riferimenti["Cassa"] == "")
    ]["Centro di costo"].unique().tolist()

    casse = riferimenti[
        (riferimenti["Cassa"].notna()) & (riferimenti["Cassa"] != "") &
        (riferimenti["Causale"] == "") & (riferimenti["Centro di costo"] == "")
    ]["Cassa"].unique().tolist()

    causali.sort()
    centri.sort()
    casse.sort()

    if not (causali and centri and casse):
        st.warning("⚠️ Alcuni valori nel foglio 'riferimenti' risultano mancanti o distribuiti in righe multiple.")

    with st.form("nuovo_movimento"):
        data_mov = st.date_input("Data", value=None)
        causale = st.selectbox("Causale", ["Seleziona..."] + causali, index=0)
        centro = st.selectbox("Centro di costo", ["Seleziona..."] + centri, index=0)
        importo = st.number_input("Importo", step=0.01, format="%.2f")
        descrizione = st.text_area("Descrizione")
        cassa = st.selectbox("Metodo di pagamento", ["Seleziona..."] + casse, index=0)
        note = st.text_input("Note")
        submitted = st.form_submit_button("💾 Salva movimento")

        if submitted:
            if causale == "Seleziona..." or centro == "Seleziona..." or cassa == "Seleziona..." or importo == 0:
                st.error("Tutti i campi obbligatori devono essere compilati.")
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
