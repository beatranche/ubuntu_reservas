# functions/calendario.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from streamlit_calendar import calendar
from .data_utils import cargar_datos, SPREADSHEET_ID, SHEET_NAME
from .gspread_client import get_gsheet_client

# Paleta de colores para actividades
COLORES_ACTIVIDADES = {
    "Kayak": "#FF6B6B",
    "Paddle surf": "#4ECDC4",
    "Hidropedales": "#FFD166",
    "Ruta Bisontes": "#06D6A0",
    "Ebikes": "#118AB2",
    "Ferrata Cistierna": "#073B4C",
    "Ferrata Sabero": "#EF476F",
    "Ferrata Valdeón": "#7209B7",
    "Alquiler equipos ferrata": "#F15BB5",
    "Grupos": "#9B5DE5",
    "Senderismo": "#00BBF9"
}

def mostrar_calendario_responsive():
    st.header("🗓️ Calendario de Actividades (Responsive)")
    
    # Cargar datos
    datos = cargar_datos()
    
    if datos.empty:
        st.info("No hay actividades programadas")
        return
    
    # Preparar eventos para el calendario
    eventos = []
    for idx, row in datos.iterrows():
        fecha_actividad = row['Fecha Actividad']
        hora_inicio = datetime.strptime(row['Hora inicio Actividad'], '%H:%M:%S').time()
        start_datetime = datetime.combine(fecha_actividad, hora_inicio)
        
        # Calcular fecha de fin (asumiendo duración fija)
        end_datetime = start_datetime + timedelta(hours=2)
        
        eventos.append({
            "title": f"{row['Actividad']} - {row['Nombre']}",
            "start": start_datetime.isoformat(),
            "end": end_datetime.isoformat(),
            "color": COLORES_ACTIVIDADES.get(row['Actividad'], "#CCCCCC"),
            "id": str(idx),  # Usar 'id' en lugar de 'resourceId'
            "extendedProps": {  # Propiedades adicionales
                "index": idx,
                "actividad": row['Actividad'],
                "nombre": row['Nombre']
            }
        })
    
    # Configuración del calendario
    modo = st.radio("Vista del calendario:", 
                   ["Mes", "Semana", "Día", "Lista"], 
                   horizontal=True,
                   index=0)
    
    calendar_options = {
        "editable": False,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,dayGridWeek,dayGridDay,listMonth"
        },
        "initialDate": datetime.now().date().isoformat(),
        "eventTimeFormat": { 
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        }
    }
    
    if modo == "Mes":
        calendar_options["initialView"] = "dayGridMonth"
    elif modo == "Semana":
        calendar_options["initialView"] = "dayGridWeek"
    elif modo == "Día":
        calendar_options["initialView"] = "dayGridDay"
    else:  # Vista de lista
        calendar_options["initialView"] = "listMonth"
    
    # Mostrar el calendario
    calendario_seleccionado = calendar(
        events=eventos,
        options=calendar_options,
        custom_css="""
            .fc-event {
                cursor: pointer;
                font-size: 0.8em;
                padding: 2px;
            }
            @media (max-width: 768px) {
                .fc-header-toolbar {
                    flex-direction: column;
                    align-items: flex-start;
                }
                .fc-toolbar-chunk {
                    margin-bottom: 5px;
                }
                .fc-event-title {
                    font-size: 0.7em;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
            }
        """,
        key="calendario_actividades"
    )
    
    # Mostrar detalles cuando se selecciona un evento
    if calendario_seleccionado and "eventClick" in calendario_seleccionado:
        evento_clic = calendario_seleccionado["eventClick"]["event"]
        st.subheader(f"Detalles de la reserva: {evento_clic['title']}")
        
        # Múltiples formas de obtener el ID del evento
        evento_id = None
        
        # Método 1: Usar 'id'
        if "id" in evento_clic:
            evento_id = evento_clic["id"]
        
        # Método 2: Usar extendedProps
        elif "extendedProps" in evento_clic and "index" in evento_clic["extendedProps"]:
            evento_id = str(evento_clic["extendedProps"]["index"])
        
        # Método 3: Usar resourceId como fallback
        elif "resourceId" in evento_clic:
            evento_id = evento_clic["resourceId"]
        
        # Método 4: Buscar por título (menos confiable pero funcional)
        else:
            titulo_evento = evento_clic.get("title", "")
            for idx, row in datos.iterrows():
                titulo_esperado = f"{row['Actividad']} - {row['Nombre']}"
                if titulo_esperado == titulo_evento:
                    evento_id = str(idx)
                    break
        
        if not evento_id:
            st.error("No se pudo obtener el ID de la reserva")
            st.write("Debug info:")
            st.json(evento_clic)  # Para debugging
            return
            
        try:
            # Convertir a entero y obtener datos
            reserva_data = datos.iloc[int(evento_id)]
        except (ValueError, TypeError, IndexError) as e:
            st.error(f"Error al obtener datos de la reserva: {str(e)}")
            st.write(f"ID del evento: {evento_id}")
            st.write(f"Número total de reservas: {len(datos)}")
            return
        
        # Mostrar detalles
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Personas", reserva_data['Personas'])
            st.metric("Precio", f"{reserva_data['Precio']}€")
        with col2:
            st.write(f"**Fecha:** {reserva_data['Fecha Actividad'].strftime('%d/%m/%Y')}")
            st.write(f"**Hora:** {reserva_data['Hora inicio Actividad']}")
            st.write(f"**Contacto:** {reserva_data.get('Email o Teléfono', '')}")
            if reserva_data.get('Notas', ''):
                st.write(f"**Notas:** {reserva_data['Notas']}")
        
        # Botones de acción
        col_edit, col_del, _ = st.columns(3)
        with col_edit:
            if st.button("✏️ Editar", key=f"edit_{evento_id}"):
                st.session_state.reserva_seleccionada = (reserva_data.to_dict(), int(evento_id))
                st.rerun()
        with col_del:
            if st.button("🗑️ Eliminar", key=f"delete_{evento_id}"):
                if eliminar_reserva(int(evento_id)):
                    st.success("Reserva eliminada")
                    st.cache_data.clear()
                    st.rerun()
    
    # Debug: Mostrar información del evento seleccionado
    if st.checkbox("Modo debug (mostrar info del evento)"):
        if calendario_seleccionado:
            st.write("Información completa del calendario:")
            st.json(calendario_seleccionado)
    
    # Leyenda de colores
    st.caption("Leyenda de actividades:")
    cols = st.columns(4)
    for i, (actividad, color) in enumerate(COLORES_ACTIVIDADES.items()):
        with cols[i % 4]:
            st.markdown(
                f"<div style='background-color:{color}; "
                f"color:white; padding:5px; border-radius:5px; margin:2px;'>"
                f"{actividad}</div>", 
                unsafe_allow_html=True
            )

def eliminar_reserva(index):
    """Elimina una reserva por su índice"""
    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        worksheet.delete_rows(index + 2)  # +2 por encabezado y base 1
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {str(e)}")
        return False