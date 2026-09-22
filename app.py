%%writefile app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Salmonera", page_icon="🐟", layout="wide")
st.title("🌊 Centro de Control Unificado - Pontón Alfa")
st.markdown("Monitorización en tiempo real de Telemetría, Biología y Alimentación.")

SHEET_URL = "https://docs.google.com/spreadsheets/d/115BG0pdWQxVlLVozHzI_ken4P0El_fZar_GTu3cRsus/export?format=csv"

def cargar_datos():
    # Leer el CSV y limpiar filas completamente vacías
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    return df

try:
    df = cargar_datos()
    
    # Limpieza extrema: Forzar conversión numérica en todas las columnas operativas
    cols = ['oxigeno_mgl', 'estado_alimentacion', 'temperatura_c', 'tasa_alimento_kg_min', 'conteo_algas_celulas']
    for col in cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Tomar la última fila válida
    actual = df.iloc[-1]
    
    # Asignar variables limpias
    oxigeno = float(actual['oxigeno_mgl'])
    alimentacion = int(actual['estado_alimentacion'])
    temp = float(actual['temperatura_c'])
    algas = int(actual['conteo_algas_celulas'])
    tasa = float(actual['tasa_alimento_kg_min'])

    # Lógica de Alertas
    if oxigeno < 5.0 and alimentacion == 1:
        st.error(f"🚨 **¡ALERTA CRÍTICA DE MORTANDAD!** Oxígeno a {oxigeno} mg/L con sopladores activos.")
        if st.button("🛑 DETENER ALIMENTACIÓN DE INMEDIATO"):
            st.warning("Señal enviada a los sopladores: APAGADOS. Deteniendo flujo de pellets.")
            
    if temp > 13.5:
        st.warning(f"⚠️ **Aviso de Temperatura:** {temp}°C. Sugerimos reducir ración para evitar estrés.")

    # Tarjetas de Indicadores
    st.markdown("### 📊 Indicadores Actuales")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Oxígeno Disuelto", f"{oxigeno} mg/L", "Crítico" if oxigeno < 5.0 else "Normal", delta_color="inverse")
    col2.metric("Temperatura", f"{temp} °C")
    col3.metric("Tasa Alimentación", f"{tasa} kg/min", "Activo" if alimentacion == 1 else "Apagado")
    col4.metric("Conteo Algas", f"{algas} células")

    # Gráfico Histórico
    st.markdown("---")
    st.markdown("### 📈 Tendencia de Oxígeno vs Alimentación")
    grafico_data = df.set_index('timestamp')[['oxigeno_mgl', 'tasa_alimento_kg_min']]
    st.line_chart(grafico_data)

except Exception as e:
    st.error(f"Error al procesar los datos. Detalle técnico: {e}")