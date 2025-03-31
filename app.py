
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import plotly.express as px
import re

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

# === Sidebar menu ===
sezioni = ["Prima Nota", "Dashboard", "Rendiconto ETS", "Donazioni", "Quote associative"]
sezione_attiva = st.sidebar.radio("📂 Sezioni", sezioni)

# === Connessione a Google Sheets ===
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
def pulisci_importo(val):
    if isinstance(val, str):
        val = val.replace("€", "").strip()
        val = re.sub(r"(?<=\d)\.(?=\d{3}(,|$))", "", val)
        val = val.replace(",", ".")
    return pd.to_numeric(val, errors="coerce")

def carica_movimenti():
    sh = client.open_by_url(SHEET_URL)
    worksheet = sh.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    df["Importo"] = df["Importo"].apply(pulisci_importo).fillna(0)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df

# === Sezione: Dashboard ===
if sezione_attiva == "Dashboard":
    st.subheader("📈 Dashboard mensile")
    df = carica_movimenti()
    if df.empty:
        st.warning("Nessun dato disponibile.")
    else:
        df["mese"] = df["data"].dt.to_period("M").astype(str)
        entrate = df[df["Importo"] > 0].groupby("mese")["Importo"].sum().reset_index()
        uscite = df[df["Importo"] < 0].groupby("mese")["Importo"].sum().abs().reset_index()

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(entrate, x="mese", y="Importo", title="Entrate per mese", labels={"Importo": "€"})
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(uscite, x="mese", y="Importo", title="Uscite per mese", labels={"Importo": "€"})
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📊 Totale per centro di costo")
        centro = df.groupby("Centro di Costo")["Importo"].sum().reset_index()
        fig3 = px.bar(centro, x="Centro di Costo", y="Importo", title="Bilancio per centro di costo", labels={"Importo": "€"})
        st.plotly_chart(fig3, use_container_width=True)
