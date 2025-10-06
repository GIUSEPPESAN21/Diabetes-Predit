# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v12.0 (Diseño Modular)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión refactorizada con una estructura modular para mayor claridad y mantenimiento.
- app.py: Contiene la interfaz de usuario de Streamlit.
- firebase_utils.py: Gestiona la conexión y operaciones con Firestore.
- gemini_utils.py: Centraliza la lógica para interactuar con la IA de Gemini.
- utils.py: Contiene funciones de cálculo y generación de PDF.
"""

import streamlit as st
from datetime import datetime
import uuid

# Importar los módulos refactorizados
from firebase_utils import FirebaseUtils
from gemini_utils import GeminiUtils
from utils import calcular_puntaje_findrisc, obtener_interpretacion_riesgo, generar_grafico_riesgo, generar_pdf

# --- CONFIGURACIÓN DE PÁGINA Y ESTADO DE SESIÓN ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide", initial_sidebar_state="collapsed")

# Inicializar estados de sesión
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "No determinado"

# --- INICIALIZACIÓN DE SERVICIOS (Cache para eficiencia) ---
@st.cache_resource
def initialize_services():
    """Inicializa los manejadores de Firebase y Gemini una sola vez."""
    try:
        firebase_handler = FirebaseUtils()
        gemini_handler = GeminiUtils()
        return firebase_handler, gemini_handler
    except Exception as e:
        st.error(f"Error crítico al inicializar los servicios: {e}")
        st.info("Por favor, verifica que las credenciales en los Streamlit Secrets (firebase_credentials y GEMINI_API_KEY) son correctas.")
        return None, None

firebase, gemini = initialize_services()

# Si los servicios no se pudieron inicializar, detener la app.
if not firebase or not gemini:
    st.stop()

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
            
            datos_usuario = {
                "fecha": datetime.now().isoformat(), "edad": edad, "sexo": sexo, "imc": imc, 
                "cintura": cintura, "actividad": actividad, "frutas_verduras": frutas_verduras, 
                "hipertension": hipertension, "glucosa_alta": glucosa_alta, 
                "familiar_diabetes": familiar_diabetes, "puntaje": puntaje, 
                "nivel_riesgo": nivel_riesgo, "estimacion": estimacion
            }

            with st.spinner("🤖 Analizando tus resultados con IA..."):
                analisis_ia = gemini.obtener_analisis_ia(datos_usuario)
                datos_usuario["analisis_ia"] = analisis_ia
                st.session_state.selected_model = gemini.get_last_used_model()

            st.subheader("Resultados de tu Evaluación")
            grafico = generar_grafico_riesgo(puntaje)
            st.plotly_chart(grafico, use_container_width=True)
            st.info(f"**Estimación a 10 años:** {estimacion}")
            st.markdown("---")
            st.subheader("🧠 Análisis y Recomendaciones por IA")
            st.markdown(analisis_ia)

            firebase.guardar_datos_en_firestore(st.session_state.user_id, datos_usuario)

            pdf_bytes = generar_pdf(datos_usuario)
            st.download_button(
                label="📥 Descargar Reporte en PDF", 
                data=pdf_bytes, 
                file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
        else:
            st.error("La altura no puede ser cero. Por favor, introduce un valor válido.")

with tab2:
    st.header("📖 Consultar Historial de Tests")
    st.markdown("Ingresa el ID de usuario que se te proporcionó al guardar tus resultados para ver tu historial.")

    user_id_input = st.text_input("Ingresa tu ID de usuario", value=st.session_state.user_id)

    if st.button("Buscar Historial", use_container_width=True):
        if user_id_input:
            historial = firebase.cargar_datos_de_firestore(user_id_input)
            if historial:
                st.success(f"Se encontraron {len(historial)} registros para el ID proporcionado.")
                for test in historial:
                    try:
                        fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                    except (ValueError, TypeError):
                        fecha_test = "Fecha desconocida"

                    expander_title = f"Test del {fecha_test} - Puntaje: {test.get('puntaje', 'N/A')} ({test.get('nivel_riesgo', 'N/A')})"
                    with st.expander(expander_title):
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

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe tu pregunta aquí..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Pensando..."):
            full_prompt = f"Como un asistente de salud experto en diabetes, responde la siguiente pregunta de forma clara y concisa en español: '{prompt}'"
            respuesta = gemini.llamar_gemini_directo(full_prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
            st.session_state.selected_model = gemini.get_last_used_model()

        with st.chat_message("assistant"):
            st.markdown(respuesta)

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("Acerca de")
    st.info(
        """
        **Predictor de Diabetes con IA**
        
        **Versión:** 12.0 (Estructura Modular)
        
        **Autor:** Joseph Javier Sánchez Acuña
        
        *Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*
        
        **Contacto:** joseph.sanchez@uniminuto.edu.co
        """
    )
    st.markdown("---")
    st.markdown("### 🤖 Estado de la IA")
    modelo_actual = st.session_state.get('selected_model', 'No determinado')
    st.metric(label="Modelo de IA Activo", value=modelo_actual)
