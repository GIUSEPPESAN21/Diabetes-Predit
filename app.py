# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v15.0 (Interfaz Centrada y Clara)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Esta versión refina por completo la interfaz de usuario, centrando los títulos,
mejorando drásticamente la legibilidad de los botones y pestañas con un nuevo
diseño de alto contraste, y reorganizando la cabecera para una experiencia
más limpia, profesional y equilibrada.
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

# --- INYECCIÓN DE CSS PARA ESTILOS PREMIUM Y ADAPTABLES (CLARO/OSCURO) ---
def load_css():
    st.markdown("""
    <style>
        /* --- Variables de Tema (Claro y Oscuro) --- */
        :root {
            --bg-color: #F0F4F8;
            --text-color: #111827;
            --card-bg: white;
            --card-shadow: 0 8px 30px rgba(0,0,0,0.05);
            --border-color: #E0E0E0;
            --primary-grad-start: #004AAD;
            --primary-grad-end: #0089BA;
            --tab-text-color: #4A5568;
            --logout-bg: #DC2626; /* Rojo Fuerte */
            --logout-hover-bg: #B91C1C; /* Rojo más oscuro */
        }

        [data-theme="dark"] {
            --bg-color: #0E1117;
            --text-color: #FAFAFA;
            --card-bg: #1F2937;
            --card-shadow: 0 8px 30px rgba(0,0,0,0.2);
            --border-color: #374151;
            --primary-grad-start: #0089BA;
            --primary-grad-end: #00DFFF;
            --tab-text-color: #9CA3AF;
            --logout-bg: #EF4444;
            --logout-hover-bg: #DC2626;
        }

        /* --- Estilos Generales --- */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        html, body, [class*="st-"] {
            font-family: 'Roboto', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
        }
        .stApp > header { background-color: transparent; }

        /* --- Cabecera y Títulos (MEJORADOS) --- */
        .main-header-container { text-align: center; margin-bottom: 2rem; }
        .main-title {
            font-size: 3.5rem; font-weight: 700;
            background: -webkit-linear-gradient(45deg, var(--primary-grad-start), var(--primary-grad-end));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: fadeIn 1s ease-in-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        .subtitle { color: #556270; }
        [data-theme="dark"] .subtitle { color: #9CA3AF; }

        /* --- Títulos de Sección Centrados --- */
        .section-header {
            text-align: center;
            font-weight: 700;
            color: var(--text-color);
            padding-bottom: 0.5rem;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid var(--primary-grad-end);
        }

        /* --- Tarjetas y Contenedores --- */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            border: 1px solid var(--border-color); border-radius: 20px; padding: 2rem;
            background-color: var(--card-bg); box-shadow: var(--card-shadow);
        }

        /* --- Pestañas de Navegación (Legibilidad Mejorada) --- */
        button[data-baseweb="tab"] {
            font-size: 1rem; font-weight: 700; border-radius: 10px; margin: 0 5px;
            transition: all 0.3s ease; padding: 0.75rem 1.2rem; white-space: nowrap;
            background-color: transparent;
        }
        button[data-baseweb="tab"] > div { color: var(--tab-text-color); }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-image: linear-gradient(45deg, var(--primary-grad-start), var(--primary-grad-end));
            box-shadow: 0 4px 15px rgba(0, 137, 186, 0.3);
            text-shadow: 0 1px 2px rgba(0,0,0,0.2); /* Sombra para resaltar texto */
        }
        button[data-baseweb="tab"][aria-selected="true"] > div { color: white !important; }

        /* --- Botón de Cerrar Sesión (Alto Contraste) --- */
        .logout-button-container { display: flex; justify-content: flex-end; align-items: center; }
        .logout-button-container .stButton>button {
            background-image: none;
            background-color: var(--logout-bg);
            color: white !important; /* Texto siempre blanco */
            border: none;
            font-weight: 700;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2); /* Sombra para resaltar texto */
        }
        .logout-button-container .stButton>button:hover { background-color: var(--logout-hover-bg); }
        
        /* --- Botones Primarios --- */
        .stButton>button {
            border-radius: 10px; border: none; background-image: linear-gradient(45deg, var(--primary-grad-start), var(--primary-grad-end));
            color: white; padding: 12px 30px; font-weight: 700; transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 137, 186, 0.2);
        }
        .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0, 137, 186, 0.3); }

        /* --- Formularios y Entradas --- */
        .stTextInput input, .stNumberInput input, .stSelectbox > div > div {
            border-radius: 10px; border: 1px solid var(--border-color);
            background-color: var(--bg-color); color: var(--text-color);
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: var(--primary-grad-end);
            box-shadow: 0 0 0 2px rgba(0, 137, 186, 0.2);
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
    # --- CABECERA REESTRUCTURADA ---
    main_header_cols = st.columns([0.2, 0.6, 0.2])
    with main_header_cols[1]:
        st.markdown('<div class="main-header-container">', unsafe_allow_html=True)
        st.markdown('<p class="main-title">SaludIA - Predictor de Diabetes</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Tu asistente inteligente para la prevención de la Diabetes</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with main_header_cols[2]:
        st.markdown('<div class="logout-button-container">', unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['logged_in'] = False
            st.session_state['user_uid'] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 **Realizar Nuevo Test**",
        "📖 **Consultar Historial**",
        "🤖 **Asistente de IA**",
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
            st.info("Aún no has realizado ningún test. ¡Completa uno en la pestaña 'Realizar Nuevo Test'!")

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
    
    with tab4:
        st.markdown('<h2 class="section-header">ℹ️ Acerca del Proyecto</h2>', unsafe_allow_html=True)
        st.markdown(
            """
            **SaludIA: Predictor de Diabetes** es una aplicación diseñada para la prevención y concienciación sobre la Diabetes tipo 2.
            - **Versión:** 15.0 (Interfaz Centrada)
            - **Autor:** Joseph Javier Sánchez Acuña
            - **Tecnologías:** Streamlit, Firebase, Google Gemini AI.
            *Este software es una herramienta de estimación y no reemplaza el diagnóstico de un profesional médico.*
            """
        )
        st.metric(label="Modelo de IA Activo", value=gemini.get_last_used_model())


# --- PÁGINA DE LOGIN Y REGISTRO ---
def login_page():
    st.markdown('<p class="main-title">SaludIA - Predictor de Diabetes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Tu asistente personal para la prevención de la diabetes. Inicia sesión o regístrate para comenzar.</p>', unsafe_allow_html=True)

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
load_css()
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if st.session_state['logged_in']:
    main_app()
else:
    with st.container(): login_page()

