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

        st.dataframe(df.style.format({
            'Accum. 2023': '€{:,.0f}', 'Accum. 2024': '€{:,.0f}',
            'Budget 2024': '€{:,.0f}', 'Δ vs 2023': '€{:,.0f}',
            'Δ vs Budget': '€{:,.0f}', 'Δ% vs 2023': '{:.1f}%',
            'Δ% vs Budget': '{:.1f}%'
        }), use_container_width=True)

        # 📈 Cargar Stato Patrimoniale para ratios
        df_sp = pd.read_excel(uploaded_file, sheet_name="Stato Patrimoniale")
        df_sp.columns = [str(c).strip().replace("Accum. ", "") for c in df_sp.columns]
        df_sp = df_sp.dropna(subset=['Voce']).fillna(0)

        # Funciones para obtener valores
        def get_val(df, voce, col):
            match = df[df['Voce'].str.contains(voce, case=False, na=False)]
            return float(match[col].values[0]) if not match.empty else np.nan

        # 📊 Ratios operativos (DIO, DSO, DPO)
        ricavi_2023 = get_val(df, "Totale Ricavi", "Accum. 2023")
        ricavi_2024 = get_val(df, "Totale Ricavi", "Accum. 2024")
        cogs_2023 = abs(get_val(df, "Costo Merce", "Accum. 2023") + get_val(df, "Trasporto per Vendite", "Accum. 2023"))
        cogs_2024 = abs(get_val(df, "Costo Merce", "Accum. 2024") + get_val(df, "Trasporto per Vendite", "Accum. 2024"))
        magazzino_2023 = get_val(df_sp, "Magazzino", "2023")
        magazzino_2024 = get_val(df_sp, "Magazzino", "2024")
        clienti_2023 = get_val(df_sp, "Crediti vs Clienti", "2023")
        clienti_2024 = get_val(df_sp, "Crediti vs Clienti", "2024")
        fornitori_2023 = get_val(df_sp, "Debiti vs Fornitori", "2023")
        fornitori_2024 = get_val(df_sp, "Debiti vs Fornitori", "2024")

        dio_2023 = abs(magazzino_2023 / cogs_2023 * 365)
        dio_2024 = abs(magazzino_2024 / cogs_2024 * 365)
        dso_2023 = clienti_2023 / ricavi_2023 * 365
        dso_2024 = clienti_2024 / ricavi_2024 * 365
        dpo_2023 = fornitori_2023 / cogs_2023 * 365
        dpo_2024 = fornitori_2024 / cogs_2024 * 365
        ciclo_2023 = dio_2023 + dso_2023 - dpo_2023
        ciclo_2024 = dio_2024 + dso_2024 - dpo_2024

        st.subheader("📊 Ciclo di Conversione di Cassa")
        df_ciclo = pd.DataFrame({
            "Anno": [2023, 2024],
            "DIO (Giorni Magazzino)": [round(dio_2023, 1), round(dio_2024, 1)],
            "DSO (Giorni Incasso Clienti)": [round(dso_2023, 1), round(dso_2024, 1)],
            "DPO (Giorni Pagamento Fornitori)": [round(dpo_2023, 1), round(dpo_2024, 1)],
            "Periodo Medio di Maturazione": [round(ciclo_2023, 1), round(ciclo_2024, 1)]
        })
        st.dataframe(df_ciclo, use_container_width=True)

        # 📈 Otros indicadores financieros clave
        utile_netto_2023 = get_val(df, "Risultato di Gruppo", "Accum. 2023")
        utile_netto_2024 = get_val(df, "Risultato di Gruppo", "Accum. 2024")
        ebitda_2023 = get_val(df, "EBITDA", "Accum. 2023")
        ebitda_2024 = get_val(df, "EBITDA", "Accum. 2024")
        att_corr_2023 = get_val(df_sp, "Attività Correnti", "2023")
        att_corr_2024 = get_val(df_sp, "Attività Correnti", "2024")
        pass_corr_2023 = get_val(df_sp, "Passività Correnti", "2023")
        pass_corr_2024 = get_val(df_sp, "Passività Correnti", "2024")
        att_tot_2023 = get_val(df_sp, "Totale Attivo", "2023")
        att_tot_2024 = get_val(df_sp, "Totale Attivo", "2024")
        patrimonio_netto_2023 = get_val(df_sp, "Patrimonio Netto", "2023")
        patrimonio_netto_2024 = get_val(df_sp, "Patrimonio Netto", "2024")
        debiti_fin_2023 = get_val(df_sp, "Debiti Fin. Import", "2023")
        debiti_fin_2024 = get_val(df_sp, "Debiti Fin. Import", "2024")

        ratios = [
            {"Indicatore": "Current Ratio", "Formula": "Att. Correnti / Pass. Correnti", "2023": att_corr_2023 / pass_corr_2023, "2024": att_corr_2024 / pass_corr_2024, "Range": "> 1.2"},
            {"Indicatore": "Acid Test", "Formula": "(Att. Correnti - Magazzino) / Pass. Correnti", "2023": (att_corr_2023 - magazzino_2023) / pass_corr_2023, "2024": (att_corr_2024 - magazzino_2024) / pass_corr_2024, "Range": "> 1"},
            {"Indicatore": "Asset Turnover", "Formula": "Ricavi / Totale Attivo", "2023": ricavi_2023 / att_tot_2023, "2024": ricavi_2024 / att_tot_2024, "Range": "> 1"},
            {"Indicatore": "ROA", "Formula": "Utile Netto / Totale Attivo", "2023": utile_netto_2023 / att_tot_2023, "2024": utile_netto_2024 / att_tot_2024, "Range": "> 5%"},
            {"Indicatore": "ROE", "Formula": "Utile Netto / Patrimonio Netto", "2023": utile_netto_2023 / patrimonio_netto_2023, "2024": utile_netto_2024 / patrimonio_netto_2024, "Range": "> 10%"},
            {"Indicatore": "Leverage", "Formula": "Totale Attivo / Patrimonio Netto", "2023": att_tot_2023 / patrimonio_netto_2023, "2024": att_tot_2024 / patrimonio_netto_2024, "Range": "< 2.0"},
            {"Indicatore": "Debt to Equity", "Formula": "Debiti Fin. / Patrimonio Netto", "2023": debiti_fin_2023 / patrimonio_netto_2023, "2024": debiti_fin_2024 / patrimonio_netto_2024, "Range": "< 1.5"},
            {"Indicatore": "Copertura Debito", "Formula": "EBITDA / Debiti Fin.", "2023": ebitda_2023 / debiti_fin_2023, "2024": ebitda_2024 / debiti_fin_2024, "Range": "> 2"},
        ]

        def valuta(v, criterio):
            if ">" in criterio:
                soglia = float(criterio.replace(">", "").replace("%", "").strip())
                return "Buono" if v > soglia / (100 if "%" in criterio else 1) else "Critico"
            elif "<" in criterio:
                soglia = float(criterio.replace("<", "").replace("%", "").strip())
                return "Buono" if v < soglia / (100 if "%" in criterio else 1) else "Critico"
            return "N/A"

        for r in ratios:
            r["Valutazione 2023"] = valuta(r["2023"], r["Range"])
            r["Valutazione 2024"] = valuta(r["2024"], r["Range"])
            if "%" in r["Range"]:
                r["2023"] = round(r["2023"] * 100, 1)
                r["2024"] = round(r["2024"] * 100, 1)
            else:
                r["2023"] = round(r["2023"], 2)
                r["2024"] = round(r["2024"], 2)

        df_ratios = pd.DataFrame(ratios)
        st.subheader("📈 Indicatori Finanziari Principali")
        st.dataframe(df_ratios, use_container_width=True)

        # 🧠 Comentario FP&A con IA
        st.subheader("🧠 Comentario automatico con IA")
        df_prompt = df[['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024', 'Δ vs 2023', 'Δ vs Budget']].copy()
        data_json = df_prompt.to_json(orient="records")
        ratios_json = df_ratios.to_json(orient="records")

        prompt = f"""
Sei un analista finanziario. Analizza il seguente conto economico e i principali indicatori:
1. Commenta i risultati del 2024 rispetto al 2023 e al budget.
2. Evidenzia variazioni rilevanti, punti di forza e criticità.
3. Valuta i KPI di liquidità, redditività, indebitamento e operativi (DIO, DSO, DPO).
4. Suggerisci azioni o priorità.

Conto Economico (JSON):
{data_json}

Indicatori Finanziari (JSON):
{ratios_json}
"""

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sei un esperto in controllo di gestione e FP&A."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
        )

        st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

