# -*- coding: utf-8 -*-
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FirebaseUtils:
    def __init__(self):
        self.db = self._initialize_firebase_admin()
        self.auth = self._initialize_pyrebase_auth()

    @staticmethod
    @st.cache_resource
    def _initialize_firebase_admin():
        """Initializes the ADMIN SDK for Firestore operations."""
        try:
            creds_dict = dict(st.secrets["firebase_credentials"])
            if 'private_key' in creds_dict:
                 creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK (Firestore) initialized successfully.")
            return firestore.client()
        except Exception as e:
            logger.error(f"Critical error connecting with Firebase Admin: {e}")
            st.error(f"Database connection error: {e}")
            return None

    @staticmethod
    @st.cache_resource
    def _initialize_pyrebase_auth():
        """Initializes Pyrebase to handle user authentication."""
        try:
            firebase_config = dict(st.secrets["firebase_config"])
            firebase = pyrebase.initialize_app(firebase_config)
            logger.info("Pyrebase (Auth) initialized successfully.")
            return firebase.auth()
        except KeyError:
            st.error("Configuration Error: 'firebase_config' not found in Streamlit secrets.")
            logger.error("'firebase_config' is missing from secrets.")
            return None
        except Exception as e:
            logger.error(f"Critical error connecting with Pyrebase Auth: {e}")
            return None

    def create_user(self, email, password):
        """Creates a new user in the Firebase Authentication service."""
        if not self.auth: return False, "Authentication service is not available."
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            uid = user['localId']
            logger.info(f"Firebase Auth user created successfully: {email}, UID: {uid}")
            
            # Optional: Create a user profile in Firestore to store additional data
            if self.db:
                self.db.collection('users').document(uid).set({
                    'email': email,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            return True, f"User '{email}' registered successfully."
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error creating Firebase Auth user {email}: {error_str}")
            if "EMAIL_EXISTS" in error_str:
                return False, f"The email '{email}' is already registered."
            if "WEAK_PASSWORD" in error_str:
                return False, "The password is too weak. It must be at least 6 characters."
            return False, "Unexpected error during user registration."

    def verify_user(self, email, password):
        """Verifies user credentials using Firebase Authentication."""
        if not self.auth: return None
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            logger.info(f"Authentication successful for: {email}")
            return user['localId']  # Returns the user's UID
        except Exception as e:
            logger.warning(f"Failed login attempt for {email}: {e}")
            return None

    def guardar_datos_test(self, user_uid, datos):
        """Saves test results for a specific user in Firestore."""
        if not self.db:
            st.warning("Cannot save data because the connection with Firebase failed.")
            return
        try:
            self.db.collection('users').document(user_uid).collection('tests').document().set(datos)
            st.success("Results saved successfully to your history!")
        except Exception as e:
            st.error(f"An error occurred while saving the data: {e}")

    def cargar_datos_test(self, user_uid):
        """Loads the test history for a specific user from Firestore."""
        if not self.db:
            st.warning("Cannot load data because the connection with Firebase failed.")
            return []
        try:
            tests_ref = self.db.collection('users').document(user_uid).collection('tests').order_by("fecha", direction=firestore.Query.DESCENDING)
            docs = tests_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"An error occurred while loading your history: {e}")
            return []

