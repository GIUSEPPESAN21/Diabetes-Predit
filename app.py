# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v7.0 (Versión Completa y Funcional)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final y estable que integra todas las funcionalidades solicitadas,
basada en la arquitectura del software BIOETHICARE 360.
- Autenticación de cliente con Pyrebase (corrige el guardado de datos).
- Análisis de riesgo detallado con Gemini AI.
- Generación de reportes profesionales en PDF con gráficos.
- Chatbot interactivo con preguntas preestablecidas.
- Visualización de riesgo con un gráfico de velocímetro (gauge chart).
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

# --- CONFIGURACIÓN DE SERVICIOS ---

# 1. SDK de Administrador (para acceder a la base de datos)
try:
    firebase_secrets_dict = dict(st.secrets["firebase_credentials"])
    firebase_secrets_dict["private_key"] = firebase_secrets_dict["private_key"].replace('\\n', '\n')
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_secrets_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Error crítico al inicializar Firebase Admin: {e}. Revisa tus secretos.")
    st.stop()

# 2. SDK de Cliente con Pyrebase (para registrar y loguear usuarios)
try:
    firebase_client_config = dict(st.secrets["firebase_client_config"])
    firebase = pyrebase.initialize_app(firebase_client_config)
    auth_client = firebase.auth()
except Exception as e:
    st.error(f"Error crítico al inicializar la autenticación de Firebase: {e}. Revisa la sección [firebase_client_config] en tus secretos.")
    st.stop()

# --- CLASES Y FUNCIONES ---
# Asegúrate de añadir tu clave de API de Gemini a los secretos de Streamlit
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "TU_API_KEY_DE_GEMINI")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

def generar_pdf(datos_reporte, grafico_path):
    pdf = PDF()
    pdf.add_page()
    
    # Datos del Paciente
    pdf.chapter_title('1. Datos del Paciente')
    fecha_reporte = datetime.now().strftime('%d/%m/%Y')
    info_paciente = (f"Fecha del reporte: {fecha_reporte}\n"
                     f"Edad: {datos_reporte['edad']} años\n"
                     f"Sexo: {datos_reporte['sexo']}\n"
                     f"IMC (Índice de Masa Corporal): {datos_reporte['imc']:.2f}\n"
                     f"Perímetro de cintura: {datos_reporte['cintura']} cm")
    pdf.chapter_body(info_paciente)

    # Resultados del Test
    pdf.chapter_title('2. Resultados del Cuestionario FINDRISC')
    resultados = (f"Puntaje Total: {datos_reporte['puntaje']} puntos\n"
                  f"Nivel de Riesgo: {datos_reporte['nivel_riesgo']}\n"
                  f"Estimación a 10 años: {datos_reporte['estimacion']}")
    pdf.chapter_body(resultados)
    
    # Gráfico de Riesgo
    if grafico_path and os.path.exists(grafico_path):
        pdf.image(grafico_path, x=pdf.get_x(), y=pdf.get_y(), w=180)
        pdf.ln(85) # Espacio después del gráfico

    # Análisis de IA
    pdf.chapter_title('3. Análisis y Recomendaciones por IA (Gemini)')
    analisis_ia_encoded = datos_reporte['analisis_ia'].encode('latin-1', 'replace').decode('latin-1')
    pdf.chapter_body(analisis_ia_encoded)

    # Información del autor
    pdf.set_y(-40)
    pdf.set_font('Arial', 'I', 9)
    autor_info = ("Software desarrollado por:\n"
                  "Joseph Javier Sánchez Acuña: Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.\n"
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
    elif 7 <= score <= 11: return "Riesgo ligeramente elevado", "1 de cada 25 personas desarrollará diabetes."
    elif 12 <= score <= 14: return "Riesgo moderado", "1 de cada 6 personas desarrollará diabetes."
    elif 15 <= score <= 20: return "Riesgo alto", "1 de cada 3 personas desarrollará diabetes."
    else: return "Riesgo muy alto", "1 de cada 2 personas desarrollará diabetes."

def llamar_gemini(prompt):
    if GEMINI_API_KEY == "TU_API_KEY_DE_GEMINI":
        return "Error: La clave de API de Gemini no está configurada en los secretos de Streamlit."
    
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Error de conexión con la API de Gemini: {e}"
    except (KeyError, IndexError) as e:
        return f"Respuesta inesperada de la API de Gemini. Detalles: {response.text}"

def obtener_analisis_ia(datos_usuario):
    prompt = f"""
    Eres un asistente de salud virtual especializado en la prevención de la diabetes.
    Un usuario ha completado el cuestionario de riesgo de diabetes FINDRISC y ha obtenido los siguientes resultados:
    - Edad: {datos_usuario['edad']} años
    - Sexo: {datos_usuario['sexo']}
    - IMC: {datos_usuario['imc']:.2f}
    - Perímetro de cintura: {datos_usuario['cintura']} cm
    - Realiza 30 min de actividad física diaria: {datos_usuario['actividad']}
    - Come frutas y verduras todos los días: {datos_usuario['frutas_verduras']}
    - Toma medicación para la hipertensión: {datos_usuario['hipertension']}
    - Ha tenido niveles de glucosa altos alguna vez: {datos_usuario['glucosa_alta']}
    - Tiene familiares con diabetes: {datos_usuario['familiar_diabetes']}
    - **Puntaje FINDRISC Total:** {datos_usuario['puntaje']}
    - **Nivel de riesgo:** {datos_usuario['nivel_riesgo']}

    Basado en esta información, proporciona un análisis detallado y recomendaciones personalizadas en español.
    Tu respuesta debe ser empática, clara y motivadora. Estructura tu respuesta de la siguiente manera:

    1.  **Análisis de tu Resultado:** Explica brevemente qué significa el puntaje y el nivel de riesgo en el contexto de los datos proporcionados. Identifica los 2 o 3 factores de riesgo que más contribuyeron a su puntaje.
    2.  **Recomendaciones Clave:** Ofrece de 3 a 5 recomendaciones prácticas y accionables para reducir su riesgo. Las recomendaciones deben ser específicas para los factores de riesgo identificados (ej. si el IMC es alto, da consejos sobre dieta y ejercicio).
    3.  **Próximos Pasos:** Aconseja al usuario que consulte a un profesional de la salud para una evaluación completa. Menciona la importancia de no autodiagnosticarse.
    """
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
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "<b>Nivel de Riesgo de Diabetes</b>"},
        gauge = {
            'axis': {'range': [0, 25], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "rgba(0,0,0,0.4)"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#cccccc",
            'steps': [
                {'range': [0, 6], 'color': 'green'},
                {'range': [7, 11], 'color': 'lightgreen'},
                {'range': [12, 14], 'color': 'yellow'},
                {'range': [15, 20], 'color': 'orange'},
                {'range': [21, 25], 'color': 'red'}],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.85,
                'value': score}
        }))
    fig.update_layout(paper_bgcolor = "rgba(0,0,0,0)", font = {'color': "#333333", 'family': "Arial"})
    return fig

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide")

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🩺 Predictor de Diabetes con IA")
    login_tab, register_tab = st.tabs(["Iniciar Sesión", "Registrar Nuevo Usuario"])
    with login_tab:
        st.subheader("Iniciar Sesión")
        with st.form("login_form"):
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            login_button = st.form_submit_button("Entrar")
            if login_button:
                try:
                    user = auth_client.sign_in_with_email_and_password(email, password)
                    st.session_state.user = user
                    st.rerun()
                except Exception as e:
                    st.error("Error: Email o contraseña incorrectos.")
    with register_tab:
        st.subheader("Crear una Cuenta Nueva")
        with st.form("register_form"):
            name = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico para registrar")
            password = st.text_input("Crea una Contraseña", type="password")
            if st.form_submit_button("Registrarse"):
                if not name or not email or not password:
                    st.warning("Por favor, completa todos los campos.")
                else:
                    try:
                        user = auth_client.create_user_with_email_and_password(email, password)
                        st.success(f"¡Cuenta creada con éxito para {email}!")
                        st.info("Ahora puedes ir a la pestaña 'Iniciar Sesión' para entrar.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error al crear la cuenta. Es posible que el correo ya esté en uso o la contraseña sea muy débil.")
else:
    user_email = st.session_state.user.get('email', 'Usuario')
    user_uid = st.session_state.user.get('localId')
    
    st.sidebar.title(f"Bienvenido, *{user_email}*")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    opcion = st.sidebar.radio("Selecciona una opción", ["Realizar nuevo test", "Consultar historial", "Chatbot de Diabetes"])
    st.sidebar.markdown("---")
    st.sidebar.subheader("Autor")
    st.sidebar.info("Joseph Javier Sánchez Acuña\n\n*Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*\n\n**Contacto:** joseph.sanchez@uniminuto.edu.co")

    if opcion == "Realizar nuevo test":
        st.title("🩺 Realizar Nuevo Test de Riesgo")
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
            submit_button = st.form_submit_button("Calcular Riesgo y Generar Reporte")
        
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
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                grafico.write_image(tmpfile.name, format="png", scale=2)
                tmpfile_path = tmpfile.name

            pdf_bytes = generar_pdf(datos_usuario, tmpfile_path)
            st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            os.unlink(tmpfile_path)

    elif opcion == "Consultar historial":
        st.title("📖 Tu Historial de Resultados")
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
            st.warning("Aún no tienes resultados guardados.")

    elif opcion == "Chatbot de Diabetes":
        st.title("🤖 Chatbot Informativo sobre Diabetes")
        st.markdown("Hazme una pregunta o selecciona una de las sugerencias.")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        preguntas_sugeridas = [
            "¿Cuáles son los primeros síntomas de la diabetes?",
            "¿Qué alimentos debe evitar una persona con prediabetes?",
            "¿Cómo afecta el ejercicio al nivel de azúcar en la sangre?",
            "Explícame la diferencia entre diabetes tipo 1 y tipo 2.",
            "¿Qué es la resistencia a la insulina?",
            "¿Es reversible la prediabetes?"
        ]
        
        def handle_q_click(q):
            st.session_state.last_question = q
        
        q_cols = st.columns(2)
        for i, q in enumerate(preguntas_sugeridas):
            q_cols[i % 2].button(q, on_click=handle_q_click, args=(q,), use_container_width=True, key=f"q_{i}")

        if prompt := st.chat_input("Escribe tu pregunta aquí...") or st.session_state.get('last_question'):
            st.session_state.last_question = ""
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("Pensando..."):
                full_prompt = f"Eres un asistente de salud experto en diabetes. Responde la siguiente pregunta de forma clara, concisa y en español: '{prompt}'"
                respuesta = llamar_gemini(full_prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
            st.rerun()

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
