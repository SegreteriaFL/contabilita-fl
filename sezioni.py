import streamlit as st
import pandas as pd
from datetime import date

# Funzione per "Prima Nota"
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

# Funzione per "Saldo da Estratto Conto"
def mostra_situazione_conti(client, SHEET_URL, SHEET_NAME):
    st.subheader("📊 Saldo da Estratto Conto")
    
    # Lista dei conti correnti
    conti_correnti = [
        "Unicredit Nazionale", 
        "Unicredit Fiume di Pace", 
        "Unicredit Kimata", 
        "Unicredit Mari e Vulcani", 
        "Banco Posta", 
        "Cassa Contanti Sede", 
        "Conto PayPal", 
        "Accrediti su c/c da regolarizzare"
    ]
    
    # Anno selezionabile per il saldo
    anno = st.selectbox("Seleziona l'anno", [str(year) for year in range(2020, 2026)])

    saldi = {}

    # Inserimento saldi per ogni conto corrente
    for conto in conti_correnti:
        saldo = st.number_input(f"Saldo {conto} ({anno})", min_value=0.0, format="%.2f", key=conto)
        saldi[conto] = saldo

    if st.button("Salva saldi"):
        # Salvataggio dei saldi per conto corrente
        try:
            worksheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
            for conto, saldo in saldi.items():
                worksheet.append_row([anno, conto, saldo])
            st.success("Saldi estratti salvati correttamente!")
        except Exception as e:
            st.error("❌ Errore durante il salvataggio dei saldi.")
            st.exception(e)

# Funzione per il "Rendiconto ETS"
def mostra_rendiconto(carica_movimenti, format_currency, download_pdf):
    df = carica_movimenti()
    st.subheader("📄 Rendiconto ETS")
    if not df.empty:
        sezione_a = df[df["Importo"] > 0].groupby("Causale")["Importo"].sum().reset_index()
        sezione_b = df[df["Importo"] < 0].groupby("Causale")["Importo"].sum().abs().reset_index()

        st.markdown("### Sezione A - Entrate")
        st.dataframe(sezione_a)

        st.markdown("### Sezione B - Uscite")
        st.dataframe(sezione_b)

        entrate = sezione_a["Importo"].sum()
        uscite = sezione_b["Importo"].sum()
        saldo = entrate - uscite

        # Confronto con i saldi estratti da "Saldo da Estratto Conto"
        saldi_estratti = { 
            "Unicredit Nazionale": 82838.02,
            "Unicredit Fiume di Pace": 13277.98,
            "Unicredit Kimata": 6469.08,
            "Unicredit Mari e Vulcani": 6428.30,
            "Banco Posta": 3276.94,
            "Cassa Contanti Sede": 10.07,
            "Conto PayPal": 95.53,
            "Accrediti su c/c da regolarizzare": 0.00
        }
        
        totale_conti = sum(saldi_estratti.values())
        delta = saldo - totale_conti

        st.markdown("### 🔢 Saldo finale e confronto contabile")
        st.metric("Sezione A - Totale Entrate", format_currency(entrate))
        st.metric("Sezione B - Totale Uscite", format_currency(uscite))
        st.metric("Saldo Finale (A - B)", format_currency(saldo))
        
        st.metric("Totale conti correnti (estratto)", format_currency(totale_conti))
        st.metric("Delta contabile", format_currency(delta))
        if abs(delta) < 1:
            st.success("Verifica superata: nessuna discrepanza.")
        else:
            st.error("Attenzione: il delta è diverso da 0!")

        testo = f"Entrate: {format_currency(entrate)}\nUscite: {format_currency(uscite)}\nSaldo: {format_currency(saldo)}"
        download_pdf(testo, "rendiconto_ets")
    else:
        st.info("Nessun dato disponibile.")
