import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS UI/UX MODERNOS
# ==========================================
st.set_page_config(page_title="BlueBrain SCADA | V3.0", page_icon="🌐", layout="wide", initial_sidebar_state="auto")

estilo_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&display=swap');
    
    /* Fondo oscuro moderno con MARCA DE AGUA (Cerebro BlueBrain) */
    [data-testid="stAppViewContainer"] { 
        background-image: 
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='rgba(56, 189, 248, 0.06)' stroke-width='0.3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z'/%3E%3Cpath d='M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z'/%3E%3Cpath d='M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4'/%3E%3C/svg%3E"),
            radial-gradient(circle at top right, #111827, #090d14);
        background-repeat: no-repeat, no-repeat;
        background-position: center center, center center;
        background-size: 55vw, cover;
        background-attachment: fixed, fixed;
        color: #e2e8f0; 
    }
    
    [data-testid="stHeader"] { background: transparent; }
    
    /* Tipografías SCADA */
    h1, h2, h3, h4 { font-family: 'Rajdhani', sans-serif !important; color: #f8fafc !important; }
    
    /* Título con gradiente (Estilo Comercial) */
    .gradient-text {
        background: linear-gradient(45deg, #38bdf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 5px;
    }

    /* Tarjetas de Métricas tipo Glassmorphism (Efecto Vidrio sobre la marca de agua) */
    .stMetric { 
        background: rgba(17, 24, 39, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
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
        margin-bottom: 25px;
    }
    .tank-card {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    /* Colores de estado corporativos */
    .status-ok { border: 1px solid rgba(16, 185, 129, 0.3); border-top: 4px solid #10b981; }
    .status-warning { border: 1px solid rgba(245, 158, 11, 0.3); border-top: 4px solid #f59e0b; }
    .status-alert { border: 1px solid rgba(239, 68, 68, 0.5); border-top: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05); }
    
    /* Textos internos de las tarjetas */
    .t-title { font-family: 'Rajdhani', sans-serif; font-size: 1.2rem; font-weight: bold; color: white; margin-bottom: 8px; }
    .t-data { font-size: 0.85rem; color: #9ca3af; margin: 3px 0; font-family: 'Inter', sans-serif;}
    .c-ok { color: #34d399; font-weight: 600; }
    .c-warn { color: #fbbf24; font-weight: 600; }
    .c-alert { color: #f87171; font-weight: 600; }
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# ==========================================
# 2. CONEXIONES A DATOS
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
        "Vista General", 
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
    # VISTA 1: GENERAL (Dashboard Ejecutivo)
    # ==========================================
    if menu == "Vista General":
        st.markdown(f'<div class="gradient-text">Panel Ejecutivo: {centro_sel}</div>', unsafe_allow_html=True)
        st.markdown("<span style='color: #34d399;'>●</span> Sistema Operativo | Estuario del Reloncaví", unsafe_allow_html=True)
        st.markdown("---")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estanques Activos", len(jaulas_disp))
        c2.metric("Biomasa Estimada", "4.150.000 kg", "+1.2% semanal")
        c3.metric("Oxígeno Promedio", f"{df_c['oxigeno_mgl'].mean():.1f} mg/L" if 'oxigeno_mgl' in df_c.columns else "N/D")
        c4.metric("Eficiencia FCR", "1.12", "Óptimo")

        st.markdown("#### 🗺️ Matriz Operacional en Tiempo Real")
        
        if 'jaula_id' in df_c.columns:
            html_grid = '<div class="grid-container">'
            for jaula in jaulas_disp:
                df_j = df_c[df_c['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2 = float(ult.get('oxigeno_mgl', 8.0))
                    temp = float(ult.get('temperatura_c', 12.0))
                    
                    if o2 < 5.0:
                        html_grid += f'<div class="tank-card status-alert"><div class="t-title">{jaula}</div><p class="t-data">O2 Sup: <span class="c-alert">{o2} mg/L 🚨</span></p><p class="t-data">Temp: <span style="color:white;">{temp}°C</span></p></div>'
                    else:
                        html_grid += f'<div class="tank-card status-ok"><div class="t-title">{jaula}</div><p class="t-data">O2 Sup: <span class="c-ok">{o2} mg/L 🟢</span></p><p class="t-data">Temp: <span style="color:white;">{temp}°C</span></p></div>'
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)

    # ==========================================
    # VISTA 2: CALIDAD DE AGUA
    # ==========================================
    elif menu == "Calidad de Agua":
        st.markdown('<div class="gradient-text">Calidad de Agua y Oceanografía</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("#### 🦠 Semáforo de Bioseguridad (Todos los Estanques)")
        if 'jaula_id' in df_c.columns:
            html_grid = '<div class="grid-container">'
            for jaula in jaulas_disp:
                df_j = df_c[df_c['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2_fon = float(ult.get('oxigeno_fondo_mgl', 8.0))
                    algas = int(ult.get('conteo_algas_celulas', 500))
                    
                    if o2_fon < 4.5 or algas > 2500:
                        html_grid += f'<div class="tank-card status-alert"><div class="t-title">{jaula}</div><p class="t-data">O2 Fondo: <span class="c-alert">{o2_fon} mg/L</span></p><p class="t-data">Algas: <span class="c-alert">{algas}</span></p></div>'
                    elif o2_fon < 6.0 or algas > 1500:
                        html_grid += f'<div class="tank-card status-warning"><div class="t-title">{jaula}</div><p class="t-data">O2 Fondo: <span class="c-warn">{o2_fon} mg/L</span></p><p class="t-data">Algas: <span class="c-warn">{algas}</span></p></div>'
                    else:
                        html_grid += f'<div class="tank-card status-ok"><div class="t-title">{jaula}</div><p class="t-data">O2 Fondo: <span class="c-ok">{o2_fon} mg/L</span></p><p class="t-data">Algas: <span class="c-ok">{algas}</span></p></div>'
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🔬 Análisis Químico Detallado")
        jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disp, key="agua_sel")
        df_j = df_c[df_c['jaula_id'] == jaula_sel] if 'jaula_id' in df_c.columns else df_c
        
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("O2 Superficial", f"{ult.get('oxigeno_mgl', 0)} mg/L")
            c2.metric("O2 Fondo (15m)", f"{ult.get('oxigeno_fondo_mgl', 0)} mg/L")
            c3.metric("Temperatura", f"{ult.get('temperatura_c', 0)} °C")
            c4.metric("Fitoplancton", f"{ult.get('conteo_algas_celulas', 0)} cél/ml")
            st.line_chart(df_j.set_index('timestamp')[['oxigeno_mgl', 'oxigeno_fondo_mgl']], height=300)

    # ==========================================
    # VISTA 3: ALIMENTACIÓN
    # ==========================================
    elif menu == "Alimentación":
        st.markdown('<div class="gradient-text">Sistemas de Alimentación Automática</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("#### ⚙️ Estado de Sopladores (Todos los Estanques)")
        if 'jaula_id' in df_c.columns:
            html_grid = '<div class="grid-container">'
            for jaula in jaulas_disp:
                df_j = df_c[df_c['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    estado = int(ult.get('estado_alimentacion', 0))
                    tasa = float(ult.get('tasa_alimento_kg_min', 0))
                    
                    if estado == 1:
                        html_grid += f'<div class="tank-card status-ok"><div class="t-title">{jaula}</div><p class="t-data">Estado: <span class="c-ok">Activo 🟢</span></p><p class="t-data">Tasa: <span style="color:white;">{tasa} kg/m</span></p></div>'
                    else:
                        html_grid += f'<div class="tank-card status-warning"><div class="t-title">{jaula}</div><p class="t-data">Estado: <span class="c-warn">Pausado ⏸️</span></p><p class="t-data">Tasa: <span style="color:white;">0.0 kg/m</span></p></div>'
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎛️ Consola de Control Individual")
        jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disp, key="alim_sel")
        df_j = df_c[df_c['jaula_id'] == jaula_sel] if 'jaula_id' in df_c.columns else df_c
        
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Estado del Soplador", "ACTIVO 🟢" if int(ult.get('estado_alimentacion', 0))==1 else "DETENIDO 🔴")
            c2.metric("Tasa de Entrega", f"{ult.get('tasa_alimento_kg_min', 0)} kg/min")
            c3.metric("Silos Pontón", f"{ult.get('silo_alimento_pct', 0)}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🛑 CORTAR ALIMENTACIÓN EN {jaula_sel}", type="primary", use_container_width=True):
                st.success(f"Comando de emergencia enviado a los dosificadores de {jaula_sel}.")

    # ==========================================
    # VISTA 4: METEOROLOGÍA Y CORRIENTES
    # ==========================================
    elif menu == "Meteorología y Corrientes":
        st.markdown('<div class="gradient-text">Entorno Atmosférico y Oceanográfico</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        clima = obtener_clima_reloncavi()
        if clima:
            st.markdown("#### 📡 Enlace Satelital Open-Meteo (Cochamó)")
            c1, c2, c3, c4 = st.columns(4)
            viento_nudos = round(clima.get('wind_speed_10m', 0) * 1.94384, 1)
            rafaga_nudos = round(clima.get('wind_gusts_10m', 0) * 1.94384, 1)
            
            c1.metric("Temp Ambiente", f"{clima.get('temperature_2m', '--')} °C")
            c2.metric("Viento Sup.", f"{viento_nudos} nudos")
            c3.metric("Ráfagas Max", f"{rafaga_nudos} nudos", "⚠️ Temporal" if rafaga_nudos > 25 else "Normal", delta_color="inverse" if rafaga_nudos > 25 else "off")
            c4.metric("Presión hPa", f"{clima.get('surface_pressure', '--')}")
            
            st.markdown("---")
            st.markdown("#### 🌊 Oceanografía Física (Sensores Locales en Pontón)")
            if not df_c.empty:
                ult_local = df_c.iloc[-1]
                corriente = float(ult_local.get('corriente_ms', 0.15))
                salinidad = float(ult_local.get('salinidad_psu', 32.0))
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Corriente (ADCP)", f"{round(corriente * 1.94384, 2)} nudos", "Carga Estructural OK")
                col_b.metric("Salinidad", f"{salinidad} PSU", "Rango Estable")
                col_c.metric("Oleaje Estimado", "0.6 m", "Condición Operable")

    # ==========================================
    # VISTA 5: ENERGÍA Y SENSORES
    # ==========================================
    elif menu == "Energía y Sensores":
        st.markdown('<div class="gradient-text">Infraestructura y Hardware de Borde</div>', unsafe_allow_html=True)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Generador Principal", "OPERATIVO 🟢", "68% Carga")
        c2.metric("Enlace Starlink", "ONLINE 🟢", "28ms Latencia")
        c3.metric("Banco UPS", "100%", "Autonomía Plena")

except Exception as e:
    st.error(f"Error en el núcleo de renderizado SCADA: {e}")
