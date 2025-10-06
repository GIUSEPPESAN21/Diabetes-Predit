# -*- coding: utf-8 -*-
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseUtils:
    def __init__(self):
        self.db = self._initialize_firebase()

    @st.cache_resource
    def _initialize_firebase(_self):
        """Inicializa el SDK de ADMIN para operaciones de base de datos."""
        try:
            if "firebase_credentials" in st.secrets:
                creds_dict = dict(st.secrets["firebase_credentials"])
                if 'private_key' in creds_dict:
                     creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(creds_dict)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                
                return firestore.client()
            
            st.error("Credenciales de Firebase no encontradas en los Streamlit Secrets.")
            return None
        except Exception as e:
            st.error(f"Error crítico al conectar con Firebase Admin: {e}")
            raise  # Levanta la excepción para que initialize_services en app.py pueda manejarla.

    def guardar_datos_en_firestore(self, user_id, datos):
        if not self.db:
            st.warning("No se pueden guardar los datos porque la conexión con Firebase falló.")
            return
        try:
            doc_ref = self.db.collection('usuarios').document(user_id).collection('tests').document()
            doc_ref.set(datos)
            st.success(f"¡Resultados guardados con éxito! Tu ID de usuario es:")
            st.code(user_id)
            st.info("Guarda este ID para consultar tus resultados en el futuro.")
        except Exception as e:
            st.error(f"Ocurrió un error al guardar los datos en Firestore: {e}")

    def cargar_datos_de_firestore(self, user_id):
        if not self.db:
            st.warning("No se pueden cargar los datos porque la conexión con Firebase falló.")
            return []
        try:
            tests_ref = self.db.collection('usuarios').document(user_id).collection('tests').order_by("fecha", direction=firestore.Query.DESCENDING)
            docs = tests_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Ocurrió un error al cargar los datos desde Firestore: {e}")
            return []
