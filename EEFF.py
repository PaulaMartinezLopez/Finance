import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.sidebar.title("📊 Navigazione")

# Upload files
st.sidebar.subheader("Carica i file Excel")
uploaded_ce = st.sidebar.file_uploader("Conto_Economico_Budget.xlsx", type=["xlsx"])
uploaded_mappings = st.sidebar.file_uploader("Mappings.xlsx", type=["xlsx"])

if not uploaded_ce or not uploaded_mappings:
    st.warning("⚠️ Carica entrambi i file per continuare.")
    st.stop()

# Read Excel files
conto = pd.read_excel(uploaded_ce, sheet_name="Conto Economico")
mappings = pd.read_excel(uploaded_mappings, sheet_name="Conto_Economico")

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

# === CONTO ECONOMICO ===
if pagina == "Conto Economico":
    st.title("📘 Conto Economico")

    conto = conto.fillna(0)
    mappings = mappings[["Voce", "Tipo", "ID_Ordine"]]
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

    # Identificar si la cuenta es un coste
    df["is_cost"] = df["Tipo"].str.lower().str.contains("costo|costi|spesa|opex", na=False)

    # Calcular desviación ajustada
    df["Δ"] = np.where(
        df["is_cost"],
        df[periodo_2] - df[periodo_1],
        df[periodo_1] - df[periodo_2]
    )

    df["Δ %"] = np.where(
        df[periodo_2] != 0,
        df["Δ"] / abs(df[periodo_2]),
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

    df_resultado = pd.DataFrame(output)

    # Aplicar orden desde mappings
    df_resultado = pd.merge(df_resultado, mappings[["Voce", "ID_Ordine"]], on="Voce", how="left")
    df_resultado = df_resultado.sort_values(by="ID_Ordine", na_position="last").drop(columns=["ID_Ordine"])

    # Formato miles y porcentaje
    for col in [periodo_1, periodo_2, "Δ"]:
        df_resultado[col] = df_resultado[col].apply(format_miles)
    df_resultado["Δ %"] = df_resultado["Δ %"].apply(format_percent)

    # Aplicar colores con emojis a Δ y Δ %
    def colorear(val, tipo, es_porcentaje=False):
        try:
            numero = float(str(val).replace(".", "").replace(",", ".").replace("%", ""))
            if es_porcentaje:
                numero = numero / 100
            if tipo:  # coste
                return f"🔴 {val}" if numero > 0 else f"🟢 {val}"
            else:     # ingreso
                return f"🟢 {val}" if numero > 0 else f"🔴 {val}"
        except:
            return val

    df_resultado["is_cost"] = df_resultado["Tipo"].str.lower().str.contains("costo|costi|spesa|opex", na=False)
    df_resultado["Δ"] = [
        colorear(v, t) for v, t in zip(df_resultado["Δ"], df_resultado["is_cost"])
    ]
    df_resultado["Δ %"] = [
        colorear(v, t, es_porcentaje=True) for v, t in zip(df_resultado["Δ %"], df_resultado["is_cost"])
    ]
    df_resultado = df_resultado.drop(columns=["is_cost"])

    if not mostrar_detalles:
        df_resultado = df_resultado.drop(columns=["Voce"], errors="ignore")

    st.dataframe(df_resultado, use_container_width=True, height=1400)

