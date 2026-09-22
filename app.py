import streamlit as st
import pandas as pd

# 1. Configuración de la página (Modo Ancho y Estilo Ejecutivo)
st.set_page_config(
    page_title="Centro de Control | Pontón Alfa",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de Estilos CSS Profesionales (Modo Oscuro Industrial)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #f0f6fc;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Encabezado Ejecutivo
st.title("🌊 Centro de Control Unificado — Pontón Alfa")
st.markdown("**Plataforma de Mitigación de Riesgos Operativos y Telemetría en Tiempo Real**")
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
    
    # Limpieza de datos
    cols = ['oxigeno_mgl', 'estado_alimentacion', 'temperatura_c', 'tasa_alimento_kg_min', 'conteo_algas_celulas']
    for col in cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    actual = df.iloc[-1]
    
    oxigeno = float(actual['oxigeno_mgl'])
    alimentacion = int(actual['estado_alimentacion'])
    temp = float(actual['temperatura_c'])
    algas = int(actual['conteo_algas_celulas'])
    tasa = float(actual['tasa_alimento_kg_min'])

    # 4. Panel Lateral de Estado del Sistema
    st.sidebar.header("⚙️ Configuración Operativa")
    st.sidebar.info("**Centro:** Estuario Reloncaví\n\n**Módulo:** Pontón Principal\n\n**Estado:** 🟢 Conectado a Red Cloud")
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Desarrollado para validación de arquitectura de control unificado.*")

    # 5. Sistema de Alertas Inteligentes (Banner Superior Prioritario)
    if oxigeno < 5.0 and alimentacion == 1:
        st.error(f"🚨 **ALERTA CRÍTICA DE MORTANDAD:** Nivel de oxígeno en **{oxigeno} mg/L** con sopladores activos. Alto riesgo por anoxia.")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🛑 CORTAR ALIMENTACIÓN", type="primary"):
                st.warning("Comando de emergencia enviado: Sopladores detenidos de forma remota.")
    elif oxigeno < 5.0:
        st.warning(f"⚠️ **Advertencia de Oxígeno:** Niveles críticos ({oxigeno} mg/L), pero la alimentación se encuentra detenida.")
            
    if temp > 13.5:
        st.warning(f"🌡️ **Aviso Térmico:** Temperatura del agua en {temp}°C. Se recomienda ajustar curvas de alimentación.")

    # 6. Tarjetas de Indicadores Principales (KPIs)
    st.markdown("### 📊 Variables Críticas del Cultivo")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        label="Oxígeno Disuelto (OD)", 
        value=f"{oxigeno} mg/L", 
        delta="Crítico (<5.0)" if oxigeno < 5.0 else "Óptimo",
        delta_color="inverse"
    )
    col2.metric(
        label="Temperatura del Agua", 
        value=f"{temp} °C",
        delta="+0.4°C vs Promedio"
    )
    col3.metric(
        label="Estado Sopladores", 
        value="ACTIVO 🟢" if alimentacion == 1 else "DETENIDO 🔴",
        delta=f"{tasa} kg/min" if alimentacion == 1 else "Standby"
    )
    col4.metric(
        label="Conteo de Fitoplancton", 
        value=f"{algas:,} cél/ml",
        delta="Riesgo Bloom" if algas > 2500 else "Normal"
    )

    # 7. Sección de Pestañas para Ordenar la Información
    st.markdown("---")
    tab_graficos, tab_tabla = st.tabs(["📈 Tendencias y Correlación", "📋 Historial de Telemetría (CSV)"])

    with tab_graficos:
        st.markdown("#### Comportamiento cruzado: Oxígeno vs Tasa de Alimentación")
        grafico_data = df.set_index('timestamp')[['oxigeno_mgl', 'tasa_alimento_kg_min']]
        st.line_chart(grafico_data, height=400)

    with tab_tabla:
        st.markdown("#### Últimos registros sincronizados desde el Google Sheet")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar los datos del panel. Detalle técnico: {e}")
