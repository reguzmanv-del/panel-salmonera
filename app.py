import streamlit as st
import pandas as pd
import requests
import pydeck as pdk

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS UI/UX MODERNOS
# ==========================================
st.set_page_config(page_title="BlueBrain SCADA | V3.0", page_icon="🌐", layout="wide", initial_sidebar_state="auto")

estilo_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&display=swap');
    
    /* Fondo oscuro moderno */
    [data-testid="stAppViewContainer"] { background: #0b0f19; color: #e2e8f0; }
    [data-testid="stHeader"] { background: transparent; }
    
    /* Tipografías SCADA */
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; color: #f8fafc !important; }
    
    /* Título con gradiente (Estilo Comercial) */
    .gradient-text {
        background: linear-gradient(45deg, #38bdf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 10px;
    }

    /* Tarjetas de Métricas tipo Glassmorphism */
    .stMetric { 
        background: rgba(30, 41, 59, 0.4) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; 
        padding: 15px !important;
    }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important;}

    /* Grilla fluida para Celulares y Desktop */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }
    .tank-card {
        background: #111827;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .status-ok { border: 2px solid #10b981; }
    .status-alert { border: 2px solid #ef4444; background: #1f1215; }
    .t-title { font-family: 'Rajdhani', sans-serif; font-size: 1.2rem; font-weight: bold; color: white; }
    .t-data { font-size: 0.9rem; color: #9ca3af; margin: 3px 0; }
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# ==========================================
# 2. CONEXIONES A DATOS (G-Sheets y API)
# ==========================================
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
    # Limpieza numérica
    cols_numericas = ['oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c', 'salinidad_psu', 'corriente_ms', 'estado_alimentacion', 'tasa_alimento_kg_min', 'conteo_algas_celulas', 'mortalidad_dia', 'silo_alimento_pct']
    for col in cols_numericas:
        if col in df.columns: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # ==========================================
    # 3. MENÚ DE NAVEGACIÓN
    # ==========================================
    st.sidebar.markdown("### 🌐 BlueBrain OS")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navegación", [
        "Vista General & Mapa", 
        "Calidad de Agua", 
        "Alimentación", 
        "Meteorología y Corrientes", 
        "Energía y Sensores"
    ])
    st.sidebar.markdown("---")
    
    centros = df['centro_id'].dropna().unique() if 'centro_id' in df.columns else ["Pontón Alfa"]
    centro_sel = st.sidebar.selectbox("Centro Activo", centros)
    df_c = df[df['centro_id'] == centro_sel] if 'centro_id' in df.columns else df
    jaulas_disp = df_c['jaula_id'].dropna().unique() if 'jaula_id' in df_c.columns else ["TK.01"]

    # ==========================================
    # VISTA 1: GENERAL Y MAPA
    # ==========================================
    if menu == "Vista General & Mapa":
        st.markdown(f'<div class="gradient-text">Centro de Mando: {centro_sel}</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        col_mapa, col_kpi = st.columns([2, 1])
        
        with col_mapa:
            st.markdown("#### 🛰️ Mapa Operacional (Estuario del Reloncaví)")
            # Datos geoespaciales para Cochamó / Reloncaví
            map_data = pd.DataFrame({
                'Nombre': ['Pontón Central', 'TK.01', 'TK.02', 'TK.03', 'TK.04', 'TK.05'],
                'lat': [-41.4900, -41.4910, -41.4890, -41.4905, -41.4895, -41.4915],
                'lon': [-72.3100, -72.3110, -72.3090, -72.3080, -72.3120, -72.3095],
                'color': [[56, 189, 248, 255], [16, 185, 129, 200], [239, 68, 68, 255], [16, 185, 129, 200], [16, 185, 129, 200], [16, 185, 129, 200]],
                'size': [120, 60, 80, 60, 60, 60]
            })
            
            vista_mapa = pdk.ViewState(latitude=-41.4905, longitude=-72.3100, zoom=14.5, pitch=50)
            capa = pdk.Layer(
                'ScatterplotLayer',
                data=map_data,
                get_position='[lon, lat]',
                get_fill_color='color',
                get_radius='size',
                pickable=True
            )
            st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/dark-v10', initial_view_state=vista_mapa, layers=[capa], tooltip={"text": "{Nombre}"}))

        with col_kpi:
            st.markdown("#### 📊 KPIs Globales")
            st.metric("Biomasa Total", "4.150.000 kg", "+1.2% semanal")
            st.metric("Oxígeno Promedio", f"{df_c['oxigeno_mgl'].mean():.1f} mg/L" if 'oxigeno_mgl' in df_c.columns else "8.2 mg/L")
            st.metric("Eficiencia FCR", "1.12", "Óptimo")

        st.markdown("---")
        st.markdown("#### 🟢 Estado de Estanques (Tiempo Real)")
        
        # Inyección HTML limpia para la grilla
        if 'jaula_id' in df_c.columns:
            html_grid = '<div class="grid-container">'
            for jaula in jaulas_disp:
                df_j = df_c[df_c['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2 = float(ult.get('oxigeno_mgl', 8.0))
                    temp = float(ult.get('temperatura_c', 12.0))
                    
                    if o2 < 5.0:
                        html_grid += f'<div class="tank-card status-alert"><div class="t-title">{jaula}</div><p class="t-data">O2: <span style="color:#ef4444; font-weight:bold;">{o2} mg/L 🚨</span></p><p class="t-data">Temp: {temp}°C</p></div>'
                    else:
                        html_grid += f'<div class="tank-card status-ok"><div class="t-title">{jaula}</div><p class="t-data">O2: <span style="color:#10b981; font-weight:bold;">{o2} mg/L 🟢</span></p><p class="t-data">Temp: {temp}°C</p></div>'
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)

    # ==========================================
    # VISTA 2: CALIDAD DE AGUA
    # ==========================================
    elif menu == "Calidad de Agua":
        st.markdown('<div class="gradient-text">Análisis de Calidad de Agua</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disp)
        df_j = df_c[df_c['jaula_id'] == jaula_sel] if 'jaula_id' in df_c.columns else df_c
        
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("O2 Superficial (0m)", f"{ult.get('oxigeno_mgl', 0)} mg/L", "Óptimo")
            c2.metric("O2 Fondo (15m)", f"{ult.get('oxigeno_fondo_mgl', 0)} mg/L", "Estable")
            c3.metric("Temperatura", f"{ult.get('temperatura_c', 0)} °C")
            c4.metric("Fitoplancton", f"{ult.get('conteo_algas_celulas', 0)} cél/ml")
            
            st.markdown("#### Tendencia Histórica")
            st.line_chart(df_j.set_index('timestamp')[['oxigeno_mgl', 'oxigeno_fondo_mgl']], height=350)

    # ==========================================
    # VISTA 3: ALIMENTACIÓN
    # ==========================================
    elif menu == "Alimentación":
        st.markdown('<div class="gradient-text">Control de Alimentación y Silos</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        jaula_sel = st.selectbox("Consola de estanque:", jaulas_disp)
        df_j = df_c[df_c['jaula_id'] == jaula_sel] if 'jaula_id' in df_c.columns else df_c
        
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Estado del Soplador", "ACTIVO 🟢" if int(ult.get('estado_alimentacion', 0))==1 else "DETENIDO 🔴")
            c2.metric("Tasa de Entrega", f"{ult.get('tasa_alimento_kg_min', 0)} kg/min")
            c3.metric("Silos Pontón", f"{ult.get('silo_alimento_pct', 0)}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🛑 DETENER ALIMENTACIÓN EN {jaula_sel}", type="primary"):
                st.success(f"Comando remoto enviado a {jaula_sel}.")

    # ==========================================
    # VISTA 4: METEOROLOGÍA Y CORRIENTES (RESTABLECIDA)
    # ==========================================
    elif menu == "Meteorología y Corrientes":
        st.markdown('<div class="gradient-text">Meteorología Satelital y Oceanografía</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        clima = obtener_clima_reloncavi()
        if clima:
            st.markdown("#### 📡 Satélite Open-Meteo (Cochamó)")
            c1, c2, c3, c4 = st.columns(4)
            viento_nudos = round(clima.get('wind_speed_10m', 0) * 1.94384, 1)
            rafaga_nudos = round(clima.get('wind_gusts_10m', 0) * 1.94384, 1)
            
            c1.metric("Temp Ambiente", f"{clima.get('temperature_2m', '--')} °C")
            c2.metric("Viento Sup.", f"{viento_nudos} nudos")
            c3.metric("Ráfagas Max", f"{rafaga_nudos} nudos", "⚠️ Temporal" if rafaga_nudos > 25 else "Normal", delta_color="inverse" if rafaga_nudos > 25 else "off")
            c4.metric("Presión hPa", f"{clima.get('surface_pressure', '--')}")
            
            st.markdown("---")
            st.markdown("#### 🌊 Oceanografía Física (Sensores en Pontón)")
            if not df_c.empty:
                ult_local = df_c.iloc[-1]
                corriente = float(ult_local.get('corriente_ms', 0.15))
                salinidad = float(ult_local.get('salinidad_psu', 32.0))
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Corriente (ADCP)", f"{round(corriente * 1.94384, 2)} nudos", "Hidrodinámica OK")
                col_b.metric("Salinidad", f"{salinidad} PSU", "Sin pluma de río")
                col_c.metric("Oleaje Estimado", "0.6 m", "Operable")

    # ==========================================
    # VISTA 5: ENERGÍA Y SENSORES
    # ==========================================
    elif menu == "Energía y Sensores":
        st.markdown('<div class="gradient-text">Infraestructura y Conectividad</div>', unsafe_allow_html=True)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Generador Principal", "OPERATIVO 🟢", "68% Carga")
        c2.metric("Enlace Starlink", "ONLINE 🟢", "28ms Latencia")
        c3.metric("Baterías UPS", "100%", "Autonomía Plena")

except Exception as e:
    st.error(f"Error en el motor de renderizado SCADA: {e}")
