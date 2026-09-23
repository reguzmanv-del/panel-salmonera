import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN Y ESTADO DE SESIÓN (Memoria)
# ==========================================
st.set_page_config(page_title="BlueBrain SCADA | V5.0", page_icon="🌐", layout="wide", initial_sidebar_state="auto")

# Inicializar variables de sesión (Para navegación y base de datos local)
if 'nav_menu' not in st.session_state:
    st.session_state.nav_menu = "Vista General"
if 'dietas_asignadas' not in st.session_state:
    st.session_state.dietas_asignadas = {}

def ir_a_alimentacion():
    st.session_state.nav_menu = "Alimentación"

# Catálogo Maestro de Dietas
catalogo_dietas = {
    "Biriwuin Alta Energía 12mm": {
        "fabricante": "Biriwuin Aqua", "tipo": "Engorda Rápida", 
        "proteina": "45%", "lipidos": "35%", "energia_digestible": "21.5 MJ/kg", 
        "demanda_o2": "ALTA", "factor_riesgo": 1.4
    },
    "OceanGrowth Estándar": {
        "fabricante": "OceanNutra", "tipo": "Mantención", 
        "proteina": "42%", "lipidos": "28%", "energia_digestible": "19.0 MJ/kg", 
        "demanda_o2": "NORMAL", "factor_riesgo": 1.0
    },
    "BioShield Funcional (Salud Branquial)": {
        "fabricante": "PharmaFish", "tipo": "Medicado / Estrés", 
        "proteina": "40%", "lipidos": "25%", "energia_digestible": "17.5 MJ/kg", 
        "demanda_o2": "BAJA", "factor_riesgo": 0.8
    }
}

# ==========================================
# 2. ESTILOS UI/UX SCADA
# ==========================================
estilo_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&display=swap');
    
    [data-testid="stAppViewContainer"] { 
        background-image: 
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='rgba(56, 189, 248, 0.02)' stroke-width='0.15' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z'/%3E%3Cpath d='M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z'/%3E%3Cpath d='M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4'/%3E%3C/svg%3E"),
            radial-gradient(circle at top right, #111827, #090d14);
        background-repeat: no-repeat, no-repeat;
        background-position: center center, center center;
        background-size: 55vw, cover;
        background-attachment: fixed, fixed;
        color: #e2e8f0; 
    }
    
    header[data-testid="stHeader"] { background: rgba(11, 15, 25, 0.95) !important; border-bottom: 1px solid rgba(56, 189, 248, 0.2) !important; }
    header[data-testid="stHeader"] button, header[data-testid="stHeader"] svg, header[data-testid="stHeader"] span { color: #38bdf8 !important; fill: #38bdf8 !important; stroke: #38bdf8 !important; }
    
    [data-testid="collapsedControl"] {
        background-color: #111827 !important; border: 1px solid #38bdf8 !important; border-radius: 8px !important;
        box-shadow: 0 0 8px rgba(56, 189, 248, 0.3) !important; margin-top: 5px !important; margin-left: 5px !important;
    }
    
    h1, h2, h3, h4 { font-family: 'Rajdhani', sans-serif !important; color: #f8fafc !important; }
    
    .gradient-text {
        background: linear-gradient(45deg, #38bdf8, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 700; font-size: 2.2rem; margin-bottom: 5px;
    }

    .stMetric { background: rgba(17, 24, 39, 0.6) !important; backdrop-filter: blur(10px) !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; padding: 15px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important;}

    .grid-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 15px; margin-top: 15px; margin-bottom: 25px; }
    .tank-card { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(8px); border-radius: 10px; padding: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); }
    
    .status-ok { border: 1px solid rgba(16, 185, 129, 0.3); border-top: 4px solid #10b981; }
    .status-warning { border: 1px solid rgba(245, 158, 11, 0.3); border-top: 4px solid #f59e0b; }
    .status-alert { border: 1px solid rgba(239, 68, 68, 0.5); border-top: 4px solid #ef4444; background: rgba(239, 68, 68, 0.1); }
    
    .t-title { font-family: 'Rajdhani', sans-serif; font-size: 1.2rem; font-weight: bold; color: white; margin-bottom: 8px; }
    .t-data { font-size: 0.85rem; color: #9ca3af; margin: 3px 0; font-family: 'Inter', sans-serif;}
    .c-ok { color: #34d399; font-weight: 600; }
    .c-warn { color: #fbbf24; font-weight: 600; }
    .c-alert { color: #f87171; font-weight: 600; }
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# ==========================================
# 3. CONEXIONES A DATOS
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

    centros = df['centro_id'].dropna().unique() if 'centro_id' in df.columns else ["Pontón Alfa"]
    centro_sel = st.sidebar.selectbox("Centro Activo", centros)
    df_c = df[df['centro_id'] == centro_sel] if 'centro_id' in df.columns else df
    jaulas_disp = df_c['jaula_id'].dropna().unique() if 'jaula_id' in df_c.columns else ["TK.01"]

    # ==========================================
    # 4. MOTOR GLOBAL DE REGLAS DURAS (Failsafe)
    # ==========================================
    alertas_globales = []
    
    if 'jaula_id' in df_c.columns:
        for jaula in jaulas_disp:
            df_j = df_c[df_c['jaula_id'] == jaula]
            if not df_j.empty:
                ult = df_j.iloc[-1]
                o2 = float(ult.get('oxigeno_mgl', 8.0))
                temp = float(ult.get('temperatura_c', 12.0))
                estado_alim = int(ult.get('estado_alimentacion', 0))
                
                # Rescatamos la dieta asignada o aplicamos la estándar por defecto
                dieta_actual = st.session_state.dietas_asignadas.get(jaula, "OceanGrowth Estándar")
                factor_riesgo = catalogo_dietas[dieta_actual]['factor_riesgo']
                
                # Regla 1: Asfixia inminente absoluta
                if o2 < 4.2 and estado_alim == 1:
                    alertas_globales.append(f"CRÍTICO: Oxígeno en nivel letal ({o2} mg/L) en **{jaula}**. Sopladores activos.")
                
                # Regla 2: Riesgo cruzado por dieta (SDA)
                elif o2 < 5.0 and factor_riesgo >= 1.4 and estado_alim == 1:
                    alertas_globales.append(f"PELIGRO (SDA): **{jaula}** con O2 marginal ({o2} mg/L) no soporta digestión de dieta Alta Energía.")

    # 4.1 Despliegue del Banner Global de Alerta
    if alertas_globales and st.session_state.nav_menu != "Alimentación":
        st.markdown(f"""
        <div style="background-color: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h3 style="color: #ef4444; margin-top: 0; font-family: 'Rajdhani', sans-serif;">🚨 ALERTA DEL SISTEMA HARD-RULES (FAILSAFE)</h3>
            <ul style="color: #f8fafc; font-family: 'Inter', sans-serif;">
                {''.join([f"<li>{alerta}</li>" for alerta in alertas_globales])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.button("🔴 ABRIR CONSOLA TÁCTICA DE ALIMENTACIÓN", on_click=ir_a_alimentacion, type="primary", use_container_width=True)
        st.markdown("---")

    # ==========================================
    # 5. MENÚ DE NAVEGACIÓN CONTROLADO
    # ==========================================
    st.sidebar.markdown("### 🌐 BlueBrain OS")
    st.sidebar.markdown("---")
    
    # Vinculamos el radio button al session_state
    opciones_menu = ["Vista General", "Calidad de Agua", "Alimentación", "Gestión de Dietas", "Meteorología y Corrientes", "Energía y Sensores"]
    menu = st.sidebar.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.nav_menu), key="nav_menu")
    st.sidebar.markdown("---")

    # ==========================================
    # VISTA 1: GENERAL
    # ==========================================
    if st.session_state.nav_menu == "Vista General":
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
    elif st.session_state.nav_menu == "Calidad de Agua":
        st.markdown('<div class="gradient-text">Calidad de Agua y Oceanografía</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("#### 🦠 Semáforo de Bioseguridad")
        if 'jaula_id' in df_c.columns:
            html_grid = '<div class="grid-container">'
            for jaula in jaulas_disp:
                df_j = df_c[df_c['jaula_id'] == jaula]
                if not df_j.empty:
                    ult = df_j.iloc[-1]
                    o2_fon = float(ult.get('oxigeno_fondo_mgl', 8.0))
                    algas = int(ult.get('conteo_algas_celulas', 500))
                    
                    if o2_fon < 4.5 or algas > 2500:
                        html_grid += f'<div class="tank-card status-alert"><div class="t-title">{jaula}</div><p class="t-data">O2 Fondo: <span class="c-alert">{o2_fon}</span></p><p class="t-data">Algas: <span class="c-alert">{algas}</span></p></div>'
                    elif o2_fon < 6.0 or algas > 1500:
                        html_grid += f'<div class="tank-card status-warning"><div class="t-title">{jaula}</div><p class="t-data">O2 Fondo: <span class="c-warn">{o2_fon}</span></p><p class="t-data">Algas: <span class="c-warn">{algas}</span></p></div>'
                    else:
                        html_grid += f'<div class="tank-card status-ok"><div class="t-title">{jaula}</div><p class="t-data">O2 Fondo: <span class="c-ok">{o2_fon}</span></p><p class="t-data">Algas: <span class="c-ok">{algas}</span></p></div>'
            html_grid += '</div>'
            st.markdown(html_grid, unsafe_allow_html=True)

        st.markdown("---")
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
    # VISTA 3: CONSOLA TÁCTICA (ALIMENTACIÓN + IA)
    # ==========================================
    elif st.session_state.nav_menu == "Alimentación":
        st.markdown('<div class="gradient-text">Consola Táctica de Alimentación</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # EL COPILOTO IA (GEMS)
        st.markdown("#### 🧠 BlueBrain Copilot (Motor de Análisis Biológico)")
        
        if alertas_globales:
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); border-left: 5px solid #ef4444; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <span style="color:#ef4444; font-weight:bold;">⚡ INTERVENCIÓN DEL FAILSAFE (Reglas Duras Activas):</span><br>
                El motor predictivo ha sido anulado por umbrales críticos de supervivencia. Ejecute el corte de sopladores inmediatamente en los estanques afectados.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.05); border-left: 5px solid #34d399; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <span style="color:#34d399; font-weight:bold;">✨ IA Copilot Conectado (Contexto Normal):</span><br>
                Tendencia de oxígeno estable en módulo. SDA (Demanda Dinámica) cubierta por corrientes actuales. Sugerencia: Mantener perfiles de entrega programados para optimización de FCR.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎛️ Tablero de Sopladores")
        jaula_sel = st.selectbox("Seleccionar estanque a intervenir:", jaulas_disp, key="alim_sel")
        df_j = df_c[df_c['jaula_id'] == jaula_sel] if 'jaula_id' in df_c.columns else df_c
        
        if not df_j.empty:
            ult = df_j.iloc[-1]
            dieta = st.session_state.dietas_asignadas.get(jaula_sel, "OceanGrowth Estándar")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Soplador", "ACTIVO 🟢" if int(ult.get('estado_alimentacion', 0))==1 else "DETENIDO 🔴")
            c2.metric("Tasa (kg/min)", f"{ult.get('tasa_alimento_kg_min', 0)}")
            c3.metric("O2 Actual", f"{ult.get('oxigeno_mgl', 0)} mg/L")
            c4.metric("Dieta en curso", dieta)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_bt1, col_bt2 = st.columns(2)
            with col_bt1:
                if st.button(f"🛑 DETENER ALIMENTACIÓN - {jaula_sel}", type="primary", use_container_width=True):
                    st.success(f"Comando enviado. Sopladores apagados en {jaula_sel}.")
            with col_bt2:
                if st.button("🔽 Reducir tasa al 50%", use_container_width=True):
                    st.info(f"Tasa reducida para digestión (SDA) controlada en {jaula_sel}.")

    # ==========================================
    # VISTA 4: GESTIÓN DE DIETAS
    # ==========================================
    elif st.session_state.nav_menu == "Gestión de Dietas":
        st.markdown('<div class="gradient-text">Configuración Nutricional</div>', unsafe_allow_html=True)
        st.markdown("Asigna matrices nutricionales. El Motor de Reglas y la IA usarán estos datos para calcular el riesgo.")
        st.markdown("---")

        col_form, col_info = st.columns([1, 1])

        with col_form:
            st.markdown("#### 📝 Asignación en Silos")
            jaula_config = st.selectbox("Estanque:", jaulas_disp)
            dieta_seleccionada = st.selectbox("Dieta:", list(catalogo_dietas.keys()))
            
            if st.button(f"💾 Guardar Asignación en {jaula_config}", type="primary", use_container_width=True):
                # Guardamos en la memoria de la sesión
                st.session_state.dietas_asignadas[jaula_config] = dieta_seleccionada
                st.success(f"¡{dieta_seleccionada} asignada a {jaula_config}!")
                st.info("Algoritmos de riesgo re-calibrados exitosamente.")

        with col_info:
            st.markdown("#### 🔬 Ficha de la Dieta")
            ficha = catalogo_dietas[dieta_seleccionada]
            st.markdown(f"""
            <div style="background: rgba(17, 24, 39, 0.7); padding: 20px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.3);">
                <h3 style="margin-top:0; color:#38bdf8;">{dieta_seleccionada}</h3>
                <p><strong>Factor de Riesgo SDA:</strong> <span style="color:{'#ef4444' if ficha['demanda_o2'] == 'ALTA' else '#10b981'}; font-weight:bold;">x{ficha['factor_riesgo']}</span></p>
                <p><strong>Lípidos:</strong> {ficha['lipidos']} | <strong>Proteína:</strong> {ficha['proteina']}</p>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # VISTAS RESTANTES: METEO Y ENERGÍA
    # ==========================================
    elif st.session_state.nav_menu == "Meteorología y Corrientes":
        st.markdown('<div class="gradient-text">Entorno Atmosférico y Oceanográfico</div>', unsafe_allow_html=True)
        st.markdown("---")
        clima = obtener_clima_reloncavi()
        if clima:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temp Ambiente", f"{clima.get('temperature_2m', '--')} °C")
            c2.metric("Viento", f"{round(clima.get('wind_speed_10m', 0) * 1.94384, 1)} nudos")
            c3.metric("Ráfagas", f"{round(clima.get('wind_gusts_10m', 0) * 1.94384, 1)} nudos")
            c4.metric("Presión", f"{clima.get('surface_pressure', '--')} hPa")

    elif st.session_state.nav_menu == "Energía y Sensores":
        st.markdown('<div class="gradient-text">Infraestructura de Borde</div>', unsafe_allow_html=True)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("Generador Principal", "OPERATIVO 🟢", "68% Carga")
        c2.metric("Enlace Starlink", "ONLINE 🟢", "28ms Latencia")
        c3.metric("Banco UPS", "100%", "Autonomía")

except Exception as e:
    st.error(f"Error en el núcleo SCADA: {e}")
