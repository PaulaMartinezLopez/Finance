import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from groq import Groq

# Configuración de la app
st.set_page_config(page_title="Analisi Conto Economico", page_icon="📊", layout="wide")
st.title("📊 Analisi Conto Economico vs Budget")

# Cargar clave API
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in .env o Streamlit Secrets.")
    st.stop()

# Subida del archivo
uploaded_file = st.file_uploader("📁 Sube el archivo Conto_Economico_Analisis.xlsx", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Conto Economico")
        df = df[['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024']].dropna(subset=['Voce']).fillna(0)

        # Calcular desviaciones
        df['Δ vs 2023'] = df['Accum. 2024'] - df['Accum. 2023']
        df['Δ vs Budget'] = df['Accum. 2024'] - df['Budget 2024']
        df['Δ% vs 2023'] = np.where(df['Accum. 2023'] != 0, df['Δ vs 2023'] / df['Accum. 2023'] * 100, np.nan)
        df['Δ% vs Budget'] = np.where(df['Budget 2024'] != 0, df['Δ vs Budget'] / df['Budget 2024'] * 100, np.nan)

        st.dataframe(df.style.format({
            'Accum. 2023': '€{:,.0f}', 'Accum. 2024': '€{:,.0f}', 'Budget 2024': '€{:,.0f}',
            'Δ vs 2023': '€{:,.0f}', 'Δ vs Budget': '€{:,.0f}',
            'Δ% vs 2023': '{:.1f}%', 'Δ% vs Budget': '{:.1f}%'
        }), use_container_width=True)

        # Leer Stato Patrimoniale
        df_sp = pd.read_excel(uploaded_file, sheet_name="Stato Patrimoniale")
        df_sp.columns = [str(c).strip().replace("Accum. ", "") for c in df_sp.columns]
        df_sp = df_sp.dropna(subset=['Voce']).fillna(0)

        # Funciones auxiliares
        def get_val(df, voce, col):
            match = df[df['Voce'].str.contains(voce, case=False, na=False)]
            return float(match[col].values[0]) if not match.empty else np.nan

        def get_val_tipo(df, tipo, col):
            match = df[df['Tipo'].str.lower().str.strip() == tipo.lower()]
            return match[col].sum() if not match.empty else np.nan

        def get_val_voce(df, voce, col):
            match = df[df['Voce'].str.lower().str.strip() == voce.lower()]
            return match[col].values[0] if not match.empty else np.nan

        # Datos para ratios
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
            "DIO (giorni)": [round(dio_2023, 1), round(dio_2024, 1)],
            "DSO (giorni)": [round(dso_2023, 1), round(dso_2024, 1)],
            "DPO (giorni)": [round(dpo_2023, 1), round(dpo_2024, 1)],
            "Cash Conversion Cycle": [round(ciclo_2023, 1), round(ciclo_2024, 1)]
        })
        st.dataframe(df_ciclo, use_container_width=True)

        # Ratios financieros
        st.subheader("📈 Indicatori Finanziari con Semaforo")

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

        ratios_def = [
            {"Nome": "Current Ratio", "Formula": "Attività Correnti / Passività Correnti", "Valori": lambda d: (d['Attività Correnti']['2023'] / d['Passività Correnti']['2023'], d['Attività Correnti']['2024'] / d['Passività Correnti']['2024']), "Range": (1.2, 1.5), "Invert": False, "Formato": "x"},
            {"Nome": "Acid Test", "Formula": "(Attività Correnti - Magazzino) / Passività Correnti", "Valori": lambda d: (
                (d['Attività Correnti']['2023'] - get_val(df_sp, "Magazzino", "2023")) / d['Passività Correnti']['2023'],
                (d['Attività Correnti']['2024'] - get_val(df_sp, "Magazzino", "2024")) / d['Passività Correnti']['2024']
            ), "Range": (1.0, 1.3), "Invert": False, "Formato": "x"},
            {"Nome": "Debt to Equity", "Formula": "Debiti Fin. / Patr. Netto", "Valori": lambda d: (
                d['Debiti Finanziari']['2023'] / d['Patrimonio Netto']['2023'],
                d['Debiti Finanziari']['2024'] / d['Patrimonio Netto']['2024']
            ), "Range": (1.5, 2.0), "Invert": True, "Formato": "x"},
            {"Nome": "Leverage", "Formula": "Totale Attivo / Patr. Netto", "Valori": lambda d: (
                d['Totale Attivo']['2023'] / d['Patrimonio Netto']['2023'],
                d['Totale Attivo']['2024'] / d['Patrimonio Netto']['2024']
            ), "Range": (2.0, 2.5), "Invert": True, "Formato": "x"},
            {"Nome": "ROA", "Formula": "Utile Netto / Totale Attivo", "Valori": lambda d: (
                d['Utile Netto']['2023'] / d['Totale Attivo']['2023'] * 100,
                d['Utile Netto']['2024'] / d['Totale Attivo']['2024'] * 100
            ), "Range": (5, 8), "Invert": False, "Formato": "%"},
            {"Nome": "ROE", "Formula": "Utile Netto / Patrimonio Netto", "Valori": lambda d: (
                d['Utile Netto']['2023'] / d['Patrimonio Netto']['2023'] * 100,
                d['Utile Netto']['2024'] / d['Patrimonio Netto']['2024'] * 100
            ), "Range": (10, 15), "Invert": False, "Formato": "%"},
            {"Nome": "Copertura Debito", "Formula": "EBITDA / Debiti Finanziari", "Valori": lambda d: (
                d['EBITDA']['2023'] / d['Debiti Finanziari']['2023'],
                d['EBITDA']['2024'] / d['Debiti Finanziari']['2024']
            ), "Range": (2, 3), "Invert": False, "Formato": "x"},
        ]

        def semaforo(val, low, high, invert=False):
            if pd.isna(val): return "⚪"
            if invert:
                return "🟢" if val < low else "🟠" if val < high else "🔴"
            else:
                return "🔴" if val < low else "🟠" if val < high else "🟢"

        df_ratios = pd.DataFrame([{
            "Indicatore": r["Nome"],
            "Formula": r["Formula"],
            "2023": f"{r['Valori'](valori)[0]:.2f}%" if r["Formato"] == "%" else round(r["Valori"](valori)[0], 2),
            "2024": f"{r['Valori'](valori)[1]:.2f}%" if r["Formato"] == "%" else round(r["Valori"](valori)[1], 2),
            "Rango Teorico": f"{'< ' if r['Invert'] else '> '}{r['Range'][0]} / {'< ' if r['Invert'] else '> '}{r['Range'][1]}",
            "Valutazione 2023": semaforo(r["Valori"](valori)[0], *r["Range"], invert=r["Invert"]),
            "Valutazione 2024": semaforo(r["Valori"](valori)[1], *r["Range"], invert=r["Invert"]),
        } for r in ratios_def])

        st.dataframe(df_ratios, use_container_width=True)

        # Comentario automático
        st.subheader("🧠 Comentario automatico di analisi FP&A")
        df_prompt = df[['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024', 'Δ vs 2023', 'Δ vs Budget']]
        prompt_json = df_prompt.to_json(orient="records")
        ratios_json = df_ratios.to_json(orient="records")

        prompt = f"""
Sei un analista finanziario senior. Analizza il seguente conto economico confrontando il 2024 con il 2023 e il budget.
Commenta le variazioni principali, valuta i trend e suggerisci azioni. Analizza anche i seguenti indicatori finanziari:

Conto Economico (JSON):
{prompt_json}

Indicatori Finanziari (JSON):
{ratios_json}
"""

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Sei un esperto di controllo di gestione e FP&A."},
                {"role": "user", "content": prompt}
            ],
        )
        st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
