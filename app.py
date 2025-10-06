# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v18.0 (Interfaz Definitiva)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final con un rediseño completo inspirado en plataformas clínicas
modernas. Se elimina la barra lateral en favor de una navegación superior
horizontal, se introduce una paleta de colores profesional y se refinan
todos los componentes con animaciones sutiles para una experiencia premium.
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
            --card-bg: #FFFFFF;
            --text-color: #334155;
            --title-color: #0F172A;
            --subtle-text: #64748B;
            --border-color: #E2E8F0;
            --primary-color: #4F46E5; /* Indigo */
            --primary-hover: #4338CA;
            --secondary-color: #EC4899; /* Pink */
            --card-shadow: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.05);
        }

        [data-theme="dark"] {
            --bg-color: #0F172A;
            --card-bg: #1E293B;
            --text-color: #CBD5E1;
            --title-color: #F8FAFC;
            --subtle-text: #94A3B8;
            --border-color: #334155;
            --primary-color: #818CF8;
            --primary-hover: #6366F1;
            --secondary-color: #F472B6;
        }

        /* --- Estructura General --- */
        html, body, [class*="st-"] {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-color);
        }
        .stApp > header { display: none; }
        .main .block-container { padding: 1rem 2rem; max-width: 1400px; }

        /* --- Tarjetas y Contenedores --- */
        .card {
            background: var(--card-bg);
            border-radius: 1.5rem;
            padding: 2.5rem;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.07), 0 10px 10px -5px rgba(0,0,0,0.04);
            transform: translateY(-5px);
        }

        /* --- Títulos y Encabezados --- */
        .page-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--title-color);
            margin-bottom: 0.5rem;
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 0.5rem;
            display: inline-block;
        }
        .app-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            margin-bottom: 1rem;
        }
        .app-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--title-color);
        }
        .app-title span {
            color: var(--primary-color);
        }

        /* --- Navegación Horizontal --- */
        .nav-container {
            display: flex;
            gap: 1rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 2rem;
        }
        .nav-button-container .stButton>button {
            background: transparent;
            color: var(--subtle-text);
            font-weight: 600;
            padding: 1rem 0.5rem;
            border-radius: 0;
            border-bottom: 3px solid transparent;
            transition: all 0.2s ease-in-out;
            box-shadow: none;
        }
        .nav-button-container .stButton>button:hover {
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
            transform: none;
            box-shadow: none;
        }
        .nav-button-container.active .stButton>button {
            color: var(--primary-color);
            border-bottom: 3px solid var(--primary-color);
        }

        /* --- Botones --- */
        .stButton>button {
            border-radius: 0.75rem;
            border: none;
            font-weight: 600;
            padding: 0.8rem 1.8rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px -5px rgba(0,0,0,0.1);
        }
        .stButton>button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 7px 20px -5px rgba(0,0,0,0.2);
        }
        
        /* Botones Primarios (Formularios) */
        div[data-testid="stForm"] .stButton>button {
            background-color: var(--primary-color);
            color: white;
        }
        div[data-testid="stForm"] .stButton>button:hover {
            background-color: var(--primary-hover);
        }
        
        /* Botón de Logout */
        .logout-button .stButton>button {
            background-color: #EF4444;
            color: white;
        }
        .logout-button .stButton>button:hover {
            background-color: #DC2626;
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

# --- Componentes de la Interfaz ---

def app_header(page_options, current_page):
    # Encabezado con título y botón de logout
    title_col, logout_col = st.columns([0.8, 0.2])
    with title_col:
        st.markdown('<div class="app-title">Salud<span>IA</span></div>', unsafe_allow_html=True)
    with logout_col:
        st.markdown('<div class="logout-button">', unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_uid'] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

    # Barra de navegación horizontal
    nav_cols = st.columns(len(page_options))
    for i, page in enumerate(page_options):
        with nav_cols[i]:
            active_class = "active" if page == current_page else ""
            st.markdown(f'<div class="nav-button-container {active_class}">', unsafe_allow_html=True)
            if st.button(page, use_container_width=True):
                st.session_state.page = page
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def new_test_page():
    st.markdown('<p class="page-header">Realizar Nuevo Test</p>', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)
    
    if "last_submission" in st.session_state and st.session_state.last_submission:
        display_results(st.session_state.last_submission)

    if submit_button:
        if altura > 0:
            imc = peso / (altura ** 2)
            puntaje = calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes)
            nivel_riesgo, estimacion = obtener_interpretacion_riesgo(puntaje)
            datos_usuario = {"fecha": datetime.now().isoformat(), "edad": edad, "sexo": sexo, "imc": imc, "cintura": cintura, "actividad": actividad, "frutas_verduras": frutas_verduras, "hipertension": hipertension, "glucosa_alta": glucosa_alta, "familiar_diabetes": familiar_diabetes, "puntaje": puntaje, "nivel_riesgo": nivel_riesgo, "estimacion": estimacion}
            with st.spinner("🤖 Analizando tus resultados con IA..."):
                analisis_ia = gemini.obtener_analisis_ia(datos_usuario)
                datos_usuario["analisis_ia"] = analisis_ia
            
            firebase.guardar_datos_test(st.session_state['user_uid'], datos_usuario)
            st.session_state.last_submission = datos_usuario
            st.rerun()
        else:
            st.error("La altura no puede ser cero.")

def display_results(datos):
    st.markdown("---")
    st.markdown('<p class="page-header">Resultados de tu Evaluación</p>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.plotly_chart(generar_grafico_riesgo(datos['puntaje']), use_container_width=True)
    with res_col2:
        st.metric("Puntaje FINDRISC", f"{datos['puntaje']} puntos")
        st.metric("Nivel de Riesgo", datos['nivel_riesgo'])
        st.info(f"**Estimación a 10 años:** {datos['estimacion']}")
        pdf_bytes = generar_pdf(datos)
        st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)
    
    st.markdown('<h3 style="font-weight: 600; margin-top: 2rem;">🧠 Análisis y Recomendaciones por IA</h3>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: var(--bg-color); padding: 1.5rem; border-radius: 10px;">{datos["analisis_ia"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def history_page():
    st.markdown('<p class="page-header">Historial de Tests</p>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    # ... (código del historial sin cambios)
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
        st.info("Aún no has realizado ningún test. ¡Completa uno para ver tu historial!")
    st.markdown('</div>', unsafe_allow_html=True)


def chatbot_page():
    st.markdown('<p class="page-header">Asistente de IA</p>', unsafe_allow_html=True)
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
    st.markdown('<p class="page-header">Acerca del Proyecto</p>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    # ... (código de "Acerca de" sin cambios)
    st.markdown(
        """
        **SaludIA: Predictor de Diabetes** es una aplicación diseñada para la prevención y concienciación sobre la Diabetes tipo 2.
        - **Versión:** 18.0 (Interfaz Definitiva)
        - **Autor:** Joseph Javier Sánchez Acuña
        - **Tecnologías:** Streamlit, Firebase, Google Gemini AI.
        *Este software es una herramienta de estimación y no reemplaza el diagnóstico de un profesional médico.*
        """
    )
    st.metric(label="Modelo de IA Activo", value=gemini.get_last_used_model())
    st.markdown('</div>', unsafe_allow_html=True)


def login_page():
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.markdown('<div style="text-align: center; margin-top: 5rem;">', unsafe_allow_html=True)
        st.markdown('<h1 class="app-title" style="font-size: 3rem;">Bienvenido a Salud<span>IA</span></h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--subtle-text); font-size: 1.1rem;">Tu asistente inteligente para la prevención.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card" style="margin-top: 2rem;">', unsafe_allow_html=True)
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
                        st.session_state['page'] = "🏠 Nuevo Test"
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
if 'page' not in st.session_state: st.session_state.page = "🏠 Nuevo Test"

if st.session_state['logged_in']:
    page_options = ["🏠 Nuevo Test", "📖 Historial", "🤖 Asistente IA", "ℹ️ Acerca de"]
    app_header(page_options, st.session_state.page)
    
    if st.session_state.page == "🏠 Nuevo Test":
        new_test_page()
    elif st.session_state.page == "📖 Historial":
        history_page()
    elif st.session_state.page == "🤖 Asistente IA":
        chatbot_page()
    elif st.session_state.page == "ℹ️ Acerca de":
        about_page()
else:
    login_page()

