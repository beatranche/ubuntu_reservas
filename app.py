# app.py
import streamlit as st
from functions.auth import check_auth, mostrar_login, mostrar_formulario_registro
from pages import reservas, agenda, calendario, reportes

# Limpiar caché al iniciar
st.cache_data.clear()

# Configuración de la página
st.set_page_config(
    page_title="Ubuntu Aventuras - Sistema de Gestión",
    page_icon="🏕️",
    layout="wide"
)

def main():
    # Inicializar estados de sesión para autenticación
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'mostrar_registro' not in st.session_state:
        st.session_state.mostrar_registro = False
    if 'mostrar_login' not in st.session_state:
        st.session_state.mostrar_login = True
    
    # Mostrar formulario de registro si está activo
    if st.session_state.mostrar_registro:
        mostrar_formulario_registro()
        return
    
    # Mostrar formulario de login si no está logueado
    if not st.session_state.logged_in and st.session_state.mostrar_login:
        mostrar_login()
        return
    
    # Usuario autenticado: mostrar la aplicación
    st.sidebar.title("Navegación")
    pagina = st.sidebar.radio(
        "Ir a:",
        ["Reservas", "Agenda", "Calendario", "Reportes"]
    )
    
    if pagina == "Reservas":
        reservas.mostrar()
    elif pagina == "Agenda":
        agenda.mostrar()
    elif pagina == "Calendario":
        calendario.mostrar()
    elif pagina == "Reportes":
        reportes.mostrar()

if __name__ == "__main__":
    main()