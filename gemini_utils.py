# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import logging

# Configuración de logging para una mejor depuración en Streamlit Cloud
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiUtils:
    def __init__(self):
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        if not self.api_key or "PEGA_AQUÍ" in self.api_key:
            raise ValueError("La clave de API de Gemini no está configurada correctamente en Streamlit Secrets.")
        
        genai.configure(api_key=self.api_key)
        self.last_used_model = "No determinado"

    def get_last_used_model(self):
        """Devuelve el último modelo que generó una respuesta exitosa."""
        return self.last_used_model

    def llamar_gemini_directo(self, prompt):
        """
        Función central para interactuar con la API de Gemini.
        - Utiliza una lista de modelos optimizada.
        - Implementa configuraciones de seguridad ajustadas para evitar bloqueos.
        - Proporciona un sistema de fallback robusto entre modelos.
        """
        generation_config = {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        }

        # --- CORRECCIÓN CLAVE ---
        # Se ajusta el umbral de bloqueo a "BLOCK_ONLY_HIGH" para reducir la
        # probabilidad de que la IA bloquee respuestas legítimas sobre temas de salud.
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
        
        # Lista de modelos actualizada, priorizando los más recientes y estables.
        # Si uno falla, automáticamente intentará con el siguiente.
        modelos_disponibles = [
            "gemini-2.0-flash-exp",    # Modelo experimental más reciente
            "gemini-1.5-flash-latest", # Versión más reciente de 1.5
            "gemini-1.5-pro-latest",   # Versión más reciente de 1.5 pro
            "gemini-1.5-flash",        # Modelo básico
            "gemini-1.5-pro",          # Modelo pro básico
        ]
        
        for modelo in modelos_disponibles:
            try:
                model = genai.GenerativeModel(
                    model_name=modelo,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                logger.info(f"Intentando generar contenido con el modelo: {modelo}")
                response = model.generate_content(prompt)
                
                # A veces la respuesta puede no tener 'parts', hay que verificarlo.
                if response.parts:
                    texto_respuesta = "".join(part.text for part in response.parts)
                    if texto_respuesta.strip():
                        logger.info(f"Respuesta exitosa usando el modelo: {modelo}")
                        self.last_used_model = modelo
                        return texto_respuesta
                
                # Este log ayuda a identificar si el problema es un bloqueo de seguridad
                logger.warning(f"Respuesta vacía o bloqueada por seguridad del modelo {modelo}. Intentando con el siguiente.")
                continue

            except Exception as modelo_error:
                logger.warning(f"Error al llamar al modelo {modelo}: {str(modelo_error)}. Intentando con el siguiente.")
                continue
        
        # Mensaje de error si ningún modelo de la lista funcionó
        error_message = "Todos los modelos de Gemini fallaron o no están disponibles en este momento. Por favor, intenta de nuevo más tarde."
        st.error(error_message)
        return f"Error: {error_message}"

    def obtener_analisis_ia(self, datos_usuario):
        """Prepara y envía el prompt específico para el análisis de diabetes."""
        prompt = f"""
        Como un experto en salud y prevención de la diabetes, analiza los siguientes datos del test FINDRISC de un paciente: {datos_usuario}.

        Basado en esta información, por favor proporciona:
        1.  **Análisis Detallado del Riesgo:** Explica qué significa el puntaje y el nivel de riesgo en términos sencillos.
        2.  **Tres Recomendaciones Clave:** Ofrece 3 consejos claros, accionables y personalizados para reducir su riesgo. Usa viñetas o una lista numerada.
        3.  **Próximos Pasos:** Sugiere qué debería hacer el paciente a continuación (ej. consultar a un médico, realizarse ciertos análisis, etc.).

        El tono debe ser profesional, empático y fácil de entender para una persona sin conocimientos médicos.
        """
        return self.llamar_gemini_directo(prompt)


