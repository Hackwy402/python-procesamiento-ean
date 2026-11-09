"""
Tablero público del proyecto integrador (Sesión 5) en Streamlit.

Usa exactamente el mismo pipeline de la clase (pipeline_bodega.py): lee los datos del curso y los datos reales de
Colpensiones y el DANE, arma la base con el modelo formal en SQLite (en memoria), entrena los modelos y muestra
el tablero. Incluye una consola SQL de solo lectura y la simulación de la llegada de meses nuevos.

Local:   streamlit run 05-proyecto-integrador/tablero_streamlit/app.py
Nube:    Streamlit Community Cloud → este archivo como "Main file path".
"""
import os
import re
import sqlite3
import sys
import threading
import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import pipeline_bodega as pb  # noqa: E402

RUTA_DATOS = os.path.join(AQUI, "..", "..", "datos") + "/"
RETENCION = {10: 0.995, 11: 0.97, 12: 0.95}       # igual que tablero/simular_llegada.py
META_PQRS = 90

# Paleta validada (categórica: slots 1-2; estado: bueno / crítico)
AZUL, NARANJA = "#2a78d6", "#eb6834"
BUENO, CRITICO = "#0ca30c", "#d03b3b"
TINTA, TINTA_2, REJILLA = "#1f2328", "#5b6068", "#e6e6e3"

st.set_page_config(page_title="Fondo de pensiones · SQL y datos reales", page_icon=":bar_chart:", layout="wide")


# ----------------------------------------------------------------------------- datos y base
@st.cache_data(show_spinner=False)
def datos_base():
    """Lee una sola vez los datos del curso y los datos reales (con su código DIVIPOLA)."""
    afiliados_raw, pqrs, aportes_raw, catalogo = pb.cargar_curso(RUTA_DATOS)
    cargas = [dict(c) for c in pb.CARGAS]
    afil_real, pens_real, edad_real, divipola = pb.cargar_reales(RUTA_DATOS)
    afil_real = pb.codificar_municipio(afil_real, divipola)
    pens_real = pb.codificar_municipio(pens_real, divipola)
    return afiliados_raw, pqrs, aportes_raw, catalogo, afil_real, pens_real, edad_real, divipola, cargas


_CANDADO = threading.Lock()


def _solo_lectura(accion, *_):
    """Autorizador de SQLite: solo deja leer (SELECT, WITH, funciones). Todo lo demás se rechaza."""
    permitido = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                 getattr(sqlite3, "SQLITE_RECURSIVE", 33)}
    return sqlite3.SQLITE_OK if accion in permitido else sqlite3.SQLITE_DENY


@st.cache_resource(show_spinner=False, max_entries=4)
def construir_bodega(meses_extra):
    """Arma la base (en memoria) con los 9 meses reales del curso + `meses_extra` meses simulados."""
    afiliados_raw, pqrs, aportes_raw, catalogo, afil_real, pens_real, edad_real, divipola, cargas = datos_base()
    pqrs, aportes_raw, cargas = pqrs.copy(), aportes_raw.copy(), [dict(c) for c in cargas]
    for mes in range(10, 10 + meses_extra):                       # "llegan" octubre, noviembre, diciembre
        nuevo, nuevas = pb.simular_mes(pb.limpiar_aportes(aportes_raw), pqrs, mes, retencion=RETENCION[mes])
        for c in ["fecha_radicacion", "fecha_respuesta"]:
            nuevas[c] = pd.to_datetime(nuevas[c])
        aportes_raw = pd.concat([aportes_raw, nuevo], ignore_index=True)
        pqrs = pd.concat([pqrs, nuevas], ignore_index=True)
        cargas.append({"archivo": f"aportes_2026-{mes:02d}.csv", "periodo": f"2026-{mes:02d}",
                       "filas": len(nuevo), "llegada": pd.Timestamp.now().floor("s")})
    with _CANDADO:                                                # CONFIG y CARGAS son globales del módulo
        pb.CONFIG["MESES"] = list(range(1, 10 + meses_extra))
        afiliados = pb.limpiar_afiliados(afiliados_raw, catalogo)
        aportes = pb.limpiar_aportes(aportes_raw)
        calidad = pb.evaluar_calidad(afiliados, aportes, pqrs, catalogo, afil_real)
        tablas = pb.construir_modelo(afiliados, aportes, pqrs, catalogo, afil_real, pens_real,
                                     edad_real, divipola, calidad)
        pb.CARGAS[:] = cargas
        tablas = pb.agregar_modelos(tablas)
    con = sqlite3.connect(":memory:", check_same_thread=False)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(pb.DDL)
    for nombre, df in tablas.items():
        df.to_sql(nombre, con, if_exists="append", index=False)
    con.executescript(pb.VISTAS)
    con.commit()
    con.set_authorizer(_solo_lectura)                             # desde aquí, nadie puede modificar la base
    return con, threading.Lock()


def consultar(con_lock, sentencia, limite_seg=5):
    """Ejecuta una sentencia de lectura con tiempo máximo."""
    con, lock = con_lock
    inicio = time.monotonic()
    with lock:
        con.set_progress_handler(lambda: int(time.monotonic() - inicio > limite_seg), 20_000)
        try:
            return pd.read_sql(sentencia, con)
        finally:
            con.set_progress_handler(None, 0)


def miles(n):
    return f"{n:,.0f}".replace(",", ".")


def millones(n):
    return f"${n / 1e6:,.0f} M".replace(",", ".")


def estilo(fig, alto=360):
    fig.update_layout(height=alto, margin=dict(l=10, r=10, t=80, b=10), title_y=0.97, plot_bgcolor="white",
                      paper_bgcolor="white", font=dict(color=TINTA, size=13), hoverlabel=dict(bgcolor="white"),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None))
    fig.update_xaxes(showgrid=False, linecolor=REJILLA, title_font_color=TINTA_2)
    fig.update_yaxes(gridcolor=REJILLA, zeroline=False, title_font_color=TINTA_2)
    return fig


# ----------------------------------------------------------------------------- barra lateral
if "meses_extra" not in st.session_state:
    st.session_state.meses_extra = 0

with st.sidebar:
    st.header("Automatización")
    st.caption("Simula que llega el archivo del mes siguiente. El pipeline completo corre otra vez: limpieza, "
               "calidad, modelo formal, modelos y vistas. Solo cambia **tu** sesión.")
    c1, c2 = st.columns(2)
    if c1.button("Llega un mes", type="primary", disabled=st.session_state.meses_extra >= 3,
                 use_container_width=True):
        st.session_state.meses_extra += 1
    if c2.button("Reiniciar", disabled=st.session_state.meses_extra == 0, use_container_width=True):
        st.session_state.meses_extra = 0

with st.spinner("Armando la base: limpiar → validar → modelo formal → modelos → vistas…"):
    BODEGA = construir_bodega(st.session_state.meses_extra)


def sql(sentencia):
    return consultar(BODEGA, sentencia)


auto = sql("SELECT * FROM v_automatizacion").iloc[0]
regionales = sql("SELECT DISTINCT regional FROM dim_afiliado WHERE regional IS NOT NULL ORDER BY 1")["regional"]

with st.sidebar:
    st.metric("Meses cargados", int(auto["meses_cargados"]), help="Enero a septiembre son los datos del curso; "
              "octubre a diciembre se simulan.")
    st.caption(f"Último periodo: **{auto['ultimo_periodo']}**")
    st.divider()
    regional = st.selectbox("Regional", ["Todas"] + list(regionales))
    st.divider()
    st.caption("Datos del fondo: **ficticios**. Datos de Colpensiones y DANE: **reales**, datos.gov.co, "
               "CC BY-SA 4.0. Universidad Ean · Python para Procesamiento, Calidad y Automatización de Datos.")

filtro_reg = "" if regional == "Todas" else f"WHERE regional = '{regional.replace(chr(39), '')}'"

# ----------------------------------------------------------------------------- encabezado
st.title("Fondo de pensiones · base de datos, SQL y datos reales")
st.caption("Proyecto integrador · Sesión 5. Todo lo que ves sale de consultas SQL sobre la base; "
           "en la pestaña **Consola SQL** puedes escribir las tuyas.")

kpi = sql("SELECT * FROM v_kpi_fondo").iloc[0]
pred = sql("SELECT * FROM pred_recaudo ORDER BY periodo")
ultimo = pred.dropna(subset=["recaudo_real"]).iloc[-1]
siguiente = pred[pred["recaudo_real"].isna()].iloc[0]
k = st.columns(5)
k[0].metric("Recaudo total", millones(kpi["recaudo_total"]))
k[1].metric(f"Recaudo {ultimo['periodo']}", millones(ultimo["recaudo_real"]))
k[2].metric(f"Pronóstico {siguiente['periodo']}", millones(siguiente["recaudo_modelo"]),
            help="Regresión lineal sobre el tiempo, reentrenada en cada carga.")
pct = float(kpi["pct_pqrs_a_tiempo"])
k[3].metric("PQRS a tiempo", f"{pct:.1f} %".replace(".", ","),
            delta=f"{pct - META_PQRS:+.1f} pp frente a la meta del 90 %".replace(".", ","),
            delta_color="normal")
k[4].metric("Afiliados en mora", int(kpi["activos_en_mora"]), help="Activos con 3 o más meses sin aportar.")

t_op, t_real, t_mod, t_sql, t_datos = st.tabs(
    ["Operación del fondo", "Datos reales de Colpensiones", "Modelos", "Consola SQL", "Tablas y cargas"])

# ----------------------------------------------------------------------------- operación
with t_op:
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = go.Figure()
        hist = pred.dropna(subset=["recaudo_real"])
        fig.add_scatter(x=hist["periodo"], y=hist["recaudo_real"] / 1e6, name="Recaudo real",
                        mode="lines+markers", line=dict(color=AZUL, width=2), marker=dict(size=9),
                        hovertemplate="%{x}<br>Real: $%{y:,.1f} M<extra></extra>")
        fig.add_scatter(x=pred["periodo"], y=pred["recaudo_modelo"] / 1e6, name="Modelo y pronóstico",
                        mode="lines+markers", line=dict(color=NARANJA, width=2, dash="dot"), marker=dict(size=8),
                        hovertemplate="%{x}<br>Modelo: $%{y:,.1f} M<extra></extra>")
        fig.add_scatter(x=[siguiente["periodo"]] * 2,
                        y=[siguiente["limite_inferior"] / 1e6, siguiente["limite_superior"] / 1e6],
                        mode="lines", line=dict(color=NARANJA, width=6), opacity=0.35, name="Rango probable (95 %)",
                        hoverinfo="skip")
        piso = hist["recaudo_real"].min() / 1e6
        fig.update_yaxes(title="Millones de pesos", range=[piso * 0.97, pred["recaudo_modelo"].max() / 1e6 * 1.02])
        fig.update_layout(title="Recaudo mensual y pronóstico del mes siguiente")
        st.plotly_chart(estilo(fig), use_container_width=True)
    with c2:
        reg = sql("SELECT regional, recaudo, aportantes FROM v_recaudo_regional ORDER BY recaudo")
        colores = [AZUL if regional in ("Todas", r) else "#b7d3f6" for r in reg["regional"]]
        fig = go.Figure(go.Bar(x=reg["recaudo"] / 1e6, y=reg["regional"], orientation="h", marker_color=colores,
                               customdata=reg["aportantes"],
                               hovertemplate="%{y}<br>$%{x:,.0f} M · %{customdata} aportantes<extra></extra>"))
        fig.update_layout(title="Recaudo acumulado por regional")
        fig.update_xaxes(title="Millones de pesos")
        st.plotly_chart(estilo(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        tema = sql("SELECT tema, radicadas, dias_promedio, pct_a_tiempo FROM v_pqrs_tema ORDER BY pct_a_tiempo")
        fig = go.Figure(go.Scatter(
            x=tema["pct_a_tiempo"], y=tema["tema"], mode="markers+text",
            marker=dict(size=14, color=[BUENO if v >= META_PQRS else CRITICO for v in tema["pct_a_tiempo"]],
                        symbol=["circle" if v >= META_PQRS else "x" for v in tema["pct_a_tiempo"]],
                        line=dict(color="white", width=2)),
            text=[("Cumple " if v >= META_PQRS else "Bajo meta ") + f"{v:.1f} %" for v in tema["pct_a_tiempo"]],
            textposition="middle right", customdata=tema[["radicadas", "dias_promedio"]],
            hovertemplate="%{y}<br>%{x:.1f} % a tiempo<br>%{customdata[0]} radicadas · "
                          "%{customdata[1]} días hábiles promedio<extra></extra>"))
        fig.add_vline(x=META_PQRS, line_dash="dash", line_color=TINTA_2, annotation_text="Meta 90 %",
                      annotation_position="top")
        fig.update_xaxes(range=[84, 96], showgrid=True, gridcolor=REJILLA, title="% respondidas a tiempo (15 días hábiles)")
        fig.update_layout(title="PQRS a tiempo por tema")
        st.plotly_chart(estilo(fig, 380), use_container_width=True)
    with c2:
        mora = sql(f"SELECT regional, COUNT(*) AS afiliados_en_mora FROM v_mora {filtro_reg} "
                   "GROUP BY regional ORDER BY afiliados_en_mora DESC")
        fig = go.Figure(go.Bar(x=mora["regional"], y=mora["afiliados_en_mora"], marker_color=AZUL,
                               text=mora["afiliados_en_mora"], textposition="outside",
                               hovertemplate="%{y} afiliados en mora<extra>%{x}</extra>"))
        fig.update_layout(title="Afiliados activos en mora (3+ meses sin aportar)")
        fig.update_yaxes(title="Afiliados")
        st.plotly_chart(estilo(fig, 380), use_container_width=True)

    st.subheader("Lista de mora (seudonimizada)")
    st.caption("Sin nombres ni documentos: `doc_seudo` es un código SHA-256 con sal (Ley 1581 de 2012).")
    st.dataframe(sql(f"SELECT * FROM v_mora {filtro_reg} ORDER BY meses_sin_aporte DESC, regional"),
                 use_container_width=True, hide_index=True, height=260)

    st.subheader("Calidad de los datos")
    cal = sql("SELECT n, tabla, regla, dimension, incumplen, pct_cumplimiento FROM calidad_regla ORDER BY n")
    cal["estado"] = np.where(cal["pct_cumplimiento"] >= 99, "Bien", np.where(cal["pct_cumplimiento"] >= 97,
                                                                              "Revisar", "Crítico"))
    st.dataframe(cal, use_container_width=True, hide_index=True,
                 column_config={"pct_cumplimiento": st.column_config.ProgressColumn(
                     "% cumplimiento", min_value=90, max_value=100, format="%.2f %%")})

# ----------------------------------------------------------------------------- datos reales
with t_real:
    tot = sql("SELECT (SELECT SUM(cantidad) FROM real_afiliados) AS af, "
              "(SELECT SUM(cantidad) FROM real_pensionados) AS pe")
    c = st.columns(3)
    c[0].metric("Afiliados a Colpensiones", miles(tot["af"][0]))
    c[1].metric("Pensionados", miles(tot["pe"][0]))
    c[2].metric("Pensionados por cada 100 afiliados", f"{100 * tot['pe'][0] / tot['af'][0]:.1f}".replace(".", ","))
    st.caption("Fuente: datos.gov.co (Colpensiones, corte 30 oct 2026; DIVIPOLA del DANE). Cifras agregadas.")

    mun = sql("SELECT municipio, departamento, latitud, longitud, afiliados, pensionados FROM v_real_municipio "
              "WHERE afiliados > 0 AND latitud IS NOT NULL")
    mun["tamano"] = np.sqrt(mun["afiliados"])
    fig = px.scatter_map(mun, lat="latitud", lon="longitud", size="tamano", size_max=40, color_discrete_sequence=[AZUL],
                         hover_name="municipio", hover_data={"departamento": True, "afiliados": ":,", "pensionados": ":,",
                                                             "tamano": False, "latitud": False, "longitud": False},
                         zoom=4.9, center={"lat": 5.8, "lon": -74.5}, map_style="open-street-map", opacity=0.55)
    fig.update_layout(title="Afiliados por municipio (el área del círculo es proporcional)", height=520,
                      margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        dep = sql("SELECT departamento, afiliados, pensionados, pensionados_por_100_afiliados AS pens_x_100 "
                  "FROM v_real_departamento WHERE afiliados > 50000 ORDER BY pens_x_100")
        fig = go.Figure(go.Bar(x=dep["pens_x_100"], y=dep["departamento"], orientation="h", marker_color=AZUL,
                               customdata=dep[["afiliados", "pensionados"]],
                               hovertemplate="%{y}<br>%{x:.1f} pensionados por cada 100 afiliados<br>"
                                             "%{customdata[0]:,} afiliados · %{customdata[1]:,} pensionados"
                                             "<extra></extra>"))
        fig.update_layout(title="Pensionados por cada 100 afiliados (departamentos con 50.000+ afiliados)")
        fig.update_xaxes(title="Pensionados por cada 100 afiliados")
        st.plotly_chart(estilo(fig, 560), use_container_width=True)
    with c2:
        edad = sql("SELECT rango_edad, genero, SUM(cantidad) AS pensionados FROM real_pensionados_edad "
                   "GROUP BY rango_edad, genero ORDER BY LENGTH(rango_edad), rango_edad")
        orden = list(dict.fromkeys(edad["rango_edad"]))
        edad["valor"] = np.where(edad["genero"] == "Masculino", -edad["pensionados"], edad["pensionados"])
        fig = go.Figure()
        for gen, color in [("Femenino", NARANJA), ("Masculino", AZUL)]:
            d = edad[edad["genero"] == gen]
            fig.add_bar(y=d["rango_edad"], x=d["valor"], orientation="h", name=gen, marker_color=color,
                        customdata=d["pensionados"], hovertemplate=gen + " %{y}: %{customdata:,}<extra></extra>")
        fig.update_layout(title="Pirámide de pensionados por edad", barmode="relative", bargap=0.1)
        fig.update_yaxes(categoryorder="array", categoryarray=orden, title="Rango de edad")
        fig.update_xaxes(title="Pensionados (hombres a la izquierda, mujeres a la derecha)",
                         tickvals=[-300000, -150000, 0, 150000, 300000],
                         ticktext=["300.000", "150.000", "0", "150.000", "300.000"])
        st.plotly_chart(estilo(fig, 560), use_container_width=True)

    st.subheader("La muestra del curso frente al país")
    st.dataframe(sql("SELECT * FROM v_comparativo_ciudades ORDER BY afiliados_reales_colpensiones DESC"),
                 use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------- modelos
with t_mod:
    met = sql("SELECT modelo, tipo, metrica, valor, observaciones, entrenado FROM modelo_metricas")
    c = st.columns(2)
    m1 = met[met["modelo"] == "pronostico_recaudo"].iloc[0]
    m2 = met[met["modelo"] == "pensionados_esperados"].iloc[0]
    c[0].metric("Pronóstico del recaudo · MAPE", f"{m1['valor']:.2f} %".replace(".", ","),
                help="Error promedio del modelo frente al recaudo real. Menor es mejor.")
    c[1].metric("Pensionados esperados · R²", f"{m2['valor']:.3f}".replace(".", ","),
                help=f"Regresión log-log sobre {int(m2['observaciones'])} municipios reales.")

    pens = sql("""
        SELECT m.municipio, d.departamento, p.afiliados, p.pensionados, p.pensionados_esperados, p.desviacion_pct
        FROM modelo_pensionados p
        JOIN dim_municipio m    ON m.cod_mpio = p.cod_mpio
        JOIN dim_departamento d ON d.cod_dpto = m.cod_dpto""")
    pens["lugar"] = pens["municipio"] + " (" + pens["departamento"] + ")"
    linea = pens.sort_values("afiliados")
    fig = go.Figure()
    fig.add_scatter(x=pens["afiliados"], y=pens["pensionados"], mode="markers", name="Municipio",
                    marker=dict(color=AZUL, size=8, opacity=0.5, line=dict(color="white", width=1)),
                    customdata=pens[["lugar", "pensionados_esperados", "desviacion_pct"]],
                    hovertemplate="%{customdata[0]}<br>%{x:,} afiliados · %{y:,} pensionados<br>"
                                  "Esperados: %{customdata[1]:,} (%{customdata[2]:+.1f} %)<extra></extra>")
    fig.add_scatter(x=linea["afiliados"], y=linea["pensionados_esperados"], mode="lines", name="Lo esperado (modelo)",
                    line=dict(color=NARANJA, width=2), hoverinfo="skip")
    arm = pens[(pens["municipio"] == "ARMENIA") & (pens["departamento"] == "ANTIOQUIA")]
    if len(arm):
        fig.add_annotation(x=np.log10(arm["afiliados"].iloc[0]), y=np.log10(arm["pensionados"].iloc[0]),
                           text="ARMENIA (ANT): 61.555 afiliados, 43 pensionados", showarrow=True, arrowhead=2,
                           ax=-140, ay=-30, font=dict(color=TINTA))
    fig.update_xaxes(type="log", title="Afiliados (escala logarítmica)")
    fig.update_yaxes(type="log", title="Pensionados (escala logarítmica)")
    fig.update_layout(title="Pensionados frente a afiliados en cada municipio (datos reales)")
    st.plotly_chart(estilo(fig, 520), use_container_width=True)

    st.subheader("Lo que no encaja: menos pensionados de lo esperado (20.000+ afiliados)")
    st.dataframe(pens[pens["afiliados"] >= 20000].nsmallest(8, "desviacion_pct").drop(columns="lugar"),
                 use_container_width=True, hide_index=True)
    st.info("**Hallazgo real.** \"ARMENIA\" en Antioquia aparece con 61.555 afiliados y solo 43 pensionados, y "
            "Armenia, la capital del Quindío, no aparece entre los afiliados. Sus afiliados quedaron registrados en el "
            "municipio equivocado en el conjunto oficial. El modelo no corrige el dato: señala qué revisar.")

# ----------------------------------------------------------------------------- consola SQL
EJEMPLOS = {
    "Indicadores de la Dirección": "SELECT * FROM v_kpi_fondo",
    "GROUP BY: recaudo por mes": "SELECT periodo,\n       SUM(valor_aporte)           AS recaudo,\n"
                                 "       COUNT(DISTINCT id_afiliado) AS aportantes\nFROM fact_aporte\n"
                                 "GROUP BY periodo\nORDER BY periodo",
    "JOIN: departamentos con más afiliados (reales)":
        "SELECT d.departamento, SUM(r.cantidad) AS afiliados\nFROM real_afiliados r\n"
        "JOIN dim_municipio m    ON m.cod_mpio = r.cod_mpio\nJOIN dim_departamento d ON d.cod_dpto = m.cod_dpto\n"
        "GROUP BY d.departamento\nORDER BY afiliados DESC\nLIMIT 10",
    "HAVING: temas de PQRS bajo la meta": "SELECT tema,\n       COUNT(*)                        AS radicadas,\n"
                                          "       ROUND(100.0 * AVG(a_tiempo), 1) AS pct_a_tiempo\nFROM fact_pqrs\n"
                                          "GROUP BY tema\nHAVING 100.0 * AVG(a_tiempo) < 90\nORDER BY pct_a_tiempo",
    "WITH + LEFT JOIN: mora por regional": "SELECT regional, COUNT(*) AS afiliados_en_mora\nFROM v_mora\n"
                                           "GROUP BY regional\nORDER BY afiliados_en_mora DESC",
    "LAG: variación mes a mes": "WITH mensual AS (\n    SELECT periodo, SUM(valor_aporte) AS recaudo\n"
                                "    FROM fact_aporte GROUP BY periodo\n)\nSELECT periodo, recaudo,\n"
                                "       ROUND(100.0 * (recaudo - LAG(recaudo) OVER (ORDER BY periodo))\n"
                                "             / LAG(recaudo) OVER (ORDER BY periodo), 2) AS variacion_pct\n"
                                "FROM mensual\nORDER BY periodo",
    "Modelo: municipios fuera de lo esperado": "SELECT m.municipio, d.departamento, p.afiliados, p.pensionados,\n"
                                               "       p.pensionados_esperados, p.desviacion_pct\n"
                                               "FROM modelo_pensionados p\n"
                                               "JOIN dim_municipio m    ON m.cod_mpio = p.cod_mpio\n"
                                               "JOIN dim_departamento d ON d.cod_dpto = m.cod_dpto\n"
                                               "WHERE p.afiliados >= 20000\nORDER BY p.desviacion_pct\nLIMIT 10",
    "Bitácora de cargas": "SELECT * FROM log_cargas ORDER BY periodo",
    "Intento de borrar (se rechaza)": "DELETE FROM fact_aporte",
}

with t_sql:
    st.markdown("Escribe una sentencia y pulsa **Ejecutar**. La base es de **solo lectura**: `SELECT` y `WITH` "
                "funcionan; `INSERT`, `UPDATE`, `DELETE` o `DROP` se rechazan. Motor: SQLite.")
    ejemplo = st.selectbox("Cargar un ejemplo", list(EJEMPLOS))
    consulta = st.text_area("Sentencia SQL", EJEMPLOS[ejemplo], height=220, key=f"sql_{ejemplo}")
    if st.button("Ejecutar", type="primary"):
        limpia = re.sub(r"--[^\n]*", "", consulta).strip().rstrip(";").strip()
        try:
            res = consultar(BODEGA, limpia)
            st.success(f"{len(res):,} filas".replace(",", "."))
            st.dataframe(res.head(5000), use_container_width=True, hide_index=True)
            st.download_button("Descargar CSV", res.to_csv(index=False).encode("utf-8"), "consulta.csv", "text/csv")
        except Exception as e:                                     # noqa: BLE001 - se muestra al estudiante
            mensaje = str(e)
            if "not authorized" in mensaje:
                mensaje = "No autorizado: esta base es de solo lectura (solo SELECT y WITH)."
            elif "interrupted" in mensaje:
                mensaje = "La consulta tardó más de 5 segundos y se detuvo. Agrega filtros o un LIMIT."
            st.error(mensaje)

    with st.expander("Tablas y columnas disponibles"):
        objetos = consultar(BODEGA, "SELECT type AS tipo, name AS nombre FROM sqlite_master "
                                    "WHERE type IN ('table', 'view') ORDER BY type, name")
        for _, fila in objetos.iterrows():
            cols = consultar(BODEGA, f"SELECT * FROM {fila['nombre']} LIMIT 0").columns
            st.markdown(f"**{fila['nombre']}** ({'vista' if fila['tipo'] == 'view' else 'tabla'}): "
                        + ", ".join(f"`{c}`" for c in cols))

# ----------------------------------------------------------------------------- tablas y cargas
with t_datos:
    st.subheader("Bitácora de cargas")
    st.dataframe(sql("SELECT * FROM log_cargas ORDER BY periodo"), use_container_width=True, hide_index=True)
    st.subheader("Filas por tabla")
    filas = [{"tabla": t, "filas": int(sql(f"SELECT COUNT(*) AS n FROM {t}")["n"][0])}
             for t in sql("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")["name"]]
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    st.caption("Código: github.com/Hackwy402/python-procesamiento-ean · 05-proyecto-integrador/tablero_streamlit")
