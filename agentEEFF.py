import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from groq import Groq

# 🎯 Configuración de la app
st.set_page_config(page_title="Analisi Conto Economico", page_icon="📊", layout="wide")
st.title("📊 Analisi Conto Economico vs Budget")

# 🔐 Cargar clave API
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in .env or en Streamlit Secrets.")
    st.stop()

# 📂 Subida de archivo
uploaded_file = st.file_uploader("📁 Sube el archivo Conto_Economico_Budget.xlsx", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Conto Economico")

        # 🧹 Filtrar y limpiar datos
        columnas_necesarias = ['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024']
        df = df[[col for col in columnas_necesarias if col in df.columns]].copy()
        df = df.dropna(subset=['Voce']).fillna(0)

        # 🧮 Cálculo de desviaciones
        df['Δ vs 2023'] = df['Accum. 2024'] - df['Accum. 2023']
        df['Δ vs Budget'] = df['Accum. 2024'] - df['Budget 2024']
        df['Δ% vs 2023'] = np.where(df['Accum. 2023'] != 0, df['Δ vs 2023'] / df['Accum. 2023'] * 100, np.nan)
        df['Δ% vs Budget'] = np.where(df['Budget 2024'] != 0, df['Δ vs Budget'] / df['Budget 2024'] * 100, np.nan)

        st.subheader("📋 Conto Economico con Deviazioni")
        st.dataframe(df.style.format({
            'Accum. 2023': '€{:,.0f}',
            'Accum. 2024': '€{:,.0f}',
            'Budget 2024': '€{:,.0f}',
            'Δ vs 2023': '€{:,.0f}',
            'Δ vs Budget': '€{:,.0f}',
            'Δ% vs 2023': '{:.1f}%',
            'Δ% vs Budget': '{:.1f}%'
        }).background_gradient(axis=None, cmap="Blues"), use_container_width=True)

        # 📈 Cargar Stato Patrimoniale para ratios
        df_sp = pd.read_excel(uploaded_file, sheet_name="Stato Patrimoniale")
        df_sp.columns = [str(c).strip().replace("Accum. ", "") for c in df_sp.columns]
        df_sp = df_sp.dropna(subset=['Voce']).fillna(0)

        st.subheader("📊 Indicatori Finanziari Chiave (2023 e 2024)")

        def estrai_valori(df_sp, df_ce):
            def get_val_by_tipo(df, tipo, col):
                match = df[df['Tipo'].str.lower().str.strip() == tipo.lower()]
                if match.empty:
                    st.warning(f"⚠️ Tipo '{tipo}' no encontrado en Stato Patrimoniale.")
                    return np.nan
                val = match[col].sum()
                if pd.isna(val):
                    st.warning(f"⚠️ Valor nulo para '{tipo}' en columna {col}.")
                return float(val)

            def get_val_exact_voce(df, voce_exact, col):
                match = df[df['Voce'].str.strip().str.lower() == voce_exact.lower()]
                if match.empty:
                    st.warning(f"⚠️ Línea exacta '{voce_exact}' no encontrada en Conto Economico.")
                    return np.nan
                val = match[col].values[0]
                if pd.isna(val):
                    st.warning(f"⚠️ Valor nulo en '{voce_exact}' ({col})")
                return float(val)

            dati = {
                'Totale Attivo': {
                    '2023': get_val_by_tipo(df_sp, 'Totale Attivo', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Totale Attivo', '2024'),
                },
                'Patrimonio Netto': {
                    '2023': get_val_by_tipo(df_sp, 'Patrimonio Netto', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Patrimonio Netto', '2024'),
                },
                'Debiti Finanziari': {
                    '2023': get_val_by_tipo(df_sp, 'Debiti Finanziari', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Debiti Finanziari', '2024'),
                },
                'Attività Correnti': {
                    '2023': df_sp[df_sp['Tipo'] == 'Attività Correnti']['2023'].sum(),
                    '2024': df_sp[df_sp['Tipo'] == 'Attività Correnti']['2024'].sum(),
                },
                'Passività Correnti': {
                    '2023': df_sp[df_sp['Tipo'] == 'Passività Correnti']['2023'].sum(),
                    '2024': df_sp[df_sp['Tipo'] == 'Passività Correnti']['2024'].sum(),
                },
                'Utile Netto': {
                    '2023': get_val_by_tipo(df_sp, 'Utile Netto', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Utile Netto', '2024'),
                },
                'Ricavi': {
                    '2023': get_val_exact_voce(df_ce, 'Totale Ricavi', 'Accum. 2023'),
                    '2024': get_val_exact_voce(df_ce, 'Totale Ricavi', 'Accum. 2024'),
                },
                'EBITDA': {
                    '2023': get_val_exact_voce(df_ce, 'ebitda', 'Accum. 2023'),
                    '2024': get_val_exact_voce(df_ce, 'ebitda', 'Accum. 2024'),
                },
                'Magazzino': {
                    '2023': get_val_exact_voce(df_sp, 'Magazzino', '2023'),
                    '2024': get_val_exact_voce(df_sp, 'Magazzino', '2024'),
                },
                'Crediti Clienti': {
                    '2023': get_val_exact_voce(df_sp, 'Crediti v Clienti', '2023'),
                    '2024': get_val_exact_voce(df_sp, 'Crediti v Clienti', '2024'),
                },
                'Debiti Fornitori': {
                    '2023': get_val_exact_voce(df_sp, 'Debiti v Fornitori', '2023'),
                    '2024': get_val_exact_voce(df_sp, 'Debiti v Fornitori', '2024'),
                },
                'COGS': {
                    '2023': abs(get_val_exact_voce(df_ce, 'Costo Merce', 'Accum. 2023') + get_val_exact_voce(df_ce, 'Trasporto per Vendite', 'Accum. 2023')),
                    '2024': abs(get_val_exact_voce(df_ce, 'Costo Merce', 'Accum. 2024') + get_val_exact_voce(df_ce, 'Trasporto per Vendite', 'Accum. 2024')),
                },
            }
            return dati

        valori = estrai_valori(df_sp, df)

        # Aquí seguiría el bloque de ratios y análisis como ya lo tenías definido...

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
