
import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from groq import Groq

st.set_page_config(page_title="Analisi Conto Economico", page_icon="📊", layout="wide")
st.title("📊 Analisi Conto Economico vs Budget")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in .env or en Streamlit Secrets.")
    st.stop()

uploaded_file = st.file_uploader("📁 Sube el archivo Conto_Economico_Analisis.xlsx", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Conto Economico")
        columnas_necesarias = ['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024']
        df = df[[col for col in columnas_necesarias if col in df.columns]].copy()
        df = df.dropna(subset=['Voce']).fillna(0)

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

        df_sp = pd.read_excel(uploaded_file, sheet_name="Stato Patrimoniale")
        df_sp.columns = [str(c).strip().replace("Accum. ", "") for c in df_sp.columns]
        df_sp = df_sp.dropna(subset=['Voce']).fillna(0)

        def get_val(df, voce, col):
            match = df[df['Voce'].str.contains(voce, case=False, na=False)]
            return float(match[col].values[0]) if not match.empty else np.nan

        def get_val_tipo(df, tipo, col):
            match = df[df['Tipo'].str.lower().str.strip() == tipo.lower()]
            return match[col].sum() if not match.empty else np.nan

        def get_val_voce(df, voce, col):
            match = df[df['Voce'].str.lower().str.strip() == voce.lower()]
            return match[col].values[0] if not match.empty else np.nan

        ricavi_2023 = get_val(df, "Totale Ricavi", "Accum. 2023")
        ricavi_2024 = get_val(df, "Totale Ricavi", "Accum. 2024")
        cogs_2023 = abs(get_val(df, "Costo Merce", "Accum. 2023") + get_val(df, "Trasporto per Vendite", "Accum. 2023"))
        cogs_2024 = abs(get_val(df, "Costo Merce", "Accum. 2024") + get_val(df, "Trasporto per Vendite", "Accum. 2024"))

        dso_2023 = get_val(df_sp, "Crediti v Clienti", "2023") / ricavi_2023 * 365
        dso_2024 = get_val(df_sp, "Crediti v Clienti", "2024") / ricavi_2024 * 365
        dpo_2023 = get_val(df_sp, "Debiti v Fornitori", "2023") / cogs_2023 * 365
        dpo_2024 = get_val(df_sp, "Debiti v Fornitori", "2024") / cogs_2024 * 365
        dio_2023 = abs(get_val(df_sp, "Magazzino", "2023") / cogs_2023 * 365)
        dio_2024 = abs(get_val(df_sp, "Magazzino", "2024") / cogs_2024 * 365)

        ciclo_2023 = dio_2023 + dso_2023 - dpo_2023
        ciclo_2024 = dio_2024 + dso_2024 - dpo_2024

        st.subheader("📊 Ciclo di Conversione di Cassa (DIO + DSO - DPO)")
        df_ciclo = pd.DataFrame({
            "Anno": [2023, 2024],
            "DIO (Giorni Magazzino)": [round(dio_2023, 1), round(dio_2024, 1)],
            "DSO (Giorni Incasso Clienti)": [round(dso_2023, 1), round(dso_2024, 1)],
            "DPO (Giorni Pagamento Fornitori)": [round(dpo_2023, 1), round(dpo_2024, 1)],
            "Periodo Medio di Maturazione": [round(ciclo_2023, 1), round(ciclo_2024, 1)]
        })
        st.dataframe(df_ciclo, use_container_width=True)

        st.subheader("📈 Indicatori Finanziari")

        valori = {
            'Totale Attivo': {'2023': get_val_tipo(df_sp, 'Totale Attivo', '2023'), '2024': get_val_tipo(df_sp, 'Totale Attivo', '2024')},
            'Patrimonio Netto': {'2023': get_val_tipo(df_sp, 'Patrimonio Netto', '2023'), '2024': get_val_tipo(df_sp, 'Patrimonio Netto', '2024')},
            'Debiti Finanziari': {'2023': get_val_tipo(df_sp, 'Debiti Finanziari', '2023'), '2024': get_val_tipo(df_sp, 'Debiti Finanziari', '2024')},
            'Attività Correnti': {'2023': get_val_tipo(df_sp, 'Attività Correnti', '2023'), '2024': get_val_tipo(df_sp, 'Attività Correnti', '2024')},
            'Passività Correnti': {'2023': get_val_tipo(df_sp, 'Passività Correnti', '2023'), '2024': get_val_tipo(df_sp, 'Passività Correnti', '2024')},
            'Utile Netto': {'2023': get_val_tipo(df_sp, 'Utile Netto', '2023'), '2024': get_val_tipo(df_sp, 'Utile Netto', '2024')},
            'Ricavi': {'2023': ricavi_2023, '2024': ricavi_2024},
            'EBITDA': {'2023': get_val_voce(df, 'ebitda', 'Accum. 2023'), '2024': get_val_voce(df, 'ebitda', 'Accum. 2024')},
        }

        # Rangos con umbrales triple (verde, naranja, rojo)
        semaforo_rules = {
            "Current Ratio": (1.2, 1.5),
            "Acid Test": (1.0, 1.3),
            "Debt to Equity": (1.5, 2.0),
            "Leverage": (2.0, 2.5),
            "ROA": (5, 8),
            "ROE": (10, 15),
            "Copertura Debito": (2, 3)
        }

        def valuta_tricolor(val, low, high, invert=False):
            if pd.isna(val):
                return "⚪"
            if invert:
                return "🟢" if val < low else "🟠" if val < high else "🔴"
            else:
                return "🔴" if val < low else "🟠" if val < high else "🟢"

        df_ratios = []
        for nome, (soglia_bassa, soglia_media) in semaforo_rules.items():
            is_percent = nome in ["ROA", "ROE"]
            invert = nome in ["Debt to Equity", "Leverage"]
            val_2023 = round(valori[nome.split()[0]]["2023"] / valori[nome.split()[-1]]["2023"], 4) if " " in nome else 0
            val_2024 = round(valori[nome.split()[0]]["2024"] / valori[nome.split()[-1]]["2024"], 4) if " " in nome else 0
        # Este bloque se completará según lo que quieras calcular...

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
