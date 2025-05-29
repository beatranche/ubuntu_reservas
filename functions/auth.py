# functions/auth.py

import streamlit as st
import pandas as pd
import hashlib
from .data_utils import cargar_usuarios, registrar_usuario

def check_auth():
    """Verifica la autenticación del usuario"""
    # Inicializar estados necesarios
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'mostrar_registro' not in st.session_state:
        st.session_state.mostrar_registro = False
    if 'mostrar_login' not in st.session_state:
        st.session_state.mostrar_login = True
    
    # Si ya está autenticado, continuar
    if st.session_state.logged_in:
        return True
    
    # Mostrar formulario de registro si está activo
    if st.session_state.mostrar_registro:
        mostrar_formulario_registro()
        return False
    
    # Mostrar formulario de login por defecto
    if st.session_state.mostrar_login:
        mostrar_login()
        return False
    
    return False

def mostrar_login():
    """Muestra el formulario de login"""
    st.title("🔐 Acceso al Sistema - Ubuntu Aventuras")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Usuario")
            password = st.text_input("🔑 Contraseña", type="password")
            submit = st.form_submit_button("🚪 Entrar")
            
            if submit:
                df_usuarios = cargar_usuarios()
                if not df_usuarios.empty:
                    # Buscar usuario (insensible a mayúsculas)
                    usuario = df_usuarios[
                        df_usuarios['usuario'].str.strip().str.lower() == username.strip().lower()
                    ]
                    
                    if not usuario.empty:
                        usuario = usuario.iloc[0]
                        # Verificar contraseña
                        input_password_hash = hashlib.sha256(password.encode()).hexdigest()
                        if input_password_hash == usuario['password']:
                            st.session_state.logged_in = True
                            st.session_state.current_user = username
                            st.rerun()
                        else:
                            st.error("Contraseña incorrecta")
                    else:
                        st.error("Usuario no encontrado")
                else:
                    st.error("No hay usuarios registrados")
        
        st.markdown("---")
        st.markdown("¿No tienes cuenta?")
        if st.button("Registrarse ahora"):
            st.session_state.mostrar_registro = True
            st.session_state.mostrar_login = False
            st.rerun()

def mostrar_formulario_registro():
    """Muestra el formulario de registro"""
    st.title("📝 Registro de nuevo usuario")
    
    with st.form("registro_form"):
        st.subheader("Información personal")
        nombre = st.text_input("Nombre*")
        apellidos = st.text_input("Apellidos*")
        email = st.text_input("Email*")
        
        st.subheader("Credenciales de acceso")
        usuario = st.text_input("Nombre de usuario*")
        password = st.text_input("Contraseña*", type="password")
        confirm_password = st.text_input("Confirmar contraseña*", type="password")
        
        st.caption("(*) Campos obligatorios")
        submit = st.form_submit_button("Registrarse")
        
        if submit:
            if not all([nombre, apellidos, email, usuario, password, confirm_password]):
                st.error("Todos los campos son obligatorios")
            elif password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                success, message = registrar_usuario(nombre, apellidos, email, usuario, password)
                if success:
                    st.success(message)
                    st.balloons()
                    st.session_state.mostrar_login = True
                    st.session_state.mostrar_registro = False
                    st.rerun()
                else:
                    st.error(message)
    
    if st.button("← Volver al login"):
        st.session_state.mostrar_login = True
        st.session_state.mostrar_registro = False
        st.rerun()
