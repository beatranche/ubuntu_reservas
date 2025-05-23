import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
import os
from gspread_client import get_gsheet_client

# Configuración de Google Sheets
SPREADSHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
ACTIVIDADES_MANUALES = ["Grupos", "Senderismo"]

@st.cache_data
def cargar_datos():
    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Obtener todos los registros
        records = worksheet.get_all_records()
        
        if not records:
            return pd.DataFrame(columns=[
                "Nombre", "Actividad", "Fecha Actividad", "Hora inicio Actividad",
                "Duración", "Personas", "Contacto", "Email o Teléfono", 
                "Precio", "Notas", "Fecha Reserva", "Precio Unitario"
            ])
            
        df = pd.DataFrame(records)
        df['Fecha Actividad'] = pd.to_datetime(df['Fecha Actividad'], dayfirst=True)
        df['Fecha Reserva'] = pd.to_datetime(df['Fecha Reserva'], dayfirst=True)
        return df.sort_values('Fecha Reserva', ascending=False)
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.exception(e)
        return pd.DataFrame()

st.title("📋 Formulario de Reservas – Ubuntu Aventuras")

def validar_campos_obligatorios():
    campos_requeridos = {
        "nombre": "Nombre completo",
        "actividad": "Actividad",
        "fecha": "Fecha de actividad",
        "hora_inicio": "Hora de inicio",
        "duracion": "Duración",
        "contacto_dato": "Datos de contacto"
    }
    faltantes = [nombre for key, nombre in campos_requeridos.items() 
                if not st.session_state.get(key)]
    if faltantes:
        st.error(f"🚨 Campos obligatorios faltantes: {', '.join(faltantes)}")
        return False
    return True

def calcular_precio(actividad, duracion, personas, precio_unitario=0, adultos=0, niños=0):
    if actividad in ACTIVIDADES_MANUALES:
        return precio_unitario * personas
    if "Ferrata" in actividad and actividad != "Alquiler equipos ferrata":
        return 49 * personas
    if actividad == "Alquiler equipos ferrata":
        dias = int(duracion.split()[0])
        return 15 * dias * personas
    
    tarifas = {
        "Kayak": {"1 hora": 10, "2 horas": 18, "Todo el día": 30},
        "Paddle surf": {"1 hora": 15, "2 horas": 25, "Todo el día": 30},
        "Hidropedales": {"1 hora": 30, "2 horas": 50},
        "Ebikes": {"1 hora": 15, "Medio día": 30, "Todo el día": 50},
        "Ruta Bisontes": {"Adulto": 59, "Niño": 49}
    }

    if actividad == "Ruta Bisontes":
        return (tarifas["Ruta Bisontes"]["Adulto"] * adultos) + (tarifas["Ruta Bisontes"]["Niño"] * niños)
    elif actividad == "Hidropedales":
        return tarifas["Hidropedales"].get(duracion, 0)
    else:
        return tarifas.get(actividad, {}).get(duracion, 0) * personas

# Inicializar campos
default_values = {
    "nombre": "",
    "actividad": "Kayak",
    "fecha": datetime.today(),
    "hora_inicio": "10:30",
    "duracion": "1 hora",
    "personas": 1,
    "adultos": 1,
    "niños": 0,
    "contacto": "WhatsApp",
    "contacto_dato": "",
    "notas": "",
    "mostrar_resumen": False,
    "reserva_guardada": False,
    "precio_unitario": 0.0
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Formulario de entrada
st.header("📝 Nueva reserva")
st.session_state["nombre"] = st.text_input("Nombre completo*", st.session_state["nombre"])

opciones_actividad = [
    "Kayak", "Paddle surf", "Hidropedales", "Ruta Bisontes", 
    "Ebikes", "Ferrata Cistierna", "Ferrata Sabero", 
    "Ferrata Valdeón", "Alquiler equipos ferrata", "Grupos", "Senderismo"
]

st.session_state["actividad"] = st.selectbox(
    "Actividad*",
    options=opciones_actividad,
    index=opciones_actividad.index(st.session_state["actividad"]) if st.session_state["actividad"] in opciones_actividad else 0
)

# Campos específicos por actividad
if st.session_state["actividad"] == "Ruta Bisontes":
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["adultos"] = st.number_input("Nº adultos (12+ años)*", 
                                                     min_value=0, max_value=30, 
                                                     value=st.session_state["adultos"])
    with col2:
        st.session_state["niños"] = st.number_input("Nº niños (0-11 años)", 
                                                   min_value=0, max_value=30, 
                                                   value=st.session_state["niños"])
    total_personas = st.session_state["adultos"] + st.session_state["niños"]
else:
    st.session_state["personas"] = st.number_input("Nº personas*", 
                                                  min_value=1, max_value=30, 
                                                  value=st.session_state["personas"])
    total_personas = st.session_state["personas"]

# Selector de precio unitario para actividades especiales
if st.session_state["actividad"] in ACTIVIDADES_MANUALES:
    st.session_state["precio_unitario"] = st.number_input(
        "💶 Precio por persona*",
        min_value=0.0,
        step=5.0,
        format="%.2f",
        value=st.session_state.get("precio_unitario", 0.0)
    )

# Selector de duración
if st.session_state["actividad"] == "Alquiler equipos ferrata":
    duracion_opciones = ["1 día", "2 días", "3 días"]
else:
    duracion_opciones = ["1 hora", "2 horas", "Medio día", "Todo el día"]

st.session_state["duracion"] = st.selectbox(
    "Duración*", 
    options=duracion_opciones,
    index=duracion_opciones.index(st.session_state["duracion"]) if st.session_state["duracion"] in duracion_opciones else 0
)

st.session_state["fecha"] = st.date_input("Fecha de la actividad (dd/mm/yyyy)*", value=st.session_state["fecha"])
st.session_state["hora_inicio"] = st.time_input("Hora de inicio*", value=st.session_state["hora_inicio"])
st.session_state["contacto"] = st.selectbox("Medio de contacto*", ["WhatsApp", "Teléfono", "Email"])
st.session_state["contacto_dato"] = st.text_input("Email o número de contacto*", st.session_state["contacto_dato"])
st.session_state["notas"] = st.text_area("Notas adicionales", st.session_state["notas"])

# Cálculo de precio
if st.session_state["actividad"] in ACTIVIDADES_MANUALES:
    precio_base = calcular_precio(
        st.session_state["actividad"],
        st.session_state["duracion"],
        total_personas,
        st.session_state["precio_unitario"]
    )
else:
    precio_base = calcular_precio(
        st.session_state["actividad"],
        st.session_state["duracion"],
        total_personas,
        adultos=st.session_state.get("adultos", 0),
        niños=st.session_state.get("niños", 0)
    )

precio_final = st.number_input(
    "💰 Precio final (editable)*",
    value=int(precio_base),
    min_value=0,
    step=1,
    format="%d"
)
st.info(f"**Precio a aplicar:** {precio_final}€")

if st.button("🧾 Revisar y confirmar"):
    if validar_campos_obligatorios():
        st.session_state.mostrar_resumen = True
        st.session_state.reserva_guardada = False

if st.session_state.mostrar_resumen and not st.session_state.reserva_guardada:
    st.subheader("✅ Revisa tu reserva")
    
    # Crear diccionario de detalles
    detalles = {
        "Nombre": st.session_state["nombre"],
        "Actividad": st.session_state["actividad"],
        "Fecha": st.session_state["fecha"].strftime("%d/%m/%Y"),
        "Hora": st.session_state["hora_inicio"].strftime("%H:%M"),
        "Duración": st.session_state["duracion"],
        "Contacto": f"{st.session_state['contacto']}: {st.session_state['contacto_dato']}",
        "Precio final": f"{precio_final}€",
        "Notas": st.session_state["notas"]
    }

    if st.session_state["actividad"] == "Ruta Bisontes":
        detalles["Adultos"] = st.session_state["adultos"]
        detalles["Niños"] = st.session_state["niños"]
    else:
        detalles["Personas"] = total_personas

    for campo, valor in detalles.items():
        st.write(f"**{campo}:** {valor}")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Confirmar reserva"):
            try:
                gc = get_gsheet_client()
                spreadsheet = gc.open_by_key(SPREADSHEET_ID)
                worksheet = spreadsheet.worksheet(SHEET_NAME)
                
                # Calcular precio unitario
                actividad_actual = st.session_state["actividad"]
                precio_final_val = precio_final
                
                if actividad_actual == "Hidropedales":
                    duracion_horas = int(st.session_state["duracion"].split()[0])
                    precio_unitario = precio_final_val / duracion_horas if duracion_horas > 0 else 0
                elif actividad_actual in ACTIVIDADES_MANUALES:
                    precio_unitario = st.session_state.get("precio_unitario", 0.0)
                else:
                    precio_unitario = precio_final_val / total_personas if total_personas > 0 else 0
                
                nueva_fila = [
                    st.session_state["nombre"],
                    st.session_state["actividad"],
                    st.session_state["fecha"].strftime("%d/%m/%Y"),
                    st.session_state["hora_inicio"].strftime("%H:%M:%S"),
                    st.session_state["duracion"],
                    total_personas,
                    st.session_state["contacto"],
                    st.session_state["contacto_dato"],
                    precio_final_val,
                    st.session_state["notas"],
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                    round(precio_unitario, 2)
                ]
                
                worksheet.append_row(nueva_fila)
                st.session_state.reserva_guardada = True
                st.session_state.mostrar_resumen = False
                st.cache_data.clear()
                
                for key in [k for k in default_values.keys() if k != "reserva_guardada"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al guardar: {str(e)}")

    with col2:
        if st.button("✏️ Modificar reserva"):
            st.session_state.mostrar_resumen = False

# Sección de últimas reservas con eliminación
st.subheader("📅 Últimas 5 reservas registradas")
try:
    datos = cargar_datos()
    if not datos.empty:
        datos['Fecha Actividad'] = datos['Fecha Actividad'].dt.strftime('%d/%m/%Y')
        datos['Fecha Reserva'] = datos['Fecha Reserva'].dt.strftime('%d/%m/%Y %H:%M')
        
        for index, row in datos.head(5).iterrows():
            cols = st.columns([5,1])
            with cols[0]:
                st.markdown(f"""
                **{row['Nombre']}** - {row['Actividad']}<br>
                📅 {row['Fecha Actividad']} ⏰ {row['Hora inicio Actividad']}<br>
                👥 {row['Personas']} personas | 💶 {row['Precio']}€
                """, unsafe_allow_html=True)
            
            with cols[1]:
                if st.button("🗑️", key=f"delete_{index}"):
                    st.session_state['delete_index'] = index
                    st.session_state['show_delete_confirm'] = True
                
                if st.session_state.get('show_delete_confirm', False) and st.session_state.get('delete_index') == index:
                    st.warning("¿Seguro que quieres eliminar esta reserva?")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✅ Confirmar", key=f"confirm_delete_{index}"):
                            try:
                                gc = get_gsheet_client()
                                spreadsheet = gc.open_by_key(SPREADSHEET_ID)
                                worksheet = spreadsheet.worksheet(SHEET_NAME)
                                
                                # 1. Obtener ID real de la fila en Sheets
                                all_data = worksheet.get_all_records()
                                sheet_row_number = index + 2  # Header + índice base 0
                                
                                # 2. Validar que la fila existe antes de eliminar
                                if len(all_data) > index:
                                    worksheet.delete_rows(sheet_row_number)
                                    
                                    # 3. Limpiar cachés y estados
                                    
                                    st.session_state.show_delete_confirm = False
                                    
                                    # 4. Recargar datos y forzar actualización
                                    st.cache_data.clear()
                                    datos = cargar_datos.__wrapped__() # Carga datos frescos
                                    st.rerun()  # Vuelve a renderizar todo
                                    break
                                    
                                else:
                                    st.error("La reserva ya fue eliminada")

                            except Exception as e:
                                st.error(f"Error al eliminar: {str(e)}")
                                st.session_state.show_delete_confirm = False
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_delete_{index}"):
                            st.session_state['show_delete_confirm'] = False
                            st.rerun()
    else:
        st.info("📭 Aún no hay reservas registradas")
except Exception as e:
    st.error(f"Error al cargar datos: {str(e)}")

# Módulo de Calendario
st.sidebar.header("🗓️ Filtros del Calendario")
current_date = datetime.now()
selected_month = st.sidebar.selectbox("Mes", list(calendar.month_name[1:]), index=current_date.month - 1)
selected_year = st.sidebar.selectbox("Año", range(current_date.year - 1, current_date.year + 2), index=1)
month_number = list(calendar.month_name).index(selected_month)
selected_activities = st.sidebar.multiselect("Filtrar por actividad:", opciones_actividad, default=opciones_actividad)
# Cargar y filtrar datos
datos_calendario = cargar_datos()
if not datos_calendario.empty:
    datos_calendario['Fecha Actividad'] = pd.to_datetime(datos_calendario['Fecha Actividad'])
    mask = (datos_calendario['Fecha Actividad'].dt.month == month_number) & \
           (datos_calendario['Fecha Actividad'].dt.year == selected_year) & \
           (datos_calendario['Actividad'].isin(selected_activities))
    datos_filtrados = datos_calendario[mask]
else:
    datos_filtrados = pd.DataFrame()

# Generar calendario
st.header(f"📅 Calendario de Actividades - {selected_month} {selected_year}")

# Crear matriz del calendario
cal = calendar.Calendar()
month_days = cal.monthdayscalendar(selected_year, month_number)

# Estilos CSS
st.markdown("""
<style>
.day-cell {
    border: 1px solid #ddd;
    padding: 10px;
    min-height: 120px;
    background-color: #f9f9f9;
}
.activity-badge {
    background-color: #4CAF50;
    color: white;
    padding: 2px 5px;
    border-radius: 3px;
    margin: 2px;
    font-size: 0.8em;
}
</style>
""", unsafe_allow_html=True)

# Mostrar calendario
for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day != 0:
                current_date = datetime(selected_year, month_number, day)
                actividades_dia = datos_filtrados[
                    datos_filtrados['Fecha Actividad'].dt.date == current_date.date()
                ] if not datos_filtrados.empty else pd.DataFrame()
                
                # Celda del día
                st.markdown(f"<div class='day-cell'>", unsafe_allow_html=True)
                st.subheader(f"{day}")
                
                if not actividades_dia.empty:
                    for _, actividad in actividades_dia.iterrows():
                        st.markdown(f"""
                        <div class='activity-badge'>
                            {actividad['Actividad']}<br>
                            ⏰ {actividad['Hora inicio Actividad']}<br>
                            👥 {int(actividad['Personas'])} personas
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("<small>Sin actividades</small>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)