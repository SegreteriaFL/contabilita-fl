
import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

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

# === Connessione a Google Sheets per scrittura ===
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]
creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/edit")
worksheet = sh.sheet1

# === Caricamento dati da CSV ===
@st.cache_data
def carica_dati():
    url = "https://docs.google.com/spreadsheets/d/1_Dj2IcT1av_UXamj0sFAuslIQ-NYrRRAyI9A31eXwS4/export?format=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    df['Importo'] = (
        df['Importo']
        .astype(str)
        .str.replace('€', '', regex=False)
        .str.replace(',', '.', regex=False)
        .str.strip()
    )
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data', 'Importo'])
    return df

movimenti = carica_dati()

if utente['ruolo'] == 'tesoriere':
    movimenti = movimenti[movimenti['Centro di Costo'].str.contains(utente['provincia'], case=False, na=False)]

# === Menu ===
menu_base = ["Prima Nota", "Dashboard"]
menu_esteso = menu_base + ["Rendiconto ETS", "Donazioni"]
menu_admin = menu_esteso + ["Quote associative"]
if utente['ruolo'] in ["superadmin", "tesoriere"]:
    menu_admin.append("➕ Nuovo movimento")

menu = st.sidebar.radio("📁 Sezioni", menu_admin if utente['ruolo'] == "superadmin"
                        else menu_esteso if utente['ruolo'] in ["supervisore", "tesoriere"]
                        else menu_base)

# === Sezioni ===
if menu == "Prima Nota":
    st.header("📒 Prima Nota - movimenti contabili")
    col1, col2 = st.columns(2)
    mesi = movimenti['data'].dt.strftime('%Y-%m').sort_values().unique()
    centri = movimenti['Centro di Costo'].dropna().unique()
    mese_sel = col1.selectbox("📆 Seleziona mese:", mesi)
    centro_sel = col2.selectbox("🏷️ Centro di costo:", ["Tutti"] + list(centri))

    df_filt = movimenti[movimenti['data'].dt.strftime('%Y-%m') == mese_sel]
    if centro_sel != "Tutti":
        df_filt = df_filt[df_filt['Centro di Costo'] == centro_sel]

    st.dataframe(df_filt, use_container_width=True)
    entrate = df_filt[df_filt['Importo'] > 0]['Importo'].sum()
    uscite = df_filt[df_filt['Importo'] < 0]['Importo'].sum()
    saldo = entrate + uscite
    st.markdown(f"**Totale entrate:** {entrate:.2f} €")
    st.markdown(f"**Totale uscite:** {uscite:.2f} €")
    st.markdown(f"**Saldo del mese:** {saldo:.2f} €")

elif menu == "Rendiconto ETS":
    st.header("📑 Rendiconto per cassa ETS (Sezione A & B)")
    sezione_a = movimenti[movimenti['Importo'] > 0].groupby("Causale")["Importo"].sum().reset_index()
    sezione_b = movimenti[movimenti['Importo'] < 0].groupby("Causale")["Importo"].sum().reset_index()
    st.subheader("📥 Sezione A – Entrate")
    st.dataframe(sezione_a, use_container_width=True)
    st.subheader("📤 Sezione B – Uscite")
    st.dataframe(sezione_b, use_container_width=True)
    totale_a = sezione_a['Importo'].sum()
    totale_b = sezione_b['Importo'].sum()
    st.markdown(f"**Totale entrate (A):** {totale_a:.2f} €")
    st.markdown(f"**Totale uscite (B):** {totale_b:.2f} €")
    st.markdown(f"**Saldo finale:** {totale_a + totale_b:.2f} €")

elif menu == "Dashboard":
    st.header("📈 Cruscotto finanziario sintetico")
    mensili = movimenti.groupby(movimenti['data'].dt.to_period('M'))['Importo'].sum().reset_index()
    mensili['data'] = mensili['data'].astype(str)
    st.line_chart(mensili.set_index('data'))
    st.subheader("📊 Ripartizione per centro di costo")
    per_centro = movimenti.groupby("Centro di Costo")["Importo"].sum().reset_index()
    st.bar_chart(per_centro.set_index("Centro di Costo"))

elif menu == "Donazioni":
    st.header("🎁 Elenco donazioni registrate")
    donazioni = movimenti[movimenti['Causale'].str.lower().str.contains("donazione")]
    st.dataframe(donazioni, use_container_width=True)
    totale_donazioni = donazioni['Importo'].sum()
    st.markdown(f"**Totale donazioni registrate:** {totale_donazioni:.2f} €")

elif menu == "Quote associative":
    st.header("👥 Gestione Quote Associative")
    st.info("🛠️ Integrazione con anagrafica soci in corso. In futuro: scadenze, ricevute, stato pagamenti.")
    st.write("Puoi sincronizzare con il tuo foglio AppSheet per tracciare le quote versate e da versare.")

elif menu == "➕ Nuovo movimento":
    st.header("➕ Aggiungi nuovo movimento contabile")

    with st.form("nuovo_movimento"):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        importo = col2.number_input("Importo (€)", step=0.01, format="%.2f")
        causale = st.text_input("Causale")
        centro = st.text_input("Centro di Costo", value=utente['provincia'] if utente['provincia'] != "Tutte" else "")
        descrizione = st.text_area("Descrizione", height=60)
        cassa = st.selectbox("Cassa", ["Cassa", "Bonifico", "Altro"])
        note = st.text_area("Note", height=40)
        submitted = st.form_submit_button("📤 Salva movimento")

        if submitted:
            try:
                nuova_riga = [str(data), causale, centro, importo, descrizione, cassa, note]
                worksheet.append_row(nuova_riga, value_input_option="USER_ENTERED")
                st.success("✅ Movimento aggiunto con successo!")
                st.balloons()
            except Exception as e:
                st.error(f"Errore durante il salvataggio: {e}")
