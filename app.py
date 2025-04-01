# ✅ Gestionale Contabilità ETS — Versione in stile chiaro, semplificata e funzionante

import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
from io import BytesIO
from fpdf import FPDF
from streamlit_option_menu import option_menu

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

# === Menu moderno (tema chiaro forzato) ===
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

# === Sezione: Prima Nota ===
if sezione_attiva == "Prima Nota":
    st.subheader("📁 Prima Nota")
    df = carica_movimenti()
    if not df.empty:
        mese = st.selectbox("📅 Mese", sorted(df['data'].dt.strftime("%Y-%m").unique()), key="mese")
        centro_sel = st.selectbox("🏷️ Centro di costo", ["Tutti"] + sorted(df['Centro di Costo'].dropna().unique()), key="centro")
        df_mese = df[df['data'].dt.strftime("%Y-%m") == mese]
        if centro_sel != "Tutti":
            df_mese = df_mese[df_mese['Centro di Costo'] == centro_sel]

        df_mese["Data"] = df_mese["data"].dt.strftime("%d/%m/%Y")
        df_mese["Importo (€)"] = df_mese["Importo"].apply(format_currency)

        st.dataframe(df_mese.drop(columns=["data", "Importo"]))

        entrate = df_mese[df_mese['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float) > 0]['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float).sum()
        uscite = df_mese[df_mese['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float) < 0]['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float).sum()

        st.success(f"💰 Entrate: {format_currency(entrate)}")
        st.error(f"💸 Uscite: {format_currency(abs(uscite))}")
        st.info(f"🧮 Saldo: {format_currency(entrate + uscite)}")
        download_excel(df_mese, "prima_nota_filtrata")
    else:
        st.warning("Nessun dato disponibile nella Prima Nota.")

# === Sezione: Dashboard ===
elif sezione_attiva == "Dashboard":
    st.subheader("📊 Dashboard mensile e per centro di costo")
    df = carica_movimenti()
    if not df.empty:
        df["mese"] = df["data"].dt.to_period("M").astype(str)
        entrate = df[df["Importo"] > 0].groupby("mese")["Importo"].sum().reset_index()
        uscite = df[df["Importo"] < 0].groupby("mese")["Importo"].sum().abs().reset_index()
        by_centro = df.groupby("Centro di Costo")["Importo"].sum().reset_index()

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.bar(entrate, x="mese", y="Importo", title="Entrate per mese"), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(uscite, x="mese", y="Importo", title="Uscite per mese"), use_container_width=True)
        st.plotly_chart(px.bar(by_centro, x="Centro di Costo", y="Importo", title="Totale per centro di costo"), use_container_width=True)
    else:
        st.warning("Nessun dato disponibile per la dashboard.")

# === Sezione: Rendiconto ETS ===
elif sezione_attiva == "Rendiconto ETS":
    st.subheader("📄 Rendiconto ETS")
    df = carica_movimenti()
    if not df.empty:
        sezione_a = df[df["Importo"] > 0].groupby("Causale")["Importo"].sum().reset_index()
        sezione_b = df[df["Importo"] < 0].groupby("Causale")["Importo"].sum().abs().reset_index()

        st.markdown("### Sezione A - Entrate")
        st.dataframe(sezione_a)
        st.markdown("### Sezione B - Uscite")
        st.dataframe(sezione_b)

        testo_pdf = """Rendiconto ETS

Entrate:
"""


Entrate:
"
        for _, row in sezione_a.iterrows():
            testo_pdf += f"- {row['Causale']}: {format_currency(row['Importo'])}
"
        testo_pdf += "
Uscite:
"
        for _, row in sezione_b.iterrows():
            testo_pdf += f"- {row['Causale']}: {format_currency(row['Importo'])}
"

        download_pdf(testo_pdf, "rendiconto_ets.pdf")
    else:
        st.warning("Nessun dato disponibile per il rendiconto.")

# === Sezione: Donazioni ===
elif sezione_attiva == "Donazioni":
    st.subheader("❤️ Donazioni")
    df = carica_movimenti()
    df_don = df[df["Causale"] == "Donazione"]
    if not df_don.empty:
        df_don["Data"] = df_don["data"].dt.strftime("%d/%m/%Y")
        df_don["Importo (€)"] = df_don["Importo"].apply(format_currency)
        st.dataframe(df_don.drop(columns=["Importo", "data"]))

        totale = df_don["Importo (€)"].str.replace('.', '').str.replace(',', '.').astype(float).sum()
        st.success(f"Totale donazioni: {format_currency(totale)}")

        if st.button("📄 Scarica ricevuta ultima donazione"):
            download_pdf(genera_ricevuta_pdf(df_don.iloc[-1]), "ricevuta_donazione.pdf")
    else:
        st.warning("Nessuna donazione registrata.")

# === Sezione: Quote associative ===
elif sezione_attiva == "Quote associative":
    st.subheader("🧾 Quote associative")
    st.info("Funzionalità in sviluppo: sarà collegata a Google Sheets o AppSheet.")

# === Sezione: Nuovo Movimento ===
elif pagina == "nuovo_movimento":
    st.subheader("➕ Inserisci nuovo movimento contabile")
    with st.form("nuovo_movimento_form"):
        data_mov = st.date_input("Data", value=date.today())
        causale = st.text_input("Causale")
        centro = st.text_input("Centro di costo")
        importo = st.number_input("Importo", step=0.01, format="%.2f")
        descrizione = st.text_area("Descrizione")
        cassa = st.selectbox("Metodo di pagamento", ["Contanti", "Bonifico", "PayPal", "Altro"])
        note = st.text_input("Note")
        submitted = st.form_submit_button("✅ Inserisci movimento")

        if submitted:
            if not causale or importo == 0:
                st.error("Causale e importo sono obbligatori!")
            else:
                sh = client.open_by_url(SHEET_URL)
                ws = sh.worksheet(SHEET_NAME)
                nuova_riga = [
                    str(data_mov),
                    causale,
                    centro,
                    round(importo, 2),
                    descrizione,
                    cassa,
                    note,
                    utente.get("provincia", "")
                ]
                ws.append_row(nuova_riga)
                st.success("✅ Movimento inserito con successo!")

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
