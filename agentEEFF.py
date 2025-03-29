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
        df_sp = df_sp.dropna(subset=['Voce']).fillna(0)

        st.subheader("📊 Indicatori Finanziari Chiave (2023 e 2024)")

        mapeo = {
            "Totale Attivo": "Totale Attivo",
            "Patrimonio Netto": "Patrimonio Netto",
            "Debiti Finanziari": "Debiti Fin. Import",
            "Attività Correnti": "Attività Correnti",
            "Passività Correnti": "Passività Correnti",
            "Crediti Clienti": "Crediti vs Clienti",
            "Debiti Fornitori": "Debiti vs Fornitori",
            "Rimanenze": "Magazzino",
        }

        def get_val(df, voce, col):
            riga = df[df['Voce'].str.contains(voce, case=False, na=False)]
            return float(riga[col].values[0]) if not riga.empty else np.nan

        def estrai_valori(df_sp, df_ce):
            dati = {}
            for nome_logico, voce_excel in mapeo.items():
                dati[nome_logico] = {
                    '2023': get_val(df_sp, voce_excel, 'Accum. 2023'),
                    '2024': get_val(df_sp, voce_excel, 'Accum. 2024'),
                }
            dati['EBITDA'] = {
                '2023': get_val(df_ce, "EBITDA", 'Accum. 2023'),
                '2024': get_val(df_ce, "EBITDA", 'Accum. 2024'),
            }
            dati['Utile Netto'] = {
                '2023': get_val(df_ce, "Risultato di Gruppo", 'Accum. 2023'),
                '2024': get_val(df_ce, "Risultato di Gruppo", 'Accum. 2024'),
            }
            dati['Ricavi'] = {
                '2023': get_val(df_ce, "Totale Ricavi", 'Accum. 2023'),
                '2024': get_val(df_ce, "Totale Ricavi", 'Accum. 2024'),
            }
            return dati

        valori = estrai_valori(df_sp, df)

        ratios = [
            {
                "Nome": "Current Ratio",
                "Formula": "Attività Correnti / Passività Correnti",
                "Valori": lambda d: (
                    d['Attività Correnti']['2023'] / d['Passività Correnti']['2023'],
                    d['Attività Correnti']['2024'] / d['Passività Correnti']['2024']
                ),
                "Range": "> 1.2"
            },
            {
                "Nome": "Debt to Equity",
                "Formula": "Debiti Finanziari / Patrimonio Netto",
                "Valori": lambda d: (
                    d['Debiti Finanziari']['2023'] / d['Patrimonio Netto']['2023'],
                    d['Debiti Finanziari']['2024'] / d['Patrimonio Netto']['2024']
                ),
                "Range": "< 1.5"
            },
            {
                "Nome": "Leverage",
                "Formula": "Totale Attivo / Patrimonio Netto",
                "Valori": lambda d: (
                    d['Totale Attivo']['2023'] / d['Patrimonio Netto']['2023'],
                    d['Totale Attivo']['2024'] / d['Patrimonio Netto']['2024']
                ),
                "Range": "< 2.0"
            },
            {
                "Nome": "ROA",
                "Formula": "Utile Netto / Totale Attivo",
                "Valori": lambda d: (
                    d['Utile Netto']['2023'] / d['Totale Attivo']['2023'],
                    d['Utile Netto']['2024'] / d['Totale Attivo']['2024']
                ),
                "Range": "> 5%"
            },
            {
                "Nome": "ROE",
                "Formula": "Utile Netto / Patrimonio Netto",
                "Valori": lambda d: (
                    d['Utile Netto']['2023'] / d['Patrimonio Netto']['2023'],
                    d['Utile Netto']['2024'] / d['Patrimonio Netto']['2024']
                ),
                "Range": "> 10%"
            },
            {
                "Nome": "Copertura Debito",
                "Formula": "EBITDA / Debiti Finanziari",
                "Valori": lambda d: (
                    d['EBITDA']['2023'] / d['Debiti Finanziari']['2023'],
                    d['EBITDA']['2024'] / d['Debiti Finanziari']['2024']
                ),
                "Range": "> 2"
            },
        ]

        def valuta(val, criterio):
            if ">" in criterio:
                soglia = float(criterio.split(">")[1].strip().replace("%", ""))
                return "Buono" if val > soglia else "Critico"
            elif "<" in criterio:
                soglia = float(criterio.split("<")[1].strip().replace("%", ""))
                return "Buono" if val < soglia else "Critico"
            else:
                return "N/A"

        tabella_ratios = []

        for r in ratios:
            try:
                val_2023, val_2024 = r["Valori"](valori)
                valut_2023 = valuta(val_2023*100 if "%" in r["Range"] else val_2023, r["Range"])
                valut_2024 = valuta(val_2024*100 if "%" in r["Range"] else val_2024, r["Range"])

                tabella_ratios.append({
                    "Indicatore": r["Nome"],
                    "Formula": r["Formula"],
                    "2023": round(val_2023*100, 1) if "%" in r["Range"] else round(val_2023, 2),
                    "2024": round(val_2024*100, 1) if "%" in r["Range"] else round(val_2024, 2),
                    "Range": r["Range"],
                    "Valutazione 2023": valut_2023,
                    "Valutazione 2024": valut_2024,
                })
            except Exception:
                continue

        df_ratios = pd.DataFrame(tabella_ratios)
        st.dataframe(df_ratios.style.highlight_null(null_color="red").format({
            "2023": "{:,.2f}",
            "2024": "{:,.2f}"
        }), use_container_width=True)

        ratios_json = df_ratios.to_json(orient="records")

        # 🧠 Comentario FP&A con IA
        st.subheader("🧠 Comentario automático di analisi FP&A")

        df_prompt = df[['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024', 'Δ vs 2023', 'Δ vs Budget']].copy()
        data_json = df_prompt.to_json(orient="records")

        prompt = f"""
Sei un analista finanziario senior. Analizza il seguente conto economico che confronta i risultati del 2024 con quelli del 2023 e con il budget.
Compiti:
- Identifica le variazioni più rilevanti.
- Commenta i trend positivi o negativi.
- Rileva eventuali superamenti del budget o sottoperformance.
- Analizza i principali indicatori finanziari calcolati.
- Suggerisci azioni correttive o interpretazioni strategiche.

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
