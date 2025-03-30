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
        columnas_necesarias = ['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024']
        df = df[[col for col in columnas_necesarias if col in df.columns]].copy()
        df = df.dropna(subset=['Voce']).fillna(0)

        df['Δ vs 2023'] = df['Accum. 2024'] - df['Accum. 2023']
        df['Δ vs Budget'] = df['Accum. 2024'] - df['Budget 2024']
        df['Δ% vs 2023'] = np.where(df['Accum. 2023'] != 0, df['Δ vs 2023'] / df['Accum. 2023'] * 100, np.nan)
        df['Δ% vs Budget'] = np.where(df['Budget 2024'] != 0, df['Δ vs Budget'] / df['Budget 2024'] * 100, np.nan)

        st.dataframe(df.style.background_gradient(cmap="Blues").format({
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

        st.subheader("📊 Indicatori Finanziari Chiave (2023 e 2024)")

        def get_val(df, voce, col):
            match = df[df['Voce'].str.contains(voce, case=False, na=False)]
            return float(match[col].values[0]) if not match.empty else np.nan

        valori = {
            'Totale Attivo': {yr: get_val(df_sp, 'Totale Attivo', str(yr)) for yr in [2023, 2024]},
            'Patrimonio Netto': {yr: get_val(df_sp, 'Patrimonio Netto', str(yr)) for yr in [2023, 2024]},
            'Debiti Finanziari': {yr: get_val(df_sp, 'Debiti Fin. Import', str(yr)) for yr in [2023, 2024]},
            'Attività Correnti': {yr: df_sp[df_sp['Tipo'] == 'Attività Correnti'][str(yr)].sum() for yr in [2023, 2024]},
            'Passività Correnti': {yr: df_sp[df_sp['Tipo'] == 'Passività Correnti'][str(yr)].sum() for yr in [2023, 2024]},
            'Utile Netto': {yr: get_val(df_sp, 'Utile Netto', str(yr)) for yr in [2023, 2024]},
            'Ricavi': {
                2023: get_val(df, 'Totale Ricavi', 'Accum. 2023'),
                2024: get_val(df, 'Totale Ricavi', 'Accum. 2024'),
            },
            'EBITDA': {
                2023: get_val(df, 'EBITDA', 'Accum. 2023'),
                2024: get_val(df, 'EBITDA', 'Accum. 2024'),
            },
            'Rimanenze': {
                2023: get_val(df_sp, 'Magazzino', '2023'),
                2024: get_val(df_sp, 'Magazzino', '2024'),
            },
            'Crediti Clienti': {
                2023: get_val(df_sp, 'Crediti vs Clienti', '2023'),
                2024: get_val(df_sp, 'Crediti vs Clienti', '2024'),
            },
            'Debiti Fornitori': {
                2023: get_val(df_sp, 'Debiti vs Fornitori', '2023'),
                2024: get_val(df_sp, 'Debiti vs Fornitori', '2024'),
            },
            'COGS': {
                2023: abs(get_val(df, 'Costo Merce', 'Accum. 2023') + get_val(df, 'Trasporto per Vendite', 'Accum. 2023')),
                2024: abs(get_val(df, 'Costo Merce', 'Accum. 2024') + get_val(df, 'Trasporto per Vendite', 'Accum. 2024')),
            }
        }

        ciclo_conversione = []
        for anno in [2023, 2024]:
            ricavi = valori['Ricavi'][anno]
            cogs = valori['COGS'][anno]
            ciclo_conversione.append({
                "Anno": anno,
                "DIO (Giorni Magazzino)": round(valori['Rimanenze'][anno] / (cogs / 365), 1) if cogs else np.nan,
                "DSO (Giorni Incasso Clienti)": round(valori['Crediti Clienti'][anno] / (ricavi / 365), 1) if ricavi else np.nan,
                "DPO (Giorni Pagamento Fornitori)": round(valori['Debiti Fornitori'][anno] / (cogs / 365), 1) if cogs else np.nan,
            })

        df_ciclo = pd.DataFrame(ciclo_conversione)
        df_ciclo["Periodo Medio di Maturazione"] = df_ciclo["DIO (Giorni Magazzino)"] + df_ciclo["DSO (Giorni Incasso Clienti)"] - df_ciclo["DPO (Giorni Pagamento Fornitori)"]

        st.subheader("🔄 Ciclo di Conversione di Cassa (DIO + DSO - DPO)")
        st.dataframe(df_ciclo.set_index("Anno").style.format("{:.1f}"), use_container_width=True)

        # Mostrar ratios nuevamente (por claridad)
        st.subheader("📈 Indicatori Finanziari Chiave (2023 e 2024) - Dettaglio")
        df_ratios = pd.DataFrame([{
            "Indicatore": k["Nome"],
            "Formula": k["Formula"],
            "2023": round(k["Valori"](valori)[0]*100, 1) if "%" in k["Range"] else round(k["Valori"](valori)[0], 2),
            "2024": round(k["Valori"](valori)[1]*100, 1) if "%" in k["Range"] else round(k["Valori"](valori)[1], 2),
            "Range": k["Range"],
            "Valutazione 2023": valuta(k["Valori"](valori)[0]*100 if "%" in k["Range"] else k["Valori"](valori)[0], k["Range"]),
            "Valutazione 2024": valuta(k["Valori"](valori)[1]*100 if "%" in k["Range"] else k["Valori"](valori)[1], k["Range"])
        } for k in ratios])

        st.dataframe(df_ratios.style.format({"2023": "{:.2f}", "2024": "{:.2f}"}), use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

