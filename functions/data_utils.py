# functions/data_utils.py

import hashlib
import streamlit as st
import pandas as pd
from datetime import datetime
from functions.gspread_client import get_gsheet_client

# Configuración desde secrets
SPREADSHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
SHEET_NAME = st.secrets["google_sheets"]["sheet_name"]
ACTIVIDADES_MANUALES = ["Grupos", "Senderismo"]

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

@st.cache_data(ttl=300)
def cargar_clientes():
    """Carga los clientes desde Google Sheets"""
    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        try:
            worksheet = spreadsheet.worksheet("Clientes")
        except:
            # Crear la hoja si no existe
            worksheet = spreadsheet.add_worksheet(title="Clientes", rows=100, cols=14)
            # Crear encabezados
            encabezados = [
                "ID", "Sexo", "Fecha Nacimiento", "Ciudad", "Pais", 
                "Actividad", "Fecha Actividad", "Hora Inicio", "Duracion", "Personas", "Precio",
                "Fecha Registro", "Edad", "Ingresos por Persona", "Notas"
            ]
            worksheet.append_row(encabezados)
        
        records = worksheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error al cargar clientes: {str(e)}")
        return pd.DataFrame()

def guardar_cliente(cliente_data):
    """Guarda un nuevo cliente en Google Sheets"""
    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet("Clientes")
        
        # Calcular edad
        fecha_nac = datetime.strptime(cliente_data['fecha_nacimiento'], '%d/%m/%Y')
        edad = (datetime.now() - fecha_nac).days // 365
        
        # Calcular ingresos por persona
        ingresos_pp = cliente_data['precio'] / cliente_data['personas'] if cliente_data['personas'] > 0 else 0
        
        # Preparar la fila
        nueva_fila = [
            cliente_data['id'],
            cliente_data['sexo'],
            cliente_data['fecha_nacimiento'],
            cliente_data['ciudad'],
            cliente_data['pais'],
            cliente_data['actividad'],
            cliente_data['fecha_actividad'],
            cliente_data['hora_inicio'],
            cliente_data['duracion'],
            cliente_data['personas'],
            cliente_data['precio'],
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            edad,
            ingresos_pp,
            cliente_data.get('notas', '')
        ]
        
        worksheet.append_row(nueva_fila)
        return True
    except Exception as e:
        st.error(f"Error al guardar cliente: {str(e)}")
        return False

def cargar_usuarios():
    """Carga los usuarios desde Google Sheets"""
    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Intentar acceder a la hoja de usuarios
        try:
            worksheet = spreadsheet.worksheet("Usuarios")
        except:
            # Crear la hoja si no existe
            worksheet = spreadsheet.add_worksheet(title="Usuarios", rows=100, cols=6)
            # Crear encabezados
            worksheet.append_row(["nombre", "apellidos", "email", "usuario", "password", "fecha_registro"])
        
        records = worksheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error al cargar usuarios: {str(e)}")
        return pd.DataFrame()

def registrar_usuario(nombre, apellidos, email, usuario, password):
    """Registra un nuevo usuario en Google Sheets"""
    try:
        # Verificar si el usuario ya existe
        df_usuarios = cargar_usuarios()
        if not df_usuarios.empty and usuario in df_usuarios['usuario'].values:
            return False, "El nombre de usuario ya está en uso"
        
        # Hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Fecha de registro
        fecha_registro = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet("Usuarios")
        
        nueva_fila = [nombre, apellidos, email, usuario, password_hash, fecha_registro]
        worksheet.append_row(nueva_fila)
        return True, "Usuario registrado con éxito"
    except Exception as e:
        return False, f"Error al registrar: {str(e)}"