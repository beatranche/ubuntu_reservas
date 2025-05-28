import streamlit as st
from functions import *

# Configuración de la página
st.set_page_config(
    page_title="Ubuntu Aventuras - Sistema de Gestión",
    page_icon="🏕️",
    layout="wide"
)
# =====================================================
# ELIMINAR MENÚ SUPERIOR DERECHO Y PIE DE PÁGINA
# =====================================================
hide_menu_style = """
<style>
/* Ocultar menú hamburguesa */
#MainMenu {visibility: hidden;}

/* Ocultar pie de página */
footer {visibility: hidden;}

/* Ocultar botón "Manage App" */
.stDeployButton {display:none;}

/* Ocultar toolbar superior derecho (share, edit, etc) */
div[data-testid="stToolbar"] {display:none !important;}

/* Ocultar botón flotante "Manage App" */
div[data-testid="stDeployButton"] {display:none !important;}

/* Ocultar botones de GitHub */
div[data-testid="baseButton-header"] {display:none !important;}

/* Ocultar el botón de "Reportar un problema" */
div[data-testid="stStatusWidget"] {display:none !important;}

/* Ocultar espacio vacío que queda al ocultar elementos */
.stApp > header {display: none !important;}
</style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

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
    
    # =================================================================
    # A PARTIR DE AQUÍ SOLO SE EJECUTA SI EL USUARIO ESTÁ AUTENTICADO
    # =================================================================
    
    # Resto de la aplicación
    st.title("🏕️ Ubuntu Aventuras - Sistema de Gestión")
    
    # Verificar si hay una reserva siendo editada
    editing_reservation = st.session_state.get('reserva_seleccionada') is not None
    
    # Si se está editando una reserva, mostrar solo el calendario
    if editing_reservation:
        st.info("📝 Editando reserva - Use el formulario de abajo para modificar o cancelar")
        mostrar_calendario()
    else:
        # Mostrar pestañas normales
        tabs = st.tabs(["📝 Nueva Reserva", "📅 Agenda", "🗓️ Calendario"])
        
        with tabs[0]:
            mostrar_formulario()
            ultimas_reservas()
        
        with tabs[1]:
            mostrar_agenda()
        
        with tabs[2]:
            mostrar_calendario()
    
    # Sección de últimas reservas en la barra lateral
    st.sidebar.header("Últimas Reservas")
    datos = cargar_datos()
    if not datos.empty:
        for _, fila in datos.head(5).iterrows():
            st.sidebar.markdown(f"""
            **{fila['Nombre']}**  
            {fila['Actividad']} - {fila['Fecha Actividad'].strftime('%d/%m')}  
            👥 {fila['Personas']} pers. | 💶 {fila['Precio']}€
            """)
    else:
        st.sidebar.info("No hay reservas recientes")
    
    # Botón para limpiar session state en caso de error
    if editing_reservation:
        if st.sidebar.button("🔄 Volver al inicio"):
            # Limpiar session state
            keys_to_clear = ['reserva_seleccionada']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    if st.sidebar.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()
    
    # Botón para cerrar sesión
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.mostrar_login = True  # Mostrar login al cerrar sesión
        st.rerun()

if __name__ == "__main__":
    main()