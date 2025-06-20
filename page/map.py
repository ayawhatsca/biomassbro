import streamlit as st
import geemap.foliumap as geemap
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import pandas as pd
import ee

def show_map(year, color_palette):
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
            Aboveground Biomass Estimator Map
        </h2>
        <h5 style="margin: 0 0 1rem 0; text-align: center; font-family: 'Onest', sans-serif;">
            Tanjung Puting National Park, Indonesia
        </h5>
    </div>
    """, unsafe_allow_html=True)

    # Get feature collections
    try:
        AGBP_per_year_fc = ee.FeatureCollection('projects/ee-sorayatriutami/assets/agb/AGBP_per_year')
        AGBP_Diff_per_year_fc = ee.FeatureCollection('projects/ee-sorayatriutami/assets/agb/AGBP_Diff_per_year')
        RMSE_per_year_fc = ee.FeatureCollection('projects/ee-sorayatriutami/assets/agb/RMSE_per_year')
    except Exception as e:
        st.error(f"Error loading FeatureCollections: {str(e)}")
        return

    # Convert to dataframes
    AGBP_per_year = fc_to_df(AGBP_per_year_fc, ['year', 'total_agb'])
    AGBP_Diff_per_year = fc_to_df(AGBP_Diff_per_year_fc, ['year', 'change'])
    RMSE_per_year = fc_to_df(RMSE_per_year_fc, ['year', 'rmse'])

    # Get palette colors
    palettes = {
        'Greens': ['f7fcf5', 'e5f5e0', 'c7e9c0', 'a1d99b', '74c476', '41ab5d', '238b45', '006d2c', '00441b'],
        'Viridis': px.colors.sequential.Viridis,
        'Plasma': px.colors.sequential.Plasma,
        'Earth': ['#f7f4f0', '#d4c5a9', '#a67c52', '#6b4423', '#3d2817']
    }

    st.markdown("""
    <div class="main-header">
        <h2 style="margin: 0; text-align: left;">
            Aboveground Biomass Distribution 2021
        </h2>
    </div>
    """, unsafe_allow_html=True)


    # Main layout: 2 columns
    col1, col2 = st.columns([3.3, 0.7])
    
    with col1:
        # Interactive Map
        # st.subheader(f"Aboveground Biomass Distribution {year}")
        display_map(year, palettes[color_palette])
    
    with col2:
        # Top: Statistics
        st.subheader("Statistics")
        st.markdown("""
        <style>
        /* Reduce gap above metric */
        [data-testid="stMetric"] {
            margin-top: -1.5rem !important;
            margin-bottom: rem !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        /* Make st.metric value font smaller */
        [data-testid="stMetricValue"] {
            font-size: 1.7rem !important;  /* Adjust as needed (e.g., 1.2rem, 1rem) */
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        display_stats(year)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bottom: Model Performance
        st.subheader("Model Performance")
        
        # Load observed vs predicted data for the year
        try:
            obs_pred_df = load_observed_vs_predicted(year)
            rmse_row = RMSE_per_year[RMSE_per_year['year'] == year]
            
            if not rmse_row.empty and not obs_pred_df.empty:
                rmse_val = rmse_row.iloc[0]['rmse']
                mean_obs = obs_pred_df['agbd'].mean()
                error_pct = (rmse_val / mean_obs) * 100 if mean_obs != 0 else 0
        
                # Create donut chart
                donut_chart = make_donut(error_pct)
                st.altair_chart(donut_chart, use_container_width=False)
            else:
                st.info("No RMSE or observed data for this year.")
        except Exception as e:
            st.error(f"Error loading performance data: {str(e)}")

    # Custom CSS untuk tab: aktif tetap, tidak aktif transparan, font besar
    st.markdown("""
    <style>
    /* Semua tab: border di seluruh sisi, font besar, padding lega */
    .stTabs [role="tab"] {
        border: 2.5px solid #b6a89d !important;
        border-bottom: none !important;
        border-radius: 0 !important;
        margin-right: -2.5px; /* agar border tengah tidak double */
        padding: 16px 38px 16px 38px !important;
        background-color: transparent !important;
        position: relative;
        z-index: 2;
        transition: background 0.2s;
    }
    /* Tab tidak aktif: transparan, font besar */
    .stTabs [role="tab"]:not([aria-selected="true"]) {
        background-color: transparent !important;
        color: #b6a89d !important;
        border-radius: 0;
        border: none !important;
        margin-bottom: 4px;
    }
    /* Tab aktif: warna highlight, font besar */
    .stTabs [role="tab"][aria-selected="true"] {
        background: rgba(60, 90, 60, 0.5) !important;
        color: #a04a1a !important;
        border-radius: 0;
        border: none !important;
        margin-bottom: 5px;
    }

    /* Ukuran font tab label */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.6rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: bold !important;
        line-height: 1.4;
        margin-bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Tab navigasi
    tab1, tab2 = st.tabs(["Total Aboveground Biomass", "Model RMSE"])

    with tab1:
        st.subheader("Total Aboveground Biomass 2021 - 2023", help= "The total mass of living vegetation above the ground surface within Tanjung Puting area")
        col1, col2 = st.columns([1,1])
        with col1:
            if not AGBP_per_year.empty:
                fig1 = px.line(
                    AGBP_per_year.sort_values('year'),
                    x='year', y='total_agb', markers=True,
                    labels={'total_agb': 'AGB (Ton)', 'year': 'Year'},
                    title=' '
                )
                fig1.update_traces(line=dict(color='#9ACD32', width=3), marker=dict(size=8))
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', size=18),
                    title=dict(font=dict(size=24)),
                    xaxis=dict(
                        type='category', 
                        showgrid=False, 
                        tickfont=dict(size=16),
                        title=dict(font=dict(size=18))  # Perbaikan: gunakan title=dict(font=dict())
                    ),
                    yaxis=dict(
                        showgrid=False, 
                        tickfont=dict(size=16),
                        title=dict(font=dict(size=18))  # Perbaikan: gunakan title=dict(font=dict())
                    ),
                    height=350,
                    margin=dict(l=30, r=30, t=40, b=30)
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("Data Total Aboveground Biomass tidak tersedia.")

    with tab2:
        st.subheader("Model RMSE 2021 - 2023",
                     help= "Predictive accuracy measure that calculates the average difference between predicted and actual values.")
        col1, col2 = st.columns([1,1])
        with col1:
            if not RMSE_per_year.empty:
                fig2 = px.line(
                    RMSE_per_year.sort_values('year'),
                    x='year', y='rmse', markers=True,
                    labels={'rmse': 'RMSE (Ton/Ha)', 'year': 'Year'},
                    title=' '
                )
                fig2.update_traces(line=dict(color='#9ACD32', width=3), marker=dict(size=8))
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', size=18),
                    title=dict(font=dict(size=24)),
                    xaxis=dict(
                        type='category', 
                        showgrid=False, 
                        tickfont=dict(size=16),
                        title=dict(font=dict(size=18))  # Perbaikan: gunakan title=dict(font=dict())
                    ),
                    yaxis=dict(
                        showgrid=False, 
                        tickfont=dict(size=16),
                        title=dict(font=dict(size=18))  # Perbaikan: gunakan title=dict(font=dict())
                    ),
                    height=350,
                    margin=dict(l=30, r=30, t=40, b=30)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Data RMSE tidak tersedia.")

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
    
# --- FeatureCollection to DataFrame ---
@st.cache_data
def fc_to_df(_feature_collection, properties):
    try:
        features = _feature_collection.getInfo()['features']
        data = [{prop: f['properties'].get(prop, None) for prop in properties} for f in features]
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error converting FeatureCollection to DataFrame: {str(e)}")
        return pd.DataFrame()

# --- Year-specific FeatureCollections ---
@st.cache_data
def load_agb(year: int):
    try:
        asset_id = f'projects/ee-sorayatriutami/assets/agb/agb_{year}'
        return ee.Image(asset_id).select('agbd')
    except Exception as e:
        st.error(f"Error loading AGB data for year {year}: {str(e)}")
        return None

@st.cache_data
def load_observed_vs_predicted(year):
    try:
        fc = ee.FeatureCollection(f'projects/ee-sorayatriutami/assets/agb/Observed_vs_Predicted_{year}')
        return fc_to_df(fc, ['agbd', 'agbd_predicted'])
    except Exception as e:
        st.error(f"Error loading observed vs predicted data for year {year}: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_tanjung_puting_geometry():
    return ee.Geometry.Polygon(
        [[[111.88610442456644, -2.634969034682339],
        [111.89125426587503, -2.655546449659222],
        [111.90876372632425, -2.6850401460514184],
        [111.89331420239847, -2.7049308420876907],
        [111.89606078442972, -2.7176195640997145],
        [111.88679107007425, -2.7258500152053013],
        [111.89331420239847, -2.7601429536574984],
        [111.86001189526957, -2.792034498640716],
        [111.84730895337503, -2.7807182425493235],
        [111.82430632886332, -2.791348668036572],
        [111.78379424390238, -2.794091988050556],
        [111.78001769360941, -2.800264434634048],
        [111.79203398999613, -2.8174099487121724],
        [111.785167534918, -2.838327133809131],
        [111.75838836011332, -2.8379842321801423],
        [111.75529845532816, -2.830097466660325],
        [111.75941832837503, -2.8108946830231907],
        [111.71272643384378, -2.77694613303973],
        [111.70208342847269, -2.7790036488120053],
        [111.70311339673441, -2.8095230435033094],
        [111.72268279370707, -2.8225535537691324],
        [111.7273823921613, -3.2221912287192493],
        [111.61477252888005, -3.2194489851511228],
        [111.62033831194752, -3.6005620583326463],
        [112.19162737444752, -3.5950797206625347],
        [112.19986712054127, -3.2420871034107583],
        [112.3001173646819, -3.243458195531875],
        [112.26990496233815, -3.207809198385169],
        [112.25023871982027, -3.206395602312007],
        [112.2571051748984, -3.176230053218437],
        [112.2406256827109, -3.033617484950588],
        [112.22002631747652, -2.892357644516766],
        [112.18294746005465, -2.844352678960637],
        [112.13788608216097, -2.7840007481915663],
        [112.13033298157504, -2.7593104271303273],
        [112.11385348938754, -2.759996276327663],
        [112.04114594826174, -2.5469780477290866],
        [112.02432313332034, -2.5469780477290866],
        [111.95771851906252, -2.546292080361117],
        [111.9505087412305, -2.5425192533115304],
        [111.94398560890627, -2.547321031276085],
        [111.9292227304883, -2.572358582696896],
        [111.92973771461916, -2.576817273307101],
        [111.92699113258791, -2.5783606625738598],
        [111.9292227304883, -2.585563121046636],
        [111.92441621193362, -2.5884783902399673],
        [111.92613282570315, -2.591736624343633],
        [111.9233862436719, -2.593965937582822],
        [111.92544618019534, -2.597224157554991],
        [111.9175497568555, -2.593451481030129],
        [111.92098298439456, -2.599967915223642],
        [111.91136994728518, -2.597567127589645],
        [111.9123999155469, -2.6047694767833836],
        [111.90484681496096, -2.602711666925904],
        [111.90484681496096, -2.610599919778431],
        [111.89523377785159, -2.614029579495644],
        [111.89832368263674, -2.621917761255445],
        [111.88768067726565, -2.6318636586595057]]]
    )

def display_map(year, palette):
    try:
        agb_layer = load_agb(year)
        if agb_layer is None:
            st.error(f"AGB data for {year} not available")
            return
            
        # Tanjung Puting center coordinates
        center_lat = -3.05
        center_lon = 112.0435
        
        vis_params = {
            'min': 0,
            'max': 300,
            'palette': palette,
            'bands': ['agbd']
        }
        
        Map = geemap.Map(center=[center_lat, center_lon], zoom=10)
        Map.addLayer(agb_layer, vis_params, f'AGB {year}')
        Map.add_colorbar(vis_params, label="AGB (Ton/Ha)")
        Map.to_streamlit(height=750)
        
    except Exception as e:
        st.error(f"Error displaying map: {str(e)}")

def display_stats(year):
    """Display statistics for selected year"""
    try:
        agb_layer = load_agb(year)
        if agb_layer is None:
            st.error(f"AGB data for {year} not available")
            return
            
        geometry = get_tanjung_puting_geometry()
        
        stats = agb_layer.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.min(), '', True
            ).combine(
                ee.Reducer.max(), '', True
            ),
            geometry=geometry,
            scale=100,
            maxPixels=1e10
        ).getInfo()
        
        st.metric(label=f"Average AGB {year}", 
                  value=f"{stats.get('agbd_mean', 0):.1f} Ton/ha",
                  help="Average aboveground biomass value per hectare (Density)")
        
    except Exception as e:
        st.error(f"Error calculating stats: {str(e)}")

def make_donut(error_pct):
    source = pd.DataFrame({
        "category": ['Error', 'Accuracy'],
        "value": [error_pct, 100 - error_pct],
        "color": ['#E74C3C', '#4CAF50']
    })
    
    # Chart tanpa .configure() di level individual
    chart = alt.Chart(source).mark_arc(
        innerRadius=40,
        outerRadius=70
    ).encode(
        theta=alt.Theta('value:Q'),
        color=alt.Color(
            'category:N',
            scale=alt.Scale(
                domain=['Error', 'Accuracy'],
                range=['#E74C3C', '#4CAF50']
            ),
            legend=None
        )
    )
    
    text = alt.Chart(pd.DataFrame({'text': [f'{100-error_pct:.1f}%']})).mark_text(
        align='center',
        baseline='middle',
        fontSize=20,
        fontWeight='bold',
        color='#ffffff'
    ).encode(text='text:N')
    
    # Gabungkan chart dan konfigurasi di level LayerChart
    combined_chart = (chart + text).resolve_scale(color='independent')
    
    # Konfigurasi background transparan di level akhir
    return combined_chart.configure(
        background='transparent',
        view={'stroke': None}  # Hilangkan border
    ).properties(
        width=140,
        height=160
    )

    
