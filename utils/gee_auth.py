import ee
import streamlit as st
from google.oauth2 import service_account

@st.cache_data
def auth_gee():
    """Authenticate Google Earth Engine"""
    try:
        credentials = ee.ServiceAccountCredentials(
            st.secrets["gee_service_account"]["client_email"],
            st.secrets["gee_service_account"]["private_key"],
            scopes=["https://www.googleapis.com/auth/earthengine"]
        )
        ee.Initialize(credentials)
        return True
    except Exception as e:
        try:
            # Fallback to default authentication
            ee.Initialize()
            return True
        except Exception as e2:
            st.error(f"GEE Authentication Error: {str(e2)}")
            return False
