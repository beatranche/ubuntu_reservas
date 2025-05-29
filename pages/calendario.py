# pages/3_🗓️_Calendario.py

import streamlit as st
from functions.calendario import mostrar_calendario_responsive

def mostrar():
    st.title("🗓️ Calendario de Actividades")
    mostrar_calendario_responsive()