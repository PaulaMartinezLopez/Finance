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
    st.warning("⚠️ Carica tutte due file per continuare.")
    st.stop()

# Read Excel files
conto = pd.read_excel(uploaded_ce, sheet_name="Conto Economico")
mappings = pd.read_excel(uploaded_mappings, sheet_name="Conto_Economico")
# Placeholder: you can use this for future features


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
    mappings = mappings[["Voce", "Tipo"]]
   
    df = pd.merge(conto, mappings, on="Voce", how="left")
    df["Tipo"] = df["Tipo"].astype(str).str.strip().replace("nan", np.nan)

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

    kpi_fissi = ["Marginalità Vendite lorda", "EBITDA", "EBIT", "EBT", "Risultato di Gruppo"]
    kpi_rows = df[df["Voce"].isin(kpi_fissi)].copy()
    for _, row in kpi_rows.iterrows():
        r = {
            "Tipo": row.get("Tipo", ""),
            "Voce": row["Voce"],
            periodo_1: row[periodo_1],
            periodo_2: row[periodo_2],
            "Δ": row["Δ"],
            "Δ %": row["Δ %"]
        }
        output.append(r)

    df_resultado = pd.DataFrame(output)

    # Formato miles
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

    st.dataframe(df_resultado, use_container_width=True, height=800)

# === STATO PATRIMONIALE ===
elif pagina == "Stato Patrimoniale + Indicatori":
    st.title("🏦 Stato Patrimoniale")

    try:
        df_raw = pd.read_excel(uploaded_ce, sheet_name="Stato Patrimoniale", header=None)

        row_idx = df_raw[df_raw.apply(lambda row: row.astype(str).str.contains("Voce", case=False).any(), axis=1)].index

        if not row_idx.empty:
            header_row = row_idx[0]
            df_sp = pd.read_excel(uploaded_ce, sheet_name="Stato Patrimoniale", header=header_row)
            df_sp = df_sp.fillna(0)

            # Asignar nombres de años
            col_anno_1 = df_sp.columns[1]
            col_anno_2 = df_sp.columns[2]

            # Calcular diferencia absoluta y %
            df_sp["Δ"] = df_sp[col_anno_2] - df_sp[col_anno_1]
            df_sp["Δ %"] = np.where(
                df_sp[col_anno_1] != 0,
                (df_sp["Δ"] / abs(df_sp[col_anno_1])),
                np.nan
            )

            # Formatear
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

# === RENDICONTO FINANZIARIO ===
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

    # Obtener orden original desde el archivo Excel (hoja Conto Economico)
orden_excel = conto["Voce"].tolist()

# Crear una columna auxiliar temporal con el orden original
df_resultado["__ordine__"] = df_resultado["Voce"].apply(lambda x: orden_excel.index(x) if x in orden_excel else 9999)

# Reordenar
df_resultado = df_resultado.sort_values(by="__ordine__").drop(columns="__ordine__")
st.dataframe(df, use_container_width=True, height=1400)


  

