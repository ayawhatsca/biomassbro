# BiomassBro: Aboveground Biomass Monitoring System

**BiomassBro** is a GeoAI web application designed to estimate, analyze, and visualize Aboveground Biomass (AGB) in **Tanjung Puting National Park, Indonesia**. By leveraging Google Earth Engine's cloud computing power and Streamlit's interactive interface, this tool provides a scalable solution for monitoring forest health and carbon stocks.

**Live Application:** [biomassbro.streamlit.app](https://biomassbro.streamlit.app/)

---

## Features
* **Satellite Data Integration:** Seamlessly fetches data from the Google Earth Engine (GEE) Data Catalog and private assets.
* **Interactive Map:** Visualize AGB distribution using `geemap` and `folium` with customizable palettes.
* **Temporal Analysis:** Compare biomass changes and density across different years (2021–2023).
* **Model Accuracy Metrics:** Real-time visualization of RMSE (Root Mean Square Error) and model performance.
* **Statistical Summaries:** Automated server-side calculation of mean AGB values for the study area.

---

## Tech Stack
* **Frontend:** [Streamlit](https://streamlit.io/)
* **Geospatial Processing:** [Google Earth Engine (GEE)](https://earthengine.google.com/)
* **Mapping Library:** [geemap](https://geemap.org/)
* **Data Visualization:** Plotly, Altair, and Pandas
* **Language:** Python 3.9+

---

## Local Setup and Installation

### 1. Prerequisites
* **Python 3.9+** installed on your system.
* **Google Earth Engine Account:** You must have a registered GEE account. [Sign up here](https://earthengine.google.com/signup/).
* **Cloud Project:** A valid Google Cloud Project ID with the Earth Engine API enabled.
* You can check the code for GEE from the **biomassbro/GEE** folder, I separate it into 3 parts (minimum errors and execution time).

### 2. Installation Steps
Clone the repository:
```bash
git clone [https://github.com/ayawhatsca/biomassbro.git](https://github.com/ayawhatsca/biomassbro.git)
cd biomassbro
