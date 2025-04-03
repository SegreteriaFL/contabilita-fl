# ✅ sezioni.py — gestione flessibile dei riferimenti + menu "Seleziona..."
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

    # Logica flessibile: prendi tutti i valori non vuoti per colonna
    causali = riferimenti["Causale"].dropna().astype(str).str.strip()
    causali = sorted(causali[causali != ""].unique().tolist())

    centri = riferimenti["Centro di costo"].dropna().astype(str).str.strip()
    centri = sorted(centri[centri != ""].unique().tolist())

    casse = riferimenti["Cassa"].dropna().astype(str).str.strip()
    casse = sorted(casse[casse != ""].unique().tolist())

    if not (causali and centri and casse):
        st.warning("⚠️ Il foglio 'riferimenti' non contiene abbastanza voci in una o più colonne.")

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
