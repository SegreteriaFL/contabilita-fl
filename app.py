import streamlit as st
from sezioni import (
    mostra_prima_nota,
    mostra_dashboard,
    mostra_rendiconto,
    mostra_donazioni,
    mostra_quote,
    mostra_nuovo_movimento,
    mostra_saldo
)
from auth import login_simulato
from sheets_utils import carica_riferimenti, get_gsheet_client

# Applicazione Streamlit
st.set_page_config(page_title="Contabilità FL", layout="wide")

# --- Stile personalizzato minimale ---
with open("theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- LOGIN UTENTE ---
utente, ruolo = login_simulato()

# --- CARICAMENTO DATI DI RIFERIMENTO ---
client = get_gsheet_client()
riferimenti = carica_riferimenti(client)

# --- SIDEBAR ---
with st.sidebar:
    st.write("### 📁 Sezioni")
    sezione = st.radio("Vai a:", [
        "Prima Nota",
        "Dashboard",
        "Rendiconto ETS",
        "Donazioni",
        "Quote associative",
        "Nuovo Movimento",
        "Saldo da Estratto Conto"
    ])

# --- LOGICA DELLA PAGINA ---
if sezione == "Prima Nota":
    mostra_prima_nota(client, ruolo, riferimenti)
elif sezione == "Dashboard":
    mostra_dashboard(client)
elif sezione == "Rendiconto ETS":
    mostra_rendiconto(client)
elif sezione == "Donazioni":
    mostra_donazioni(client)
elif sezione == "Quote associative":
    mostra_quote(client)
elif sezione == "Nuovo Movimento":
    mostra_nuovo_movimento(client, ruolo, riferimenti)
elif sezione == "Saldo da Estratto Conto":
    mostra_saldo(client)
