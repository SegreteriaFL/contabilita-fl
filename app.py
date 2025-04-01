# ✅ Gestionale Contabilità ETS — Versione completa con interfaccia moderna

import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
from io import BytesIO
from fpdf import FPDF
from streamlit_option_menu import option_menu

# === Impostazioni tema dinamico ===
tema = st.sidebar.radio("🎨 Tema", ["Chiaro", "Scuro"])
if tema == "Scuro":
    menu_style = {
        "container": {"padding": "0!important", "background-color": "#262730"},
        "icon": {"color": "white", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "left",
            "margin": "0px",
            "color": "#FFFFFF",
            "--hover-color": "#444",
        },
        "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
    }
else:
    menu_style = {
        "container": {"padding": "0!important", "background-color": "#f5f5f5"},
        "icon": {"color": "#000", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "left",
            "margin": "0px",
            "color": "#000000",
            "--hover-color": "#e0e0e0",
        },
        "nav-link-selected": {"background-color": "#4CAF50", "color": "white", "font-weight": "bold"},
    }

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📊 Gestionale Contabilità ETS 2024")

# === Utility ===
def format_currency(val):
    try:
        return f"{float(val):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return val

def format_date(dt):
    return dt.strftime("%d/%m/%Y") if not pd.isna(dt) else ""

def download_excel(df, nome_file):
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button("📥 Scarica Excel", data=output.getvalue(), file_name=f"{nome_file}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def download_pdf(text, nome_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)
    output = BytesIO()
    pdf.output(output)
    st.download_button("📄 Scarica PDF", data=output.getvalue(), file_name=nome_file, mime="application/pdf")

def genera_ricevuta_pdf(d):
    lines = [
        "Ricevuta Donazione",
        f"Data: {format_date(d['data'])}",
        f"Importo: {format_currency(d['Importo'])}",
        f"Causale: {d['Causale']}",
        f"Centro di Costo: {d['Centro di Costo']}",
        f"Metodo: {d['Cassa']}",
        f"Note: {d['Note']}"
    ]
    return "\n".join(lines)

# === Login simulato ===
st.info("🔐 Login simulato. OAuth Google reale in sviluppo.")
utenti = [
    {"nome": "Mario Rossi", "email": "mario@fl.org", "ruolo": "superadmin", "provincia": "Tutte"},
    {"nome": "Lucia Bianchi", "email": "lucia@fl.org", "ruolo": "supervisore", "provincia": "Tutte"},
    {"nome": "Paolo Verdi", "email": "paolo.siena@fl.org", "ruolo": "tesoriere", "provincia": "Siena"},
    {"nome": "Anna Neri", "email": "anna.firenze@fl.org", "ruolo": "tesoriere", "provincia": "Firenze"},
    {"nome": "Franca Gialli", "email": "franca@fl.org", "ruolo": "lettore", "provincia": "Pisa"},
]
utente_sel = st.sidebar.selectbox("👤 Seleziona utente:", [f"{u['nome']} ({u['ruolo']})" for u in utenti])
utente = next(u for u in utenti if f"{u['nome']} ({u['ruolo']})" == utente_sel)

st.sidebar.markdown(f"**Ruolo:** {utente['ruolo']}")
if utente['provincia'] != "Tutte":
    st.sidebar.markdown(f"**Provincia:** {utente['provincia']}")

# === Menu moderno ===
with st.sidebar:
    sezione_attiva = option_menu(
        menu_title="📂 Sezioni",
        options=["Prima Nota", "Dashboard", "Rendiconto ETS", "Donazioni", "Quote associative"],
        icons=["file-earmark-text", "bar-chart", "clipboard-data", "gift", "people"],
        menu_icon="folder",
        default_index=0,
        styles=menu_style
    )

pagina = "home"
if utente["ruolo"] in ["tesoriere", "superadmin"]:
    if st.sidebar.button("➕ Nuovo movimento"):
        pagina = "nuovo_movimento"

# === Connessione ===
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/edit"
SHEET_NAME = "prima_nota_2024"

def carica_movimenti():
    df = pd.DataFrame(client.open_by_url(SHEET_URL).worksheet(SHEET_NAME).get_all_records())
    df.columns = df.columns.str.strip()
    if "Provincia" not in df.columns:
        df["Provincia"] = ""
    df["Importo"] = pd.to_numeric(df["Importo"], errors="coerce").fillna(0)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df[df["data"].notna()]
    if utente["ruolo"] == "tesoriere":
        df = df[df["Provincia"] == utente["provincia"]]
    return df
