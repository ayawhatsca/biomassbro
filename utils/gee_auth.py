import ee
import streamlit as st

@st.cache_data
def auth_gee():
    """Authenticate Google Earth Engine using service account"""
    try:
        # Use Earth Engine's built-in service account authentication
        credentials = ee.ServiceAccountCredentials(
            st.secrets["gee_service_account"]["client_email"],
            key_data=st.secrets["gee_service_account"]["private_key"]
        )
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"GEE Authentication Error: {str(e)}")
        return False
