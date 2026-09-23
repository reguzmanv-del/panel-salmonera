import streamlit as st
import pandas as pd
import requests

# 1. Configuración de la página (Adaptativa para móviles)
st.set_page_config(
    page_title="BlueBrain SCADA | Control Total",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="auto" # <-- Ajuste para que se oculte en celulares automáticamente
)

# 2. Estilos CSS industriales y de Alto Contraste
st.markdown("""
    <style>
    /* Fondos oscuros */
    .main, [data-testid="stAppViewContainer"] { background-color: #0b0f19; color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
    
    /* Cajas de métricas */
    .stMetric { background-color: #111827; padding: 12px; border-radius: 6px; border: 1px solid #1f2937; }
    
    /* FORZAR CONTRASTE DE NÚMEROS Y TEXTOS EN MÓVILES */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #a1a1aa !important; }
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif; color: #f8fafc !important; font-weight: 600; }
    p, span, div { color: #f8fafc; }
    
    /* Tarjetas de estado de tanques */
    .tank-card-normal { background-color: #111827; border: 2px solid #10b981; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; }
    .tank-card-alert { background-color: #1f1215; border: 2px solid #ef4444; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. Conexiones a Datos
SHEET_URL = "https://docs.google.com/spreadsheets/d/115BG0pdWQxVlLVozHzI_ken4P0El_fZar_GTu3cRsus/export?format=csv"

@st.cache_data(ttl=5)
def cargar_datos():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    return df

@st.cache_data(ttl=600)
def obtener_clima_reloncavi():
    try:
        lat, lon = -41.49, -72.31
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure&wind_speed_unit=ms&timezone=America%2FSantiago"
        respuesta = requests.get(url, timeout=5).json()
        return respuesta.get('current', None)
    except:
        return None

try:
    df = cargar_datos()
    
    # Limpieza
    cols_numericas = ['oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c', 'salinidad_psu', 'corriente_ms', 'estado_alimentacion', 'tasa_alimento_kg_min', 'conteo_algas_celulas', 'mortalidad_dia', 'silo_alimento_pct']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # 4. BARRA LATERAL SCADA
    st.sidebar.markdown("### 🔵 BlueBrain RAS")
    st.sidebar.markdown("**Módulo Central - Estuario**")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Navegación", [
        "Vista General (Matriz)", 
        "Calidad de Agua", 
        "Alimentación", 
        "Meteorología y Entorno",
        "Energía y Sensores"
    ])
    
    st.sidebar.markdown("---")
    centros = df['centro_id'].dropna().unique() if 'centro_id' in df.columns else ["Pontón Alfa"]
    centro_seleccionado = st.sidebar.selectbox("Centro Activo", centros)
    df_centro = df[df['centro_id'] == centro_seleccionado] if 'centro_id' in df.columns else df
    jaulas_disponibles = df_centro['jaula_id'].dropna().unique() if 'jaula_id' in df_centro.columns else ["TK.01"]

    # ==========================================
    # VISTA 1: VISTA GENERAL (MATRIZ)
    # ==========================================
    if menu == "Vista General (Matriz)":
        st.markdown(f"## Módulo RAS - Control de Estanques ({centro_seleccionado})")
        st.markdown(f"<span style='color: #10b981;'>●</span> Monitoreo en línea activo | Protocolo SCADA V2", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### 🗺️ Mapa Operacional - Retícula de Estanques")
        
        if 'jaula_id' in df_centro.columns:
            cols_grid = st.columns(5)
            for i, jaula in enumerate(jaulas_disponibles):
                df_j = df_centro[df_centro['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2 = float(ult.get('oxigeno_mgl', 8.0))
                    temp_j = float(ult.get('temperatura_c', 12.0))
                    
                    with cols_grid[i % 5]:
                        if o2 < 5.0:
                            st.markdown(f'<div class="tank-card-alert"><strong>{jaula}</strong><br><span style="color:#ef4444; font-size:12px;">🚨 O2: {o2} mg/L</span><br><span style="font-size:11px; color:#9ca3af;">Temp: {temp_j}°C</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="tank-card-normal"><strong>{jaula}</strong><br><span style="color:#10b981; font-size:12px;">🟢 O2: {o2} mg/L</span><br><span style="font-size:11px; color:#9ca3af;">Temp: {temp_j}°C</span></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Estanques Activos", len(jaulas_disponibles))
        c2.metric("Biomasa Estimada", "4.150.000 kg")
        c3.metric("Oxígeno Promedio", f"{df_centro['oxigeno_mgl'].mean():.1f} mg/L" if 'oxigeno_mgl' in df_centro.columns else "N/D")
        c4.metric("pH Promedio", "7.12")
        c5.metric("Mortalidad Acumulada", f"{df_centro['mortalidad_dia'].sum() if 'mortalidad_dia' in df_centro.columns else 0} peces")

    # ==========================================
    # VISTA METEOROLÓGICA
    # ==========================================
    elif menu == "Meteorología y Entorno":
        st.markdown(f"## 🌦️ Condiciones Meteorológicas y Oceanográficas")
        st.markdown("**Ubicación:** Estuario del Reloncaví, Sector Cochamó (Lat: 41°29'S, Lon: 72°18'W)")
        st.info("🌐 Conectado en tiempo real a la red satelital de Open-Meteo API.")
        st.markdown("---")

        clima = obtener_clima_reloncavi()
        
        if clima:
            temp_ext = clima.get('temperature_2m', '--')
            viento_ms = clima.get('wind_speed_10m', 0)
            viento_nudos = round(viento_ms * 1.94384, 1)
            rafaga_nudos = round(clima.get('wind_gusts_10m', 0) * 1.94384, 1)
            dir_viento = clima.get('wind_direction_10m', '--')
            presion = clima.get('surface_pressure', '--')

            st.markdown("#### 📡 Telemetría Atmosférica en Superficie")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temperatura Ambiente", f"{temp_ext} °C")
            c2.metric("Velocidad del Viento", f"{viento_nudos} nudos", f"Dir: {dir_viento}°", delta_color="off")
            
            if rafaga_nudos > 25:
                c3.metric("Ráfagas Máximas", f"{rafaga_nudos} nudos", "⚠️ Temporal", delta_color="inverse")
            else:
                c3.metric("Ráfagas Máximas", f"{rafaga_nudos} nudos", "Normal", delta_color="off")
                
            c4.metric("Presión Atmosférica", f"{presion} hPa")

            st.markdown("---")
            st.markdown("#### 🌊 Oceanografía Física (Sensores Locales)")
            if not df_centro.empty:
                ult_local = df_centro.iloc[-1]
                corriente = float(ult_local.get('corriente_ms', 0.15))
                corriente_nudos = round(corriente * 1.94384, 2)
                salinidad = float(ult_local.get('salinidad_psu', 32.0))
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Corriente Submarina (ADCP)", f"{corriente_nudos} nudos", "Carga OK")
                col_b.metric("Salinidad Superficial", f"{salinidad} PSU", "Pluma dulce" if salinidad < 25 else "Estable")
                col_c.metric("Altura de Ola Estimada", "0.6 m", "Mar rizada")
        else:
            st.error("No se pudo establecer conexión con el satélite meteorológico. Verificando enlaces de red...")

    # ==========================================
    # VISTAS RESTANTES
    # ==========================================
    elif menu == "Calidad de Agua":
        st.markdown("## 🧪 Panel de Calidad de Agua")
        st.info("Selecciona un estanque para ver el detalle en profundidad de la columna de agua.")
        jaula_sel = st.selectbox("Seleccionar Estanque:", jaulas_disponibles)
        df_j = df_centro[df_centro['jaula_id'] == jaula_sel] if 'jaula_id' in df_centro.columns else df_centro
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("O2 Superficial", f"{ult.get('oxigeno_mgl', 0)} mg/L")
            c2.metric("O2 Fondo (15m)", f"{ult.get('oxigeno_fondo_mgl', 0)} mg/L")
            c3.metric("Temperatura", f"{ult.get('temperatura_c', 0)} °C")
            c4.metric("Fitoplancton", f"{ult.get('conteo_algas_celulas', 0)} cél/ml")
            st.line_chart(df_j.set_index('timestamp')[['oxigeno_mgl', 'temperatura_c']], height=300)

    elif menu == "Alimentación":
        st.markdown("## 🍽️ Control de Alimentación y Silos")
        jaula_sel = st.selectbox("Seleccionar Estanque:", jaulas_disponibles)
        df_j = df_centro[df_centro['jaula_id'] == jaula_sel] if 'jaula_id' in df_centro.columns else df_centro
        if not df_j.empty:
            ult = df_j.iloc[-1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Sopladores", "ACTIVO 🟢" if int(ult.get('estado_alimentacion', 0))==1 else "DETENIDO 🔴")
            c2.metric("Tasa Entrega", f"{ult.get('tasa_alimento_kg_min', 0)} kg/min")
            c3.metric("Silos Pontón", f"{ult.get('silo_alimento_pct', 0)}%")

    elif menu == "Energía y Sensores":
        st.markdown("## ⚡ Infraestructura y Conectividad")
        c1, c2, c3 = st.columns(3)
        c1.metric("Generador Principal", "OPERATIVO 🟢", "68% carga")
        c2.metric("Enlace Starlink", "ONLINE", "28ms latencia")
        c3.metric("Baterías UPS", "100%", "Autonomía plena")

except Exception as e:
    st.error(f"Error crítico en el sistema SCADA: {e}")
