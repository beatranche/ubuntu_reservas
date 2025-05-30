# functions/agenda.py

import streamlit as st
from datetime import datetime, timedelta
from functions.data_utils import cargar_datos

def mostrar_agenda():
    st.header("📅 Agenda de Actividades")
    datos = cargar_datos()
    
    if datos.empty:
        st.info("No hay actividades programadas")
        return
    
    # Filtros
    st.sidebar.header("🔍 Filtros Agenda")
    fecha_desde = st.sidebar.date_input("Desde", datetime.today())
    fecha_hasta = st.sidebar.date_input("Hasta", datetime.today() + timedelta(days=30))
    actividades = st.sidebar.multiselect("Actividades", datos['Actividad'].unique())
    
    # Aplicar filtros
    mask = (datos['Fecha Actividad'].dt.date >= fecha_desde) & \
           (datos['Fecha Actividad'].dt.date <= fecha_hasta)
    if actividades:
        mask &= datos['Actividad'].isin(actividades)
    
    datos_filtrados = datos[mask]
    
    # Mostrar actividades
    for fecha in datos_filtrados['Fecha Actividad'].dt.date.unique():
        actividades_dia = datos_filtrados[datos_filtrados['Fecha Actividad'].dt.date == fecha]
        
        with st.expander(f"📅 {fecha.strftime('%A %d/%m/%Y')} ({len(actividades_dia)} actividades)"):
            for _, actividad in actividades_dia.iterrows():
                col1, col2 = st.columns([1,4])
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; 
                                background-color: #f0f2f6; 
                                padding: 10px; 
                                border-radius: 10px;">
                        <h4>{actividad['Hora inicio Actividad'][:5]}</h4>
                        <small>{actividad['Duración']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    try:
                        hora_actividad = datetime.strptime(actividad['Hora inicio Actividad'], '%H:%M:%S').time()
                        fecha_hora_actividad = datetime.combine(fecha, hora_actividad)
                        dif = fecha_hora_actividad - datetime.now()
                        status_color = "#28a745" if dif.total_seconds() >= 0 else "#dc3545"
                        status_text = f"En {dif.days + 1} días" if dif.days >= 0 else "Pasada"
                    except ValueError:
                        status_color = "#6c757d"
                        status_text = "Hora no válida"
                    
                    st.markdown(f"""
                    <div style="border: 1px solid #dee2e6;
                                padding: 15px;
                                border-radius: 10px;
                                margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <h4 style="margin: 0;">{actividad['Actividad']}</h4>
                            <div style="background-color: {status_color};
                                        color: white;
                                        padding: 2px 10px;
                                        border-radius: 15px;">
                                {status_text}
                            </div>
                        </div>
                        <hr style="margin: 10px 0;">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                            <div>👤 {actividad['Nombre']}</div>
                            <div>👥 {actividad['Personas']} personas</div>
                            <div>📞 {actividad['Email o Teléfono']}</div>
                            <div>💶 {actividad['Precio']}€</div>
                        </div>
                        {f"<div style='margin-top: 10px;'>📝 {actividad['Notas']}</div>" if actividad['Notas'] else ""}
                    </div>
                    """, unsafe_allow_html=True)