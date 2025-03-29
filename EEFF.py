import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.sidebar.title("📊 Navigazione")

uploaded_ce = st.sidebar.file_uploader("Conto_Economico_Budget.xlsx", type=["xlsx"])

if not uploaded_ce:
    st.warning("⚠️ Carica il file Excel per continuare.")
    st.stop()

conto = pd.read_excel(uploaded_ce, sheet_name="Conto Economico")
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

def colorear(val, tipo, es_porcentaje=False):
    try:
        numero = float(str(val).replace(".", "").replace(",", ".").replace("%", ""))
        if es_porcentaje:
            numero = numero / 100
        if tipo:
            return f"🔴 {val}" if numero > 0 else f"🟢 {val}"
        else:
            return f"🟢 {val}" if numero > 0 else f"🔴 {val}"
    except:
        return val

# Listas para formato
formato_azul = ["Marginalità Vendite lorda", "% Marginalità Vendite lorda", "EBITDA", "% EBITDA", "EBIT", "% EBIT", "EBT", "% EBT", "Risultato di Gruppo", "% Risultato di Gruppo"]
formato_negrita = ["Totale Ricavi", "Totale Costi", "Costi senza Personale"]

if pagina == "Conto Economico":
    st.title("📘 Conto Economico")

    conto = conto.fillna(0)
    periodi = list(conto.columns[1:4])
    index1 = 2 if len(periodi) > 2 else len(periodi) - 1
    index2 = 1 if len(periodi) > 1 else 0

    col1, col2 = st.columns(2)
    with col1:
        periodo_1 = st.selectbox("Periodo 1", periodi, index=index1)
    with col2:
        periodo_2 = st.selectbox("Periodo 2", periodi, index=index2)

    df = conto.copy()
    df["Tipo"] = df["Tipo"].astype(str).str.strip()
    df["is_cost"] = df["Tipo"].str.lower().str.contains("costo|costi|spesa|opex", na=False)

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
            "Voce": "",
            periodo_1: total[periodo_1],
            periodo_2: total[periodo_2],
            "Δ": total["Δ"],
            "Δ %": delta_pct
        }
        output.append(riga_totale)

        if mostrar_detalles and tipo in ["Vendite", "Personal", "Altri Opex", "Oneri Finanziari"]:
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

    # Orden por ID_Ordine si existe
    if "Voce" in df_resultado.columns and "ID_Ordine" in df.columns:
        orden_dict = df.set_index("Voce")["ID_Ordine"].to_dict()
        df_resultado["__ordine__"] = df_resultado["Voce"].map(orden_dict)
        df_resultado = df_resultado.sort_values(by="__ordine__", na_position="last").drop(columns="__ordine__")

    df_resultado["is_cost"] = df_resultado["Tipo"].str.lower().str.contains("costo|costi|spesa|opex", na=False)

    for col in [periodo_1, periodo_2, "Δ"]:
        df_resultado[col] = df_resultado[col].apply(format_miles)
    df_resultado["Δ %"] = df_resultado["Δ %"].apply(format_percent)

    df_resultado["Δ"] = [
        colorear(v, t) for v, t in zip(df_resultado["Δ"], df_resultado["is_cost"])
    ]
    df_resultado["Δ %"] = [
        colorear(v, t, es_porcentaje=True) for v, t in zip(df_resultado["Δ %"], df_resultado["is_cost"])
    ]
    df_resultado = df_resultado.drop(columns=["is_cost"])

    # Reordenar columnas
    cols = ["Tipo", "Voce", periodo_1, periodo_2, "Δ", "Δ %"]
    df_resultado = df_resultado[cols]

    # Mostrar con st.markdown + HTML
    def render_table(df):
        html = "<table style='width:100%; border-collapse: collapse;'>"
        html += "<tr>" + "".join(f"<th style='border-bottom: 1px solid #ccc; text-align:left;'>{col}</th>" for col in df.columns) + "</tr>"
        for _, row in df.iterrows():
            voce = str(row["Voce"])
            estilo = ""
            if voce in formato_azul:
                estilo = "font-weight:bold; background-color:#DAE9F8; font-size:1.1em;"
            elif voce in formato_negrita:
                estilo = "font-weight:bold;"
            html += "<tr>" + "".join(
                f"<td style='padding:4px; {estilo}'>{row[col]}</td>" for col in df.columns
            ) + "</tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

    render_table(df_resultado)
