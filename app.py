# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v12.0 (Autenticación y UI Mejorada)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Esta versión introduce un sistema de autenticación de usuarios (login y registro)
y renueva por completo la interfaz de usuario. Se elimina la barra lateral para
integrar todo en una navegación por pestañas más limpia y moderna. También se
aplica un nuevo estilo visual para mejorar la experiencia del usuario.
"""

import streamlit as st
from firebase_utils import FirebaseUtils
from gemini_utils import GeminiUtils
from utils import generar_pdf, calcular_puntaje_findrisc, obtener_interpretacion_riesgo, generar_grafico_riesgo
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SaludIA | Predictor de Diabetes",
    layout="wide",
    page_icon="🩺"
)

# --- INYECCIÓN DE CSS PARA ESTILOS MODERNOS ---
def load_css():
    st.markdown("""
    <style>
        /* --- Fuentes y Colores Base --- */
        html, body, [class*="st-"] {
            font-family: 'Inter', sans-serif;
            background-color: #F0F2F6; /* Fondo gris claro */
        }

        /* --- Títulos --- */
        h1, h2, h3 {
            font-weight: 700 !important;
            color: #1E3A8A; /* Azul oscuro */
        }
        
        /* --- Contenedores y Tarjetas --- */
        .stApp > header {
            background-color: transparent;
        }
        
        .main-container {
            padding: 2rem;
            background-color: #FFFFFF;
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        }

        /* --- Pestañas de Navegación --- */
        button[data-baseweb="tab"] {
            font-size: 1.1rem;
            font-weight: 600;
            background-color: transparent;
            border-radius: 8px;
            margin: 0 5px;
            transition: all 0.3s ease;
            color: #4B5563; /* Gris */
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #1E3A8A;
            color: white;
            box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
        }

        /* --- Botones --- */
        .stButton>button {
            border-radius: 12px;
            border: 2px solid #1E3A8A;
            background-color: #1E3A8A;
            color: white;
            padding: 12px 28px;
            font-weight: 700;
            transition: all 0.3s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #2563EB; /* Azul más claro */
            border-color: #2563EB;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
        }

        /* --- Formularios y Entradas --- */
        .stTextInput, .stNumberInput, .stSelectbox {
            background-color: #F9FAFB;
            border-radius: 10px;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE SERVICIOS ---
@st.cache_resource
def initialize_services():
    """Inicializa Firebase y Gemini una sola vez."""
    try:
        firebase_handler = FirebaseUtils()
        gemini_handler = GeminiUtils()
        return firebase_handler, gemini_handler
    except Exception as e:
        st.error(f"Error Crítico de Inicialización: No se pudo conectar a los servicios. Detalles: {e}")
        return None, None

firebase, gemini = initialize_services()

if not firebase or not gemini:
    st.stop()


# --- PÁGINA PRINCIPAL DE LA APLICACIÓN (POST-LOGIN) ---
def main_app():
    st.title("🩺 SaludIA: Predictor de Riesgo de Diabetes")
    st.markdown("Una herramienta inteligente que utiliza el **Cuestionario FINDRISC** y la **IA de Gemini** para estimar tu riesgo de desarrollar Diabetes tipo 2.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "**🏠 Realizar Nuevo Test**",
        "**📖 Consultar Historial**",
        "**🤖 Asistente de IA**",
        "**ℹ️ Acerca de**"
    ])

    with tab1:
        st.header("Cuestionario de Riesgo FINDRISC")
        with st.form("findrisc_form_v3"):
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
            submit_button = st.form_submit_button("Calcular Riesgo y Generar Reporte", use_container_width=True)

        if submit_button:
            if altura > 0:
                imc = peso / (altura ** 2)
                puntaje = calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes)
                nivel_riesgo, estimacion = obtener_interpretacion_riesgo(puntaje)
                datos_usuario = {"fecha": datetime.now().isoformat(), "edad": edad, "sexo": sexo, "imc": imc, "cintura": cintura, "actividad": actividad, "frutas_verduras": frutas_verduras, "hipertension": hipertension, "glucosa_alta": glucosa_alta, "familiar_diabetes": familiar_diabetes, "puntaje": puntaje, "nivel_riesgo": nivel_riesgo, "estimacion": estimacion}
                
                with st.spinner("🤖 Analizando tus resultados con IA..."):
                    analisis_ia = gemini.obtener_analisis_ia(datos_usuario)
                    datos_usuario["analisis_ia"] = analisis_ia

                st.subheader("Resultados de tu Evaluación")
                st.plotly_chart(generar_grafico_riesgo(puntaje), use_container_width=True)
                st.info(f"**Estimación a 10 años:** {estimacion}")
                st.markdown("---")
                st.subheader("🧠 Análisis y Recomendaciones por IA")
                st.markdown(analisis_ia)

                firebase.guardar_datos_test(st.session_state['user_uid'], datos_usuario)
                
                pdf_bytes = generar_pdf(datos_usuario)
                st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)
            else:
                st.error("La altura no puede ser cero. Por favor, introduce un valor válido.")

    with tab2:
        st.header("📖 Tu Historial de Tests")
        st.markdown("Aquí puedes ver todos los tests que has realizado.")
        
        historial = firebase.cargar_datos_test(st.session_state['user_uid'])
        if historial:
            st.success(f"Se encontraron {len(historial)} registros en tu historial.")
            for test in historial:
                fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                with st.expander(f"Test del {fecha_test} - Puntaje: {test.get('puntaje', 'N/A')} ({test.get('nivel_riesgo', 'N/A')})"):
                    st.write(f"**IMC:** {test.get('imc', 0):.2f}, **Cintura:** {test.get('cintura', 'N/A')} cm")
                    st.markdown("---")
                    st.subheader("Análisis de IA de este resultado:")
                    st.markdown(test.get("analisis_ia", "No hay análisis disponible."))
        else:
            st.info("Aún no has realizado ningún test. ¡Completa uno en la pestaña 'Realizar Nuevo Test'!")

    with tab3:
        st.header("🤖 Asistente de Diabetes con IA (Chatbot)")
        st.markdown("Hazme una pregunta sobre la diabetes, nutrición o hábitos saludables.")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

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
            
            with st.chat_message("assistant"):
                st.markdown(respuesta)
    
    with tab4:
        st.header("ℹ️ Acerca del Proyecto")
        st.markdown(
            """
            **SaludIA: Predictor de Diabetes** es una aplicación diseñada para la prevención y concienciación sobre la Diabetes tipo 2.
            
            - **Versión:** 12.0 (Interfaz Renovada y Autenticación)
            - **Autor:** Joseph Javier Sánchez Acuña
            - **Tecnologías:** Streamlit, Firebase, Google Gemini AI.
            
            *Este software es una herramienta de estimación y no reemplaza el diagnóstico de un profesional médico.*
            """
        )
        st.metric(label="Modelo de IA Activo", value=gemini.get_last_used_model())
        
        if st.button("Cerrar Sesión"):
            st.session_state['logged_in'] = False
            st.session_state['user_uid'] = None
            st.experimental_rerun()


# --- PÁGINA DE LOGIN Y REGISTRO ---
def login_page():
    st.title("Bienvenido a SaludIA 🩺")
    st.markdown("Tu asistente personal para la prevención de la diabetes. Inicia sesión o regístrate para comenzar.")

    login_tab, signup_tab = st.tabs(["**Iniciar Sesión**", "**Registrarse**"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            login_button = st.form_submit_button("Ingresar", use_container_width=True)

            if login_button:
                user_uid = firebase.verify_user(email, password)
                if user_uid:
                    st.session_state['logged_in'] = True
                    st.session_state['user_uid'] = user_uid
                    st.experimental_rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")
    
    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("Correo Electrónico para registrarse")
            new_password = st.text_input("Crea una Contraseña", type="password")
            signup_button = st.form_submit_button("Registrarme", use_container_width=True)

            if signup_button:
                if new_email and new_password:
                    success, message = firebase.create_user(new_email, new_password)
                    if success:
                        st.success(message)
                        st.info("Ahora puedes iniciar sesión en la pestaña 'Iniciar Sesión'.")
                    else:
                        st.error(message)
                else:
                    st.warning("Por favor, ingresa un correo y una contraseña.")


# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
load_css()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    st.container(border=True, height=None).write(main_app())
else:
    st.container(border=True, height=None).write(login_page())

