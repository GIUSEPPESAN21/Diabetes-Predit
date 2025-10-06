# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v11.0 (Diseño con Pestañas)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final con una interfaz de usuario mejorada que utiliza pestañas para la
navegación principal. Se reintroduce el Asistente de IA (Chatbot) como una
función principal para una experiencia más completa.

CORRECCIÓN: Se actualiza la función de llamada a Gemini para usar el SDK oficial
de Google y se implementa un sistema de fallback de modelos para resolver el error 404.
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from datetime import datetime
import plotly.graph_objects as go
import uuid
import logging

# Importación de la librería oficial de Google (CORREGIDA)
import google.generativeai as genai

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- CONFIGURACIÓN DE PÁGINA Y ESTADO DE SESIÓN ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide", initial_sidebar_state="collapsed")

# Inicializar estados de sesión
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "No determinado"


# --- CONEXIÓN CON FIREBASE ---

@st.cache_resource
def initialize_firebase_admin():
    """Inicializa el SDK de ADMIN para operaciones de base de datos."""
    try:
        if "firebase_credentials" in st.secrets:
            creds_dict = dict(st.secrets["firebase_credentials"])
            if 'private_key' in creds_dict:
                 creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            return firestore.client()
        st.error("Credenciales de Firebase no encontradas en los secretos.")
        return None
    except Exception as e:
        st.error(f"Error crítico al conectar con Firebase Admin: {e}")
        return None

db = initialize_firebase_admin()

# --- FUNCIONES DE LA APLICACIÓN ---

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

# --- FUNCIÓN GEMINI CORREGIDA Y OPTIMIZADA ---
def llamar_gemini(prompt):
    """
    Función corregida que usa el SDK oficial de Google y un sistema de fallback
    para evitar errores 404 y mejorar la robustez.
    """
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY or "PEGA_AQUÍ" in GEMINI_API_KEY:
        error_msg = "Error: La clave de API de Gemini no está configurada correctamente en los secretos."
        st.error(error_msg)
        return error_msg
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        }

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
        
        modelos_disponibles = [
            "gemini-2.0-flash-exp",  # Modelo experimental más reciente
            "gemini-1.5-flash-latest",  # Versión más reciente de 1.5
            "gemini-1.5-pro-latest",   # Versión más reciente de 1.5 pro
            "gemini-1.5-flash",        # Modelo básico
            "gemini-1.5-pro",          # Modelo pro básico
        ]
        
        for modelo in modelos_disponibles:
            try:
                model = genai.GenerativeModel(
                    model_name=modelo,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                response = model.generate_content(prompt)
                
                if response.parts:
                    texto_respuesta = "".join(part.text for part in response.parts)
                    if texto_respuesta.strip():
                        logger.info(f"Respuesta exitosa usando modelo: {modelo}")
                        st.session_state.selected_model = modelo
                        return texto_respuesta
                
                logger.warning(f"Respuesta vacía o bloqueada del modelo {modelo}. Probando siguiente modelo.")
                continue

            except Exception as modelo_error:
                logger.warning(f"Error con modelo {modelo}: {str(modelo_error)}. Probando siguiente modelo...")
                continue
        
        error_message = "Todos los modelos de Gemini fallaron o no están disponibles."
        st.error(error_message)
        return f"Error: {error_message}"

    except Exception as e:
        error_message = f"Error crítico al configurar o llamar a la API de Gemini: {e}"
        st.error(error_message)
        return error_message

def obtener_analisis_ia(datos_usuario):
    prompt = f"Como un experto en salud y prevención de la diabetes, analiza los siguientes datos del test FINDRISC de un paciente: {datos_usuario}. Basado en esta información, proporciona un análisis detallado del nivel de riesgo, ofrece 3 recomendaciones clave, claras y accionables para reducir su riesgo, y sugiere los próximos pasos a seguir. El tono debe ser profesional, empático y fácil de entender para una persona sin conocimientos médicos."
    return llamar_gemini(prompt)

def guardar_datos_en_firestore(user_id, datos):
    if not db:
        st.warning("No se pueden guardar los datos porque la conexión con Firebase falló.")
        return
    try:
        doc_ref = db.collection('usuarios').document(user_id).collection('tests').document()
        doc_ref.set(datos)
        st.success(f"¡Resultados guardados con éxito! Tu ID de usuario es:")
        st.code(user_id)
        st.info("Guarda este ID para consultar tus resultados en el futuro.")
    except Exception as e:
        st.error(f"Ocurrió un error al guardar los datos: {e}")

def cargar_datos_de_firestore(user_id):
    if not db:
        st.warning("No se pueden cargar los datos porque la conexión con Firebase falló.")
        return []
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

st.title("🩺 Predictor de Diabetes con IA")
st.markdown("Esta herramienta utiliza el **Cuestionario FINDRISC** para estimar tu riesgo de desarrollar Diabetes tipo 2 en los próximos 10 años.")

# --- NAVEGACIÓN POR PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["**Realizar Nuevo Test**", "**Consultar Historial**", "**Asistente de IA (Chatbot)**"])

with tab1:
    st.header("Cuestionario de Riesgo")
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
        if altura > 0:
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

            guardar_datos_en_firestore(st.session_state.user_id, datos_usuario)
            
            pdf_bytes = generar_pdf(datos_usuario)
            st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.error("La altura no puede ser cero. Por favor, introduce un valor válido.")

with tab2:
    st.header("📖 Consultar Historial de Tests")
    st.markdown("Ingresa el ID de usuario que se te proporcionó al guardar tus resultados para ver tu historial.")

    user_id_input = st.text_input("Ingresa tu ID de usuario", value=st.session_state.user_id)

    if st.button("Buscar Historial", use_container_width=True):
        if user_id_input:
            historial = cargar_datos_de_firestore(user_id_input)
            if historial:
                st.success(f"Se encontraron {len(historial)} registros para el ID proporcionado.")
                for test in historial:
                    try:
                        fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                    except (ValueError, TypeError):
                        fecha_test = "Fecha desconocida"
                    
                    with st.expander(f"Test del {fecha_test} - Puntaje: {test.get('puntaje', 'N/A')} ({test.get('nivel_riesgo', 'N/A')})"):
                        st.write(f"**IMC:** {test.get('imc', 0):.2f}, **Cintura:** {test.get('cintura', 'N/A')} cm")
                        st.markdown("---")
                        st.subheader("Análisis de IA de este resultado:")
                        st.markdown(test.get("analisis_ia", "No hay análisis disponible."))
            else:
                st.warning("No se encontraron resultados para este ID. Verifica que sea correcto.")
        else:
            st.error("Por favor, ingresa un ID de usuario.")

with tab3:
    st.header("🤖 Asistente de Diabetes con IA (Chatbot)")
    st.markdown("Hazme una pregunta sobre la diabetes o la salud en general.")

    # Mostrar historial del chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu pregunta aquí..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):
            full_prompt = f"Como un asistente de salud experto en diabetes, responde la siguiente pregunta de forma clara y concisa en español: '{prompt}'"
            respuesta = llamar_gemini(full_prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
        
        with st.chat_message("assistant"):
            st.markdown(respuesta)


# --- BARRA LATERAL (PARA INFORMACIÓN ADICIONAL) ---
with st.sidebar:
    st.title("Acerca de")
    st.info(
        """
        **Predictor de Diabetes con IA**
        
        **Versión:** 11.2 (Modelos de IA actualizados)
        
        **Autor:** Joseph Javier Sánchez Acuña
        
        *Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*
        
        **Contacto:** joseph.sanchez@uniminuto.edu.co
        """
    )
    st.markdown("---")
    st.markdown("### 🤖 Estado de la IA")
    modelo_actual = st.session_state.get('selected_model', 'No determinado')
    st.metric(label="Modelo de IA Activo", value=modelo_actual)

