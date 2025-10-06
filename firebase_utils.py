# -*- coding: utf-8 -*-
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import secrets
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FirebaseUtils:
    def __init__(self):
        self.db = self._initialize_firebase()

    @staticmethod
    @st.cache_resource
    def _initialize_firebase():
        """Inicializa el SDK de ADMIN para operaciones de base de datos."""
        try:
            creds_dict = dict(st.secrets["firebase_credentials"])
            if 'private_key' in creds_dict:
                 creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK inicializado correctamente.")
            return firestore.client()
        except Exception as e:
            logger.error(f"Error crítico al conectar con Firebase Admin: {e}")
            st.error(f"Error de conexión con la base de datos: {e}")
            return None

    def _hash_password(self, password, salt=None):
        """Genera un hash seguro para la contraseña con un salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Usamos scrypt que es más seguro que sha256 para contraseñas
        hashed_password = hashlib.scrypt(
            password.encode('utf-8'), salt=salt.encode('utf-8'), n=16384, r=8, p=1, dklen=64
        ).hex()
        return hashed_password, salt

    def create_user(self, email, password):
        """Crea un nuevo usuario en la colección 'users' de Firestore."""
        if not self.db: return False, "La base de datos no está disponible."
        
        users_ref = self.db.collection('users')
        # Verificar si el correo ya existe
        if users_ref.where('email', '==', email).get():
            return False, f"El correo electrónico '{email}' ya está registrado."

        hashed_password, salt = self._hash_password(password)
        
        try:
            # El ID del documento será el UID del usuario
            doc_ref = users_ref.document()
            doc_ref.set({
                'email': email,
                'password_hash': hashed_password,
                'salt': salt,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Usuario creado con éxito: {email}")
            return True, f"Usuario '{email}' registrado con éxito."
        except Exception as e:
            logger.error(f"Error al crear usuario {email}: {e}")
            return False, f"Error inesperado al registrar el usuario: {e}"

    def verify_user(self, email, password):
        """Verifica las credenciales del usuario y devuelve su UID si son correctas."""
        if not self.db: return None
        
        users_ref = self.db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).get()

        if not query:
            return None # Usuario no encontrado

        user_doc = query[0]
        user_data = user_doc.to_dict()
        
        stored_hash = user_data.get('password_hash')
        salt = user_data.get('salt')
        
        # Comparamos el hash de la contraseña ingresada con el almacenado
        hashed_password_attempt, _ = self._hash_password(password, salt)

        if hashed_password_attempt == stored_hash:
            logger.info(f"Autenticación exitosa para: {email}")
            return user_doc.id # Devuelve el UID del documento
        else:
            logger.warning(f"Intento de inicio de sesión fallido para: {email}")
            return None

    def guardar_datos_test(self, user_uid, datos):
        """Guarda los resultados de un test para un usuario específico."""
        if not self.db:
            st.warning("No se pueden guardar los datos porque la conexión con Firebase falló.")
            return
        try:
            # Guardamos los tests en una subcolección dentro del documento del usuario
            doc_ref = self.db.collection('users').document(user_uid).collection('tests').document()
            doc_ref.set(datos)
            st.success("¡Resultados guardados con éxito en tu historial!")
        except Exception as e:
            st.error(f"Ocurrió un error al guardar los datos: {e}")

    def cargar_datos_test(self, user_uid):
        """Carga el historial de tests de un usuario específico."""
        if not self.db:
            st.warning("No se pueden cargar los datos porque la conexión con Firebase falló.")
            return []
        try:
            tests_ref = self.db.collection('users').document(user_uid).collection('tests').order_by("fecha", direction=firestore.Query.DESCENDING)
            docs = tests_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Ocurrió un error al cargar tu historial: {e}")
            return []

