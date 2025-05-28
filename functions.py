import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from gspread_client import get_gsheet_client
import hashlib

# Configuración desde secrets
SPREADSHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
ACTIVIDADES_MANUALES = ["Grupos", "Senderismo"]

# Configuración de usuarios (en un sistema real deberían estar en una base de datos segura)
USERS = {
    "admin": {
        "password_hash": hashlib.sha256("ubuntu2024".encode()).hexdigest(),
        "role": "admin"
    },
    "usuario": {
        "password_hash": hashlib.sha256("aventuras123".encode()).hexdigest(),
        "role": "user"
    }
}

def check_auth():
    """Verifica la autenticación del usuario"""
    # Si ya está autenticado, continuar
    if st.session_state.get('logged_in'):
        return True
    
    # Mostrar formulario de login
    st.title("🔐 Acceso al Sistema - Ubuntu Aventuras")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Usuario")
            password = st.text_input("🔑 Contraseña", type="password")
            submit = st.form_submit_button("🚪 Entrar")
            
            if submit:
                if username in USERS:
                    # Verificar contraseña
                    input_password_hash = hashlib.sha256(password.encode()).hexdigest()
                    if input_password_hash == USERS[username]["password_hash"]:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.user_role = USERS[username]["role"]
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
                else:
                    st.error("Usuario no encontrado")
    
    # Información de usuarios de prueba (solo para desarrollo)
    with col2:
        with st.expander("ℹ️ Usuarios de prueba"):
            st.info("""
            **Usuarios disponibles:**
            - Usuario: `admin` | Contraseña: `ubuntu2024`
            - Usuario: `usuario` | Contraseña: `aventuras123`
            """)
    
    return False

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        records = worksheet.get_all_records()

        df = pd.DataFrame(records)
        df['Fecha Actividad'] = pd.to_datetime(df['Fecha Actividad'], dayfirst=True)
        df['Fecha Reserva'] = pd.to_datetime(df['Fecha Reserva'], dayfirst=True)
        return df.sort_values('Fecha Actividad', ascending=True)
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()

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

def mostrar_formulario():
    st.header("📝 Nueva Reserva")
    
    # Inicializar campos
    default_values = {
        "nombre": "",
        "actividad": "Kayak",
        "fecha": datetime.today(),
        "hora_inicio": datetime.strptime("10:30", "%H:%M").time(),
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

    # Selector de precio unitario
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
    st.session_state["hora_inicio"] = st.time_input("Hora de inicio*", value=st.session_state["hora_inicio"], step=300) # Paso de 5 minutos (opcional))
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
                    # CORRECCIÓN: Extraer solo la hora de la cadena de tiempo
                    try:
                        hora_actividad = datetime.strptime(actividad['Hora inicio Actividad'], '%H:%M:%S').time()
                        fecha_hora_actividad = datetime.combine(fecha, hora_actividad)
                        dif = fecha_hora_actividad - datetime.now()
                        status_color = "#28a745" if dif.total_seconds() >= 0 else "#dc3545"
                        status_text = f"En {dif.days + 1} días" if dif.days >= 0 else "Pasada"
                    except ValueError:
                        # Manejar caso donde el formato de hora no es el esperado
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

def mostrar_reserva_detalle(reserva_data, index):
    """Muestra los detalles de una reserva y permite modificarla"""
    st.subheader(f"✏️ Modificar Reserva - {reserva_data['Nombre']}")
    
    with st.form(f"form_modificar_{index}"):
        # Cargar datos actuales
        nuevo_nombre = st.text_input("Nombre completo*", value=reserva_data['Nombre'])
        
        opciones_actividad = [
            "Kayak", "Paddle surf", "Hidropedales", "Ruta Bisontes", 
            "Ebikes", "Ferrata Cistierna", "Ferrata Sabero", 
            "Ferrata Valdeón", "Alquiler equipos ferrata", "Grupos", "Senderismo"
        ]
        
        actividad_actual = reserva_data['Actividad']
        actividad_index = opciones_actividad.index(actividad_actual) if actividad_actual in opciones_actividad else 0
        nueva_actividad = st.selectbox("Actividad*", options=opciones_actividad, index=actividad_index)
        
        # Fecha y hora
        fecha_actual = pd.to_datetime(reserva_data['Fecha Actividad']).date()
        nueva_fecha = st.date_input("Fecha de la actividad*", value=fecha_actual)
        
        try:
            hora_actual = datetime.strptime(reserva_data['Hora inicio Actividad'], '%H:%M:%S').time()
        except:
            hora_actual = time(10, 0)
        nueva_hora = st.time_input("Hora de inicio*", value=hora_actual)
        
        # Duración
        if nueva_actividad == "Alquiler equipos ferrata":
            duracion_opciones = ["1 día", "2 días", "3 días"]
        else:
            duracion_opciones = ["1 hora", "2 horas", "Medio día", "Todo el día"]
        
        duracion_actual = reserva_data['Duración']
        duracion_index = duracion_opciones.index(duracion_actual) if duracion_actual in duracion_opciones else 0
        nueva_duracion = st.selectbox("Duración*", options=duracion_opciones, index=duracion_index)
        
        # Personas
        if nueva_actividad == "Ruta Bisontes":
            col1, col2 = st.columns(2)
            with col1:
                nuevos_adultos = st.number_input("Nº adultos (12+ años)*", min_value=0, max_value=30, value=1)
            with col2:
                nuevos_niños = st.number_input("Nº niños (0-11 años)", min_value=0, max_value=30, value=0)
            total_personas = nuevos_adultos + nuevos_niños
        else:
            nuevas_personas = st.number_input("Nº personas*", min_value=1, max_value=30, value=int(reserva_data['Personas']))
            total_personas = nuevas_personas
        
        # Precio
        if nueva_actividad in ACTIVIDADES_MANUALES:
            nuevo_precio_unitario = st.number_input("💶 Precio por persona*", min_value=0.0, step=5.0, format="%.2f", value=0.0)
            precio_calculado = calcular_precio(nueva_actividad, nueva_duracion, total_personas, nuevo_precio_unitario)
        else:
            if nueva_actividad == "Ruta Bisontes":
                precio_calculado = calcular_precio(nueva_actividad, nueva_duracion, total_personas, adultos=nuevos_adultos, niños=nuevos_niños)
            else:
                precio_calculado = calcular_precio(nueva_actividad, nueva_duracion, total_personas)
        
        nuevo_precio = st.number_input("💰 Precio final*", value=int(reserva_data['Precio']), min_value=0, step=1)
        
        # Contacto
        contacto_opciones = ["WhatsApp", "Teléfono", "Email"]
        contacto_actual = reserva_data.get('Medio de contacto', 'WhatsApp')
        contacto_index = contacto_opciones.index(contacto_actual) if contacto_actual in contacto_opciones else 0
        nuevo_contacto = st.selectbox("Medio de contacto*", contacto_opciones, index=contacto_index)
        nuevo_contacto_dato = st.text_input("Email o número de contacto*", value=reserva_data.get('Email o Teléfono', ''))
        
        nuevas_notas = st.text_area("Notas adicionales", value=reserva_data.get('Notas', ''))
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.form_submit_button("💾 Guardar cambios", type="primary"):
                try:
                    gc = get_gsheet_client()
                    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
                    worksheet = spreadsheet.worksheet(SHEET_NAME)
                    
                    # Encontrar la fila a actualizar (index + 2 porque las hojas empiezan en 1 y hay headers)
                    fila_actualizar = index + 2
                    
                    # Calcular precio unitario
                    if nueva_actividad == "Hidropedales":
                        duracion_horas = int(nueva_duracion.split()[0])
                        precio_unitario = nuevo_precio / duracion_horas if duracion_horas > 0 else 0
                    elif nueva_actividad in ACTIVIDADES_MANUALES:
                        precio_unitario = nuevo_precio_unitario if nueva_actividad in ACTIVIDADES_MANUALES else 0
                    else:
                        precio_unitario = nuevo_precio / total_personas if total_personas > 0 else 0
                    
                    # Actualizar fila
                    nueva_fila = [
                        nuevo_nombre,
                        nueva_actividad,
                        nueva_fecha.strftime("%d/%m/%Y"),
                        nueva_hora.strftime("%H:%M:%S"),
                        nueva_duracion,
                        total_personas,
                        nuevo_contacto,
                        nuevo_contacto_dato,
                        nuevo_precio,
                        nuevas_notas,
                        datetime.now().strftime("%d/%m/%Y %H:%M"),  # Fecha de modificación
                        round(precio_unitario, 2)
                    ]
                    
                    # Actualizar la fila completa
                    worksheet.delete_rows(fila_actualizar)
                    worksheet.insert_row(nueva_fila, fila_actualizar)
                    
                    st.success("✅ Reserva actualizada correctamente")
                    st.cache_data.clear()
                    
                    # Limpiar session state
                    if 'reserva_seleccionada' in st.session_state:
                        del st.session_state['reserva_seleccionada']
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al actualizar: {str(e)}")
        
        with col2:
            if st.form_submit_button("🗑️ Eliminar reserva"):
                try:
                    gc = get_gsheet_client()
                    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
                    worksheet = spreadsheet.worksheet(SHEET_NAME)
                    
                    # Eliminar fila (index + 2 porque las hojas empiezan en 1 y hay headers)
                    worksheet.delete_rows(index + 2)
                    
                    st.success("✅ Reserva eliminada correctamente")
                    st.cache_data.clear()
                    
                    # Limpiar session state
                    if 'reserva_seleccionada' in st.session_state:
                        del st.session_state['reserva_seleccionada']
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al eliminar: {str(e)}")
        
        with col3:
            if st.form_submit_button("❌ Cancelar"):
                if 'reserva_seleccionada' in st.session_state:
                    del st.session_state['reserva_seleccionada']
                st.rerun()

def mostrar_calendario():
    st.header("🗓️ Calendario de Actividades")
    
    # Inicializar session state para reserva seleccionada
    if 'reserva_seleccionada' not in st.session_state:
        st.session_state.reserva_seleccionada = None
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox("Mes", list(calendar.month_name[1:]), index=datetime.now().month-1)
    with col2:
        selected_year = st.selectbox("Año", range(datetime.now().year-1, datetime.now().year+2), index=1)
    
    month_number = list(calendar.month_name).index(selected_month)
    datos = cargar_datos()
    
    # Si hay una reserva seleccionada, mostrar el formulario de edición
    if st.session_state.reserva_seleccionada is not None:
        reserva_data, reserva_index = st.session_state.reserva_seleccionada
        mostrar_reserva_detalle(reserva_data, reserva_index)
        return
    
    # Generar calendario
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
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .activity-badge:hover {
        background-color: #45a049;
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
                    actividades_dia = datos[datos['Fecha Actividad'].dt.date == current_date.date()] if not datos.empty else pd.DataFrame()
                    
                    with st.container():
                        st.markdown(f"<div class='day-cell'>", unsafe_allow_html=True)
                        st.subheader(f"{day}")
                        
                        if not actividades_dia.empty:
                            for idx, (original_idx, actividad) in enumerate(actividades_dia.iterrows()):
                                # Crear un botón único para cada actividad
                                button_key = f"actividad_{selected_year}_{month_number}_{day}_{idx}"
                                
                                if st.button(
                                    f"{actividad['Actividad']}\n⏰ {actividad['Hora inicio Actividad'][:5]}\n👥 {actividad['Personas']} pers.",
                                    key=button_key,
                                    help="Click para editar esta reserva"
                                ):
                                    # Guardar la reserva seleccionada en session state
                                    st.session_state.reserva_seleccionada = (actividad.to_dict(), original_idx)
                                    st.rerun()
                        else:
                            st.markdown("<small>Sin actividades</small>", unsafe_allow_html=True)

def ultimas_reservas():
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
                    # Usar clave única para cada botón
                    if st.button("🗑️", key=f"delete_{index}_{row['Nombre']}"):
                        st.session_state['delete_index'] = index
                        st.session_state['show_delete_confirm'] = True

            # Mostrar confirmación después de renderizar todas las reservas
            if st.session_state.get('show_delete_confirm', False):
                index = st.session_state.get('delete_index')
                if index is not None:
                    st.warning("¿Seguro que quieres eliminar esta reserva?")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✅ Confirmar", key=f"confirm_delete_{index}"):
                            try:
                                gc = get_gsheet_client()
                                spreadsheet = gc.open_by_key(SPREADSHEET_ID)
                                worksheet = spreadsheet.worksheet(SHEET_NAME)
                                
                                # Eliminar fila (index + 2 porque las hojas empiezan en 1 y hay headers)
                                worksheet.delete_rows(index + 2)
                                
                                # Limpiar estados y caché
                                st.session_state.show_delete_confirm = False
                                st.session_state.delete_index = None
                                st.cache_data.clear()
                                st.success("✅ Reserva eliminada correctamente")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error al eliminar: {str(e)}")
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_delete_{index}"):
                            st.session_state.show_delete_confirm = False
                            st.rerun()
        else:
            st.info("📭 Aún no hay reservas registradas")
            
        # Botón de actualización fuera del loop
        if st.button("🔄 Actualizar reservas", key="refresh_reservations"):
            st.cache_data.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")