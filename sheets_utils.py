import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json
import os

SHEET_NAME = "Prima Nota 2024"

def get_gsheet_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = st.secrets["gcp_service_account"]
        else:
            creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Errore nella connessione a Google Sheets: {e}")
        st.stop()

def carica_riferimenti(client):
    try:
        sh = client.open(SHEET_NAME)
        ws = sh.worksheet("riferimenti")
        return ws.get_all_records()
    except Exception as e:
        st.warning(f"Impossibile caricare il foglio 'riferimenti': {e}")
        return []
