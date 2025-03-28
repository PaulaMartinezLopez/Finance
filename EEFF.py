if pagina == "Conto Economico":
    st.title("📘 Conto Economico")

    conto = conto.fillna(0)
    mappings = mappings[["Voce", "Tipo"]]
    df = pd.merge(conto, mappings, on="Voce", how="left")

    # Limpieza de espacios invisibles en Tipo
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

    # Identificar si es coste
    df["is_cost"] = df["Tipo"].str.lower().str.contains("costo|costi|spesa|opex", na=False)

    # Desviaciones corregidas
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

    # Agrega los KPI fissi si no se duplican
    kpi_fissi = ["Marginalità Vendite lorda", "EBITDA", "EBIT", "EBT", "Risultato di Gruppo"]
    kpi_rows = df[df["Voce"].isin(kpi_fissi) & ~df["Voce"].isin([r.get("Voce") for r in output])].copy()
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

    # Ordenar según el Excel original
    orden_excel = conto["Voce"].tolist()
    df_resultado["__ordine__"] = df_resultado["Voce"].apply(lambda x: orden_excel.index(x) if x in orden_excel else 9999)
    df_resultado = df_resultado.sort_values(by="__ordine__").drop(columns="__ordine__")

    # Formato miles y porcentaje
    for col in [periodo_1, periodo_2, "Δ"]:
        df_resultado[col] = df_resultado[col].apply(format_miles)
    df_resultado["Δ %"] = df_resultado["Δ %"].apply(format_percent)

    # Añadir emojis como "semáforo" visual
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

    # Ocultar columna Voce si no se muestran detalles
    if not mostrar_detalles:
        df_resultado = df_resultado.drop(columns=["Voce"], errors="ignore")

    st.dataframe(df_resultado, use_container_width=True, height=1200)


