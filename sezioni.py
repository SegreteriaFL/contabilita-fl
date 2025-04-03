# ✅ sezioni.py — versione finale compatibile con app.py, con mostra_dashboard inclusa
import streamlit as st
import plotly.express as px
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

def mostra_prima_nota(utente, carica_movimenti, format_currency, format_date, download_excel):
    df = carica_movimenti()
    st.subheader("📁 Prima Nota")
    if not df.empty:
        mesi = sorted(df['data'].dt.strftime("%Y-%m").unique())
        mese = st.selectbox("📅 Mese:", mesi)
        centro_sel = st.selectbox("🏷️ Centro di costo:", ["Tutti"] + sorted(df['Centro di Costo'].dropna().unique()))
        df_mese = df[df['data'].dt.strftime("%Y-%m") == mese]
        if centro_sel != "Tutti":
            df_mese = df_mese[df_mese['Centro di Costo'] == centro_sel]

        df_mese = df_mese.copy()
        df_mese["Data"] = df_mese["data"].apply(format_date)
        df_mese["Importo (€)"] = df_mese["Importo"].apply(format_currency)

        st.dataframe(df_mese.drop(columns=["Importo", "data"]))

        entrate = df_mese[df_mese["Importo"] > 0]["Importo"].sum()
        uscite = df_mese[df_mese["Importo"] < 0]["Importo"].sum()
        st.markdown(f"**Totale entrate:** {format_currency(entrate)}")
        st.markdown(f"**Totale uscite:** {format_currency(abs(uscite))}")
        st.markdown(f"**Saldo:** {format_currency(entrate + uscite)}")

        download_excel(df_mese.drop(columns=["Importo", "data"]), "prima_nota")
    else:
        st.info("Nessun movimento disponibile.")

def mostra_dashboard(carica_movimenti):
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

        st.plotly_chart(
            px.bar(
                df.groupby("Centro di Costo")["Importo"].sum().reset_index(),
                x="Centro di Costo",
                y="Importo",
                title="Totale per centro di costo"
            ),
            use_container_width=True
        )
    else:
        st.info("Nessun dato disponibile.")

def mostra_rendiconto(carica_movimenti, format_currency, download_pdf):
    df = carica_movimenti()
    st.subheader("📄 Rendiconto ETS")
    if not df.empty:
        entrate = df[df["Importo"] > 0]["Importo"].sum()
        uscite = df[df["Importo"] < 0]["Importo"].sum().abs()
        saldo = entrate - uscite

        st.metric("Sezione A - Entrate", format_currency(entrate))
        st.metric("Sezione B - Uscite", format_currency(uscite))
        st.metric("Saldo Finale", format_currency(saldo))

        saldi_bancari = {
            "Unicredit Nazionale": 82838.02,
            "Unicredit Fiume di Pace": 13277.98,
            "Unicredit Kimata": 6469.08,
            "Unicredit Mari e Vulcani": 6428.30,
            "Banco Posta": 3276.94,
            "Cassa Contanti Sede": 10.07,
            "Conto PayPal": 95.53,
            "Accrediti da regolarizzare": 0.00
        }
        totale_conti = sum(saldi_bancari.values())
        delta = saldo - totale_conti

        st.metric("Totale conti correnti", format_currency(totale_conti))
        st.metric("Delta contabile", format_currency(delta))
        if abs(delta) < 1:
            st.success("Verifica superata: nessuna discrepanza.")
        else:
            st.error("Attenzione: il delta è diverso da 0!")

        testo = f"Entrate: {format_currency(entrate)}\nUscite: {format_currency(uscite)}\nSaldo: {format_currency(saldo)}"
        download_pdf(testo, "rendiconto_ets")
    else:
        st.info("Nessun dato disponibile.")

def mostra_donazioni(carica_movimenti, format_currency, format_date, genera_ricevuta_pdf, download_pdf):
    df = carica_movimenti()
    st.subheader("❤️ Donazioni")
    df_don = df[df["Causale"].str.lower().str.contains("donazione", na=False)]
    if not df_don.empty:
        df_don = df_don.copy()
        df_don["Data"] = df_don["data"].apply(format_date)
        df_don["Importo (€)"] = df_don["Importo"].apply(format_currency)
        st.dataframe(df_don.drop(columns=["Importo", "data"]))
        st.markdown(f"**Totale donazioni:** {format_currency(df_don['Importo'].sum())}")

        for i, row in df_don.iterrows():
            with st.expander(f"📄 Ricevuta {i+1} - {format_currency(row['Importo'])}"):
                testo = genera_ricevuta_pdf(row)
                download_pdf(testo, f"ricevuta_donazione_{i+1}.pdf")
    else:
        st.info("Nessuna donazione registrata.")

def mostra_quote():
    st.subheader("🧾 Quote associative")
    st.info("Funzionalità in sviluppo: collegamento con AppSheet previsto.")

def mostra_nuovo_movimento(utente, client, SHEET_URL, SHEET_NAME):
    st.subheader("➕ Nuovo Movimento")
    if utente["ruolo"] not in ["superadmin", "tesoriere"]:
        st.warning("Sezione riservata ai tesorieri e al superadmin.")
        return

    riferimenti = pd.DataFrame(client.open_by_url(SHEET_URL).worksheet("riferimenti").get_all_records())
    causali = riferimenti['Causale'].dropna().unique().tolist()
    centri = riferimenti['Centro di costo'].dropna().unique().tolist()
    casse = riferimenti['Cassa'].dropna().unique().tolist()

    with st.form("nuovo_movimento"):
        data_mov = st.date_input("Data", value=date.today())
        causale = st.selectbox("Causale", causali)
        centro = st.selectbox("Centro di costo", centri)
        importo = st.number_input("Importo", step=0.01, format="%.2f")
        descrizione = st.text_area("Descrizione")
        cassa = st.selectbox("Metodo di pagamento", casse)
        note = st.text_input("Note")
        submitted = st.form_submit_button("💾 Salva movimento")

        if submitted:
            if not causale or importo == 0:
                st.error("Causale e importo sono obbligatori!")
            else:
                ws = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
                nuova_riga = [
                    str(data_mov), causale, centro, importo,
                    descrizione, cassa, note, utente["provincia"]
                ]
                ws.append_row(nuova_riga)
                st.success("Movimento inserito correttamente!")
