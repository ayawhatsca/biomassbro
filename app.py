import streamlit as st
import ee
from google.oauth2 import service_account
import pandas as pd
import os
import plotly.express as px
from page import map
from utils.gee_auth import auth_gee
from st_on_hover_tabs import on_hover_tabs
from page import home as home_page
from page import map as map_page  # Import fungsi dari pages

st.set_page_config(
    page_title="Aboveground Biomass Monitoring",
    page_icon="assets/icon.svg", 
    layout="wide")

if not auth_gee():
        st.error(" Google Earth Engine authentication failed!")
        st.stop()

st.markdown("""
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    /* Ensure Material Icons are properly loaded */
    .material-icons {
        font-family: 'Material Icons';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap');
html, body, [data-testid="stAppViewContainer"], .main {
    min-height: 100vh;
    background: radial-gradient(circle, rgba(0, 0, 0, 1) 0%, rgba(66, 92, 37, 1) 100%, rgba(41, 77, 41, 1) 11%, rgba(0, 0, 0, 1) 100%);
    font-family: 'Space Grotesk', sans-serif !important;
}
[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0);
    font-family: 'Space Grotesk', sans-serif !important;
}
.main, .block-container {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.image("assets/logo.svg", use_container_width=True)
with st.sidebar:
    st.markdown("---")
    tabs = on_hover_tabs(
        tabName=['Home', 'Map'],
        iconName=['home', 'map'],
        styles={
            'navtab': {
                'background-color': '#2d2d2d',
                'color': '#A9A9A9',
                'font-size': '16px',
                'font-family': "'Space Grotesk', sans-serif !important",  # aktifkan ini
                'font-weight': 'bold',
                'transition': '.3s',
                'text-transform': 'uppercase',
            },
            'tabStyle': {
                'font-family': "'Space Grotesk', sans-serif !important",  # aktifkan ini
                'list-style-type': 'none',
                'margin-bottom': '10px',
                'padding-left': '20px',
                'padding-top': '5px',
                'background-color': '#2d2d2d',
                'color': '#A9A9A9',
                'transition': 'color 0.2s ease',
            },
            'tabStyle:hover': {
                'font-family': "'Space Grotesk', sans-serif !important",  # aktifkan ini
                'color': '#fff',
                'cursor': 'pointer'
            },
            'tabStyleActive': {
                'font-family': "'Space Grotesk', sans-serif !important",  # aktifkan ini
                'color': '#ffffff',
                'background-color': '#238b45',
                'box-shadow': '0 2px 12px rgba(35,139,69,0.12)',
                'border-radius': '10px',
                'font-weight': 'bold'
            },
            'iconStyle': {
                'position': 'fixed',
                'margin-right': '15px',
                'font-size': '24px'
            }
        },
        default_choice=0
    )
    st.markdown("---")

    # Konten atas menu, berbeda tiap halaman
    if tabs == "Home":
        st.success("""
            **Welcome to Home page!**  
            Explore more about the project.  
        """)
    elif tabs == "Map":
        st.success("""
            **Map Visualization Control**  
                   
            Select the following parameters to customize the map display:  
            1. **Color Palette** – Adjust the color scheme for visual analysis
            2. **Year** – Display data for selected year
        """)
        
        # Color palette selection
        palettes = {
            'Greens': ['f7fcf5', 'e5f5e0', 'c7e9c0', 'a1d99b', '74c476', '41ab5d', '238b45', '006d2c', '00441b'],
            'Viridis': px.colors.sequential.Viridis,
            'Plasma': px.colors.sequential.Plasma,
            'Earth': ['#f7f4f0', '#d4c5a9', '#a67c52', '#6b4423', '#3d2817']
        }
        selected_palette = st.selectbox("Color Pallete", list(palettes.keys()))


        # Year selection
        year_options = [2021, 2022, 2023]
        # year_options = sorted([int(y) for y in AGBP_per_year['year'].unique()])
        selected_year = st.selectbox("Year:", year_options, index=0)

# Konten utama
if tabs == "Home":
    home_page.show_home()
elif tabs == "Map":
    map_page.show_map(selected_year, selected_palette)
