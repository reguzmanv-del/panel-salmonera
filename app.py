import streamlit as st
import pandas as pd

# 1. Configuración de la página (Modo Ancho)
st.set_page_config(
    page_title="BlueBrain SCADA | Control de Estanques",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos CSS avanzados estilo Industrial / SCADA
st.markdown("""
    <style>
    .main { background-color: #0b0f19; color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
    .stMetric { background-color: #111827; padding: 12px; border-radius: 6px; border: 1px solid #1f2937; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #f8fafc; font-weight: 600; }
    
    /* Tarjetas de estado de tanques estilo grilla industrial */
    .tank-card-normal {
        background-color: #111827;
        border: 2px solid #10b981;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        color: #f8fafc;
        margin-bottom: 10px;
    }
    .tank-card-alert {
        background-color: #1f1215;
        border: 2px solid #ef4444;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        color: #f8fafc;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Enlace de tu Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/115BG0pdWQxVlLVozHzI_ken4P0El_fZar_GTu3cRsus/export?format=csv"

@st.cache_data(ttl=5)
def cargar_datos():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    return df

try:
    df = cargar_datos()
    
    # Limpieza de datos numéricos
    cols_numericas = [
        'oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c', 'salinidad_psu', 
        'corriente_ms', 'estado_alimentacion', 'tasa_alimento_kg_min', 
        'conteo_algas_celulas', 'mortalidad_dia', 'silo_alimento_pct'
    ]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # 3. BARRA LATERAL ESTILO SCADA
    st.sidebar.markdown("### 🔵 BlueBrain RAS")
    st.sidebar.markdown("**Módulo Central - Estanques**")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Navegación", ["Vista General (Matriz)", "Calidad de Agua", "Alimentación", "Energía y Sensores"])
    
    st.sidebar.markdown("---")
    if 'centro_id' in df.columns:
        centros = df['centro_id'].dropna().unique()
        centro_seleccionado = st.sidebar.selectbox("Centro Activo", centros)
        df_centro = df[df['centro_id'] == centro_seleccionado]
    else:
        df_centro = df
        centro_seleccionado = "Pontón Principal"

    # Encabezado Superior Estilo Dashboard Industrial
    st.markdown(f"## Módulo RAS - Control de Estanques ({centro_seleccionado})")
    st.markdown(f"<span style='color: #10b981;'>●</span> Monitoreo en línea activo | Protocolo SCADA V2", unsafe_allow_html=True)
    st.markdown("---")

    if menu == "Vista General (Matriz)":
        st.markdown("#### 🗺️ Mapa Operacional - Retícula de Estanques")
        st.markdown("Estado en tiempo real de cada estanque/jaula del módulo:")

        # Si tenemos múltiples jaulas, creamos la grilla estilo la foto
        if 'jaula_id' in df_centro.columns:
            jaulas = df_centro['jaula_id'].dropna().unique()
            
            # Dibujar en filas de 5 columnas estilo grilla industrial
            cols_grid = st.columns(5)
            for i, jaula in enumerate(jaulas):
                df_j = df_centro[df_centro['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2 = float(ult.get('oxigeno_mgl', 8.0))
                    temp_j = float(ult.get('temperatura_c', 12.0))
                    
                    with cols_grid[i % 5]:
                        if o2 < 5.0:
                            st.markdown(f"""
                                <div class="tank-card-alert">
                                    <strong>{jaula}</strong><br>
                                    <span style="color:#ef4444; font-size:12px;">🚨 O2: {o2} mg/L</span><br>
                                    <span style="font-size:11px; color:#9ca3af;">Temp: {temp_j}°C</span>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div class="tank-card-normal">
                                    <strong>{jaula}</strong><br>
                                    <span style="color:#10b981; font-size:12px;">🟢 O2: {o2} mg/L</span><br>
                                    <span style="font-size:11px; color:#9ca3af;">Temp: {temp_j}°C</span>
                                </div>
                            """, unsafe_allow_html=True)
        else:
            st.info("Agrega la columna `jaula_id` en tu Google Sheet (ej. TK.01, TK.02, TK.03) para ver la retícula completa estilo BlueBrain.")

        st.markdown("---")
        st.markdown("#### Resumen del Módulo")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Estanques Activos", len(df_centro['jaula_id'].unique()) if 'jaula_id' in df_centro.columns else 1)
        c2.metric("Biomasa Estimada", "4.150.000 kg")
        c3.metric("Oxígeno Promedio", f"{df_centro['oxigeno_mgl'].mean():.1f} mg/L" if 'oxigeno_mgl' in df_centro.columns else "N/D")
        c4.metric("pH Promedio", "7.12")
        c5.metric("CO2 Disuelto", "11.2 mg/L")

    else:
        # Vistas detalladas para las otras pestañas del menú lateral
        if 'jaula_id' in df_centro.columns:
            jaulas = df_centro['jaula_id'].dropna().unique()
            jaula_seleccionada = st.selectbox("Seleccionar estanque específico para análisis:", jaulas)
            df_actual = df_centro[df_centro['jaula_id'] == jaula_seleccionada]
        else:
            df_actual = df_centro
            jaula_seleccionada = "Estanque General"

        if not df_actual.empty:
            actual = df_actual.iloc[-1]
            st.markdown(f"### Parámetros detallados para: {jaula_seleccionada}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Oxígeno Superficial", f"{actual.get('oxigeno_mgl', 0)} mg/L")
            col2.metric("Temperatura", f"{actual.get('temperatura_c', 0)} °C")
            col3.metric("Tasa Alimentación", f"{actual.get('tasa_alimento_kg_min', 0)} kg/min")
            col4.metric("Fitoplancton", f"{actual.get('conteo_algas_celulas', 0)} cél/ml")

            st.markdown("#### Tendencia Histórica")
            cols_graf = [c for c in ['oxigeno_mgl', 'temperatura_c'] if c in df_actual.columns]
            if cols_graf:
                st.line_chart(df_actual.set_index('timestamp')[cols_graf], height=350)
        else:
            st.warning("No hay registros para la selección actual.")

except Exception as e:
    st.error(f"Error al cargar la interfaz SCADA: {e}")
