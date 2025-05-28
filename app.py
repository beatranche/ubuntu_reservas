import streamlit as st
from functions import *

# Configuración de la página
st.set_page_config(
    page_title="Ubuntu Aventuras - Sistema de Gestión",
    page_icon="🏕️",
    layout="wide"
)

def main():
    # Verificar autenticación primero
    if not check_auth():
        st.stop()
    
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
        st.rerun()

if __name__ == "__main__":
    main()