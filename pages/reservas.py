# pages/1_📝_Reservas.py

import streamlit as st
from functions.reservas import mostrar_formulario, ultimas_reservas

def mostrar():
    st.title("📝 Nueva Reserva")
    mostrar_formulario()
    ultimas_reservas()