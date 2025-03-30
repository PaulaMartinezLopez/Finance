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
                return match[col].sum() if not match.empty else np.nan

            def get_val_exact_voce(df, voce_exact, col):
                match = df[df['Voce'].str.strip().str.lower() == voce_exact.lower()]
                return match[col].values[0] if not match.empty else np.nan

            return {
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

        valori = estrai_valori(df_sp, df)

        ratios = [
            {"Nome": "Current Ratio", "Formula": "Attività Correnti / Passività Correnti", "Valori": lambda d: (d['Attività Correnti']['2023'] / d['Passività Correnti']['2023'], d['Attività Correnti']['2024'] / d['Passività Correnti']['2024']), "Range": "> 1.2"},
            {"Nome": "Debt to Equity", "Formula": "Debiti Finanziari / Patrimonio Netto", "Valori": lambda d: (d['Debiti Finanziari']['2023'] / d['Patrimonio Netto']['2023'], d['Debiti Finanziari']['2024'] / d['Patrimonio Netto']['2024']), "Range": "< 1.5"},
            {"Nome": "Leverage", "Formula": "Totale Attivo / Patrimonio Netto", "Valori": lambda d: (d['Totale Attivo']['2023'] / d['Patrimonio Netto']['2023'], d['Totale Attivo']['2024'] / d['Patrimonio Netto']['2024']), "Range": "< 2.0"},
            {"Nome": "ROA", "Formula": "Utile Netto / Totale Attivo", "Valori": lambda d: (d['Utile Netto']['2023'] / d['Totale Attivo']['2023'], d['Utile Netto']['2024'] / d['Totale Attivo']['2024']), "Range": "> 5%"},
            {"Nome": "ROE", "Formula": "Utile Netto / Patrimonio Netto", "Valori": lambda d: (d['Utile Netto']['2023'] / d['Patrimonio Netto']['2023'], d['Utile Netto']['2024'] / d['Patrimonio Netto']['2024']), "Range": "> 10%"},
            {"Nome": "Copertura Debito", "Formula": "EBITDA / Debiti Finanziari", "Valori": lambda d: (d['EBITDA']['2023'] / d['Debiti Finanziari']['2023'], d['EBITDA']['2024'] / d['Debiti Finanziari']['2024']), "Range": "> 2"},
        ]

        def valuta(val, criterio):
            if ">" in criterio:
                soglia = float(criterio.split(">")[1].strip().replace("%", ""))
                return "Buono" if val > soglia else "Critico"
            elif "<" in criterio:
                soglia = float(criterio.split("<")[1].strip().replace("%", ""))
                return "Buono" if val < soglia else "Critico"
            return "N/A"

        tabella_ratios = []
        for r in ratios:
            try:
                val_2023, val_2024 = r["Valori"](valori)
                valut_2023 = valuta(val_2023 * 100 if "%" in r["Range"] else val_2023, r["Range"])
                valut_2024 = valuta(val_2024 * 100 if "%" in r["Range"] else val_2024, r["Range"])
                tabella_ratios.append({
                    "Indicatore": r["Nome"],
                    "Formula": r["Formula"],
                    "2023": round(val_2023 * 100, 1) if "%" in r["Range"] else round(val_2023, 2),
                    "2024": round(val_2024 * 100, 1) if "%" in r["Range"] else round(val_2024, 2),
                    "Range": r["Range"],
                    "Valutazione 2023": valut_2023,
                    "Valutazione 2024": valut_2024,
                })
            except Exception:
                continue

        df_ratios = pd.DataFrame(tabella_ratios)

        st.dataframe(df_ratios.style.format({
            "2023": "{:,.2f}",
            "2024": "{:,.2f}"
        }), use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
