import ee
import streamlit as st

@st.cache_data
def auth_gee():
    """Authenticate Google Earth Engine"""
    try:
        credentials = ee.ServiceAccountCredentials(
            st.secrets["gee_service_account"]["client_email"],
            st.secrets["gee_service_account"]["private_key"]
        )  # Added missing closing parenthesis
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"GEE Authentication Error: {str(e)}")
        return False
