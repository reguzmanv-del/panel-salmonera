import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(
    page_title="SCADA Salmonera | Control Total",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS industriales
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; color: #f0f6fc; }
    </style>
""", unsafe_allow_html=True)

st.title("🌊 Centro de Control Multi-Jaula y Oceanografía")
st.markdown("**Plataforma Integrada de Telemetría, Variables Ambientales y Logística de Cultivo**")
st.markdown("---")

# Enlace de tu Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/115BG0pdWQxVlLVozHzI_ken4P0El_fZar_GTu3cRsus/export?format=csv"

@st.cache_data(ttl=5)
def cargar_datos():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    return df

try:
    df = cargar_datos()
    
    # Limpieza general de columnas numéricas si existen
    cols_numericas = [
        'oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c', 'salinidad_psu', 
        'corriente_ms', 'estado_alimentacion', 'tasa_alimento_kg_min', 
        'conteo_algas_celulas', 'mortalidad_dia', 'silo_alimento_pct'
    ]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # 2. PANEL LATERAL: Selector de Centro y Jaula / Estanque
    st.sidebar.header("🎛️ Selector de Cultivo")
    
    if 'centro_id' in df.columns:
        centros = df['centro_id'].dropna().unique()
        centro_seleccionado = st.sidebar.selectbox("Seleccionar Centro", centros)
        df_centro = df[df['centro_id'] == centro_seleccionado]
    else:
        df_centro = df

    if 'jaula_id' in df_centro.columns:
        jaulas = df_centro['jaula_id'].dropna().unique()
        jaula_seleccionada = st.sidebar.selectbox("Seleccionar Jaula / Estanque", jaulas)
        df_actual = df_centro[df_centro['jaula_id'] == jaula_seleccionada]
    else:
        jaula_seleccionada = "Jaula General"
        df_actual = df_centro

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Consejo:** Asegúrate de que tu Google Sheet tenga las columnas `centro_id` y `jaula_id` para aprovechar el selector múltiple.")

    # Tomar la última fila de la jaula seleccionada
    if not df_actual.empty:
        actual = df_actual.iloc[-1]
        
        oxigeno_sup = float(actual.get('oxigeno_mgl', 8.0))
        oxigeno_fon = float(actual.get('oxigeno_fondo_mgl', 7.5))
        temp = float(actual.get('temperatura_c', 12.0))
        salinidad = float(actual.get('salinidad_psu', 32.0))
        corriente = float(actual.get('corriente_ms', 0.15))
        alimentacion = int(actual.get('estado_alimentacion', 0))
        tasa = float(actual.get('tasa_alimento_kg_min', 0.0))
        algas = int(actual.get('conteo_algas_celulas', 500))
        mortalidad = int(actual.get('mortalidad_dia', 0))
        silo = float(actual.get('silo_alimento_pct', 80.0))

        # 3. Alertas Inteligentes Cruzadas
        if oxigeno_sup < 5.0 and alimentacion == 1:
            st.error(f"🚨 **ALERTA CRÍTICA EN {jaula_seleccionada}:** Oxígeno superficial en **{oxigeno_sup} mg/L** con sopladores activos.")
            if st.button("🛑 CORTAR ALIMENTACIÓN DE ESTA JAULA", type="primary"):
                st.warning(f"Señal de parada enviada a los sopladores de {jaula_seleccionada}.")
        
        if oxigeno_fon < 4.5:
            st.warning(f"⚠️ **Riesgo en Columna de Fondo:** El oxígeno a 15 metros cayó a {oxigeno_fon} mg/L. Posible acumulación orgánica.")

        # 4. KPIs Principales Organizados por Capas
        st.markdown(f"### 📊 Estado Actual: *{jaula_seleccionada}*")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Oxígeno Superficial", f"{oxigeno_sup} mg/L", "Crítico" if oxigeno_sup < 5.0 else "Óptimo", delta_color="inverse")
        col2.metric("Oxígeno de Fondo (15m)", f"{oxigeno_fon} mg/L", "Alerta" if oxigeno_fon < 4.5 else "Normal", delta_color="inverse")
        col3.metric("Temperatura / Salinidad", f"{temp} °C", f"{salinidad} PSU")
        col4.metric("Corriente Marina", f"{corriente} m/s", "Hidrodinámica OK")

        st.markdown("#### ⚙️ Capa Operativa y Sanitaria")
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Estado Alimentación", "ACTIVO 🟢" if alimentacion == 1 else "DETENIDO 🔴", f"{tasa} kg/min")
        col6.metric("Fitoplancton (Algas)", f"{algas:,} cél/ml", "Bloom Nocivo" if algas > 2500 else "Normal")
        col7.metric("Mortalidad Diaria", f"{mortalidad} peces", "Revisar Red" if mortalidad > 10 else "Estable")
        col8.metric("Silos de Alimento (Pontón)", f"{silo}%", "Reabastecer" if silo < 20 else "Suficiente")

        # 5. Pestañas de Análisis Histórico
        st.markdown("---")
        tab_tendencias, tab_logistica = st.tabs(["📈 Tendencias Oceanográficas", "📋 Base de Datos Completa"])

        with tab_tendencias:
            st.markdown(f"#### Comportamiento histórico para {jaula_seleccionada}")
            cols_a_graficar = [c for c in ['oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c'] if c in df_actual.columns]
            if cols_a_graficar:
                st.line_chart(df_actual.set_index('timestamp')[cols_a_graficar], height=350)

        with tab_logistica:
            st.dataframe(df_actual, use_container_width=True)
    else:
        st.info("No hay datos disponibles para la selección actual en el Google Sheet.")

except Exception as e:
    st.error(f"Error al procesar la estructura de datos multijaula: {e}")
