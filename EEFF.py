import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.sidebar.title("📊 Navigazione")

# Upload files
st.sidebar.subheader("Carica i file Excel")
uploaded_ce = st.sidebar.file_uploader("Conto_Economico_Budget.xlsx", type=["xlsx"])
uploaded_mappings = st.sidebar.file_uploader("Mappings.xlsx", type=["xlsx"])
uploaded_output = st.sidebar.file_uploader("Output design.xlsx", type=["xlsx"])

if not uploaded_ce or not uploaded_mappings or not uploaded_output:
    st.warning("⚠️ Carica tutti e tre i file per continuare.")
    st.stop()

# Read Excel files
conto = pd.read_excel(uploaded_ce, sheet_name="Conto Economico")
mappings = pd.read_excel(uploaded_mappings, sheet_name="Conto_Economico")
# Placeholder: you can use this for future features
output_design = pd.read_excel(uploaded_output, sheet_name=0)

pagina = st.sidebar.radio("Seleziona la sezione:", [
    "Conto Economico",
    "Stato Patrimoniale + Indicatori",
    "Rendiconto Finanziario"
])

def format_miles(x):
    try:
        return f"{x:,.0f}".replace(",", ".")
    except:
        return x

def format_percent(x):
    try:
        return f"{x:.1%}"
    except:
        return x

if pagina == "Conto Economico":
    st.title("📘 Conto Economico")

    conto = conto.fillna(0)
    mappings = mappings[["Voce", "Tipo"]]
    df = pd.merge(conto, mappings, on="Voce", how="left")
    df = df.drop_duplicates(subset=["Voce"], keep="first")

    periodi = list(conto.columns[1:4])
    index1 = 2 if len(periodi) > 2 else len(periodi) - 1
    index2 = 1 if len(periodi) > 1 else 0

    col1, col2 = st.columns(2)
    with col1:
        periodo_1 = st.selectbox("Periodo 1", periodi, index=index1)
    with col2:
        periodo_2 = st.selectbox("Periodo 2", periodi, index=index2)

    df["Δ"] = df[periodo_1] - df[periodo_2]
    df["Δ %"] = np.where(
        df[periodo_2] != 0,
        (df[periodo_1] - df[periodo_2]) / abs(df[periodo_2]),
        np.nan
    )

    mostrar_detalles = st.checkbox("Mostrar dettagli", value=False)

    output = []
    for tipo in df["Tipo"].dropna().unique():
        subset = df[df["Tipo"] == tipo]
        total = subset[[periodo_1, periodo_2, "Δ"]].sum().to_dict()
        delta_pct = (total["Δ"] / abs(total[periodo_2])) if total[periodo_2] != 0 else np.nan
        riga_totale = {
            "Tipo": tipo,
            periodo_1: total[periodo_1],
            periodo_2: total[periodo_2],
            "Δ": total["Δ"],
            "Δ %": delta_pct
        }
        output.append(riga_totale)

        if mostrar_detalles and tipo in ["Vendite", "Altri Opex"]:
            for _, row in subset.iterrows():
                r = {
                    "Tipo": row["Tipo"],
                    "Voce": row["Voce"],
                    periodo_1: row[periodo_1],
                    periodo_2: row[periodo_2],
                    "Δ": row["Δ"],
                    "Δ %": row["Δ %"]
                }
                output.append(r)

    kpi_fissi = ["Marginalità Vendite lorda", "EBITDA", "EBIT", "EBT", "Risultato di Gruppo"]
    kpi_rows = df[df["Voce"].isin(kpi_fissi) & df["Tipo"].isna()].copy()
    for _, row in kpi_rows.iterrows():
        r = {
            "Tipo": "",
            "Voce": row["Voce"],
            periodo_1: row[periodo_1],
            periodo_2: row[periodo_2],
            "Δ": row["Δ"],
            "Δ %": row["Δ %"]
        }
        output.append(r)

    df_resultado = pd.DataFrame(output)

    for col in [periodo_1, periodo_2, "Δ"]:
        df_resultado[col] = df_resultado[col].apply(format_miles)

    df_resultado["Δ %"] = df_resultado["Δ %"].apply(format_percent)

    if not mostrar_detalles:
        df_resultado = df_resultado.drop(columns=["Voce"], errors="ignore")

    st.dataframe(df_resultado, use_container_width=True, height=800)

elif pagina == "Stato Patrimoniale + Indicatori":
    st.title("🏦 Stato Patrimoniale + Indicatori")
    df = pd.read_excel(uploaded_ce, sheet_name="Stato Patrimoniale")
    df = df.fillna(0)
    df.iloc[:, 1:] = df.iloc[:, 1:].applymap(format_miles)
    st.dataframe(df, use_container_width=True, height=800)

elif pagina == "Rendiconto Finanziario":
    st.title("💧 Rendiconto Finanziario")
    df = pd.read_excel(uploaded_ce, sheet_name="Rendiconto Finanziario")
    df = df.fillna(0)

    if df.shape[1] > 1:
        prima_colonna = df.columns[0]
        df[prima_colonna] = pd.to_numeric(df[prima_colonna], errors='coerce')
        df = df.sort_values(by=prima_colonna).drop(columns=[prima_colonna])

        col_val = df.columns[1]
        df[col_val] = df[col_val].apply(format_miles)

    st.dataframe(df, use_container_width=True, height=800)
