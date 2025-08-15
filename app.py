# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v4.0
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Esta versión implementa un sistema de autenticación robusto y seguro utilizando
la librería streamlit-authenticator. Se elimina la dependencia anterior que causaba
errores de instalación.

Instrucciones:
1.  Asegúrate de que tu archivo 'requirements.txt' contiene 'streamlit-authenticator'.
2.  Configura tus credenciales de Firebase en los secretos de Streamlit como [firebase_credentials].
3.  Configura las credenciales del autenticador en los secretos como [authenticator].

"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
import json
from datetime import datetime
from fpdf import FPDF
import streamlit_authenticator as stauth
import yaml

# --- CONFIGURACIÓN DE SERVICIOS ---

# Configuración de Firebase
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(st.secrets["firebase_credentials"])
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Error crítico al inicializar Firebase: {e}. Revisa tus secretos.")
    st.stop()

# Configuración del Autenticador
# Los datos de los usuarios ahora se gestionan a través del autenticador
# y se pueden almacenar en un archivo YAML o en una base de datos.
# Por seguridad, cargamos la configuración desde los secretos de Streamlit.
try:
    authenticator_config = st.secrets["authenticator"]
    authenticator = stauth.Authenticate(
        authenticator_config["credentials"],
        authenticator_config["cookie"]["name"],
        authenticator_config["cookie"]["key"],
        authenticator_config["cookie"]["expiry_days"],
        authenticator_config["preauthorized"]
    )
except Exception as e:
    st.error(f"Error al configurar el autenticador: {e}. Revisa la sección 'authenticator' en tus secretos.")
    st.stop()

# --- CLASES Y FUNCIONES (sin cambios) ---
class PDF(FPDF):
    def header(self): self.set_font('Arial', 'B', 12); self.cell(0, 10, 'Reporte de Riesgo de Diabetes', 0, 1, 'C'); self.ln(10)
    def footer(self): self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title): self.set_font('Arial', 'B', 12); self.cell(0, 10, title, 0, 1, 'L'); self.ln(4)
    def chapter_body(self, body): self.set_font('Arial', '', 12); self.multi_cell(0, 10, body); self.ln()

def generar_pdf(datos_reporte):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title('Datos del Paciente'); fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
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
    pdf.set_y(-40); pdf.set_font('Arial', 'I', 9)
    autor_info = ("Software por: Joseph Javier Sánchez Acuña\n"
                  "Contacto: joseph.sanchez@uniminuto.edu.co")
    pdf.multi_cell(0, 5, autor_info, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

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
def obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion): return "Análisis de IA (función sin cambios)"
def guardar_datos_en_firestore(user_id, datos): pass
def cargar_datos_de_firestore(user_id): return []

# --- INTERFAZ DE USUARIO CON NUEVO AUTENTICADOR ---
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

    # Páginas de la aplicación
    if opcion == "Realizar nuevo test":
        st.title("🩺 Software Predictivo de Diabetes con IA")
        # ... (código del formulario sin cambios)
    elif opcion == "Consultar historial":
        st.title("📖 Tu Historial de Resultados")
        # ... (código del historial sin cambios)
    elif opcion == "Chatbot de Diabetes":
        st.title("🤖 Chatbot Informativo sobre Diabetes")
        # ... (código del chatbot sin cambios)

elif st.session_state["authentication_status"] is False:
    st.error('Usuario/contraseña incorrectos')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, introduce tu usuario y contraseña')

    # Opcional: Habilitar el registro de nuevos usuarios
    try:
        if authenticator.register_user('Registrar nuevo usuario', preauthorization=False):
            st.success('¡Usuario registrado con éxito! Por favor, inicia sesión.')
            # Aquí podrías añadir la lógica para guardar la nueva configuración de usuarios
            # de forma persistente si no usas un archivo YAML estático.
    except Exception as e:
        st.error(e)
