import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
import plotly.express as px
import tempfile

# ✅ Funzioni utili
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


# === Connessione Google Sheets ===
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


# === Carica i dati da Google Sheets ===
def carica_movimenti():
    df = pd.DataFrame(client.open_by_url(SHEET_URL).worksheet(SHEET_NAME).get_all_records())
    df.columns = df.columns.str.strip()
    df["Importo"] = pd.to_numeric(df["Importo"], errors="coerce").fillna(0)
    return df


# === Sezioni dell'App ===
def mostra_prima_nota():
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


def mostra_dashboard():
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


# === Routing - Navigazione ===
def routing():
    sezione_attiva = st.sidebar.selectbox(
        "Seleziona Sezione",
        ["Prima Nota", "Dashboard"]
    )

    if sezione_attiva == "Prima Nota":
        mostra_prima_nota()
    elif sezione_attiva == "Dashboard":
        mostra_dashboard()


# === Avvia l'app ===
if __name__ == "__main__":
    routing()
