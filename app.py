import streamlit as st
import pandas as pd

# 1. Configuración de la página (Modo Ancho)
st.set_page_config(
    page_title="BlueBrain SCADA | Control Total",
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
    
    # Limpieza de datos numéricos con respaldo por defecto
    cols_numericas = [
        'oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c', 'salinidad_psu', 
        'corriente_ms', 'estado_alimentacion', 'tasa_alimento_kg_min', 
        'conteo_algas_celulas', 'mortalidad_dia', 'silo_alimento_pct'
    ]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # 3. BARRA LATERAL SCADA
    st.sidebar.markdown("### 🔵 BlueBrain RAS")
    st.sidebar.markdown("**Módulo Central - Estanques**")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Navegación", [
        "Vista General (Matriz)", 
        "Calidad de Agua", 
        "Alimentación", 
        "Energía y Sensores"
    ])
    
    st.sidebar.markdown("---")
    if 'centro_id' in df.columns:
        centros = df['centro_id'].dropna().unique()
        centro_seleccionado = st.sidebar.selectbox("Centro Activo", centros)
        df_centro = df[df['centro_id'] == centro_seleccionado]
    else:
        df_centro = df
        centro_seleccionado = "Pontón Principal"

    # Selector global de estanque/jaula para las vistas detalladas
    if 'jaula_id' in df_centro.columns:
        jaulas_disponibles = df_centro['jaula_id'].dropna().unique()
    else:
        jaulas_disponibles = ["Estanque 01", "Estanque 02"]

    # ==========================================
    # VISTA 1: VISTA GENERAL (MATRIZ DE ESTANQUES)
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
            st.info("Añade la columna `jaula_id` en tu Google Sheet para activar la retícula interactiva de estanques.")

        st.markdown("---")
        st.markdown("#### Resumen Operativo del Módulo")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Estanques Activos", len(jaulas_disponibles))
        c2.metric("Biomasa Total", "4.150.000 kg", "+1.2% vs ayer")
        c3.metric("Oxígeno Promedio", f"{df_centro['oxigeno_mgl'].mean():.1f} mg/L" if 'oxigeno_mgl' in df_centro.columns else "8.2 mg/L")
        c4.metric("pH Promedio", "7.14", "Estable")
        c5.metric("Mortalidad Acumulada", f"{df_centro['mortalidad_dia'].sum() if 'mortalidad_dia' in df_centro.columns else 3} peces")

    # ==========================================
    # VISTA 2: CALIDAD DE AGUA
    # ==========================================
    elif menu == "Calidad de Agua":
        st.markdown(f"## 🧪 Panel de Calidad de Agua y Oceanografía")
        st.markdown("Análisis físico-químico de la columna de agua, perfiles de profundidad y bioseguridad.")
        st.markdown("---")

        jaula_sel = st.selectbox("Seleccionar Estanque para Análisis Detallado:", jaulas_disponibles)
        df_j = df_centro[df_centro['jaula_id'] == jaula_sel] if 'jaula_id' in df_centro.columns else df_centro

        if not df_j.empty:
            ult = df_j.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Oxígeno Superficial (0m)", f"{ult.get('oxigeno_mgl', 8.1)} mg/L", "Óptimo")
            col2.metric("Oxígeno de Fondo (15m)", f"{ult.get('oxigeno_fondo_mgl', 7.5)} mg/L", "Revisar estratificación" if float(ult.get('oxigeno_fondo_mgl', 7.5)) < 5 else "Estable")
            col3.metric("Temperatura del Agua", f"{ult.get('temperatura_c', 12.5)} °C", "Rango normal")
            col4.metric("Salinidad", f"{ult.get('salinidad_psu', 32.4)} PSU", "Normal")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("pH del Estanque", "7.18", "pH Óptimo (6.8 - 7.5)")
            col6.metric("Fitoplancton (Algas)", f"{int(ult.get('conteo_algas_celulas', 450)):,} cél/ml", "Sin Bloom")
            col7.metric("Turbidez", "1.4 NTU", "Baja")
            col8.metric("Amonio Total (TAN)", "0.05 mg/L", "Seguro (<0.1)")

            st.markdown("---")
            st.markdown("#### 📈 Histórico Multivariable de Calidad de Agua")
            cols_agua = [c for c in ['oxigeno_mgl', 'oxigeno_fondo_mgl', 'temperatura_c'] if c in df_j.columns]
            if cols_agua:
                st.line_chart(df_j.set_index('timestamp')[cols_agua], height=380)

    # ==========================================
    # VISTA 3: ALIMENTACIÓN
    # ==========================================
    elif menu == "Alimentación":
        st.markdown(f"## 🍽️ Control de Alimentación y Silos (Pontón)")
        st.markdown("Gestión de sopladores, tasas de entrega de pellet y optimización del Factor de Conversión (FCR).")
        st.markdown("---")

        jaula_sel = st.selectbox("Seleccionar Estanque para Control de Ración:", jaulas_disponibles)
        df_j = df_centro[df_centro['jaula_id'] == jaula_sel] if 'jaula_id' in df_centro.columns else df_centro

        if not df_j.empty:
            ult = df_j.iloc[-1]
            estado_soplador = int(ult.get('estado_alimentacion', 0))
            tasa_kg = float(ult.get('tasa_alimento_kg_min', 0.0))
            silo_pct = float(ult.get('silo_alimento_pct', 75.0))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Estado de Sopladores", "ACTIVO 🟢" if estado_soplador == 1 else "STANDBY 🔴", f"{tasa_kg} kg/min")
            c2.metric("Silos Principales (Pontón)", f"{silo_pct}%", "Autonomía: 3.5 días" if silo_pct > 20 else "⚠️ REABASTECER")
            c3.metric("Ración Diaria Programada", "1.450 kg", "Cumplimiento 94%")
            c4.metric("FCR Biológico Actual", "1.12", "Eficiente")

            st.markdown("---")
            st.markdown("#### ⚙️ Consola de Respuesta Operativa Rápida")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"**Estanque seleccionado:** {jaula_sel}\n\nPuede enviar comandos directos de parada de emergencia o ajuste de ración si las alertas de oxígeno fluctúan.")
                if st.button("🛑 DETENER ALIMENTACIÓN DE ESTE ESTANQUE", type="primary"):
                    st.success(f"Comando enviado con éxito: Sopladores de {jaula_sel} detenidos.")
            with col_b:
                st.markdown("#### Tendencia de Suministro vs Oxígeno")
                cols_alim = [c for c in ['tasa_alimento_kg_min', 'oxigeno_mgl'] if c in df_j.columns]
                if cols_alim:
                    st.line_chart(df_j.set_index('timestamp')[cols_alim], height=250)

    # ==========================================
    # VISTA 4: ENERGÍA Y SENSORES
    # ==========================================
    elif menu == "Energía y Sensores":
        st.markdown(f"## ⚡ Infraestructura, Energía y Conectividad")
        st.markdown("Estado de respaldos eléctricos, generadores del pontón y salud de sondas de telemetría.")
        st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Generador Principal", "OPERATIVO 🟢", "Carga: 68%")
        c2.metric("Estabilidad Red Eléctrica", "99.8%", "Sin microcortes hoy")
        c3.metric("Banco de Baterías UPS", "100%", "Autonomía: 4 horas")
        c4.metric("Enlace Satelital (Starlink)", "CONECTADO 🟢", "Latencia: 28 ms")

        st.markdown("---")
        st.markdown("#### 🩺 Diagnóstico de Sondas y Red de Sensores de Campo")
        
        # Tabla simulada de estado de hardware
        data_sensores = {
            "ID Sonda / Dispositivo": ["Sonda O2-E01", "Sensor Temp-E01", "Cámara Submarina E01", "Flujómetro Soplador 1", "Sonda O2-Fondo 15m"],
            "Ubicación": ["Estanque 01 (Sup)", "Estanque 01", "Jaula Central", "Pontón Principal", "Estanque 01 (Fondo)"],
            "Estado": ["🟢 OK", "🟢 OK", "🟢 OK", "🟡 Calibración Pendiente", "🟢 OK"],
            "Batería / Alimentación": ["Externa (PoE)", "Externa (PoE)", "12V OK", "Red AC", "Externa (PoE)"],
            "Última Sincronización": ["Hace 12 seg", "Hace 5 seg", "En vivo", "Hace 1 min", "Hace 12 seg"]
        }
        df_sensores = pd.DataFrame(data_sensores)
        st.dataframe(df_sensores, use_container_width=True)

        st.markdown("---")
        st.info("ℹ️ Sistema integrado mediante API REST y telemetría por protocolo Modbus TCP hacia el colector central del pontón.")

except Exception as e:
    st.error(f"Error al cargar el panel SCADA industrial: {e}")
