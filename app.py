# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v17.0 (Diseño Final y Definitivo)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final con un rediseño completo de la interfaz, adoptando un layout
profesional con una barra de navegación lateral. Se introduce una paleta de
colores "health-tech", iconos, tarjetas con sombras suaves y micro-animaciones
en todos los elementos para una experiencia de usuario premium.
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

# --- INYECCIÓN DE CSS PARA UN REDISEÑO TOTAL ---
def load_css():
    st.markdown("""
    <style>
        /* --- Fuentes y Tema Base --- */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        
        :root {
            --bg-color: #F8FAFC;
            --sidebar-bg: #FFFFFF;
            --card-bg: #FFFFFF;
            --text-color: #334155;
            --title-color: #0F172A;
            --subtle-text: #64748B;
            --border-color: #E2E8F0;
            --primary-color: #3B82F6;
            --primary-hover: #2563EB;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --gradient: linear-gradient(135deg, #3B82F6 0%, #6D28D9 100%);
        }

        [data-theme="dark"] {
            --bg-color: #0F172A;
            --sidebar-bg: #1E293B;
            --card-bg: #1E293B;
            --text-color: #CBD5E1;
            --title-color: #F8FAFC;
            --subtle-text: #94A3B8;
            --border-color: #334155;
            --primary-color: #60A5FA;
            --primary-hover: #3B82F6;
        }

        /* --- Estructura y Ocultar Elementos de Streamlit --- */
        html, body, [class*="st-"] {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-color);
        }
        .stApp > header { display: none; }
        .main .block-container { padding: 2rem 3rem; }

        /* --- Barra de Navegación Lateral --- */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 1.5rem;
        }
        .sidebar-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 2rem;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        /* Ocultar el punto del radio button */
        [data-testid="stRadio"] > label > div:first-child { display: none; }
        /* Estilo de los links de navegación */
        [data-testid="stRadio"] > label {
            display: block;
            padding: 0.8rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--subtle-text);
            transition: all 0.2s ease-in-out;
        }
        [data-testid="stRadio"] > label:hover {
            background-color: var(--primary-hover);
            color: white;
            transform: translateX(5px);
        }
        /* Estilo del link activo */
        [data-testid="stRadio"] > div[role="radiogroup"] > label[data-in-selection="true"] {
            background: var(--gradient);
            color: white;
            box-shadow: 0 4px 15px -5px rgba(59, 130, 246, 0.4);
        }
        .sidebar-footer {
            position: absolute;
            bottom: 2rem;
            width: calc(100% - 3rem);
        }

        /* --- Contenido Principal y Tarjetas --- */
        .card {
            background: var(--card-bg);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--border-color);
        }
        .page-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--title-color);
            margin-bottom: 2rem;
        }

        /* --- Botones con Animación Mejorada --- */
        .stButton>button {
            border-radius: 0.5rem;
            border: none;
            font-weight: 600;
            padding: 0.8rem 1.5rem;
            transition: all 0.3s ease;
            background: var(--gradient);
            color: white;
            box-shadow: 0 4px 15px -5px rgba(59, 130, 246, 0.4);
        }
        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 20px -5px rgba(59, 130, 246, 0.6);
        }
        .stButton>button:active {
            transform: translateY(-1px);
        }
        .stButton.logout-button>button {
            background: #DC2626;
        }
        .stButton.logout-button>button:hover {
            background: #B91C1C;
        }
        
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE SERVICIOS ---
@st.cache_resource
def initialize_services():
    try:
        firebase_handler = FirebaseUtils()
        gemini_handler = GeminiUtils()
        return firebase_handler, gemini_handler
    except Exception as e:
        st.error(f"Error Crítico de Inicialización: {e}")
        return None, None

firebase, gemini = initialize_services()
if not firebase or not gemini:
    st.stop()

# --- PÁGINAS DE LA APLICACIÓN ---

def new_test_page():
    st.markdown('<p class="page-title">Realizar Nuevo Test</p>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("findrisc_form_v3"):
            # ... (código del formulario sin cambios)
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
            # ... (código de procesamiento de resultados sin cambios)
            if altura > 0:
                imc = peso / (altura ** 2)
                puntaje = calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes)
                nivel_riesgo, estimacion = obtener_interpretacion_riesgo(puntaje)
                datos_usuario = {"fecha": datetime.now().isoformat(), "edad": edad, "sexo": sexo, "imc": imc, "cintura": cintura, "actividad": actividad, "frutas_verduras": frutas_verduras, "hipertension": hipertension, "glucosa_alta": glucosa_alta, "familiar_diabetes": familiar_diabetes, "puntaje": puntaje, "nivel_riesgo": nivel_riesgo, "estimacion": estimacion}
                with st.spinner("🤖 Analizando tus resultados con IA..."):
                    analisis_ia = gemini.obtener_analisis_ia(datos_usuario)
                    datos_usuario["analisis_ia"] = analisis_ia
                st.markdown('<h2 class="section-header">Resultados de tu Evaluación</h2>', unsafe_allow_html=True)
                res_col1, res_col2 = st.columns([1, 1])
                with res_col1:
                    st.plotly_chart(generar_grafico_riesgo(puntaje), use_container_width=True)
                with res_col2:
                    st.metric("Puntaje FINDRISC", f"{puntaje} puntos")
                    st.metric("Nivel de Riesgo", nivel_riesgo)
                    st.info(f"**Estimación a 10 años:** {estimacion}")
                st.markdown('<h3 class="section-header">🧠 Análisis y Recomendaciones por IA</h3>', unsafe_allow_html=True)
                st.markdown(f'<div style="background-color: var(--bg-color); padding: 1.5rem; border-radius: 10px;">{analisis_ia}</div>', unsafe_allow_html=True)
                firebase.guardar_datos_test(st.session_state['user_uid'], datos_usuario)
                pdf_bytes = generar_pdf(datos_usuario)
                st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)
            else:
                st.error("La altura no puede ser cero.")

        st.markdown('</div>', unsafe_allow_html=True)

def history_page():
    st.markdown('<p class="page-title">Historial de Tests</p>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        historial = firebase.cargar_datos_test(st.session_state['user_uid'])
        if historial:
            st.success(f"Se encontraron {len(historial)} registros en tu historial.")
            for test in historial:
                # ... (código del historial sin cambios)
                fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                with st.expander(f"Test del {fecha_test} - Puntaje: {test.get('puntaje', 'N/A')} ({test.get('nivel_riesgo', 'N/A')})"):
                    st.write(f"**IMC:** {test.get('imc', 0):.2f}, **Cintura:** {test.get('cintura', 'N/A')} cm")
                    st.markdown("---")
                    st.subheader("Análisis de IA de este resultado:")
                    st.markdown(test.get("analisis_ia", "No hay análisis disponible."))
        else:
            st.info("Aún no has realizado ningún test. ¡Completa uno para ver tu historial!")
        st.markdown('</div>', unsafe_allow_html=True)

def chatbot_page():
    st.markdown('<p class="page-title">Asistente de IA</p>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        # ... (código del chatbot sin cambios)
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("Escribe tu pregunta aquí..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.spinner("Pensando..."):
                full_prompt = f"Como un asistente de salud experto en diabetes, responde la siguiente pregunta de forma clara y concisa en español: '{prompt}'"
                respuesta = gemini.llamar_gemini_directo(full_prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
            with st.chat_message("assistant"): st.markdown(respuesta)
        st.markdown('</div>', unsafe_allow_html=True)

def about_page():
    st.markdown('<p class="page-title">Acerca del Proyecto</p>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        # ... (código de "Acerca de" sin cambios)
        st.markdown(
            """
            **SaludIA: Predictor de Diabetes** es una aplicación diseñada para la prevención y concienciación sobre la Diabetes tipo 2.
            - **Versión:** 17.0 (Diseño Final)
            - **Autor:** Joseph Javier Sánchez Acuña
            - **Tecnologías:** Streamlit, Firebase, Google Gemini AI.
            *Este software es una herramienta de estimación y no reemplaza el diagnóstico de un profesional médico.*
            """
        )
        st.metric(label="Modelo de IA Activo", value=gemini.get_last_used_model())
        st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA DE LOGIN Y REGISTRO ---
def login_page():
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    st.markdown('<h1 class="sidebar-title" style="font-size: 3rem; margin-bottom: 1rem;">Bienvenido a SaludIA</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--subtle-text); font-size: 1.1rem;">Tu asistente inteligente para la prevención de la diabetes.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
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
                            st.rerun()
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
                                st.info("Ahora puedes iniciar sesión.")
                            else:
                                st.error(message)
                        else:
                            st.warning("Por favor, ingresa un correo y una contraseña.")
            st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN ---
load_css()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    # --- LAYOUT CON BARRA LATERAL ---
    with st.sidebar:
        st.markdown('<p class="sidebar-title">SaludIA</p>', unsafe_allow_html=True)
        
        # Menú de Navegación
        page_options = ["🏠 Nuevo Test", "📖 Historial", "🤖 Asistente IA", "ℹ️ Acerca de"]
        selected_page = st.radio("Navegación", page_options, label_visibility="collapsed")

        # Footer de la barra lateral con el botón de logout
        st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
        st.button("🚪 Cerrar Sesión", key="logout_sidebar", on_click=lambda: st.session_state.update({'logged_in': False, 'user_uid': None}), use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Contenido de la página seleccionada ---
    if selected_page == "🏠 Nuevo Test":
        new_test_page()
    elif selected_page == "📖 Historial":
        history_page()
    elif selected_page == "🤖 Asistente IA":
        chatbot_page()
    elif selected_page == "ℹ️ Acerca de":
        about_page()

else:
    login_page()

