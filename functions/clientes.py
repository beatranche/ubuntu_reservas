# functions/clientes.py
# functions/clientes.py
import streamlit as st
from datetime import datetime
from functions.data_utils import cargar_clientes, guardar_cliente
from functions.reservas import calcular_precio, ACTIVIDADES_MANUALES

def mostrar_formulario_cliente():
    st.header("Formulario de Clientes")

    if st.button("🔄 Actualizar reservas", key="refresh_reservations"):
        st.cache_data.clear()
        st.rerun()    
    
    # Campos que afectan el precio - FUERA del formulario para que se actualicen automáticamente
    actividad = st.selectbox("Actividad*", [
        "Kayak", "Paddle surf", "Hidropedales", "Ruta Bisontes", 
        "Ebikes","Alquiler equipos ferrata", "Grupos", "Senderismo"
    ], key="actividad_select")
    
    duracion = st.selectbox("Duración*", ["1 hora", "2 horas", "Medio día", "Todo el día"], key="duracion_select")
    
    personas = st.number_input("Número de Personas*", min_value=1, max_value=50, value=1, key="personas_input")
    
    # Cálculo automático del precio en tiempo real
    precio_calculado = calcular_precio(
        actividad,
        duracion,
        personas,
        0.0  # precio base para cálculo
    )
    
    # Campo de precio editable que se actualiza automáticamente
    precio_final = st.number_input(
        "💰 Precio final (editable)*",
        value=float(precio_calculado),
        min_value=0.0,
        step=0.01,
        format="%.2f",
        help="Este precio se calcula automáticamente, pero puedes editarlo si es necesario",
        key="precio_input"
    )
    
    with st.form("form_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            id_cliente = st.text_input("ID Cliente*")
            sexo = st.selectbox("Sexo*", ["Masculino", "Femenino"])
            fecha_nacimiento = st.date_input("Fecha de Nacimiento*", min_value=datetime(1900,1,1))
            ciudad = st.text_input("Ciudad*", value="León")
            pais = st.text_input("País*", value="España")
        
        with col2:
            fecha_actividad = st.date_input("Fecha de Actividad*", min_value=datetime(1900,1,1))
            hora_inicio = st.time_input("Hora de Inicio*")
        
        notas = st.text_area("Notas Adicionales")
        
        submitted = st.form_submit_button("💾 Guardar Cliente")
        
        if submitted:  
            # Validar campos obligatorios
            if not all([id_cliente, sexo, fecha_nacimiento, ciudad, pais, actividad, fecha_actividad, hora_inicio, duracion, personas]):
                st.error("Por favor complete todos los campos obligatorios (*)")
            else:
                cliente_data = {
                    'id': id_cliente,
                    'sexo': sexo,
                    'fecha_nacimiento': fecha_nacimiento.strftime("%d/%m/%Y"),
                    'ciudad': ciudad,
                    'pais': pais,
                    'actividad': actividad,
                    'fecha_actividad': fecha_actividad.strftime("%d/%m/%Y"),
                    'hora_inicio': hora_inicio.strftime("%H:%M"),
                    'duracion': duracion,
                    'personas': personas,
                    'precio': precio_final,
                    'notas': notas
                }
                
                if guardar_cliente(cliente_data):
                    st.success("Cliente guardado exitosamente!")
                    st.balloons()
                else:
                    st.error("Error al guardar el cliente")