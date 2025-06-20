import ee
import streamlit as st
from google.oauth2 import service_account

@st.cache_data
def auth_gee():
    """Authenticate Google Earth Engine"""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gee_service_account"],
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
