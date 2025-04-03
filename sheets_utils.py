import streamlit as st

def login_simulato():
    utenti = {
        "Mario Rossi (superadmin)": "superadmin",
        "Anna Bianchi (tesoriere)": "tesoriere",
        "Luca Verdi (supervisore)": "supervisore",
        "Elisa Neri (lettore)": "lettore"
    }

    utente = st.sidebar.selectbox("Seleziona utente:", list(utenti.keys()))
    ruolo = utenti[utente]
    st.sidebar.markdown(f"**Ruolo**: {ruolo}")

    return utente, ruolo
