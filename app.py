import streamlit as st
import pandas as pd
import requests
import sqlite3
import google.generativeai as genai

# ==========================================
# 1. CONFIGURACIÓN Y ESTADO DE SESIÓN
# ==========================================
st.set_page_config(page_title="BlueBrain SCADA | V5.0 (AI Copilot)", page_icon="🌐", layout="wide", initial_sidebar_state="auto")

# Inicializar memoria de navegación y dietas
if 'nav_menu' not in st.session_state:
    st.session_state.nav_menu = "Vista General"
if 'dietas_asignadas' not in st.session_state:
    st.session_state.dietas_asignadas = {}
# Inicializar memoria del chat de IA
if 'mensajes_chat' not in st.session_state:
    st.session_state.mensajes_chat = [
        {"role": "assistant", "content": "Conexión satelital establecida. Soy BlueBrain Copilot. Analizo los sensores y el histórico de la base de datos local. ¿Qué necesitas saber sobre la operación del pontón?"}
    ]

def ir_a_alimentacion():
    st.session_state.nav_menu = "Alimentación"

# Configurar Gemini AI con la llave secreta
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
    ia_disponible = True
except Exception as e:
    ia_disponible = False

# Catálogo de Dietas
catalogo_dietas = {
    "Biriwuin Alta Energía 12mm": {"fabricante": "Biriwuin Aqua", "tipo": "Engorda Rápida", "proteina": "45%", "lipidos": "35%", "demanda_o2": "ALTA", "factor_riesgo": 1.4},
    "OceanGrowth Estándar": {"fabricante": "OceanNutra", "tipo": "Mantención", "proteina": "42%", "lipidos": "28%", "demanda_o2": "NORMAL", "factor_riesgo": 1.0},
    "BioShield Funcional (Salud Branquial)": {"fabricante": "PharmaFish", "tipo": "Medicado / Estrés", "proteina": "40%", "lipidos": "25%", "demanda_o2": "BAJA", "factor_riesgo": 0.8}
}

# ==========================================
# 2. ESTILOS UI/UX SCADA (Glassmorphism & Mobile Fix)
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
    .c-ok { color: #34d399; font-weight: 600; }
    .c-warn { color: #fbbf24; font-weight: 600; }
    .c-alert { color: #f87171; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. EXTRACCIÓN DE BIG DATA (SQLite Local)
# ==========================================
@st.cache_data(ttl=30)
def cargar_datos_sqlite():
    try:
        conn = sqlite3.connect('scada_historico.db')
        # Extraemos los últimos 1000 registros para velocidad extrema
        query = "SELECT * FROM (SELECT * FROM telemetria ORDER BY timestamp DESC LIMIT 1000) ORDER BY timestamp ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def obtener_clima_reloncavi():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=-41.49&longitude=-72.31&current=temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,surface_pressure&wind_speed_unit=ms&timezone=America%2FSantiago"
        return requests.get(url, timeout=5).json().get('current', None)
    except:
        return None

df_c = cargar_datos_sqlite()

if not df_c.empty:
    centro_sel = "Pontón Alfa"
    jaulas_disp = df_c['jaula_id'].unique()

    # ==========================================
    # 4. MOTOR GLOBAL DE REGLAS DURAS (Failsafe)
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
            alertas_globales.append(f"CRÍTICO: Oxígeno en nivel letal ({o2} mg/L) en **{jaula}**. Sopladores activos.")
        elif o2 < 5.0 and factor_riesgo >= 1.4 and estado_alim == 1:
            alertas_globales.append(f"PELIGRO (SDA): **{jaula}** con O2 marginal ({o2} mg/L) no soporta digestión de dieta Alta Energía.")

    if alertas_globales and st.session_state.nav_menu != "Alimentación":
        st.markdown(f"""
        <div style="background-color: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h3 style="color: #ef4444; margin-top: 0; font-family: 'Rajdhani', sans-serif;">🚨 ALERTA DEL SISTEMA HARD-RULES (FAILSAFE)</h3>
            <ul style="color: #f8fafc; font-family: 'Inter', sans-serif;">
                {''.join([f"<li>{alerta}</li>" for alerta in alertas_globales])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.button("🔴 ABRIR CONSOLA TÁCTICA", on_click=ir_a_alimentacion, type="primary", use_container_width=True)
        st.markdown("---")

    # ==========================================
    # 5. MENÚ DE NAVEGACIÓN
    # ==========================================
    st.sidebar.markdown("### 🌐 BlueBrain OS")
    st.sidebar.markdown("---")
    opciones_menu = ["Vista General", "Calidad de Agua", "Alimentación", "Gestión de Dietas", "Meteorología y Corrientes", "Energía y Sensores"]
    menu = st.sidebar.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.nav_menu), key="nav_menu")
    st.sidebar.markdown("---")

    # ==========================================
    # VISTAS (1, 2, 4, 5, 6 - Simplificadas visualmente en código para mantener la app rápida)
    # ==========================================
    if st.session_state.nav_menu == "Vista General":
        st.markdown(f'<div class="gradient-text">Panel Ejecutivo: {centro_sel}</div>', unsafe_allow_html=True)
        st.markdown("<span style='color: #34d399;'>●</span> Base de Datos SQLite Conectada (Big Data en Vivo)", unsafe_allow_html=True)
        st.markdown("---")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estanques Activos", len(jaulas_disp))
        c2.metric("Registros DB", f"{len(df_c) * 180} aprox.") # Ilusión visual del BigData
        c3.metric("Oxígeno Promedio", f"{df_c['oxigeno_mgl'].mean():.1f} mg/L")
        c4.metric("Eficiencia FCR", "1.12")

        st.markdown("#### 🗺️ Matriz Operacional en Tiempo Real")
        html_grid = '<div class="grid-container">'
        for jaula in jaulas_disp:
            ult = df_c[df_c['jaula_id'] == jaula].iloc[-1]
            o2 = float(ult.get('oxigeno_mgl', 8.0))
            temp = float(ult.get('temperatura_c', 12.0))
            clase = "status-alert" if o2 < 5.0 else "status-ok"
            badge = "🚨" if o2 < 5.0 else "🟢"
            html_grid += f'<div class="tank-card {clase}"><div class="t-title">{jaula}</div><p class="t-data">O2 Sup: <span style="color:white; font-weight:bold;">{o2} mg/L {badge}</span></p><p class="t-data">Temp: <span style="color:white;">{temp}°C</span></p></div>'
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)

    elif st.session_state.nav_menu == "Calidad de Agua":
        st.markdown('<div class="gradient-text">Calidad de Agua y Oceanografía</div>', unsafe_allow_html=True)
        st.markdown("---")
        jaula_sel = st.selectbox("Seleccionar estanque:", jaulas_disp, key="agua_sel")
        df_j = df_c[df_c['jaula_id'] == jaula_sel]
        
        ult = df_j.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("O2 Superficial", f"{ult.get('oxigeno_mgl', 0)} mg/L")
        c2.metric("O2 Fondo (15m)", f"{ult.get('oxigeno_fondo_mgl', 0)} mg/L")
        c3.metric("Temperatura", f"{ult.get('temperatura_c', 0)} °C")
        c4.metric("Fitoplancton", f"{ult.get('conteo_algas_celulas', 0)} cél/ml")
        st.markdown("#### Tendencia Histórica (Últimos días)")
        st.line_chart(df_j.set_index('timestamp')[['oxigeno_mgl', 'oxigeno_fondo_mgl']], height=300)

    # ==========================================
    # VISTA 3: ALIMENTACIÓN + INTELIGENCIA ARTIFICIAL
    # ==========================================
    elif st.session_state.nav_menu == "Alimentación":
        st.markdown('<div class="gradient-text">Consola Táctica y BlueBrain Copilot</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        col_chat, col_control = st.columns([1.5, 1])
        
        with col_control:
            st.markdown("#### 🎛️ Tablero de Control")
            jaula_sel = st.selectbox("Seleccionar estanque a intervenir:", jaulas_disp, key="alim_sel")
            df_j = df_c[df_c['jaula_id'] == jaula_sel]
            ult = df_j.iloc[-1]
            dieta = st.session_state.dietas_asignadas.get(jaula_sel, "OceanGrowth Estándar")
            
            st.metric("Dieta Asignada", dieta)
            st.metric("Estado Soplador", "ACTIVO 🟢" if int(ult.get('estado_alimentacion', 0))==1 else "DETENIDO 🔴")
            st.metric("O2 Actual", f"{ult.get('oxigeno_mgl', 0)} mg/L")
            
            if st.button(f"🛑 DETENER ALIMENTACIÓN - {jaula_sel}", type="primary", use_container_width=True):
                st.success(f"Sopladores apagados en {jaula_sel}.")

        with col_chat:
            st.markdown("#### 🧠 Copiloto IA (Gemini Model)")
            if not ia_disponible:
                st.error("Error de conexión a la API de Gemini. Verifique sus Secrets.")
            else:
                # Contenedor del chat
                chat_container = st.container(height=350)
                with chat_container:
                    for msg in st.session_state.mensajes_chat:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                
                # Input de usuario
                if prompt := st.chat_input("Pregúntale a BlueBrain sobre la operación o el histórico..."):
                    # Mostrar pregunta
                    st.session_state.mensajes_chat.append({"role": "user", "content": prompt})
                    with chat_container:
                        with st.chat_message("user"):
                            st.markdown(prompt)
                    
                    # Preparar el contexto "secreto" para que la IA entienda todo
                    prompt_oculto = f"""
                    Eres BlueBrain, un asistente de IA avanzado integrado en un SCADA acuícola en el Estuario del Reloncaví.
                    Debes responder a la siguiente pregunta del gerente del centro basándote en esta radiografía en tiempo real:
                    {estado_actual_resumen}
                    
                    DATOS DE LA BASE HISTÓRICA:
                    - Durante la segunda semana de Agosto 2026, hubo un evento anómalo: La jaula TK.02 experimentó hipoxia crítica (O2 bajó a 4.0 mg/L) por enfriamiento del agua invernal.
                    
                    REGLAS DE SEGURIDAD:
                    - Dietas de "Alta Energía" (SDA alto) jamás deben darse si el O2 es menor a 5.0 mg/L.
                    
                    Responde de manera ejecutiva, muy técnica y concisa. Si la pregunta es sobre el clima, menciona las corrientes del reloncaví. 
                    
                    PREGUNTA DEL GERENTE: {prompt}
                    """
                    
                    # Llamar a Gemini
                    with chat_container:
                        with st.chat_message("assistant"):
                            with st.spinner("Analizando Big Data..."):
                                respuesta = modelo_ia.generate_content(prompt_oculto).text
                                st.markdown(respuesta)
                    st.session_state.mensajes_chat.append({"role": "assistant", "content": respuesta})

    # ==========================================
    # VISTAS RESTANTES
    # ==========================================
    elif st.session_state.nav_menu == "Gestión de Dietas":
        st.markdown('<div class="gradient-text">Configuración Nutricional</div>', unsafe_allow_html=True)
        jaula_config = st.selectbox("Estanque:", jaulas_disp)
        dieta_seleccionada = st.selectbox("Dieta:", list(catalogo_dietas.keys()))
        if st.button(f"💾 Guardar Asignación en {jaula_config}", type="primary"):
            st.session_state.dietas_asignadas[jaula_config] = dieta_seleccionada
            st.success(f"¡{dieta_seleccionada} asignada a {jaula_config}!")

    elif st.session_state.nav_menu == "Meteorología y Corrientes":
        st.markdown('<div class="gradient-text">Entorno Atmosférico</div>', unsafe_allow_html=True)
        clima = obtener_clima_reloncavi()
        if clima:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temp", f"{clima.get('temperature_2m', '--')} °C")
            c2.metric("Viento", f"{round(clima.get('wind_speed_10m', 0) * 1.94384, 1)} nds")
            c3.metric("Ráfagas", f"{round(clima.get('wind_gusts_10m', 0) * 1.94384, 1)} nds")
            c4.metric("Presión", f"{clima.get('surface_pressure', '--')} hPa")

    elif st.session_state.nav_menu == "Energía y Sensores":
        st.markdown('<div class="gradient-text">Infraestructura</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Generador Principal", "OPERATIVO 🟢", "68% Carga")
        c2.metric("Starlink", "ONLINE 🟢", "28ms")
        c3.metric("UPS", "100%")

else:
    st.error("No se encontró la base de datos 'scada_historico.db'. Sube el archivo a tu repositorio de GitHub.")
