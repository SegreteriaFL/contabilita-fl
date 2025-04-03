import streamlit as st
import pandas as pd

def mostra_donazioni(df):
    st.subheader("Elenco Donazioni")

    donazioni = df[df["Causale"].str.lower().str.contains("donazione", na=False)]
    st.dataframe(donazioni)

    totale_donazioni = donazioni["Importo"].sum()
    st.metric("Totale Donazioni", f"€ {totale_donazioni:,.2f}")

    if donazioni.empty:
        st.warning("Nessuna donazione trovata.")
