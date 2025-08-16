# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v9.0 (Versión Estable Final)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final que integra una arquitectura de autenticación probada y funcional,
basada en una estructura estable para resolver problemas de conexión persistentes.
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
from fpdf import FPDF
from datetime import datetime
import requests
import json
import plotly.graph_objects as go
import os
import tempfile

# --- CONFIGURACIÓN DE PÁGINA Y ESTADO DE SESIÓN ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide", initial_sidebar_state="collapsed")

# Inicializar el estado de la sesión para el usuario
if 'user' not in st.session_state:
    st.session_state.user = None

# --- CONEXIÓN CON FIREBASE (MÉTODO PROBADO) ---

@st.cache_resource
def initialize_firebase_admin():
    """Inicializa el SDK de ADMIN para operaciones de base de datos."""
    try:
        if "firebase_credentials" in st.secrets:
            creds_dict = dict(st.secrets["firebase_credentials"])
            # Asegurar formato correcto de la clave privada
            if 'private_key' in creds_dict:
                 creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            return firestore.client()
        return None
    except Exception as e:
        st.error(f"Error crítico al conectar con Firebase Admin: {e}")
        return None

@st.cache_resource
def initialize_firebase_auth():
    """Inicializa el SDK de CLIENTE para autenticación."""
    try:
        if "firebase_client_config" in st.secrets:
            firebase_client_config = dict(st.secrets["firebase_client_config"])
            return pyrebase.initialize_app(firebase_client_config)
        return None
    except Exception as e:
        st.error(f"Error crítico al inicializar Pyrebase: {e}")
        return None

db = initialize_firebase_admin()
firebase_auth_app = initialize_firebase_auth()

# --- FUNCIONES DE LA APLICACIÓN (SIN CAMBIOS) ---

class PDF(FPDF):
    def header(self): self.set_font('Arial', 'B', 12); self.cell(0, 10, 'Reporte de Riesgo de Diabetes', 0, 1, 'C'); self.ln(10)
    def footer(self): self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title): self.set_font('Arial', 'B', 12); self.cell(0, 10, title, 0, 1, 'L'); self.ln(4)
    def chapter_body(self, body): self.set_font('Arial', '', 11); self.multi_cell(0, 6, body); self.ln()

def generar_pdf(datos_reporte):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title('1. Datos del Paciente'); fecha_reporte = datetime.now().strftime('%d/%m/%Y')
    info_paciente = (f"Fecha del reporte: {fecha_reporte}\n"
                     f"Edad: {datos_reporte['edad']} años\n"
                     f"Sexo: {datos_reporte['sexo']}\n"
                     f"IMC (Índice de Masa Corporal): {datos_reporte['imc']:.2f}\n"
                     f"Perímetro de cintura: {datos_reporte['cintura']} cm")
    pdf.chapter_body(info_paciente)
    pdf.chapter_title('2. Resultados del Cuestionario FINDRISC')
    resultados = (f"Puntaje Total: {datos_reporte['puntaje']} puntos\n"
                  f"Nivel de Riesgo: {datos_reporte['nivel_riesgo']}\n"
                  f"Estimación a 10 años: {datos_reporte['estimacion']}")
    pdf.chapter_body(resultados)
    pdf.chapter_body("El gráfico de riesgo interactivo está disponible en la aplicación web.")
    pdf.chapter_title('3. Análisis y Recomendaciones por IA (Gemini)')
    analisis_ia_encoded = datos_reporte['analisis_ia'].encode('latin-1', 'replace').decode('latin-1')
    pdf.chapter_body(analisis_ia_encoded)
    pdf.set_y(-40); pdf.set_font('Arial', 'I', 9)
    autor_info = ("Software desarrollado por:\n"
                  "Joseph Javier Sánchez Acuña: Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.\n"
                  "Contacto: joseph.sanchez@uniminuto.edu.co")
    pdf.multi_cell(0, 5, autor_info, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

def calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes):
    score = 0
    if 45 <= edad <= 54: score += 2
    elif 55 <= edad <= 64: score += 3
    elif edad > 64: score += 4
    if 25 <= imc < 30: score += 1
    elif imc >= 30: score += 3
    if sexo == "Masculino":
        if 94 <= cintura <= 102: score += 3
        elif cintura > 102: score += 4
    elif sexo == "Femenino":
        if 80 <= cintura <= 88: score += 3
        elif cintura > 88: score += 4
    if actividad == "No": score += 2
    if frutas_verduras == "No todos los días": score += 1
    if hipertension == "Sí": score += 2
    if glucosa_alta == "Sí": score += 5
    if familiar_diabetes == "Sí: padres, hermanos o hijos": score += 5
    elif familiar_diabetes == "Sí: abuelos, tíos o primos": score += 3
    return score

def obtener_interpretacion_riesgo(score):
    if score < 7: return "Riesgo bajo", "1 de cada 100 personas desarrollará diabetes."
    elif 7 <= score <= 11: return "Riesgo ligeramente elevado", "1 de cada 25 personas desarrollará diabetes."
    elif 12 <= score <= 14: return "Riesgo moderado", "1 de cada 6 personas desarrollará diabetes."
    elif 15 <= score <= 20: return "Riesgo alto", "1 de cada 3 personas desarrollará diabetes."
    else: return "Riesgo muy alto", "1 de cada 2 personas desarrollará diabetes."

def llamar_gemini(prompt):
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY or "PEGA_AQUÍ" in GEMINI_API_KEY:
        return "Error: La clave de API de Gemini no está configurada en los secretos."
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Error de conexión con la API de Gemini: {e}"
    except (KeyError, IndexError):
        return f"Respuesta inesperada de la API de Gemini. Verifica que tu clave de API sea correcta."

def obtener_analisis_ia(datos_usuario):
    prompt = f"Como experto en salud, analiza estos datos del test FINDRISC: {datos_usuario} y ofrece un análisis del resultado, recomendaciones clave y próximos pasos."
    return llamar_gemini(prompt)

def guardar_datos_en_firestore(user_id, datos):
    if not db: return
    try:
        doc_ref = db.collection('usuarios').document(user_id).collection('tests').document()
        doc_ref.set(datos)
        st.success("¡Resultados guardados con éxito en tu historial!")
    except Exception as e:
        st.error(f"Ocurrió un error al guardar los datos: {e}")

def cargar_datos_de_firestore(user_id):
    if not db: return []
    try:
        tests_ref = db.collection('usuarios').document(user_id).collection('tests').order_by("fecha", direction=firestore.Query.DESCENDING)
        docs = tests_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Ocurrió un error al cargar los datos: {e}")
        return []

def generar_grafico_riesgo(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, domain={'x': [0, 1], 'y': [0, 1]}, title={'text': "<b>Nivel de Riesgo de Diabetes</b>"},
        gauge={'axis': {'range': [0, 25], 'tickwidth': 1, 'tickcolor': "darkblue"}, 'bar': {'color': "rgba(0,0,0,0.4)"}, 'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "#cccccc",
               'steps': [{'range': [0, 6], 'color': '#28a745'}, {'range': [7, 11], 'color': '#a3d900'}, {'range': [12, 14], 'color': '#ffc107'}, {'range': [15, 20], 'color': '#fd7e14'}, {'range': [21, 25], 'color': '#dc3545'}],
               'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.85, 'value': score}}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#333333", 'family': "Arial"})
    return fig

# --- INTERFAZ DE USUARIO ---

def display_login_form():
    """Muestra el formulario de inicio de sesión y registro."""
    st.title("🩺 Predictor de Diabetes con IA")
    st.markdown("Bienvenido. Por favor, inicie sesión o regístrese para continuar.")

    if not firebase_auth_app:
        st.error("La configuración de autenticación no está disponible. Contacta al administrador.")
        return

    auth_client = firebase_auth_app.auth()
    col1, col2 = st.columns([1,1])

    with col1:
        with st.container(border=True):
            st.subheader("Iniciar Sesión")
            email = st.text_input("Correo Electrónico", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", use_container_width=True, type="primary"):
                try:
                    user = auth_client.sign_in_with_email_and_password(email, password)
                    st.session_state.user = user
                    st.rerun()
                except Exception:
                    st.error("Error: Email o contraseña incorrectos.")
    
    with col2:
        with st.container(border=True):
            st.subheader("Registrar Nuevo Usuario")
            name = st.text_input("Nombre Completo", key="reg_name")
            email_reg = st.text_input("Correo Electrónico para registrar", key="reg_email")
            password_reg = st.text_input("Crea una Contraseña (mín. 6 caracteres)", type="password", key="reg_pass")
            if st.button("Registrarse", use_container_width=True):
                if not all([name, email_reg, password_reg]):
                    st.warning("Por favor, completa todos los campos.")
                else:
                    try:
                        user = auth_client.create_user_with_email_and_password(email_reg, password_reg)
                        st.success(f"¡Cuenta creada con éxito para {email_reg}!")
                        st.info("Ahora puedes iniciar sesión con tus credenciales.")
                        st.balloons()
                    except Exception:
                        st.error("Error al crear la cuenta. Es posible que el correo ya esté en uso o la contraseña sea muy débil.")

def display_main_app():
    """Muestra la aplicación principal una vez que el usuario está autenticado."""
    user_email = st.session_state.user.get('email', 'Usuario')
    user_uid = st.session_state.user.get('localId')
    
    with st.sidebar:
        st.title(f"Bienvenido,")
        st.markdown(f"*{user_email}*")
        if st.button("Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.user = None
            st.rerun()
        st.markdown("---")
        st.subheader("Autor")
        st.info("Joseph Javier Sánchez Acuña\n\n*Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*\n\n**Contacto:** joseph.sanchez@uniminuto.edu.co")

    st.title("🩺 Predictor de Diabetes con IA")
    
    tab1, tab2, tab3 = st.tabs(["**Análisis de Caso**", "**Asistente de Diabetes (Chatbot)**", "**Consultar Casos Anteriores**"])

    with tab1:
        st.header("Realizar Nuevo Test de Riesgo")
        with st.form("findrisc_form_v2"):
            col1, col2 = st.columns(2)
            with col1:
                edad = st.number_input("1. Edad", 18, 120, 40)
                sexo = st.selectbox("2. Sexo", ("Masculino", "Femenino"))
                peso = st.number_input("3. Peso (kg)", 30.0, 300.0, 70.0, 0.5)
                altura = st.number_input("4. Altura (m)", 1.0, 2.5, 1.75, 0.01)
                cintura = st.number_input("5. Perímetro de cintura (cm)", 50, 200, 90)
            with col2:
                actividad = st.radio("6. ¿Realizas al menos 30 min de actividad física diaria?", ("Sí", "No"))
                frutas_verduras = st.radio("7. ¿Comes frutas y verduras todos los días?", ("Sí", "No todos los días"))
                hipertension = st.radio("8. ¿Tomas medicamentos para la presión alta?", ("Sí", "No"))
                glucosa_alta = st.radio("9. ¿Has tenido niveles de glucosa altos alguna vez?", ("Sí", "No"))
            familiar_diabetes = st.selectbox("10. ¿Familiares con diabetes?", ("No", "Sí: abuelos, tíos o primos", "Sí: padres, hermanos o hijos"))
            submit_button = st.form_submit_button("Calcular Riesgo y Generar Reporte", use_container_width=True, type="primary")
        
        if submit_button:
            imc = peso / (altura ** 2)
            puntaje = calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes)
            nivel_riesgo, estimacion = obtener_interpretacion_riesgo(puntaje)
            datos_usuario = {"fecha": datetime.now().isoformat(), "edad": edad, "sexo": sexo, "imc": imc, "cintura": cintura, "actividad": actividad, "frutas_verduras": frutas_verduras, "hipertension": hipertension, "glucosa_alta": glucosa_alta, "familiar_diabetes": familiar_diabetes, "puntaje": puntaje, "nivel_riesgo": nivel_riesgo, "estimacion": estimacion}
            
            with st.spinner("🤖 Analizando tus resultados con IA..."):
                analisis_ia = obtener_analisis_ia(datos_usuario)
                datos_usuario["analisis_ia"] = analisis_ia

            st.subheader("Resultados de tu Evaluación")
            grafico = generar_grafico_riesgo(puntaje)
            st.plotly_chart(grafico, use_container_width=True)
            st.info(f"**Estimación a 10 años:** {estimacion}")
            st.markdown("---")
            st.subheader("🧠 Análisis y Recomendaciones por IA")
            st.markdown(analisis_ia)

            guardar_datos_en_firestore(user_uid, datos_usuario)
            
            pdf_bytes = generar_pdf(datos_usuario)
            st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)

    with tab2:
        st.header("🤖 Asistente de Diabetes con Gemini")
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        preguntas = ["¿Cuáles son los primeros síntomas de la diabetes?", "¿Qué alimentos debe evitar una persona con prediabetes?", "¿Cómo afecta el ejercicio al nivel de azúcar en la sangre?", "Explícame la diferencia entre diabetes tipo 1 y tipo 2."]
        q_cols = st.columns(2)
        for i, q in enumerate(preguntas):
            if q_cols[i % 2].button(q, use_container_width=True, key=f"q_{i}"):
                st.session_state.last_question = q
        if prompt := st.chat_input("Escribe tu pregunta aquí...") or st.session_state.get('last_question'):
            st.session_state.last_question = ""
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("Pensando..."):
                respuesta = llamar_gemini(f"Como experto en salud, responde: '{prompt}'")
                st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    with tab3:
        st.header("📖 Consultar Mis Casos Anteriores")
        historial = cargar_datos_de_firestore(user_uid)
        if historial:
            st.success(f"Se encontraron {len(historial)} registros.")
            for test in historial:
                fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                with st.expander(f"Test del {fecha_test} - Puntaje: {test['puntaje']} ({test['nivel_riesgo']})"):
                    st.write(f"**IMC:** {test['imc']:.2f}, **Cintura:** {test['cintura']} cm")
                    st.markdown("---")
                    st.subheader("Análisis de IA de este resultado:")
                    st.markdown(test.get("analisis_ia", "No hay análisis disponible."))
        else:
            st.info("Aún no tienes casos guardados.")

# --- FLUJO PRINCIPAL DE LA APLICACIÓN ---
def main():
    """Función principal que dirige al login o a la app."""
    if 'user' not in st.session_state or st.session_state.user is None:
        display_login_form()
    else:
        display_main_app()

if __name__ == "__main__":
    main()
