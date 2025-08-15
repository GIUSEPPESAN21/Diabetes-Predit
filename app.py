# -*- coding: utf-8 -*-
"""
Software Predictivo de Diabetes con IA usando Streamlit, Firebase y Gemini.

Descripción:
Esta aplicación utiliza el cuestionario FINDRISC para evaluar el riesgo de una persona
de desarrollar diabetes tipo 2 en los próximos 10 años.
Integra la IA de Gemini para proporcionar un análisis y recomendaciones personalizadas
y utiliza Firebase Firestore para almacenar los resultados de los usuarios de forma segura.

Instrucciones para ejecutar:
1.  Asegúrate de tener Python instalado.
2.  Instala las bibliotecas necesarias:
    pip install streamlit firebase-admin requests

3.  Configura Firebase:
    - Crea un proyecto en la Consola de Firebase (https://console.firebase.google.com/).
    - Ve a la configuración del proyecto -> Cuentas de servicio.
    - Haz clic en "Generar nueva clave privada" y descarga el archivo JSON.
    - **IMPORTANTE**: Renombra este archivo a "firebase_credentials.json" y colócalo
      en el mismo directorio que este script.
    - Ve a la sección de Firestore Database y crea una base de datos en modo de prueba
      para empezar.

4.  Configura la API de Gemini:
    - Obtén tu clave de API desde Google AI Studio (https://aistudio.google.com/app/apikey).
    - Reemplaza el valor de la variable `GEMINI_API_KEY` más abajo con tu clave.

5.  Ejecuta la aplicación desde tu terminal:
    streamlit run nombre_de_este_archivo.py
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json
import uuid
from datetime import datetime

# --- CONFIGURACIÓN DE SERVICIOS ---

# Configuración de la API de Gemini
# IMPORTANTE: Reemplaza "TU_API_KEY_DE_GEMINI" con tu clave de API real.
GEMINI_API_KEY = "TU_API_KEY_DE_GEMINI"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# Configuración de Firebase
# Asegúrate de que el archivo 'firebase_credentials.json' esté en el mismo directorio.
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    # Si las credenciales no se encuentran, la app mostrará un error y no usará Firebase.
    st.error(f"Error al inicializar Firebase: {e}")
    st.warning("La funcionalidad de guardar y cargar datos estará deshabilitada. "
               "Asegúrate de que tu archivo 'firebase_credentials.json' esté configurado correctamente.")
    db = None

# --- FUNCIONES AUXILIARES ---

def calcular_puntaje_findrisc(edad, imc, cintura, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes):
    """Calcula el puntaje FINDRISC basado en las entradas del usuario."""
    score = 0
    # 1. Edad
    if 45 <= edad <= 54:
        score += 2
    elif 55 <= edad <= 64:
        score += 3
    elif edad > 64:
        score += 4

    # 2. Índice de Masa Corporal (IMC)
    if 25 <= imc < 30:
        score += 1
    elif imc >= 30:
        score += 3

    # 3. Perímetro de la cintura
    if 94 <= cintura <= 102: # Hombres
        score += 3
    elif cintura > 102: # Hombres
        score += 4
    # Para mujeres los valores son diferentes, aquí asumimos una simplificación o se podría añadir un selector de sexo.
    # Por simplicidad del ejemplo, usamos los rangos más comunes.
    # En una app real, se diferenciaría por sexo.
    # if 80 <= cintura <= 88: # Mujeres -> score += 3
    # if cintura > 88: # Mujeres -> score += 4

    # 4. Actividad física
    if actividad == "No":
        score += 2

    # 5. Consumo de frutas y verduras
    if frutas_verduras == "No todos los días":
        score += 1

    # 6. Medicación para la hipertensión
    if hipertension == "Sí":
        score += 2

    # 7. Niveles de glucosa altos
    if glucosa_alta == "Sí":
        score += 5

    # 8. Familiares con diabetes
    if familiar_diabetes == "Sí: padres, hermanos o hijos":
        score += 5
    elif familiar_diabetes == "Sí: abuelos, tíos o primos hermanos":
        score += 3
        
    return score

def obtener_interpretacion_riesgo(score):
    """Devuelve el nivel de riesgo y una estimación basada en el puntaje."""
    if score < 7:
        return "Riesgo bajo", "1 de cada 100 personas desarrollará diabetes."
    elif 7 <= score <= 11:
        return "Riesgo ligeramente elevado", "1 de cada 25 personas desarrollará diabetes."
    elif 12 <= score <= 14:
        return "Riesgo moderado", "1 de cada 6 personas desarrollará diabetes."
    elif 15 <= score <= 20:
        return "Riesgo alto", "1 de cada 3 personas desarrollará diabetes."
    else: # score > 20
        return "Riesgo muy alto", "1 de cada 2 personas desarrollará diabetes."

def obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion):
    """
    Llama a la API de Gemini para obtener un análisis y recomendaciones personalizadas.
    """
    if GEMINI_API_KEY == "TU_API_KEY_DE_GEMINI":
        return ("Por favor, configura tu API Key de Gemini en el código para activar el análisis por IA. "
                "Sin la clave, la IA no puede generar recomendaciones.")

    prompt = f"""
    Eres un asistente de salud virtual especializado en la prevención de la diabetes.
    Un usuario ha completado el cuestionario de riesgo de diabetes FINDRISC y ha obtenido los siguientes resultados:

    Datos del usuario:
    - Edad: {datos_usuario['edad']} años
    - IMC: {datos_usuario['imc']:.2f}
    - Perímetro de cintura: {datos_usuario['cintura']} cm
    - Realiza 30 min de actividad física diaria: {datos_usuario['actividad']}
    - Come frutas y verduras todos los días: {datos_usuario['frutas_verduras']}
    - Toma medicación para la hipertensión: {datos_usuario['hipertension']}
    - Ha tenido niveles de glucosa altos alguna vez: {datos_usuario['glucosa_alta']}
    - Tiene familiares con diabetes: {datos_usuario['familiar_diabetes']}

    Resultados del test:
    - Puntaje FINDRISC: {puntaje}
    - Nivel de riesgo: {nivel_riesgo}
    - Estimación de riesgo a 10 años: {estimacion}

    Basado en esta información, proporciona un análisis detallado y recomendaciones personalizadas en español.
    Tu respuesta debe ser empática, clara y motivadora. Estructura tu respuesta de la siguiente manera:

    1.  **Análisis de tu resultado:** Explica brevemente qué significa el puntaje y el nivel de riesgo en el contexto de los datos proporcionados por el usuario. Identifica los principales factores de riesgo que contribuyeron a su puntaje.
    2.  **Recomendaciones Clave:** Ofrece 3 a 5 recomendaciones prácticas y accionables para reducir su riesgo. Las recomendaciones deben ser específicas para los factores de riesgo identificados (por ejemplo, si el IMC es alto, da consejos sobre dieta y ejercicio; si no come verduras, sugiere formas de incorporarlas).
    3.  **Próximos Pasos:** Aconseja al usuario que consulte a un profesional de la salud para una evaluación completa. Menciona la importancia de no autodiagnosticarse y de usar esta herramienta solo como una guía informativa.

    Utiliza un tono cercano y alentador. Finaliza con un mensaje positivo.
    """

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Lanza un error si la petición no fue exitosa
        result = response.json()
        # Extraer el texto de la respuesta de Gemini
        return result['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Error al contactar la IA de Gemini: {e}"
    except (KeyError, IndexError) as e:
        return f"Respuesta inesperada de la IA de Gemini. Detalles: {response.text}"


def guardar_datos_en_firestore(user_id, datos):
    """Guarda los datos de un test en Firestore."""
    if not db:
        st.warning("No se pueden guardar los datos porque Firebase no está conectado.")
        return
    try:
        doc_ref = db.collection('usuarios').document(user_id).collection('tests').document()
        doc_ref.set(datos)
        st.success(f"¡Resultados guardados con éxito! Tu ID de usuario es: **{user_id}**")
        st.info("Guarda este ID para consultar tus resultados en el futuro.")
    except Exception as e:
        st.error(f"Ocurrió un error al guardar los datos: {e}")

def cargar_datos_de_firestore(user_id):
    """Carga el historial de tests de un usuario desde Firestore."""
    if not db:
        st.warning("No se pueden cargar los datos porque Firebase no está conectado.")
        return []
    try:
        tests_ref = db.collection('usuarios').document(user_id).collection('tests')
        docs = tests_ref.stream()
        resultados = [doc.to_dict() for doc in docs]
        # Ordenar por fecha para mostrar el más reciente primero
        return sorted(resultados, key=lambda x: x['fecha'], reverse=True)
    except Exception as e:
        st.error(f"Ocurrió un error al cargar los datos: {e}")
        return []

# --- INTERFAZ DE USUARIO CON STREAMLIT ---

st.set_page_config(page_title="Predictor de Diabetes con IA", layout="wide", initial_sidebar_state="expanded")

# --- BARRA LATERAL ---
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Selecciona una opción", ["Realizar nuevo test", "Consultar historial"])

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# --- PÁGINA: REALIZAR NUEVO TEST ---
if opcion == "Realizar nuevo test":
    st.title("🩺 Software Predictivo de Diabetes con IA")
    st.markdown("""
    Esta herramienta utiliza el **Cuestionario FINDRISC** (FINnish Diabetes Risk Score) para estimar tu riesgo de desarrollar
    Diabetes Mellitus tipo 2 en los próximos 10 años. Responde a las siguientes preguntas con la mayor sinceridad posible.
    
    **Nota:** Esta es una herramienta de orientación y no reemplaza el diagnóstico de un profesional de la salud.
    """)

    with st.form("findrisc_form"):
        st.header("Cuestionario de Riesgo")

        # Columnas para una mejor distribución
        col1, col2 = st.columns(2)

        with col1:
            edad = st.number_input("1. ¿Cuál es tu edad?", min_value=18, max_value=120, value=40)
            peso = st.number_input("2. ¿Cuál es tu peso en kg?", min_value=30.0, max_value=300.0, value=70.0, step=0.5)
            altura = st.number_input("3. ¿Cuál es tu altura en metros? (Ej: 1.75)", min_value=1.0, max_value=2.5, value=1.75, step=0.01)
            cintura = st.number_input("4. ¿Cuál es el perímetro de tu cintura en cm? (medido a la altura del ombligo)", min_value=50, max_value=200, value=90)

        with col2:
            actividad = st.radio("5. ¿Realizas al menos 30 minutos de actividad física todos los días (en el trabajo o tiempo libre)?", ("Sí", "No"))
            frutas_verduras = st.radio("6. ¿Comes frutas, bayas o verduras todos los días?", ("Sí", "No todos los días"))
            hipertension = st.radio("7. ¿Has tomado alguna vez medicamentos para la presión arterial alta de forma regular?", ("Sí", "No"))
            glucosa_alta = st.radio("8. ¿Alguna vez te han encontrado un nivel de glucosa en sangre alto (en un chequeo, enfermedad o embarazo)?", ("Sí", "No"))
        
        familiar_diabetes = st.selectbox(
            "9. ¿Se le ha diagnosticado diabetes a alguno de tus familiares?",
            ("No", "Sí: abuelos, tíos o primos hermanos", "Sí: padres, hermanos o hijos")
        )

        submit_button = st.form_submit_button(label="Calcular Riesgo")

    if submit_button:
        if altura > 0:
            imc = peso / (altura * altura)
            st.subheader(f"Tu Índice de Masa Corporal (IMC) es: {imc:.2f}")

            puntaje = calcular_puntaje_findrisc(edad, imc, cintura, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes)
            nivel_riesgo, estimacion = obtener_interpretacion_riesgo(puntaje)

            # Mostrar resultados
            st.subheader("Resultados de tu Evaluación")
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.metric(label="Puntaje FINDRISC Total", value=f"{puntaje} puntos")
            with res_col2:
                st.metric(label="Nivel de Riesgo", value=nivel_riesgo)
            
            st.info(f"**Estimación a 10 años:** {estimacion}")

            # Datos para guardar y enviar a la IA
            datos_usuario = {
                "fecha": datetime.now().isoformat(),
                "edad": edad,
                "peso": peso,
                "altura": altura,
                "imc": imc,
                "cintura": cintura,
                "actividad": actividad,
                "frutas_verduras": frutas_verduras,
                "hipertension": hipertension,
                "glucosa_alta": glucosa_alta,
                "familiar_diabetes": familiar_diabetes,
                "puntaje": puntaje,
                "nivel_riesgo": nivel_riesgo,
                "estimacion": estimacion
            }

            # Obtener y mostrar análisis de IA
            with st.spinner("🤖 Un momento, nuestra IA está analizando tus resultados..."):
                analisis_ia = obtener_analisis_ia(datos_usuario, puntaje, nivel_riesgo, estimacion)
                st.subheader("🧠 Análisis y Recomendaciones por IA (Gemini)")
                st.markdown(analisis_ia)
                datos_usuario["analisis_ia"] = analisis_ia

            # Guardar datos en Firebase
            if db:
                guardar_datos_en_firestore(st.session_state.user_id, datos_usuario)

        else:
            st.error("La altura debe ser mayor que cero para calcular el IMC.")

# --- PÁGINA: CONSULTAR HISTORIAL ---
elif opcion == "Consultar historial":
    st.title("📖 Consulta de Historial")
    st.markdown("Ingresa el ID de usuario que se te proporcionó al guardar tus resultados para ver tu historial.")

    user_id_input = st.text_input("Ingresa tu ID de usuario", value=st.session_state.get('user_id', ''))

    if st.button("Buscar Historial"):
        if user_id_input:
            st.session_state.user_id = user_id_input
            historial = cargar_datos_de_firestore(user_id_input)
            if historial:
                st.success(f"Se encontraron {len(historial)} registros para el usuario.")
                for i, test in enumerate(historial):
                    fecha_test = datetime.fromisoformat(test['fecha']).strftime('%d-%m-%Y %H:%M')
                    with st.expander(f"Test del {fecha_test} - Puntaje: {test['puntaje']} ({test['nivel_riesgo']})", expanded=(i==0)):
                        st.write(f"**Edad:** {test['edad']}, **IMC:** {test['imc']:.2f}, **Cintura:** {test['cintura']} cm")
                        st.write(f"**Estimación:** {test['estimacion']}")
                        st.markdown("---")
                        st.subheader("Análisis de IA de este resultado:")
                        st.markdown(test.get("analisis_ia", "No hay análisis disponible para este registro."))
            else:
                st.warning("No se encontraron resultados para este ID. Verifica que sea correcto.")
        else:
            st.error("Por favor, ingresa un ID de usuario.")
