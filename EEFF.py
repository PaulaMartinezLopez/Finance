import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.sidebar.title("📊 Navigazione")

# Upload file
uploaded_ce = st.sidebar.file_uploader("Conto_Economico_Budget.xlsx", type=["xlsx"])

if not uploaded_ce:
    st.warning("⚠️ Carica il file Excel per continuare.")
    st.stop()

# Leer hoja principal
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

if pagina == "Conto Economico":
    st.title("📘 Conto Economico")

    conto = pd.read_excel(uploaded_ce, sheet_name="Conto Economico").fillna(0)

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

    # Ordenar por ID_Ordine del archivo Excel
    if "Voce" in df_resultado.columns and "ID_Ordine" in df.columns:
        orden_dict = df.set_index("Voce")["ID_Ordine"].to_dict()
        df_resultado["__ordine__"] = df_resultado["Voce"].map(orden_dict)
        df_resultado = df_resultado.sort_values(by="__ordine__", na_position="last").drop(columns="__ordine__")

    for col in [periodo_1, periodo_2, "Δ"]:
        df_resultado[col] = df_resultado[col].apply(format_miles)
    df_resultado["Δ %"] = df_resultado["Δ %"].apply(format_percent)

    # Reordenar columnas: Tipo, Voce, valores
    cols = df_resultado.columns.tolist()
    if "Voce" in cols and "Tipo" in cols:
        reordered = ["Tipo", "Voce"] + [c for c in cols if c not in ["Tipo", "Voce"]]
        df_resultado = df_resultado[reordered]

    st.dataframe(df_resultado, use_container_width=True, height=1400)

elif pagina == "Stato Patrimoniale + Indicatori":
    st.title("🏦 Stato Patrimoniale")

    try:
        df_raw = pd.read_excel(uploaded_ce, sheet_name="Stato Patrimoniale", header=None)
        row_idx = df_raw[df_raw.apply(lambda row: row.astype(str).str.contains("Voce", case=False).any(), axis=1)].index

        if not row_idx.empty:
            header_row = row_idx[0]
            df_sp = pd.read_excel(uploaded_ce, sheet_name="Stato Patrimoniale", header=header_row)
            df_sp = df_sp.fillna(0)

            col_anno_1 = df_sp.columns[1]
            col_anno_2 = df_sp.columns[2]
            df_sp["Δ"] = df_sp[col_anno_2] - df_sp[col_anno_1]
            df_sp["Δ %"] = np.where(df_sp[col_anno_1] != 0, df_sp["Δ"] / abs(df_sp[col_anno_1]), np.nan)

            df_vis = df_sp.copy()
            for col in [col_anno_1, col_anno_2, "Δ"]:
                df_vis[col] = df_vis[col].apply(format_miles)
            df_vis["Δ %"] = df_vis["Δ %"].apply(format_percent)

            st.subheader("📋 Stato Patrimoniale")
            st.dataframe(df_vis, use_container_width=True, height=800)
        else:
            st.error("❌ Intestazione 'Voce' non trovata nel foglio 'Stato Patrimoniale'.")

    except Exception as e:
        st.error(f"❌ Errore nel caricamento del 'Stato Patrimoniale': {e}")

elif pagina == "Rendiconto Finanziario":
    st.title("💧 Rendiconto Finanziario")
    df = pd.read_excel(uploaded_ce, sheet_name="Rendiconto Finanziario")
    df = df.fillna(0)

    if df.shape[1] >= 2:
        prima_colonna = df.columns[0]
        seconda_colonna = df.columns[1]
        try:
            df[seconda_colonna] = pd.to_numeric(df[seconda_colonna], errors="coerce")
            df[seconda_colonna] = df[seconda_colonna].apply(format_miles)
        except Exception as e:
            st.warning(f"⚠️ Errore nel processamento dei dati numerici: {e}")
    else:
        st.warning("⚠️ Il foglio 'Rendiconto Finanziario' non ha abbastanza colonne.")

    st.dataframe(df, use_container_width=True, height=1200)

