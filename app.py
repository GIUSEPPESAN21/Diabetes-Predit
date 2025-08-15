# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v5.0
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final que utiliza un archivo de configuración 'config.yaml' para el
autenticador y carga las credenciales de Firebase desde los secretos de Streamlit,
solucionando todos los errores anteriores de formato e inicialización.
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# --- CONFIGURACIÓN DE SERVICIOS ---

# Carga de la configuración del autenticador desde el archivo YAML
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'config.yaml'. Asegúrate de que esté en tu repositorio de GitHub.")
    st.stop()

# Configuración de Firebase desde los secretos de Streamlit
try:
    # Corrige el error de inicialización asegurando que private_key se formatee correctamente
    firebase_secrets = st.secrets["firebase_credentials"]
    firebase_secrets['private_key'] = firebase_secrets['private_key'].replace('\\n', '\n')
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_secrets)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Error crítico al inicializar Firebase: {e}. Revisa tus secretos.")
    st.stop()

# Creación de la instancia del autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# --- (El resto del código como PDF, cálculos, etc., no necesita cambios) ---
# ... (Puedes pegar aquí el resto de tus funciones: PDF, calcular_puntaje, etc.)


# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide")

# Renderiza el widget de login
authenticator.login()

if st.session_state["authentication_status"]:
    # --- APLICACIÓN PRINCIPAL (SI EL USUARIO ESTÁ LOGUEADO) ---
    st.sidebar.title(f"Bienvenido, *{st.session_state['name']}*")
    authenticator.logout("Cerrar Sesión", "sidebar")
    
    opcion = st.sidebar.radio("Selecciona una opción", ["Realizar nuevo test", "Consultar historial", "Chatbot de Diabetes"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Autor")
    st.sidebar.info("Joseph Javier Sánchez Acuña\n\n*Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*\n\n**Contacto:** joseph.sanchez@uniminuto.edu.co")

    if opcion == "Realizar nuevo test":
        st.title("🩺 Software Predictivo de Diabetes con IA")
        st.write("Página en construcción.")
    elif opcion == "Consultar historial":
        st.title("📖 Tu Historial de Resultados")
        st.write("Página en construcción.")
    elif opcion == "Chatbot de Diabetes":
        st.title("🤖 Chatbot Informativo sobre Diabetes")
        st.write("Página en construcción.")

elif st.session_state["authentication_status"] is False:
    st.error('Usuario/contraseña incorrectos')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, introduce tu usuario y contraseña')

    # Habilitar el registro de nuevos usuarios
    try:
        if authenticator.register_user('Registrar nuevo usuario', preauthorization=False):
            st.success('¡Usuario registrado con éxito! Por favor, inicia sesión.')
            # Para guardar el nuevo usuario, debes actualizar tu archivo config.yaml manualmente
            # y subirlo a GitHub.
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            st.info("Para activar tu cuenta, el administrador debe actualizar el archivo de configuración.")
    except Exception as e:
        st.error(e)
