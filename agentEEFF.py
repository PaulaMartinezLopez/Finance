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

        st.dataframe(df.style.format({
            'Accum. 2023': '€{:,.0f}',
            'Accum. 2024': '€{:,.0f}',
            'Budget 2024': '€{:,.0f}',
            'Δ vs 2023': '€{:,.0f}',
            'Δ vs Budget': '€{:,.0f}',
            'Δ% vs 2023': '{:.1f}%',
            'Δ% vs Budget': '{:.1f}%'
        }), use_container_width=True)

        # 📈 Cargar Stato Patrimoniale para ratios
        df_sp = pd.read_excel(uploaded_file, sheet_name="Stato Patrimoniale")
        df_sp.columns = [str(c).strip().replace("Accum. ", "") for c in df_sp.columns]
        df_sp = df_sp.dropna(subset=['Voce']).fillna(0)

        st.subheader("📊 Indicatori Finanziari Chiave (2023 e 2024)")

        def estrai_valori(df_sp, df_ce):
            def get_val_by_voce(df, voce, col):
                match = df[df['Voce'].str.strip().str.lower() == voce.lower()]
                return match[col].values[0] if not match.empty else np.nan

            def get_val_by_tipo(df, tipo, col):
                match = df[df['Tipo'].str.strip().str.lower() == tipo.lower()]
                return match[col].sum() if not match.empty else np.nan

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
                    '2023': get_val_by_tipo(df_sp, 'Attività Correnti', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Attività Correnti', '2024'),
                },
                'Passività Correnti': {
                    '2023': get_val_by_tipo(df_sp, 'Passività Correnti', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Passività Correnti', '2024'),
                },
                'Magazzino': {
                    '2023': get_val_by_voce(df_sp, 'Magazzino', '2023'),
                    '2024': get_val_by_voce(df_sp, 'Magazzino', '2024'),
                },
                'Crediti Clienti': {
                    '2023': get_val_by_voce(df_sp, 'Crediti v Clienti', '2023'),
                    '2024': get_val_by_voce(df_sp, 'Crediti v Clienti', '2024'),
                },
                'Debiti Fornitori': {
                    '2023': get_val_by_voce(df_sp, 'Debiti v Fornitori', '2023'),
                    '2024': get_val_by_voce(df_sp, 'Debiti v Fornitori', '2024'),
                },
                'Utile Netto': {
                    '2023': get_val_by_tipo(df_sp, 'Utile Netto', '2023'),
                    '2024': get_val_by_tipo(df_sp, 'Utile Netto', '2024'),
                },
                'Ricavi': {
                    '2023': get_val_by_voce(df_ce, 'Totale Ricavi', 'Accum. 2023'),
                    '2024': get_val_by_voce(df_ce, 'Totale Ricavi', 'Accum. 2024'),
                },
                'EBITDA': {
                    '2023': get_val_by_voce(df_ce, 'ebitda', 'Accum. 2023'),
                    '2024': get_val_by_voce(df_ce, 'ebitda', 'Accum. 2024'),
                },
                'Costo del Venduto': {
                    '2023': get_val_by_voce(df_ce, 'Costo Merce', 'Accum. 2023') + get_val_by_voce(df_ce, 'Trasporto per Vendite', 'Accum. 2023'),
                    '2024': get_val_by_voce(df_ce, 'Costo Merce', 'Accum. 2024') + get_val_by_voce(df_ce, 'Trasporto per Vendite', 'Accum. 2024'),
                },
            }
            return dati

        valori = estrai_valori(df_sp, df)

        # 📒 Calcular ciclo de conversión de efectivo
        def safe_ratio(numer, denom):
            return numer / denom if denom != 0 else np.nan

        ciclo = []
        for year in ['2023', '2024']:
            DIO = safe_ratio(valori['Magazzino'][year], valori['Costo del Venduto'][year]) * 365
            DSO = safe_ratio(valori['Crediti Clienti'][year], valori['Ricavi'][year]) * 365
            DPO = safe_ratio(valori['Debiti Fornitori'][year], valori['Costo del Venduto'][year]) * 365
            ciclo.append({
                "Anno": year,
                "DIO (Giorni Magazzino)": round(DIO, 1),
                "DSO (Giorni Incasso Clienti)": round(DSO, 1),
                "DPO (Giorni Pagamento Fornitori)": round(DPO, 1),
                "Periodo Medio di Maturazione": round(DIO + DSO - DPO, 1)
            })

        df_ciclo = pd.DataFrame(ciclo)
        st.subheader("📊 Ciclo di Conversione di Cassa (DIO + DSO - DPO)")
        st.dataframe(df_ciclo.set_index("Anno"), use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

