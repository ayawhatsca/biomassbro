import ee
import streamlit as st
from google.oauth2 import service_account

@st.cache_data
def auth_gee():
    """Authenticate Google Earth Engine using service account"""
    try:
        # Use google.oauth2.service_account instead of ee.ServiceAccountCredentials
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gee_service_account"]
        )
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"GEE Authentication Error: {str(e)}")
        return False
