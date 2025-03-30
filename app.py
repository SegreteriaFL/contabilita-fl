import streamlit as st
import pandas as pd

st.set_page_config(page_title="Contabilità ETS", layout="wide")
st.title("📊 Gestionale Contabilità ETS 2024")

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

# Carica dati
movimenti = carica_dati()

# Navigazione con tabs
menu = st.sidebar.radio("📁 Sezioni", ["Prima Nota", "Rendiconto ETS", "Dashboard", "Donazioni", "Quote associative"])

# -------------------
# 1. PRIMA NOTA
# -------------------
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

# -------------------
# 2. RENDICONTO ETS
# -------------------
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

# -------------------
# 3. DASHBOARD
# -------------------
elif menu == "Dashboard":
    st.header("📈 Cruscotto finanziario sintetico")
    mensili = movimenti.groupby(movimenti['data'].dt.to_period('M'))['Importo'].sum().reset_index()
    mensili['data'] = mensili['data'].astype(str)
    st.line_chart(mensili.set_index('data'))

    st.subheader("📊 Ripartizione per centro di costo")
    per_centro = movimenti.groupby("Centro di Costo")["Importo"].sum().reset_index()
    st.bar_chart(per_centro.set_index("Centro di Costo"))

# -------------------
# 4. DONAZIONI
# -------------------
elif menu == "Donazioni":
    st.header("🎁 Elenco donazioni registrate")
    donazioni = movimenti[movimenti['Causale'].str.lower().str.contains("donazione")]
    st.dataframe(donazioni, use_container_width=True)
    totale_donazioni = donazioni['Importo'].sum()
    st.markdown(f"**Totale donazioni registrate:** {totale_donazioni:.2f} €")

# -------------------
# 5. QUOTE ASSOCIATIVE
# -------------------
elif menu == "Quote associative":
    st.header("👥 Gestione Quote Associative")
    st.info("🛠️ Integrazione con anagrafica soci in corso. In futuro: scadenze, ricevute, stato pagamenti.")
    st.write("Puoi sincronizzare con il tuo foglio AppSheet per tracciare le quote versate e da versare.")
