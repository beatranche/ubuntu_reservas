# pages/2_📅_Agenda.py

import streamlit as st
from functions.agenda import mostrar_agenda

def mostrar():
    st.title("📅 Agenda de Actividades")
    mostrar_agenda()