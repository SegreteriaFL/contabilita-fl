import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
from fpdf import FPDF
import tempfile

# === Connessione a Google Sheets ===
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/edit"
SHEET_NAME = "prima_nota_2024"

# === Funzione di prova per la gestione degli errori ===
def carica_movimenti():
    df = pd.DataFrame(client.open_by_url(SHEET_URL).worksheet(SHEET_NAME).get_all_records())
    df.columns = df.columns.str.strip()
    df["Importo"] = pd.to_numeric(df["Importo"], errors="coerce").fillna(0)
    return df

# === Import delle sezioni modulari ===
from sezioni import (
    mostra_prima_nota,
    mostra_dashboard,
    mostra_rendiconto,
    mostra_donazioni,
    mostra_quote,
    mostra_nuovo_movimento,
)

# === Menu laterale ===
menu_style = {
    "container": {"padding": "0!important", "background-color": "#111"},
    "icon": {"color": "white", "font-size": "18px"},
    "nav-link": {"font-size": "16px", "color": "#EEE", "margin": "4px", "--hover-color": "#333"},
    "nav-link-selected": {"background-color": "#4CAF50", "font-weight": "bold", "color": "white"},
}

with st.sidebar:
    sezione_attiva = option_menu(
        menu_title="📂 Sezioni",
        options=["Prima Nota", "Dashboard", "Rendiconto ETS", "Donazioni", "Quote associative", "Nuovo Movimento"],  # Semplificato
        icons=["file-earmark-text", "bar-chart", "clipboard-data", "gift", "people", "plus-circle"],
        menu_icon="folder",
        default_index=0,
        styles=menu_style
    )

# === Routing ===
if sezione_attiva == "Prima Nota":
    mostra_prima_nota(carica_movimenti)
elif sezione_attiva == "Dashboard":
    mostra_dashboard(carica_movimenti)
elif sezione_attiva == "Rendiconto ETS":
    mostra_rendiconto(carica_movimenti)
elif sezione_attiva == "Donazioni":
    mostra_donazioni(carica_movimenti)
elif sezione_attiva == "Quote associative":
    mostra_quote()
elif sezione_attiva == "Nuovo Movimento":
    mostra_nuovo_movimento()
