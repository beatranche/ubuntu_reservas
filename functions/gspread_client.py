import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

def get_gsheet_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],  # Usa tus secrets de Streamlit
        scopes=scopes
    )
    return gspread.authorize(credentials)
