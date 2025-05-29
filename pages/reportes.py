# pages/4_📊_Reportes.py

import streamlit as st
from functions.auth import check_auth
from functions.clientes import mostrar_formulario_cliente
from functions.reportes import generar_reportes

def mostrar():
    # Verificar autenticación
    if not check_auth():
        st.stop()

    # ELIMINAR st.set_page_config() DE AQUÍ
    st.title("📊 Reportes Avanzados y Gestión de Clientes")

    # Tabs principales
    tab1, tab2 = st.tabs(["📝 Ingresar Datos de Clientes", "📈 Gráficos y Predicciones"])

    with tab1:
        mostrar_formulario_cliente()

    with tab2:
        generar_reportes()