import streamlit as st

def mostra_prima_nota(client, ruolo, riferimenti):
    st.subheader("📄 Prima Nota")
    st.info("Questa è una sezione placeholder.")

def mostra_dashboard(client):
    st.subheader("📊 Dashboard")
    st.info("Dashboard in costruzione.")

def mostra_rendiconto(client):
    st.subheader("📋 Rendiconto ETS")
    st.info("Sezione A e B del rendiconto in arrivo.")

def mostra_donazioni(client):
    st.subheader("🎁 Donazioni")
    st.info("Donazioni in arrivo.")

def mostra_quote(client):
    st.subheader("👥 Quote associative")
    st.info("Placeholder per quote associative.")

def mostra_nuovo_movimento(client, ruolo, riferimenti):
    st.subheader("➕ Nuovo Movimento")
    if ruolo not in ["superadmin", "tesoriere"]:
        st.warning("Non hai i permessi per inserire nuovi movimenti.")
        return
    st.success("Form in arrivo!")

def mostra_saldo(client):
    st.subheader("💳 Saldo da Estratto Conto")
    st.info("Sezione in sviluppo.")
    
