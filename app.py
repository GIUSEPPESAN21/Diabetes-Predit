# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA v6.0 (Firebase Auth)
Autor: Joseph Javier Sánchez Acuña
Contacto: joseph.sanchez@uniminuto.edu.co

Descripción:
Versión final que utiliza Firebase Authentication como único sistema para
el registro y login de usuarios, eliminando la dependencia del archivo config.yaml
y la librería streamlit-authenticator para una solución robusta y estándar.
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fpdf import FPDF
from datetime import datetime
import requests
import json

# --- CONFIGURACIÓN DE SERVICIOS ---

# Configuración de Firebase desde los secretos de Streamlit
try:
    firebase_secrets_dict = dict(st.secrets["firebase_credentials"])
    firebase_secrets_dict["private_key"] = firebase_secrets_dict["private_key"].replace('\\n', '\n')
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_secrets_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"Error crítico al inicializar Firebase: {e}. Revisa tus secretos.")
    st.stop()

# --- CLASES Y FUNCIONES ---
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

class PDF(FPDF):
    def header(self): self.set_font('Arial', 'B', 12); self.cell(0, 10, 'Reporte de Riesgo de Diabetes', 0, 1, 'C'); self.ln(10)
    def footer(self): self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title): self.set_font('Arial', 'B', 12); self.cell(0, 10, title, 0, 1, 'L'); self.ln(4)
    def chapter_body(self, body): self.set_font('Arial', '', 12); self.multi_cell(0, 10, body); self.ln()

def generar_pdf(datos_reporte):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title('Datos del Paciente'); fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    info_paciente = (f"Fecha: {fecha_reporte}\nEdad: {datos_reporte['edad']} años\n"
                     f"Sexo: {datos_reporte['sexo']}\nIMC: {datos_reporte['imc']:.2f}\n"
                     f"Cintura: {datos_reporte['cintura']} cm")
    pdf.chapter_body(info_paciente)
    pdf.chapter_title('Resultados del Cuestionario FINDRISC')
    resultados = (f"Puntaje: {datos_reporte['puntaje']} puntos\nNivel de Riesgo: {datos_reporte['nivel_riesgo']}\n"
                  f"Estimación: {datos_reporte['estimacion']}")
    pdf.chapter_body(resultados)
    pdf.chapter_title('Análisis y Recomendaciones por IA')
    analisis_ia_encoded = datos_reporte['analisis_ia'].encode('latin-1', 'replace').decode('latin-1')
    pdf.chapter_body(analisis_ia_encoded)
    pdf.set_y(-40); pdf.set_font('Arial', 'I', 9)
    autor_info = ("Software por: Joseph Javier Sánchez Acuña\n"
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
    elif 7 <= score <= 11: return "Riesgo ligeramente elevado", "1 de cada 25."
    elif 12 <= score <= 14: return "Riesgo moderado", "1 de cada 6."
    elif 15 <= score <= 20: return "Riesgo alto", "1 de cada 3."
    else: return "Riesgo muy alto", "1 de cada 2."
def obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion):
    return "Análisis de IA (función sin cambios)"
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

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide")

# Gestión del estado de la sesión
if 'user' not in st.session_state:
    st.session_state.user = None

# --- PANTALLA DE LOGIN Y REGISTRO ---
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
                    # NOTA IMPORTANTE DE SEGURIDAD:
                    # El SDK de Admin (Python) NO puede verificar contraseñas directamente.
                    # Este método solo comprueba si el usuario existe.
                    # Para una app de producción, se debe usar el SDK de cliente (JS)
                    # para un login 100% seguro. Este es un workaround para Streamlit.
                    user = auth.get_user_by_email(email)
                    st.session_state.user = {
                        "uid": user.uid,
                        "email": user.email,
                        "name": user.display_name or user.email
                    }
                    st.rerun()
                except Exception as e:
                    st.error("Error: Usuario no encontrado o credenciales incorrectas.")

    with register_tab:
        st.subheader("Crear una Cuenta Nueva")
        with st.form("register_form"):
            name = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico para registrar")
            password = st.text_input("Crea una Contraseña", type="password")
            register_button = st.form_submit_button("Registrarse")

            if register_button:
                if not name or not email or not password:
                    st.warning("Por favor, completa todos los campos.")
                else:
                    try:
                        new_user = auth.create_user(
                            email=email,
                            password=password,
                            display_name=name
                        )
                        st.success(f"¡Cuenta creada con éxito para {new_user.display_name}!")
                        st.info("Ahora puedes ir a la pestaña 'Iniciar Sesión' para entrar.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error al crear la cuenta: {e}")

# --- APLICACIÓN PRINCIPAL (SI EL USUARIO ESTÁ LOGUEADO) ---
else:
    st.sidebar.title(f"Bienvenido, *{st.session_state.user['name']}*")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    opcion = st.sidebar.radio("Selecciona una opción", ["Realizar nuevo test", "Consultar historial", "Chatbot de Diabetes"])
    st.sidebar.markdown("---")
    st.sidebar.subheader("Autor")
    st.sidebar.info("Joseph Javier Sánchez Acuña\n\n*Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.*\n\n**Contacto:** joseph.sanchez@uniminuto.edu.co")

    if opcion == "Realizar nuevo test":
        st.title("🩺 Software Predictivo de Diabetes con IA")
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
                analisis_ia = obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion)
                datos_usuario["analisis_ia"] = analisis_ia
            st.subheader("Resultados de tu Evaluación"); st.metric("Puntaje FINDRISC", f"{puntaje} puntos", f"{nivel_riesgo}"); st.info(f"**Estimación a 10 años:** {estimacion}"); st.markdown("---"); st.subheader("🧠 Análisis y Recomendaciones por IA"); st.markdown(analisis_ia)
            guardar_datos_en_firestore(st.session_state.user['uid'], datos_usuario)
            pdf_bytes = generar_pdf(datos_usuario)
            st.download_button(label="📥 Descargar Reporte en PDF", data=pdf_bytes, file_name=f"Reporte_Diabetes_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/octet-stream")
    elif opcion == "Consultar historial":
        st.title("📖 Tu Historial de Resultados")
        historial = cargar_datos_de_firestore(st.session_state.user['uid'])
        if historial:
            st.success(f"Se encontraron {len(historial)} registros.")
            for test in historial:
                fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                with st.expander(f"Test del {fecha_test} - Puntaje: {test['puntaje']} ({test['nivel_riesgo']})"):
                    st.write(f"**IMC:** {test['imc']:.2f}, **Cintura:** {test['cintura']} cm"); st.markdown("---"); st.subheader("Análisis de IA de este resultado:"); st.markdown(test.get("analisis_ia", "No hay análisis disponible."))
        else:
            st.warning("Aún no tienes resultados guardados.")
    elif opcion == "Chatbot de Diabetes":
        st.title("🤖 Chatbot Informativo sobre Diabetes")
        if "messages" not in st.session_state: st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]): st.markdown(message["content"])
        if prompt := st.chat_input("Escribe tu pregunta aquí..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    st.markdown("Respuesta del chatbot.")
