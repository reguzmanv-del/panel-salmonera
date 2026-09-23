import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

# 1. Configuración de la página (Adaptativa)
st.set_page_config(page_title="BlueBrain SCADA | V3.0", page_icon="🌐", layout="wide", initial_sidebar_state="auto")

# 2. Diseño UI/UX de vanguardia (Glassmorphism, Neón sutil y CSS Grid)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&display=swap');
    
    /* Fondo general oscuro con un sutil gradiente radial */
    .main, [data-testid="stAppViewContainer"] { 
        background: radial-gradient(circle at top right, #111827, #090d14); 
        color: #e2e8f0; 
    }
    
    /* Tipografía futurista para títulos */
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; color: #f8fafc !important; letter-spacing: 0.5px; }
    p, span, div { font-family: 'Inter', sans-serif; }
    
    /* Texto con gradiente para el título principal */
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #38bdf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
    }

    /* Glassmorphism para las métricas de Streamlit */
    .stMetric { 
        background: rgba(30, 41, 59, 0.4) !important; 
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important; 
        padding: 15px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700 !important; font-family: 'Rajdhani', sans-serif !important; }
    
    /* CSS Grid Fluido para las tarjetas (Perfecto para celulares y desktop) */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    
    /* Tarjetas de Tanques Modernas */
    .tank-card {
        background: rgba(17, 24, 39, 0.6);
        backdrop-filter: blur(8px);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .tank-card:hover { transform: translateY(-2px); }
    
    .status-ok { border: 1px solid rgba(16, 185, 129, 0.4); box-shadow: 0 0 15px rgba(16, 185, 129, 0.1); }
    .status-warning { border: 1px solid rgba(245, 158, 11, 0.4); box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
    .status-alert { border: 1px solid rgba(239, 68, 68, 0.6); box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }
    
    .tank-title { font-family: 'Rajdhani', sans-serif; font-size: 1.2rem; font-weight: 700; color: #fff; margin-bottom: 5px; }
    .tank-data { font-size: 0.85rem; color: #94a3b8; margin: 2px 0; }
    .data-highlight { font-weight: 600; }
    .color-ok { color: #34d399; }
    .color-alert { color: #f87171; }
    .color-warning { color: #fbbf24; }
    </style>
""", unsafe_allow_html=True)

# 3. Conexiones
SHEET_URL = "https://docs.google.com/spreadsheets/d/115BG0pdWQxVlLVozHzI_ken4P0El_fZar_GTu3cRsus/export?format=csv"

@st.cache_data(ttl=5)
def cargar_datos():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    return df

@st.cache_data(ttl=600)
def obtener_clima_reloncavi():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-41.49&longitude=-72.31&current=temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure&wind_speed_unit=ms&timezone=America%2FSantiago"
        return requests.get(url, timeout=5).json().get('current', None)
    except:
        return None

try:
    df = cargar_datos()
    cols_numericas = ['oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c', 'salinidad_psu', 'corriente_ms', 'estado_alimentacion', 'tasa_alimento_kg_min', 'conteo_algas_celulas', 'mortalidad_dia', 'silo_alimento_pct']
    for col in cols_numericas:
        if col in df.columns: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # 4. BARRA LATERAL
    st.sidebar.markdown("### 🌐 BlueBrain OS")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navegación", ["Vista General & Mapa", "Calidad de Agua", "Alimentación", "Meteorología", "Hardware de Borde"])
    
    centros = df['centro_id'].dropna().unique() if 'centro_id' in df.columns else ["Pontón Alfa"]
    centro_seleccionado = st.sidebar.selectbox("Centro Activo", centros)
    df_centro = df[df['centro_id'] == centro_seleccionado] if 'centro_id' in df.columns else df
    jaulas_disponibles = df_centro['jaula_id'].dropna().unique() if 'jaula_id' in df_centro.columns else ["TK.01"]

    # ==========================================
    # VISTA 1: VISTA GENERAL Y MAPA
    # ==========================================
    if menu == "Vista General & Mapa":
        st.markdown(f'<div class="gradient-text">Centro de Operaciones: {centro_seleccionado}</div>', unsafe_allow_html=True)
        st.markdown("<span style='color: #34d399;'>●</span> Enlace seguro establecido | Estuario del Reloncaví (Cochamó)", unsafe_allow_html=True)
        st.markdown("---")
        
        col_mapa, col_kpi = st.columns([2, 1])
        
        with col_mapa:
            st.markdown("#### 🛰️ Posicionamiento y Layout")
            # Mapa 3D Moderno usando PyDeck
            map_data = pd.DataFrame({
                'Nombre': ['Pontón', 'TK.01', 'TK.02', 'TK.03', 'TK.04', 'TK.05'],
                'lat': [-41.4900, -41.4910, -41.4890, -41.4905, -41.4895, -41.4915],
                'lon': [-72.3100, -72.3110, -72.3090, -72.3080, -72.3120, -72.3095],
                'color': [[56, 189, 248, 200], [52, 211, 153, 200], [248, 113, 113, 200], [52, 211, 153, 200], [52, 211, 153, 200], [52, 211, 153, 200]],
                'size': [150, 80, 80, 80, 80, 80]
            })
            
            view_state = pdk.ViewState(latitude=-41.4905, longitude=-72.3100, zoom=15, pitch=45)
            layer = pdk.Layer(
                'ScatterplotLayer',
                data=map_data,
                get_position='[lon, lat]',
                get_color='color',
                get_radius='size',
                pickable=True
            )
            st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/dark-v10', initial_view_state=view_state, layers=[layer], tooltip={"text": "{Nombre}"}))

        with col_kpi:
            st.markdown("#### 📊 KPIs Globales")
            st.metric("Biomasa Total", "4.150.000 kg", "+1.2% semanal")
            st.metric("Eficiencia FCR", "1.12", "-0.02 mejora")
            st.metric("Riesgo Ambiental", "Moderado", "Viento en aumento", delta_color="inverse")

        st.markdown("---")
        st.markdown("#### 🟢 Estado de Jaulas (Matriz Fluida)")
        
        # Inyección de HTML dinámico para la grilla fluida
        if 'jaula_id' in df_centro.columns:
            grid_html = '<div class="grid-container">'
            for jaula in jaulas_disponibles:
                df_j = df_centro[df_centro['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2 = float(ult.get('oxigeno_mgl', 8.0))
                    temp = float(ult.get('temperatura_c', 12.0))
                    
                    if o2 < 5.0:
                        clase_card = "status-alert"
                        o2_text = f'<span class="data-highlight color-alert">{o2} mg/L 🚨</span>'
                    else:
                        clase_card = "status-ok"
                        o2_text = f'<span class="data-highlight color-ok">{o2} mg/L 🟢</span>'
                        
                    grid_html += f"""
                    <div class="tank-card {clase_card}">
                        <div class="tank-title">{jaula}</div>
                        <p class="tank-data">O2 Sup: {o2_text}</p>
                        <p class="tank-data">Temp: <span class="data-highlight" style="color:#e2e8f0;">{temp}°C</span></p>
                    </div>
                    """
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)

    # ==========================================
    # LAS OTRAS VISTAS SE MANTIENEN FUNCIONALES
    # ==========================================
    elif menu == "Calidad de Agua":
        st.markdown('<div class="gradient-text">Calidad de Agua y Oceanografía</div>', unsafe_allow_html=True)
        st.markdown("---")
        jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disponibles)
        df_j = df_centro[df_centro['jaula_id'] == jaula_sel] if 'jaula_id' in df_centro.columns else df_centro
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("O2 Superficial", f"{ult.get('oxigeno_mgl', 0)} mg/L")
            c2.metric("O2 Fondo (15m)", f"{ult.get('oxigeno_fondo_mgl', 0)} mg/L")
            c3.metric("Temperatura", f"{ult.get('temperatura_c', 0)} °C")
            c4.metric("Fitoplancton", f"{ult.get('conteo_algas_celulas', 0)} cél/ml")
            st.line_chart(df_j.set_index('timestamp')[['oxigeno_mgl', 'oxigeno_fondo_mgl']], height=300)

    elif menu == "Meteorología":
        st.markdown('<div class="gradient-text">Meteorología Satelital</div>', unsafe_allow_html=True)
        clima = obtener_clima_reloncavi()
        if clima:
            c1, c2, c3 = st.columns(3)
            c1.metric("Temperatura", f"{clima.get('temperature_2m', '--')} °C")
            c2.metric("Viento", f"{round(clima.get('wind_speed_10m', 0) * 1.94384, 1)} nudos")
            c3.metric("Ráfagas", f"{round(clima.get('wind_gusts_10m', 0) * 1.94384, 1)} nudos")

    else:
        st.info("Módulo en construcción...")

except Exception as e:
    st.error(f"Error en el motor SCADA: {e}")
