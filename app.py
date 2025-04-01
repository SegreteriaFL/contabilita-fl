# ✅ Gestionale Contabilità ETS — Versione SCURA con controllo accessi e mobile-friendly

import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import date
from io import BytesIO
from fpdf import FPDF
from streamlit_option_menu import option_menu
import tempfile

st.set_page_config(page_title="Contabilità ETS", layout="wide")

# 🌙 Tema scuro con miglioramenti responsive base (senza downgrade)
st.markdown("""
    <style>
        html, body, .main, .block-container {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .stButton > button, .stDownloadButton > button {
            background-color: #4CAF50;
            color: white;
            width: 100%;
        }
        .css-1d391kg, .css-1v0mbdj {
            overflow-wrap: break-word;
        }
        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

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
        try:
            pdf.cell(200, 10, txt=line.encode("latin-1", "replace").decode("latin-1"), ln=True)
        except:
            pdf.cell(200, 10, txt="[Errore codifica]", ln=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        st.download_button("📄 Scarica PDF", data=tmp.read(), file_name=nome_file, mime="application/pdf")

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

# === Menu moderno (tema SCURO forzato) ===
menu_style = {
    "container": {"padding": "0!important", "background-color": "#1e1e1e"},
    "icon": {"color": "white", "font-size": "18px"},
    "nav-link": {
        "font-size": "16px",
        "text-align": "left",
        "margin": "0px",
        "color": "#FFFFFF",
        "--hover-color": "#444",
    },
    "nav-link-selected": {"background-color": "#4CAF50", "color": "white", "font-weight": "bold"},
}

with st.sidebar:
    sezione_attiva = option_menu(
        menu_title="📂 Sezioni",
        options=["Prima Nota", "Dashboard", "Rendiconto ETS", "Donazioni", "Quote associative", "Nuovo Movimento"],
        icons=["file-earmark-text", "bar-chart", "clipboard-data", "gift", "people", "plus-circle"],
        menu_icon="folder",
        default_index=0,
        styles=menu_style
    )

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

# === Sezioni operative ===
if sezione_attiva == "Prima Nota":
    df = carica_movimenti()
    st.subheader("📁 Prima Nota")
    if not df.empty:
        mese = st.selectbox("📅 Mese:", sorted(df['data'].dt.strftime("%Y-%m").unique()))
        centro_sel = st.selectbox("🏷️ Centro di costo:", ["Tutti"] + sorted(df['Centro di Costo'].dropna().unique()))
        df_mese = df[df['data'].dt.strftime("%Y-%m") == mese]
        if centro_sel != "Tutti":
            df_mese = df_mese[df_mese['Centro di Costo'] == centro_sel]

        df_mese = df_mese.copy()
        df_mese["Data"] = df_mese["data"].apply(format_date)
        df_mese["Importo (€)"] = df_mese["Importo"].apply(format_currency)
        st.dataframe(df_mese.drop(columns=["Importo", "data"]))
        st.markdown(f"**Totale entrate:** {format_currency(df_mese[df_mese['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float) > 0]['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float).sum())}")
        st.markdown(f"**Totale uscite:** {format_currency(abs(df_mese[df_mese['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float) < 0]['Importo (€)'].str.replace('.', '').str.replace(',', '.').astype(float).sum()))}")
    else:
        st.info("Nessun movimento disponibile.")

elif sezione_attiva == "Dashboard":
    df = carica_movimenti()
    st.subheader("📊 Dashboard")
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

elif sezione_attiva == "Rendiconto ETS":
    df = carica_movimenti()
    st.subheader("📄 Rendiconto ETS")
    if not df.empty:
        sezione_a = df[df["Importo"] > 0].groupby("Causale")["Importo"].sum().reset_index()
        sezione_b = df[df["Importo"] < 0].groupby("Causale")["Importo"].sum().abs().reset_index()
        st.markdown("### Sezione A - Entrate")
        st.dataframe(sezione_a)
        st.markdown("### Sezione B - Uscite")
        st.dataframe(sezione_b)
        testo_pdf = f"Rendiconto ETS\n\nEntrate:\n" + sezione_a.to_string(index=False) + "\n\nUscite:\n" + sezione_b.to_string(index=False)
        download_pdf(testo_pdf, "rendiconto_ets.pdf")
    else:
        st.info("Nessun dato disponibile.")

elif sezione_attiva == "Donazioni":
    df = carica_movimenti()
    st.subheader("❤️ Donazioni")
    df_don = df[df["Causale"] == "Donazione"]
    if not df_don.empty:
        st.dataframe(df_don)
        st.markdown(f"**Totale donazioni:** {format_currency(df_don['Importo'].sum())}")
        for i, r in df_don.iterrows():
            with st.expander(f"📄 Ricevuta per donazione del {format_date(r['data'])} ({format_currency(r['Importo'])})"):
                ricevuta = genera_ricevuta_pdf(r)
                download_pdf(ricevuta, f"ricevuta_donazione_{i}.pdf")
    else:
        st.info("Nessuna donazione registrata.")

elif sezione_attiva == "Quote associative":
    st.subheader("🧾 Quote associative")
    st.info("Funzionalità in sviluppo. Collegamento a AppSheet previsto.")

elif sezione_attiva == "Nuovo Movimento":
    if utente["ruolo"] in ["superadmin", "tesoriere"]:
        st.subheader("➕ Nuovo Movimento")
        df = carica_movimenti()
        today = date.today()
        data_mov = st.date_input("Data", today)
        causale = st.text_input("Causale")
        centro = st.text_input("Centro di Costo")
        importo = st.number_input("Importo (€)", step=0.01)
        descrizione = st.text_input("Descrizione")
        cassa = st.selectbox("Metodo di pagamento", ["Contanti", "Bonifico", "Carta", "PayPal"])
        note = st.text_area("Note")
        submitted = st.button("📤 Inserisci movimento")
        if submitted:
            if not causale or importo == 0:
                st.error("Causale e importo sono obbligatori!")
            else:
                try:
                    ws = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
                    nuova_riga = [str(data_mov), causale, centro, importo, descrizione, cassa, note, utente["provincia"]]
                    ws.append_row(nuova_riga)
                    st.success("Movimento registrato con successo!")
                except Exception as e:
                    st.error(f"Errore durante l'inserimento: {e}")
    else:
        st.warning("Sezione riservata ai tesorieri e al superadmin.")
