import streamlit as st
import pandas as pd

def rendiconto_ets(df, saldi_finali_dict):
    st.subheader("Rendiconto ETS")

    sezione_a = df[df["Tipo"] == "Entrata"]["Importo"].sum()
    sezione_b = df[df["Tipo"] == "Uscita"]["Importo"].sum()
    saldo_finale = sezione_a - sezione_b

    st.metric("Sezione A (Entrate)", f"€ {sezione_a:,.2f}")
    st.metric("Sezione B (Uscite)", f"€ {sezione_b:,.2f}")
    st.metric("Saldo Finale (A - B)", f"€ {saldo_finale:,.2f}")

    tabella_saldi = pd.DataFrame(list(saldi_finali_dict.items()), columns=["Cassa", "Saldo"])
    totale_saldi = tabella_saldi["Saldo"].sum()

    delta = saldo_finale - totale_saldi
    st.metric("Totale Saldi Contabili", f"€ {totale_saldi:,.2f}")
    st.metric("Delta (contabile - reale)", f"€ {delta:,.2f}")

    if abs(delta) > 1:
        st.error("Attenzione: delta diverso da 0. Verifica i movimenti.")
    else:
        st.success("Controllo superato: Delta = 0")
