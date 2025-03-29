import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from groq import Groq

# 🎯 Configuración de la app
st.set_page_config(page_title="Analisi Conto Economico", page_icon="📊", layout="wide")
st.title("📊 Analisi Conto Economico 2023 vs 2024 vs Budget")

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
        df = pd.read_excel(uploaded_file, sheet_name="Conto_Economico")

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

        # 🤖 Comentario FP&A con IA
        st.subheader("🧠 Comentario automático de análisis FP&A")

        # Reducir la tabla para el prompt
        df_prompt = df[['Voce', 'Accum. 2023', 'Accum. 2024', 'Budget 2024', 'Δ vs 2023', 'Δ vs Budget']].copy()
        data_json = df_prompt.to_json(orient="records")

        prompt = f"""
Sei un analista finanziario senior. Analizza il seguente conto economico che confronta i risultati del 2024 con quelli del 2023 e con il budget.

Compiti:
- Identifica le variazioni più rilevanti.
- Commenta i trend positivi o negativi.
- Rileva eventuali superamenti del budget o sottoperformance.
- Suggerisci azioni correttive o interpretazioni strategiche.

Dati (formato JSON):
{data_json}
"""

        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Sei un analista esperto in controllo di gestione."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
        )

        commentary = response.choices[0].message.content
        st.markdown(commentary)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
