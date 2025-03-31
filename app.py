# ✅ App Streamlit completa e ottimizzata dopo normalizzazione importi
# Include: Prima Nota, Dashboard, Rendiconto ETS, Donazioni, Quote associative, Nuovo Movimento
# Estensioni: export Excel, ricevute txt, login OAuth placeholder, foglio Google pulito

import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
import base64
from io import BytesIO

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📊 Gestionale Contabilità ETS 2024")

# === Funzione formattazione importi ===
def format_currency(val):
    try:
        return f"{float(val):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return val

# === Funzioni utility ===
def download_excel(df, nome_file):
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button("📥 Scarica Excel", data=output.getvalue(), file_name=f"{nome_file}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def download_txt(content, filename):
    st.download_button("📄 Scarica ricevuta", data=content, file_name=filename, mime="text/plain")

def genera_ricevuta(d):
    return f"Ricevuta per {format_currency(d['Importo'])} ricevuta da {d['Causale']} il {d['data'].date()} - CENTRO: {d['Centro di Costo']}"

# === Login simulato con placeholder OAuth ===
st.warning("🔐 Login reale OAuth con Google in sviluppo. Attualmente login simulato.")
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
pagina = "home"
if utente["ruolo"] in ["tesoriere", "superadmin"]:
    if st.sidebar.button("➕ Nuovo movimento"):
        pagina = "nuovo_movimento"

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

# ✅ Ora che la colonna Importo è stata normalizzata nel foglio Google, il parser può essere semplificato

def pulisci_importo(val):
    return pd.to_numeric(val, errors="coerce")

def carica_movimenti():
    sh = client.open_by_url(SHEET_URL)
    worksheet = sh.worksheet(SHEET_NAME)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    df["Importo"] = df["Importo"].apply(pulisci_importo).fillna(0)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df[df["data"].notna()]
    if utente["ruolo"] == "tesoriere":
        df = df[df["Provincia"] == utente["provincia"]]
    return df

# === Prima Nota ===

if sezione_attiva == "Prima Nota":
    st.subheader("🧪 Debug Importi")
st.write("Valori grezzi di 'Importo':")
st.write(df["Importo"].head(10))

st.write("Tipi di dati letti:")
st.write(df["Importo"].apply(lambda x: f"{x} → {type(x)}").head(10))

    st.subheader("📁 Prima Nota")
    df = carica_movimenti()
    if not df.empty:
        mese = st.selectbox("📅 Mese:", sorted(df['data'].dt.strftime("%Y-%m").unique()))
        centro_sel = st.selectbox("🏷️ Centro di costo:", ["Tutti"] + sorted(df['Centro di Costo'].dropna().unique()))
        df_mese = df[df['data'].dt.strftime("%Y-%m") == mese]
        if centro_sel != "Tutti":
            df_mese = df_mese[df_mese['Centro di Costo'] == centro_sel]
        st.dataframe(df_mese.drop(columns=["Importo"]).assign(**{"Importo (€)": df_mese["Importo"].apply(format_currency)}))
        st.markdown(f"**Totale entrate:** {format_currency(df_mese[df_mese['Importo'] > 0]['Importo'].sum())}")
        st.markdown(f"**Totale uscite:** {format_currency(abs(df_mese[df_mese['Importo'] < 0]['Importo'].sum()))}")
        st.markdown(f"**Saldo:** {format_currency(df_mese['Importo'].sum())}")
        download_excel(df_mese, "prima_nota")
    else:
        st.info("Nessun movimento disponibile.")

# === Dashboard ===
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
        cdc = df.groupby("Centro di Costo")["Importo"].sum().reset_index()
        st.dataframe(cdc.assign(**{"Importo (€)": cdc["Importo"].apply(format_currency)}).drop(columns="Importo"))
        download_excel(cdc, "centro_di_costo")
    else:
        st.info("Nessun dato disponibile.")

# === Rendiconto ETS ===
if sezione_attiva == "Rendiconto ETS":
    st.subheader("📄 Rendiconto ETS")
    df = carica_movimenti()
    if not df.empty:
        entrate = df[df["Importo"] > 0].groupby("Causale")["Importo"].sum().reset_index()
        uscite = df[df["Importo"] < 0].groupby("Causale")["Importo"].sum().abs().reset_index()
        totale_entrate = entrate["Importo"].sum()
        totale_uscite = uscite["Importo"].sum()
        entrate["Importo"] = entrate["Importo"].apply(format_currency)
        uscite["Importo"] = uscite["Importo"].apply(format_currency)
        st.markdown("### Sezione A - Entrate")
        st.dataframe(entrate)
        st.markdown(f"**Totale entrate:** {format_currency(totale_entrate)}")
        st.markdown("### Sezione B - Uscite")
        st.dataframe(uscite)
        st.markdown(f"**Totale uscite:** {format_currency(totale_uscite)}")
        st.markdown(f"**Saldo operativo:** {format_currency(totale_entrate - totale_uscite)}")
    else:
        st.info("Nessun dato disponibile.")

# === Donazioni ===
if sezione_attiva == "Donazioni":
    st.subheader("❤️ Donazioni")
    df = carica_movimenti()
    df_don = df[df["Causale"] == "Donazione"]
    if not df_don.empty:
        mesi = sorted(df_don["data"].dt.strftime("%Y-%m").unique())
        mesi.insert(0, "Tutti")
        sel_mese = st.selectbox("📅 Filtro mese:", mesi)
        if sel_mese != "Tutti":
            df_don = df_don[df_don["data"].dt.strftime("%Y-%m") == sel_mese]
        centro_sel = st.selectbox("🏷️ Centro di costo:", ["Tutti"] + sorted(df_don["Centro di Costo"].dropna().unique()))
        if centro_sel != "Tutti":
            df_don = df_don[df_don["Centro di Costo"] == centro_sel]
        st.dataframe(df_don.drop(columns="Importo").assign(**{"Importo (€)": df_don["Importo"].apply(format_currency)}))
        st.markdown(f"**Totale donazioni:** {format_currency(df_don['Importo'].sum())}")
        if st.checkbox("📄 Genera ricevuta per prima donazione visibile"):
            ricevuta = genera_ricevuta(df_don.iloc[0])
            download_txt(ricevuta, "ricevuta_donazione.txt")
        download_excel(df_don, "donazioni")
    else:
        st.info("Nessuna donazione registrata.")

# === Quote associative ===
if sezione_attiva == "Quote associative":
    st.subheader("🧾 Quote associative")
    df_quote = pd.DataFrame([
        {"Nome": "Giulia Bianchi", "Anno": 2024, "Importo": 25, "Pagato": "Sì"},
        {"Nome": "Carlo Neri", "Anno": 2024, "Importo": 25, "Pagato": "No"},
    ])
    df_quote["Importo (€)"] = df_quote["Importo"].apply(format_currency)
    st.dataframe(df_quote.drop(columns="Importo"))
    st.info("Dati fittizi. In attesa di collegamento con AppSheet.")

# === Nuovo Movimento ===
if pagina == "nuovo_movimento":
    st.subheader("➕ Inserisci nuovo movimento contabile")
    with st.form("inserimento"):
        data_mov = st.date_input("Data", value=date.today())
        causale = st.text_input("Causale")
        centro = st.text_input("Centro di Costo")
        importo = st.number_input("Importo", step=0.01, format="%.2f")
        descrizione = st.text_area("Descrizione")
        cassa = st.selectbox("Metodo di pagamento", ["Contanti", "Bonifico", "Carta", "Altro"])
        note = st.text_input("Note")
        provincia = utente["provincia"] if utente["ruolo"] == "tesoriere" else "Tutte"
        submitted = st.form_submit_button("✅ Inserisci")
    if submitted:
        new_row = [str(data_mov), causale, centro, importo, descrizione, cassa, note, provincia]
        try:
            sh = client.open_by_url(SHEET_URL)
            ws = sh.worksheet(SHEET_NAME)
            ws.append_row(new_row)
            st.success("Movimento inserito correttamente!")
        except Exception as e:
            st.error(f"Errore durante l'inserimento: {e}")

# === Suggerimenti PDF e OAuth ===
st.sidebar.markdown("---")
st.sidebar.markdown("📤 Export PDF consigliato:")
st.sidebar.markdown("- `fpdf`\n- `pdfkit` (richiede wkhtmltopdf)\n- `reportlab`")
st.sidebar.markdown("🔐 Login Google Workspace in sviluppo (OAuth)")
