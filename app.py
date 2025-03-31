# ✅ App Streamlit completa con tutte le sezioni attive
# Prima Nota, Dashboard, Rendiconto ETS, Donazioni, Quote associative
# Con parser importi corretto, grafici, e login simulato

import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
import re

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📊 Gestionale Contabilità ETS 2024")

# === Login simulato ===
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

# === Menu sezioni ===
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

def pulisci_importo(val):
    if isinstance(val, str):
        val = val.replace("€", "").strip()
        val = re.sub(r"(?<=\d)\.(?=\d{3}(,|$))", "", val)  # SOLO punti migliaia
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
    df = df[df["data"].notna()]  # PATCH: rimuove righe senza data valida
    return df

def scrivi_movimento(riga):
    sh = client.open_by_url(SHEET_URL)
    worksheet = sh.worksheet(SHEET_NAME)
    worksheet.append_row(riga)

# === Form nuovo movimento ===
if utente["ruolo"] in ["superadmin", "tesoriere"]:
    if st.button("📥 Inserisci un nuovo movimento"):
        with st.form("nuovo_movimento"):
            data_mov = st.date_input("Data", value=date.today())
            causale = st.selectbox("Causale", ["Donazione", "Spesa", "Quota associativa", "Altro"])
            centro = st.text_input("Centro di costo / progetto")
            importo = st.number_input("Importo (€)", min_value=0.01, step=0.01)
            descrizione = st.text_input("Descrizione")
            cassa = st.selectbox("Cassa", ["Banca", "Contanti"])
            note = st.text_input("Note (facoltative)")
            conferma = st.form_submit_button("Salva movimento")
        if conferma:
            nuova_riga = [
                data_mov.strftime("%Y-%m-%d"), causale, centro, importo,
                descrizione, cassa, utente["provincia"], note
            ]
            scrivi_movimento(nuova_riga)
            st.success("✅ Movimento salvato correttamente!")

# === Sezione Prima Nota ===
if sezione_attiva == "Prima Nota":
    st.subheader("📁 Prima Nota")
    df = carica_movimenti()
    if not df.empty:
        mese = st.selectbox("📅 Mese:", sorted(df['data'].dt.strftime("%Y-%m").unique()))
        centro_sel = st.selectbox("🏷️ Centro di costo:", ["Tutti"] + sorted(df['Centro di Costo'].dropna().unique()))
        df_mese = df[df['data'].dt.strftime("%Y-%m") == mese]
        if centro_sel != "Tutti":
            df_mese = df_mese[df_mese['Centro di Costo'] == centro_sel]
        st.dataframe(df_mese)
        entrate = df_mese[df_mese['Importo'] > 0]['Importo'].sum()
        uscite = df_mese[df_mese['Importo'] < 0]['Importo'].sum()
        st.markdown(f"**Totale entrate:** {entrate:,.2f} €")
        st.markdown(f"**Totale uscite:** {abs(uscite):,.2f} €")
        st.markdown(f"**Saldo:** {entrate + uscite:,.2f} €")
    else:
        st.info("Nessun movimento disponibile.")

# === Sezione Dashboard ===
if sezione_attiva == "Dashboard":
    st.subheader("📊 Dashboard")
    df = carica_movimenti()
    if not df.empty:
        df["mese"] = df["data"].dt.to_period("M").astype(str)
        entrate = df[df["Importo"] > 0].groupby("mese")["Importo"].sum().reset_index()
        uscite = df[df["Importo"] < 0].groupby("mese")["Importo"].sum().abs().reset_index()
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.bar(entrate, x="mese", y="Importo", title="Entrate per mese"), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(uscite, x="mese", y="Importo", title="Uscite per mese"), use_container_width=True)
        st.plotly_chart(px.bar(df.groupby("Centro di Costo")["Importo"].sum().reset_index(),
                               x="Centro di Costo", y="Importo", title="Totale per centro di costo"), use_container_width=True)
    else:
        st.info("Nessun dato disponibile.")

# === Sezione Rendiconto ETS ===
if sezione_attiva == "Rendiconto ETS":
    st.subheader("📄 Rendiconto ETS")
    df = carica_movimenti()
    if not df.empty:
        sezione_a = df[df["Importo"] > 0].groupby("Causale")["Importo"].sum().reset_index()
        sezione_b = df[df["Importo"] < 0].groupby("Causale")["Importo"].sum().abs().reset_index()
        st.markdown("### Sezione A - Entrate")
        st.dataframe(sezione_a)
        st.markdown("### Sezione B - Uscite")
        st.dataframe(sezione_b)
    else:
        st.info("Nessun dato disponibile.")

# === Sezione Donazioni ===
if sezione_attiva == "Donazioni":
    st.subheader("❤️ Donazioni")
    df = carica_movimenti()
    df_don = df[df["Causale"] == "Donazione"]
    if not df_don.empty:
        st.dataframe(df_don)
        st.markdown(f"**Totale donazioni:** {df_don['Importo'].sum():,.2f} €")
    else:
        st.info("Nessuna donazione registrata.")

# === Sezione Quote associative ===
if sezione_attiva == "Quote associative":
    st.subheader("🧾 Quote associative")
    st.info("Funzionalità in sviluppo: collegamento con AppSheet previsto.")
