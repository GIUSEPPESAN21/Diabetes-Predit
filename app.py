# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v2.0
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Esta aplicación ha sido mejorada para incluir un sistema de autenticación de usuarios,
generación de reportes en PDF, un chatbot informativo sobre diabetes y un cálculo
de riesgo más preciso basado en el género. Utiliza Streamlit, Firebase (Authentication y Firestore)
y la IA de Gemini.

Instrucciones para ejecutar:
1.  Asegúrate de tener Python instalado.
2.  Instala las bibliotecas necesarias:
    pip install streamlit firebase-admin requests fpdf

3.  Configura Firebase:
    - Sigue los pasos para crear tu proyecto y obtener tu 'firebase_credentials.json'.
    - En la Consola de Firebase, ve a la sección "Authentication" (Compilación -> Authentication).
    - Haz clic en "Comenzar" y en la pestaña "Sign-in method", habilita el proveedor "Correo electrónico/Contraseña".

4.  Configura la API de Gemini:
    - Obtén tu clave de API desde Google AI Studio (https://aistudio.google.com/app/apikey).
    - Reemplaza el valor de la variable `GEMINI_API_KEY` con tu clave.

5.  Ejecuta la aplicación desde tu terminal:
    streamlit run nombre_de_este_archivo.py
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
import json
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURACIÓN DE SERVICIOS ---

# Configuración de la API de Gemini
# IMPORTANTE: Reemplaza "TU_API_KEY_DE_GEMINI" con tu clave de API real.
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# Configuración de Firebase
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Error al inicializar Firebase: {e}")
    st.warning("La funcionalidad de base de datos estará deshabilitada. "
               "Asegúrate de que tu archivo 'firebase_credentials.json' esté configurado correctamente.")
    db = None

# --- CLASE PARA GENERAR PDF ---
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
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def generar_pdf(datos_reporte):
    """Crea un archivo PDF con los resultados del test y el análisis de IA."""
    pdf = PDF()
    pdf.add_page()

    # Información del paciente
    pdf.chapter_title('Datos del Paciente')
    fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    info_paciente = (
        f"Fecha del reporte: {fecha_reporte}\n"
        f"Edad: {datos_reporte['edad']} años\n"
        f"Sexo: {datos_reporte['sexo']}\n"
        f"IMC: {datos_reporte['imc']:.2f}\n"
        f"Perímetro de cintura: {datos_reporte['cintura']} cm"
    )
    pdf.chapter_body(info_paciente)

    # Resultados del test
    pdf.chapter_title('Resultados del Cuestionario FINDRISC')
    resultados = (
        f"Puntaje Total: {datos_reporte['puntaje']} puntos\n"
        f"Nivel de Riesgo: {datos_reporte['nivel_riesgo']}\n"
        f"Estimación a 10 años: {datos_reporte['estimacion']}"
    )
    pdf.chapter_body(resultados)

    # Análisis de IA
    pdf.chapter_title('Análisis y Recomendaciones por IA')
    # Usamos 'latin-1' para manejar caracteres especiales en el PDF
    analisis_ia_encoded = datos_reporte['analisis_ia'].encode('latin-1', 'replace').decode('latin-1')
    pdf.chapter_body(analisis_ia_encoded)

    # Información del autor
    pdf.set_y(-40)
    pdf.set_font('Arial', 'I', 9)
    autor_info = (
        "Software desarrollado por:\n"
        "Joseph Javier Sánchez Acuña: Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.\n"
        "Contacto: joseph.sanchez@uniminuto.edu.co"
    )
    pdf.multi_cell(0, 5, autor_info, 0, 'C')

    return pdf.output(dest='S').encode('latin-1')


# --- FUNCIONES PRINCIPALES DE LA APP ---

def calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes):
    """Calcula el puntaje FINDRISC (versión mejorada con distinción de género)."""
    score = 0
    # 1. Edad
    if 45 <= edad <= 54: score += 2
    elif 55 <= edad <= 64: score += 3
    elif edad > 64: score += 4

    # 2. IMC
    if 25 <= imc < 30: score += 1
    elif imc >= 30: score += 3

    # 3. Perímetro de cintura (más preciso)
    if sexo == "Masculino":
        if 94 <= cintura <= 102: score += 3
        elif cintura > 102: score += 4
    elif sexo == "Femenino":
        if 80 <= cintura <= 88: score += 3
        elif cintura > 88: score += 4

    # 4. Actividad física
    if actividad == "No": score += 2

    # 5. Consumo de frutas y verduras
    if frutas_verduras == "No todos los días": score += 1

    # 6. Hipertensión
    if hipertension == "Sí": score += 2

    # 7. Glucosa alta
    if glucosa_alta == "Sí": score += 5

    # 8. Familiares con diabetes
    if familiar_diabetes == "Sí: padres, hermanos o hijos": score += 5
    elif familiar_diabetes == "Sí: abuelos, tíos o primos hermanos": score += 3
        
    return score

def obtener_interpretacion_riesgo(score):
    """Devuelve el nivel de riesgo y una estimación basada en el puntaje."""
    if score < 7: return "Riesgo bajo", "1 de cada 100 personas desarrollará diabetes."
    elif 7 <= score <= 11: return "Riesgo ligeramente elevado", "1 de cada 25 personas desarrollará diabetes."
    elif 12 <= score <= 14: return "Riesgo moderado", "1 de cada 6 personas desarrollará diabetes."
    elif 15 <= score <= 20: return "Riesgo alto", "1 de cada 3 personas desarrollará diabetes."
    else: return "Riesgo muy alto", "1 de cada 2 personas desarrollará diabetes."

def obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion):
    """Llama a la API de Gemini para obtener un análisis y recomendaciones."""
    if GEMINI_API_KEY == "TU_API_KEY_DE_GEMINI":
        return "API Key de Gemini no configurada. El análisis por IA está desactivado."

    prompt = f"""
    Eres un asistente de salud virtual especializado en la prevención de la diabetes.
    Un usuario ha completado el cuestionario FINDRISC y ha obtenido los siguientes resultados:
    Datos del usuario: {datos_usuario}
    Resultados: Puntaje={puntaje}, Nivel de riesgo={nivel_riesgo}, Estimación={estimacion}.
    Proporciona un análisis detallado, empático y motivador en español, estructurado en:
    1. **Análisis de tu resultado:** Explica qué significa el puntaje y los factores de riesgo clave.
    2. **Recomendaciones Clave:** Ofrece 3-5 consejos prácticos y personalizados.
    3. **Próximos Pasos:** Aconseja consultar a un profesional de la salud.
    """
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error al contactar la IA de Gemini: {e}"

def guardar_datos_en_firestore(user_id, datos):
    """Guarda los datos de un test en Firestore."""
    if not db: return
    try:
        doc_ref = db.collection('usuarios').document(user_id).collection('tests').document()
        doc_ref.set(datos)
        st.success("¡Resultados guardados con éxito en tu historial!")
    except Exception as e:
        st.error(f"Ocurrió un error al guardar los datos: {e}")

def cargar_datos_de_firestore(user_id):
    """Carga el historial de tests de un usuario desde Firestore."""
    if not db: return []
    try:
        tests_ref = db.collection('usuarios').document(user_id).collection('tests').order_by("fecha", direction=firestore.Query.DESCENDING)
        docs = tests_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"Ocurrió un error al cargar los datos: {e}")
        return []

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide", initial_sidebar_state="expanded")

# --- GESTIÓN DE ESTADO DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'page' not in st.session_state:
    st.session_state.page = "login"

# --- PANTALLAS DE LOGIN Y REGISTRO ---
if not st.session_state.logged_in:
    st.title("Bienvenido al Software Predictivo de Diabetes")
    
    choice = st.selectbox("Selecciona una acción", ["Iniciar Sesión", "Registrarse"])

    if choice == "Iniciar Sesión":
        st.subheader("Iniciar Sesión")
        with st.form("login_form"):
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            login_button = st.form_submit_button("Iniciar Sesión")
            if login_button:
                try:
                    user = auth.get_user_by_email(email)
                    # NOTA: Firebase Admin SDK no verifica contraseñas.
                    # La verificación real se haría en el lado del cliente con Firebase JS SDK.
                    # Aquí asumimos que si el email existe, el login es "exitoso" para este ejemplo.
                    st.session_state.logged_in = True
                    st.session_state.user_info = {'uid': user.uid, 'email': user.email}
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al iniciar sesión: Email o contraseña incorrectos.")

    elif choice == "Registrarse":
        st.subheader("Crear una Cuenta")
        with st.form("register_form"):
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            register_button = st.form_submit_button("Registrarse")
            if register_button:
                try:
                    user = auth.create_user(email=email, password=password)
                    st.success("¡Cuenta creada con éxito! Ahora puedes iniciar sesión.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error al registrarse: {e}")
else:
    # --- APLICACIÓN PRINCIPAL (SI EL USUARIO ESTÁ LOGUEADO) ---
    st.sidebar.title("Navegación")
    st.sidebar.write(f"Bienvenido, **{st.session_state.user_info['email']}**")
    
    opcion = st.sidebar.radio("Selecciona una opción", ["Realizar nuevo test", "Consultar historial", "Chatbot de Diabetes"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Autor")
    st.sidebar.info(
        """
        **Joseph Javier Sánchez Acuña**
        *Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*
        **Contacto:** joseph.sanchez@uniminuto.edu.co
        """
    )

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

    # --- PÁGINA: REALIZAR NUEVO TEST ---
    if opcion == "Realizar nuevo test":
        st.title("🩺 Software Predictivo de Diabetes con IA")
        st.markdown("Responde a las siguientes preguntas para estimar tu riesgo de desarrollar Diabetes tipo 2.")

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
            
            datos_usuario = {
                "fecha": datetime.now().isoformat(), "edad": edad, "sexo": sexo, "imc": imc, "cintura": cintura,
                "actividad": actividad, "frutas_verduras": frutas_verduras, "hipertension": hipertension,
                "glucosa_alta": glucosa_alta, "familiar_diabetes": familiar_diabetes, "puntaje": puntaje,
                "nivel_riesgo": nivel_riesgo, "estimacion": estimacion
            }

            with st.spinner("🤖 Analizando tus resultados con IA..."):
                analisis_ia = obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion)
                datos_usuario["analisis_ia"] = analisis_ia
            
            st.subheader("Resultados de tu Evaluación")
            st.metric("Puntaje FINDRISC", f"{puntaje} puntos", f"{nivel_riesgo}")
            st.info(f"**Estimación a 10 años:** {estimacion}")
            st.markdown("---")
            st.subheader("🧠 Análisis y Recomendaciones por IA")
            st.markdown(analisis_ia)

            guardar_datos_en_firestore(st.session_state.user_info['uid'], datos_usuario)
            
            # Generar y ofrecer descarga del PDF
            pdf_bytes = generar_pdf(datos_usuario)
            st.download_button(
                label="📥 Descargar Reporte en PDF",
                data=pdf_bytes,
                file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/octet-stream"
            )

    # --- PÁGINA: CONSULTAR HISTORIAL ---
    elif opcion == "Consultar historial":
        st.title("📖 Tu Historial de Resultados")
        historial = cargar_datos_de_firestore(st.session_state.user_info['uid'])
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
            st.warning("Aún no tienes resultados guardados. Realiza un nuevo test para empezar.")

    # --- PÁGINA: CHATBOT ---
    elif opcion == "Chatbot de Diabetes":
        st.title("🤖 Chatbot Informativo sobre Diabetes")
        st.markdown("Hazme una pregunta sobre la diabetes, sus síntomas, prevención o tratamiento.")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Escribe tu pregunta aquí..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    chat_prompt = f"Eres un chatbot asistente de salud. Responde la siguiente pregunta sobre diabetes de forma clara, concisa y en español: '{prompt}'"
                    headers = {"Content-Type": "application/json"}
                    payload = {"contents": [{"parts": [{"text": chat_prompt}]}]}
                    try:
                        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
                        response.raise_for_status()
                        result = response.json()
                        respuesta_ia = result['candidates'][0]['content']['parts'][0]['text']
                        st.markdown(respuesta_ia)
                        st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                    except Exception as e:
                        st.error("Lo siento, no pude procesar tu pregunta en este momento.")
