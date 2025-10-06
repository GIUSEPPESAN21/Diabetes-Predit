# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v16.0 (Rediseño Total y Animaciones)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Esta es la versión definitiva con un rediseño completo de la interfaz.
Se introduce un nuevo "hero section" para el título, una paleta de colores
vibrante, y animaciones fluidas en todos los botones y elementos interactivos
para una experiencia de usuario de primer nivel.
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
            --bg-color: #F7F9FC;
            --text-color: #2D3748;
            --card-bg: white;
            --card-shadow: 0 10px 35px rgba(0, 0, 0, 0.05);
            --border-color: #E2E8F0;
            --primary-color: #3B82F6;
            --primary-hover: #2563EB;
            --primary-gradient: linear-gradient(90deg, #3B82F6, #1D4ED8);
            --logout-bg: #EF4444;
            --logout-hover-bg: #DC2626;
        }

        [data-theme="dark"] {
            --bg-color: #1A202C;
            --text-color: #E2E8F0;
            --card-bg: #2D3748;
            --card-shadow: 0 10px 35px rgba(0, 0, 0, 0.15);
            --border-color: #4A5568;
            --primary-color: #60A5FA;
            --primary-hover: #3B82F6;
            --primary-gradient: linear-gradient(90deg, #60A5FA, #2563EB);
            --logout-bg: #F87171;
            --logout-hover-bg: #EF4444;
        }

        html, body, [class*="st-"] {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
        }
        .stApp > header { background-color: transparent; }

        /* --- Hero Section para el Título --- */
        .hero-container {
            padding: 3rem 1rem;
            text-align: center;
            background: var(--card-bg);
            border-radius: 20px;
            margin-bottom: 2rem;
            box-shadow: var(--card-shadow);
            animation: slideIn 0.8s ease-out;
        }
        @keyframes slideIn { from { opacity: 0; transform: translateY(-30px); } to { opacity: 1; transform: translateY(0); } }

        .hero-title {
            font-size: 3.8rem;
            font-weight: 700;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: #718096;
            margin-top: -1rem;
        }
        [data-theme="dark"] .hero-subtitle { color: #A0AEC0; }

        /* --- Títulos de Sección --- */
        .section-header { text-align: center; font-weight: 600; font-size: 1.8rem; color: var(--text-color); padding-bottom: 0.5rem; margin: 2rem 0 1.5rem 0; }

        /* --- Contenedor Principal con Espaciado --- */
        .main-container {
            max-width: 1200px;
            margin: auto;
        }

        /* --- Pestañas Animadas --- */
        .stTabs {
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 2rem;
        }
        button[data-baseweb="tab"] {
            font-size: 1rem; font-weight: 600; border-radius: 8px 8px 0 0; margin: 0 5px;
            padding: 0.8rem 1.5rem; transition: all 0.3s ease;
            background-color: transparent; color: #718096; border: none;
        }
        button[data-baseweb="tab"]:hover {
            background-color: var(--primary-hover);
            color: white;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: var(--primary-gradient);
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }

        /* --- Botones con Animación "Cool" --- */
        .stButton>button {
            border-radius: 12px; border: none; font-weight: 600;
            padding: 14px 32px; transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .stButton>button:hover {
            transform: translateY(-4px) scale(1.03);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }
        .stButton>button:active {
            transform: translateY(-1px) scale(0.98);
        }
        
        /* Botón Primario */
        .stButton>button:not(.logout-button) {
             background: var(--primary-gradient);
             color: white;
        }
        /* Botón de Cerrar Sesión */
        .logout-button {
            background: var(--logout-bg) !important;
            color: white !important;
        }
        .logout-button:hover {
            background: var(--logout-hover-bg) !important;
        }

        /* --- Formularios --- */
        .stTextInput input, .stNumberInput input, .stSelectbox > div > div {
            border-radius: 10px; border: 2px solid var(--border-color);
            background-color: var(--bg-color); color: var(--text-color);
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
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

# --- PÁGINA PRINCIPAL (POST-LOGIN) ---
def main_app():
    # --- CABECERA ---
    with st.container():
        st.markdown('<div class="hero-container">', unsafe_allow_html=True)
        st.markdown('<p class="hero-title">SaludIA</p>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">Tu Predictor Inteligente de Riesgo de Diabetes</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 **Nuevo Test**",
        "📖 **Historial**",
        "🤖 **Asistente IA**",
        "ℹ️ **Acerca de**"
    ])

    with tab1:
        st.markdown('<h2 class="section-header">Cuestionario de Riesgo FINDRISC</h2>', unsafe_allow_html=True)
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

    with tab4:
        st.markdown('<h2 class="section-header">ℹ️ Acerca del Proyecto</h2>', unsafe_allow_html=True)
        st.markdown("""**SaludIA: Predictor de Diabetes**...""")
        st.metric(label="Modelo de IA Activo", value=gemini.get_last_used_model())
        
        # Botón de Cerrar Sesión ahora dentro de la última pestaña
        if st.button("🚪 Cerrar Sesión", key="logout_main", help="Haz clic para salir de tu cuenta"):
             st.session_state['logged_in'] = False
             st.session_state['user_uid'] = None
             st.rerun()

    with tab2:
        st.markdown('<h2 class="section-header">📖 Tu Historial de Tests</h2>', unsafe_allow_html=True)
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
            st.info("Aún no has realizado ningún test.")

    with tab3:
        st.markdown('<h2 class="section-header">🤖 Asistente de Diabetes con IA (Chatbot)</h2>', unsafe_allow_html=True)
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


# --- PÁGINA DE LOGIN Y REGISTRO ---
def login_page():
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown('<p class="hero-title">SaludIA</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Tu Predictor Inteligente de Riesgo de Diabetes</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
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


# --- LÓGICA PRINCIPAL ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)
load_css()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if st.session_state['logged_in']:
    main_app()
else:
    login_page()
st.markdown('</div>', unsafe_allow_html=True)

