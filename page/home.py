import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import ee
import geemap.foliumap as geemap

def show_home():
    st.markdown("""
    <style>
    html, body, [class*="css"], .main, div, p, h1, h2, h3, h4, h5, h6, span, button, input {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 0.01em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h2 style="margin: 0; text-align: center;">
            Aboveground Biomass Monitor System<br> for Tanjung Puting National Park
        </h2>
        <h5 style="margin: 0 0 1rem 0; text-align: center; "font-family: 'Onest', sans-serif;">
            Central Kalimantan, Indonesia
        </h5>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in columns
    col1, col2 = st.columns([2.5, 1])
    with col1:
        st.markdown("""
        <div class="info-card">
            <h3 style="color: #ffffff";>
                About BIOMASSBRO</h3>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                <br>This biomass monitoring system uses Random Forest Machine Learning to estimate
                 aboveground biomass density in the <strong>Tanjung Puting National Park area</strong>.
            </p>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                This project aims to support forest conservation and monitor land cover changes using 
                <strong>Google Earth Engine</strong> and <strong>Remote Sensing</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Statistics cards
        st.markdown('<div class="stats-col">', unsafe_allow_html=True)
        st.markdown('<div class="stats-title">Project Statistics</div>', unsafe_allow_html=True)
        
        # Sample metrics (replace with real data)
        metrics = [
            ("Area Coverage", "400,000+ ha", "#ffffff"),
            # ("Data Points", "10,000+", "#ffffff"),
            ("Model Accuracy", "80%+", "#ffffff"),
            ("Year Analyzed", "2021-2023", "#ffffff")
        ]
        
        # CSS untuk metric kecil dan background berbeda
        st.markdown("""
        <style>
        .stats-col {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: auto;
        }
        .stats-title {
            text-align: center;
            color: #ffffff;
            font-weight: bold;
            font-size: 1.8rem;
            margin-bottom: 0;
        }
        .metric-container {
            background: rgba(60, 90, 60, 0.25);
            border-radius: 10px;
            padding: 0.2rem 0.2rem;
            min-width: 110px;
            text-align: center;
            border: 2px solid #3a3a3a;
            margin: 0.4rem 0;
        }
        .metric-value {
            font-size: 1rem;
            font-weight: 600;
            margin: 0;
        }
        .metric-label {
            font-size: 0.8rem;
            color: #cccccc;
            margin: 0 0 0 0;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for label, value, color in metrics:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value" style="color:{color};">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # How it works section
    st.markdown("---")
    st.markdown("""
            <h3 style="color: #ffffff"; text-align: center; margin: 0;>
                How it Works</h3>
        """, unsafe_allow_html=True)
    
    steps = [
        ("01", "Data Acquisition", "Collecting Landsat and Sentinel-2 satellite data from Google Earth Engine."),
        ("02", "Data Processing", "Preprocessing and extraction of spectral and textural features."),
        ("03", "Machine Learning", "Training a Random Forest model with ground truth data."),
        ("04", "Prediction & Mapping", "Biomass prediction and visualization of results on an interactive map."),
        ("05", "Analysis & Monitoring", "Temporal analysis and monitoring of biomass trend.")
    ]
    
    cols = st.columns(len(steps))
    for i, (num, title, desc) in enumerate(steps):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 0;">
                <div style="background-color: rgba(60, 90, 60, 0.25); color: white; border-radius: 50%; 
                           width: 50px; height: 50px; display: flex; align-items: center; 
                           justify-content: center; margin: 1rem auto 1rem auto; font-weight: bold;">
                    {num}
                </div>
                <h5 style="color: #9ACD32; margin: 0;">{title}</h5>
                <p style="font-size: 0.8rem; opacity: 1;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
   
    st.markdown("---")
     # Sample chart
    st.markdown("### Biomass Trend")

    # 1. Load data dari GEE
    agb_2021 = load_layer('projects/ee-sorayatriutami/assets/agb/agb_2021')
    agb_trend = load_layer('projects/ee-sorayatriutami/assets/agb/agb_trend')

    # 2. Parameter visualisasi yang sesuai dengan GEE
    vis_params_agb_2021 = {
    'bands': 'agbd',
    'min': 0,
    'max': 300,
    'palette': ['#edf8fb','#b2e2e2','#66c2a4','#2ca25f','#006d2c']
    }

    vis_params_agb_trend = {
        'bands': 'agbd',
        'min': -20,
        'max': 5,
        'palette': ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60']
    }

    # 3. Buat peta split-panel
    Map = geemap.Map(center=[-3.05, 112], zoom=10)
    
    # Tambahkan layer dengan parameter visualisasi
    left_layer = geemap.ee_tile_layer(agb_2021, vis_params_agb_2021, 'AGB 2021')
    right_layer = geemap.ee_tile_layer(agb_trend, vis_params_agb_trend, 'Trend AGB')
    
    # Split map
    Map.split_map(left_layer, right_layer)
    
    # Tambahkan legenda
    Map.add_colorbar(vis_params_agb_2021, label='AGB 2021 (ton/ha)', position='top-left')
    Map.add_colorbar(vis_params_agb_trend, label='Trend AGB 2021-2023 (ton/ha/year)', position='top-right')

    # Buat 3 kolom: kiri, tengah, kanan
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        Map.to_streamlit(height=750)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; 
                background-color: rgba(60, 90, 60, 0.25); border-radius: 0px;">
        <p style="margin: 0; opacity: 0.7;">
            © 2025 | Biomassbro<br>
            Aboveground Biomass Monitoring System — Developed for academic research purposes.<br>
            Part of a thesis project at Binus University.
        </p>
    </div>
    """, unsafe_allow_html=True)


def load_layer(asset_id):
    try:
        return ee.Image(asset_id)
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return None
