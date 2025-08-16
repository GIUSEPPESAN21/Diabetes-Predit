# -*- coding: utf-8 -*-
"""
Aplicación de Prueba Mínima para Autenticación de Firebase
Versión 1.0

Objetivo: Isolar y verificar la funcionalidad de registro e inicio de sesión
con Pyrebase y Streamlit, sin ninguna otra librería o función.
"""

import streamlit as st
import pyrebase

# --- 1. CONFIGURACIÓN DE FIREBASE ---
# Intenta inicializar la autenticación del cliente de Firebase.
# Utiliza la sección [firebase_client_config] de tu archivo secrets.toml
try:
    firebase_client_config = dict(st.secrets["firebase_client_config"])
    firebase = pyrebase.initialize_app(firebase_client_config)
    auth_client = firebase.auth()
    st.info("✅ Conexión con Firebase establecida correctamente.")
except Exception as e:
    st.error(f"❌ Error crítico al conectar con Firebase: {e}")
    st.warning("Verifica que la sección [firebase_client_config] en tus secretos sea correcta.")
    st.stop()

# --- 2. INTERFAZ DE USUARIO ---

st.title("Prueba de Autenticación de Firebase")
st.write("Esta app solo prueba el registro y el inicio de sesión.")

# Inicializar estado de sesión para el usuario
if 'user' not in st.session_state:
    st.session_state.user = None

# Si no hay un usuario logueado, mostrar los formularios
if st.session_state.user is None:

    col1, col2 = st.columns(2)

    # --- Formulario de Registro ---
    with col1:
        with st.form("register_form", clear_on_submit=True):
            st.header("Registrar Nuevo Usuario")
            email_reg = st.text_input("Correo Electrónico para registrar")
            password_reg = st.text_input("Crea una Contraseña (mín. 6 caracteres)", type="password")
            register_button = st.form_submit_button("Registrarse", use_container_width=True)

            if register_button:
                if not email_reg or not password_reg:
                    st.warning("Por favor, completa todos los campos.")
                else:
                    try:
                        # Intenta crear el usuario en Firebase
                        user = auth_client.create_user_with_email_and_password(email_reg, password_reg)
                        st.success(f"¡Usuario registrado con éxito!")
                        st.json(user) # Muestra la respuesta de Firebase
                    except Exception as e:
                        st.error("Error durante el registro:")
                        st.exception(e) # Muestra el error completo de Firebase

    # --- Formulario de Inicio de Sesión ---
    with col2:
        with st.form("login_form", clear_on_submit=True):
            st.header("Iniciar Sesión")
            email_login = st.text_input("Correo Electrónico")
            password_login = st.text_input("Contraseña", type="password")
            login_button = st.form_submit_button("Entrar", use_container_width=True)

            if login_button:
                try:
                    # Intenta iniciar sesión
                    user = auth_client.sign_in_with_email_and_password(email_login, password_login)
                    st.session_state.user = user
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun() # Recarga la página para mostrar el estado de logueado
                except Exception as e:
                    st.error("Error durante el inicio de sesión:")
                    st.exception(e) # Muestra el error completo

# Si el usuario ya inició sesión, mostrar un mensaje de bienvenida
else:
    st.header("🎉 ¡Has iniciado sesión correctamente!")
    st.success(f"Bienvenido. Tu información de usuario es:")
    st.json(st.session_state.user)

    if st.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

