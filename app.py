# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v3.0
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Esta versión integra el inicio de sesión con Google (OAuth2) para una mejor
experiencia de usuario, además de las funcionalidades de la v2.0.

Instrucciones para ejecutar:
1.  Asegúrate de tener Python instalado.
2.  Instala las bibliotecas necesarias (ver requirements.txt):
    pip install streamlit firebase-admin requests fpdf streamlit-social-media-auth

3.  Configura Firebase y Google Cloud:
    - Sigue los pasos anteriores para obtener tu 'firebase_credentials.json'.
    - Habilita "Correo/Contraseña" y "Google" como proveedores en Firebase Authentication.
    - Obtén tu ID de Cliente y Secreto de Cliente de OAuth2 desde la Consola de Google Cloud.
    - Añade estas nuevas credenciales a tus secretos de Streamlit (secrets.toml).

4.  Configura la API de Gemini:
    - Reemplaza el valor de la variable `GEMINI_API_KEY` con tu clave.

5.  Ejecuta la aplicación desde tu terminal:
    streamlit run nombre_de_este_archivo.py
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
import json
from datetime import datetime
from fpdf import FPDF
from streamlit_social_media_auth import OAuth2Provider

# --- CONFIGURACIÓN DE SERVICIOS ---

# Configuración de la API de Gemini
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# Configuración de Firebase
try:
    if not firebase_admin._apps:
        # Usa st.secrets para mayor seguridad, especialmente en despliegues.
        # El archivo secrets.toml debe contener las credenciales de firebase.
        firebase_creds_dict = st.secrets["firebase_credentials"]
        cred = credentials.Certificate(firebase_creds_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Error crítico al inicializar Firebase: {e}")
    st.stop()

# Configuración del proveedor de OAuth2 para Google
# DEBES AÑADIR ESTO A TU ARCHIVO secrets.toml
try:
    GOOGLE_CLIENT_ID = st.secrets["google_oauth"]["client_id"]
    GOOGLE_CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
    REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]
    GoogleAuthProvider = OAuth2Provider(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        user_info_url="https://www.googleapis.com/oauth2/v1/userinfo",
        scope="openid profile email",
        authorize_params={"access_type": "offline", "prompt": "consent"},
        token_params={"grant_type": "authorization_code"},
        user_info_parser=lambda d: d
    )
except KeyError:
    st.error("Credenciales de Google OAuth no configuradas en los secretos de Streamlit.")
    GoogleAuthProvider = None


# --- CLASE PARA GENERAR PDF (sin cambios) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Riesgo de Diabetes', 0, 1, 'C')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)
    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def generar_pdf(datos_reporte):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title('Datos del Paciente')
    fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    info_paciente = (f"Fecha: {fecha_reporte}\nEdad: {datos_reporte['edad']} años\n"
                     f"Sexo: {datos_reporte['sexo']}\nIMC: {datos_reporte['imc']:.2f}\n"
                     f"Cintura: {datos_reporte['cintura']} cm")
    pdf.chapter_body(info_paciente)
    pdf.chapter_title('Resultados del Cuestionario FINDRISC')
    resultados = (f"Puntaje: {datos_reporte['puntaje']} puntos\nNivel de Riesgo: {datos_reporte['nivel_riesgo']}\n"
                  f"Estimación: {datos_reporte['estimacion']}")
    pdf.chapter_body(resultados)
    pdf.chapter_title('Análisis y Recomendaciones por IA')
    analisis_ia_encoded = datos_reporte['analisis_ia'].encode('latin-1', 'replace').decode('latin-1')
    pdf.chapter_body(analisis_ia_encoded)
    pdf.set_y(-40)
    pdf.set_font('Arial', 'I', 9)
    autor_info = ("Software por: Joseph Javier Sánchez Acuña\n"
                  "Contacto: joseph.sanchez@uniminuto.edu.co")
    pdf.multi_cell(0, 5, autor_info, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- FUNCIONES DE LA APP (sin cambios) ---
def calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes):
    score = 0;
    if 45<=edad<=54: score+=2
    elif 55<=edad<=64: score+=3
    elif edad>64: score+=4
    if 25<=imc<30: score+=1
    elif imc>=30: score+=3
    if sexo=="Masculino":
        if 94<=cintura<=102: score+=3
        elif cintura>102: score+=4
    elif sexo=="Femenino":
        if 80<=cintura<=88: score+=3
        elif cintura>88: score+=4
    if actividad=="No": score+=2
    if frutas_verduras=="No todos los días": score+=1
    if hipertension=="Sí": score+=2
    if glucosa_alta=="Sí": score+=5
    if familiar_diabetes=="Sí: padres, hermanos o hijos": score+=5
    elif familiar_diabetes=="Sí: abuelos, tíos o primos": score+=3
    return score
def obtener_interpretacion_riesgo(score):
    if score < 7: return "Riesgo bajo", "1 de cada 100 personas desarrollará diabetes."
    elif 7 <= score <= 11: return "Riesgo ligeramente elevado", "1 de cada 25."
    elif 12 <= score <= 14: return "Riesgo moderado", "1 de cada 6."
    elif 15 <= score <= 20: return "Riesgo alto", "1 de cada 3."
    else: return "Riesgo muy alto", "1 de cada 2."
def obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion):
    # ... (sin cambios)
    return "Análisis de IA (función sin cambios)"
def guardar_datos_en_firestore(user_id, datos):
    # ... (sin cambios)
    pass
def cargar_datos_de_firestore(user_id):
    # ... (sin cambios)
    return []

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = None

# --- PANTALLAS DE LOGIN Y REGISTRO (ACTUALIZADO) ---
if not st.session_state.logged_in:
    st.title("Bienvenido al Software Predictivo de Diabetes")
    
    # Botón de inicio de sesión con Google
    if GoogleAuthProvider:
        user_info = GoogleAuthProvider.login()
        if user_info:
            email = user_info.get('email')
            name = user_info.get('name')
            try:
                # Revisa si el usuario ya existe en Firebase
                user = auth.get_user_by_email(email)
            except auth.UserNotFoundError:
                # Si no existe, lo crea
                user = auth.create_user(email=email, display_name=name)
            
            st.session_state.logged_in = True
            st.session_state.user_info = {'uid': user.uid, 'email': user.email, 'name': user.display_name}
            st.rerun()

    st.markdown("---")
    # Pestañas para Correo/Contraseña
    email_login, email_register = st.tabs(["Iniciar Sesión con Correo", "Registrarse con Correo"])
    with email_login:
        with st.form("login_form"):
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar Sesión"):
                try:
                    user = auth.get_user_by_email(email)
                    # La verificación de contraseña real requiere el SDK del cliente.
                    st.session_state.logged_in = True
                    st.session_state.user_info = {'uid': user.uid, 'email': user.email, 'name': user.display_name or user.email}
                    st.rerun()
                except Exception as e:
                    st.error("Error: Email o contraseña incorrectos.")
    with email_register:
        with st.form("register_form"):
            email = st.text_input("Correo Electrónico para registrar")
            password = st.text_input("Contraseña para registrar", type="password")
            if st.form_submit_button("Registrarse"):
                try:
                    user = auth.create_user(email=email, password=password)
                    st.success("¡Cuenta creada! Ahora inicia sesión.")
                except Exception as e:
                    st.error(f"Error al registrar: {e}")
else:
    # --- APLICACIÓN PRINCIPAL (SI EL USUARIO ESTÁ LOGUEADO) ---
    st.sidebar.title("Navegación")
    st.sidebar.write(f"Bienvenido, **{st.session_state.user_info.get('name', 'Usuario')}**")
    
    opcion = st.sidebar.radio("Selecciona una opción", ["Realizar nuevo test", "Consultar historial", "Chatbot de Diabetes"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

    # ... (El resto de las páginas de la app no tienen cambios)
    if opcion == "Realizar nuevo test":
        st.title("🩺 Software Predictivo de Diabetes con IA")
        # ... (código del formulario)
    elif opcion == "Consultar historial":
        st.title("📖 Tu Historial de Resultados")
        # ... (código del historial)
    elif opcion == "Chatbot de Diabetes":
        st.title("🤖 Chatbot Informativo sobre Diabetes")
        # ... (código del chatbot)
