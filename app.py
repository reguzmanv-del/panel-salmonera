import streamlit as st
import pandas as pd
import requests
import sqlite3
import google.generativeai as genai

# ==========================================
# 1. CONFIGURACIÓN Y ESTADO DE SESIÓN
# ==========================================
st.set_page_config(page_title="BlueBrain SCADA | V5.0 (AI Copilot)", page_icon="🌐", layout="wide", initial_sidebar_state="auto")

if 'nav_menu' not in st.session_state:
    st.session_state.nav_menu = "Vista General"
if 'dietas_asignadas' not in st.session_state:
    st.session_state.dietas_asignadas = {}
if 'mensajes_chat' not in st.session_state:
    st.session_state.mensajes_chat = [
        {"role": "assistant", "content": "Conexión satelital establecida. Soy BlueBrain Copilot. Analizo los sensores y el histórico de la base de datos local. ¿Qué necesitas saber sobre la operación del pontón?"}
    ]

def ir_a_alimentacion():
    st.session_state.nav_menu = "Alimentación"

# Configurar Gemini AI con manejo de errores inicial
# Configurar Gemini AI con Auto-Descubrimiento
# Configurar Gemini AI con Auto-Descubrimiento
# Configurar Gemini AI (Versión 3.6 - Requerida por el servidor)
# Configurar Gemini AI (Optimizado para Velocidad de Respuesta)
# Configurar Gemini AI (Optimizado para Velocidad y Conexión Válida)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Usamos el modelo exigido por la API pero con menor temperatura para acelerar la respuesta
    modelo_ia = genai.GenerativeModel(
        model_name='gemini-3.6-flash',
        generation_config={"temperature": 0.2, "max_output_tokens": 300}
    )
    ia_disponible = True
except Exception as e:
    ia_disponible = False

catalogo_dietas = {
    "Biriwuin Alta Energía 12mm": {"fabricante": "Biriwuin Aqua", "tipo": "Engorda Rápida", "proteina": "45%", "lipidos": "35%", "demanda_o2": "ALTA", "factor_riesgo": 1.4},
    "OceanGrowth Estándar": {"fabricante": "OceanNutra", "tipo": "Mantención", "proteina": "42%", "lipidos": "28%", "demanda_o2": "NORMAL", "factor_riesgo": 1.0},
    "BioShield Funcional (Salud Branquial)": {"fabricante": "PharmaFish", "tipo": "Medicado / Estrés", "proteina": "40%", "lipidos": "25%", "demanda_o2": "BAJA", "factor_riesgo": 0.8}
}

# ==========================================
# 2. ESTILOS UI/UX SCADA
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500&display=swap');
    
    [data-testid="stAppViewContainer"] { 
        background-image: 
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='rgba(56, 189, 248, 0.02)' stroke-width='0.15' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z'/%3E%3Cpath d='M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z'/%3E%3Cpath d='M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4'/%3E%3C/svg%3E"),
            radial-gradient(circle at top right, #111827, #090d14);
        background-repeat: no-repeat, no-repeat; background-position: center center, center center; background-size: 55vw, cover; background-attachment: fixed, fixed; color: #e2e8f0; 
    }
    header[data-testid="stHeader"] { background: rgba(11, 15, 25, 0.95) !important; border-bottom: 1px solid rgba(56, 189, 248, 0.2) !important; }
    header[data-testid="stHeader"] button, header[data-testid="stHeader"] svg, header[data-testid="stHeader"] span { color: #38bdf8 !important; fill: #38bdf8 !important; stroke: #38bdf8 !important; }
    [data-testid="collapsedControl"] { background-color: #111827 !important; border: 1px solid #38bdf8 !important; border-radius: 8px !important; box-shadow: 0 0 8px rgba(56, 189, 248, 0.3) !important; margin-top: 5px !important; margin-left: 5px !important; }
    h1, h2, h3, h4 { font-family: 'Rajdhani', sans-serif !important; color: #f8fafc !important; }
    .gradient-text { background: linear-gradient(45deg, #38bdf8, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; font-size: 2.2rem; margin-bottom: 5px; }
    .stMetric { background: rgba(17, 24, 39, 0.6) !important; backdrop-filter: blur(10px) !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; padding: 15px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important;}
    .grid-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 15px; margin-top: 15px; margin-bottom: 25px; }
    .tank-card { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(8px); border-radius: 10px; padding: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); }
    .status-ok { border: 1px solid rgba(16, 185, 129, 0.3); border-top: 4px solid #10b981; }
    .status-warning { border: 1px solid rgba(245, 158, 11, 0.3); border-top: 4px solid #f59e0b; }
    .status-alert { border: 1px solid rgba(239, 68, 68, 0.5); border-top: 4px solid #ef4444; background: rgba(239, 68, 68, 0.1); }
    .t-title { font-family: 'Rajdhani', sans-serif; font-size: 1.2rem; font-weight: bold; color: white; margin-bottom: 8px; }
    .t-data { font-size: 0.85rem; color: #9ca3af; margin: 3px 0; font-family: 'Inter', sans-serif;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CONEXIÓN A SQLITE
# ==========================================
@st.cache_data(ttl=30)
def cargar_datos_sqlite():
    try:
        conn = sqlite3.connect('scada_historico.db')
        query = "SELECT * FROM (SELECT * FROM telemetria ORDER BY timestamp DESC LIMIT 1000) ORDER BY timestamp ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()

df_c = cargar_datos_sqlite()

if not df_c.empty:
    centro_sel = "Pontón Alfa"
    jaulas_disp = df_c['jaula_id'].unique()

    # ==========================================
    # 4. MOTOR GLOBAL DE REGLAS DURAS
    # ==========================================
    alertas_globales = []
    estado_actual_resumen = ""
    
    for jaula in jaulas_disp:
        df_j = df_c[df_c['jaula_id'] == jaula]
        ult = df_j.iloc[-1]
        o2 = float(ult.get('oxigeno_mgl', 8.0))
        temp = float(ult.get('temperatura_c', 12.0))
        estado_alim = int(ult.get('estado_alimentacion', 0))
        
        dieta_actual = st.session_state.dietas_asignadas.get(jaula, "OceanGrowth Estándar")
        factor_riesgo = catalogo_dietas[dieta_actual]['factor_riesgo']
        estado_actual_resumen += f"- {jaula}: O2 {o2} mg/L, Temp {temp} °C, Dieta: {dieta_actual}.\n"
        
        if o2 < 4.2 and estado_alim == 1:
            alertas_globales.append(f"CRÍTICO: Oxígeno letal ({o2} mg/L) en **{jaula}**.")
        elif o2 < 5.0 and factor_riesgo >= 1.4 and estado_alim == 1:
            alertas_globales.append(f"PELIGRO (SDA): **{jaula}** con O2 marginal ({o2} mg/L) no soporta Alta Energía.")

    if alertas_globales and st.session_state.nav_menu != "Alimentación":
        st.markdown(f"""
        <div style="background-color: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h3 style="color: #ef4444; margin-top: 0; font-family: 'Rajdhani', sans-serif;">🚨 ALERTA DEL SISTEMA HARD-RULES</h3>
            <ul style="color: #f8fafc; font-family: 'Inter', sans-serif;">
                {''.join([f"<li>{alerta}</li>" for alerta in alertas_globales])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.button("🔴 ABRIR CONSOLA TÁCTICA", on_click=ir_a_alimentacion, type="primary", use_container_width=True)

    # ==========================================
    # 5. MENÚ DE NAVEGACIÓN
    # ==========================================
    st.sidebar.markdown("### 🌐 BlueBrain OS")
    st.sidebar.markdown("---")
    opciones_menu = ["Vista General", "Calidad de Agua", "Alimentación", "Gestión de Dietas", "Meteorología y Corrientes", "Energía y Sensores"]
    menu = st.sidebar.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.nav_menu), key="nav_menu")
    st.sidebar.markdown("---")

    if st.session_state.nav_menu == "Vista General":
        st.markdown(f'<div class="gradient-text">Panel Ejecutivo: {centro_sel}</div>', unsafe_allow_html=True)
        st.markdown("---")
        html_grid = '<div class="grid-container">'
        for jaula in jaulas_disp:
            ult = df_c[df_c['jaula_id'] == jaula].iloc[-1]
            o2 = float(ult.get('oxigeno_mgl', 8.0))
            temp = float(ult.get('temperatura_c', 12.0))
            clase = "status-alert" if o2 < 5.0 else "status-ok"
            html_grid += f'<div class="tank-card {clase}"><div class="t-title">{jaula}</div><p class="t-data">O2: <span style="color:white; font-weight:bold;">{o2} mg/L</span></p></div>'
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)

    elif st.session_state.nav_menu == "Calidad de Agua":
        st.markdown('<div class="gradient-text">Calidad de Agua</div>', unsafe_allow_html=True)
        jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disp, key="agua_sel")
        df_j = df_c[df_c['jaula_id'] == jaula_sel]
        st.line_chart(df_j.set_index('timestamp')[['oxigeno_mgl', 'oxigeno_fondo_mgl']], height=300)

    elif st.session_state.nav_menu == "Alimentación":
        st.markdown('<div class="gradient-text">Consola Táctica y BlueBrain Copilot</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        col_chat, col_control = st.columns([1.5, 1])
        
        with col_control:
            st.markdown("#### 🎛️ Tablero de Control")
            jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disp, key="alim_sel")
            if st.button(f"🛑 DETENER ALIMENTACIÓN - {jaula_sel}", type="primary", use_container_width=True):
                st.success(f"Sopladores apagados en {jaula_sel}.")

        with col_chat:
            st.markdown("#### 🧠 Copiloto IA (Gemini Model)")
            if not ia_disponible:
                st.error("Error de inicialización de Gemini. Verifica tus Secrets.")
            else:
                chat_container = st.container(height=350)
                with chat_container:
                    for msg in st.session_state.mensajes_chat:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                
                if prompt := st.chat_input("Pregúntale a BlueBrain..."):
                    st.session_state.mensajes_chat.append({"role": "user", "content": prompt})
                    with chat_container:
                        with st.chat_message("user"):
                            st.markdown(prompt)
                    
                    prompt_oculto = f"""Eres BlueBrain, IA SCADA acuícola. Responde técnico y conciso basado en: {estado_actual_resumen}. 
                    Histórico: En agosto 2026, TK.02 sufrió hipoxia invernal (O2 4.0 mg/L). 
                    Pregunta: {prompt}"""
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            with st.spinner("Analizando Big Data..."):
                                try:
                                    respuesta_obj = modelo_ia.generate_content(prompt_oculto)
                                    respuesta = respuesta_obj.text
                                    st.markdown(respuesta)
                                except Exception as e:
                                    respuesta = f"⚠️ Falló la conexión con la API de Google: `{e}`. Verifica que la API Key guardada en Streamlit Settings sea válida."
                                    st.error(respuesta)
                    st.session_state.mensajes_chat.append({"role": "assistant", "content": respuesta})

    elif st.session_state.nav_menu == "Gestión de Dietas":
        st.markdown('<div class="gradient-text">Configuración Nutricional</div>', unsafe_allow_html=True)

    elif st.session_state.nav_menu == "Meteorología y Corrientes":
        st.markdown('<div class="gradient-text">Entorno Atmosférico</div>', unsafe_allow_html=True)

    elif st.session_state.nav_menu == "Energía y Sensores":
        st.markdown('<div class="gradient-text">Infraestructura</div>', unsafe_allow_html=True)

else:
    st.error("Sube el archivo scada_historico.db a tu repositorio.")
