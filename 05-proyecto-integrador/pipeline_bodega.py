#!/usr/bin/env python3
"""
pipeline_bodega.py — Proyecto integrador (Sesión 5) en versión "de producción".
Universidad Ean · PY-EAN · Python para Procesamiento, Calidad y Automatización de Datos

Toma los datos del curso (afiliados, aportes, PQRS) y los datos REALES de Colpensiones y del DANE
(datos.gov.co), los limpia, mide su calidad y los guarda en una base de datos con un modelo formal
(tablas de dimensiones y de hechos, llaves primarias y foráneas). Encima crea las vistas que
alimentan el tablero de Grafana.

Uso:
    python pipeline_bodega.py --datos ../datos --salida salidas
    python pipeline_bodega.py --datos ../datos --salida salidas --postgres tablero/init

Salidas:
    salidas/bodega_pensiones.db     base SQLite (se abre con DB Browser for SQLite, DBeaver o Python)
    tablero/init/*.sql + csv/       carga inicial de PostgreSQL para el tablero (docker compose)
"""
import argparse
import os
import re
import sqlite3
import unicodedata

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- configuración
CONFIG = {
    "SMMLV": 1_750_905,             # salario mínimo 2026 (dato de referencia del curso)
    "TASA_APORTE": 0.16,            # aporte a pensión = 16 % del IBC
    "DIAS_HABILES_RESPUESTA": 15,   # término general de respuesta a peticiones
    "MESES": range(1, 10),          # enero a septiembre de 2026
    "MESES_MORA": 3,                # 3 o más meses sin aportar = mora
    "SAL": "ean-curso-2026",        # en la vida real: fuera del código
}
FESTIVOS_2026 = ["2026-01-01", "2026-01-12", "2026-03-23", "2026-04-02", "2026-04-03",
                 "2026-05-01", "2026-05-18", "2026-06-08", "2026-06-15", "2026-06-29",
                 "2026-07-20", "2026-08-07", "2026-08-17", "2026-10-12", "2026-11-02",
                 "2026-11-16", "2026-12-08", "2026-12-25"]


def log(mensaje):
    """Bitácora mínima: hora + mensaje."""
    print(f"[{pd.Timestamp.now():%H:%M:%S}] {mensaje}")


# ----------------------------------------------------------------------------- 1. ingestar
def cargar_curso(ruta):
    """Datos del curso: afiliados, PQRS, los 9 meses de aportes y el catálogo de ciudades."""
    afiliados = pd.read_csv(ruta + "afiliados.csv", dtype={"numero_documento": str, "telefono": str})
    pqrs = pd.read_csv(ruta + "pqrs.csv", parse_dates=["fecha_radicacion", "fecha_respuesta"])
    catalogo = pd.read_excel(ruta + "oficinas.xlsx", sheet_name="ciudades")
    partes = []
    for mes in CONFIG["MESES"]:
        df = pd.read_csv(f"{ruta}aportes/aportes_2026-{mes:02d}.csv", sep=None, engine="python")
        df.columns = df.columns.str.strip().str.lower()        # julio llega en MAYÚSCULA y con ;
        partes.append(df)
    aportes = pd.concat(partes, ignore_index=True)
    log(f"Curso: {len(afiliados):,} afiliados · {len(pqrs):,} PQRS · {len(aportes):,} aportes")
    return afiliados, pqrs, aportes, catalogo


def cargar_reales(ruta):
    """Datos abiertos reales (datos.gov.co): Colpensiones y DIVIPOLA del DANE."""
    r = ruta + "reales/"
    afil = pd.read_csv(r + "colpensiones_afiliados_municipio.csv")
    pens = pd.read_csv(r + "colpensiones_pensionados_municipio.csv")
    edad = pd.read_csv(r + "colpensiones_pensionados_edad.csv")
    divipola = pd.read_csv(r + "divipola_municipios.csv", dtype=str)
    log(f"Reales: {afil['cantidad'].sum():,} afiliados y {pens['cantidad'].sum():,} pensionados "
        f"en {len(divipola):,} municipios DIVIPOLA")
    return afil, pens, edad, divipola


# ----------------------------------------------------------------------------- 2. procesar
def normalizar_texto(s):
    """minúsculas, sin tildes, sin puntos ni signos, espacios simples."""
    if pd.isna(s):
        return s
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"\(.*?\)", "", s.lower())                     # quita aclaraciones: "(amz)"
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


ALIAS_CIUDAD = {"bogota": "bogota d c", "bogota dc": "bogota d c", "b quilla": "barranquilla", "b manga": "bucaramanga",
                "santiago de cali": "cali", "cartagena de indias": "cartagena"}


def a_fecha(serie):
    """Acepta AAAA-MM-DD y DD/MM/AAAA; fechas imposibles → NaT."""
    f = pd.to_datetime(serie, format="%Y-%m-%d", errors="coerce")
    f = f.fillna(pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce"))
    return f.where((f >= "1920-01-01") & (f <= pd.Timestamp.today()))


def limpiar_afiliados(df, catalogo):
    """Estandariza afiliados (lo de la Sesión 2)."""
    df = df.drop_duplicates().copy()
    texto = ["tipo_documento", "numero_documento", "nombres", "apellidos", "genero",
             "ciudad", "departamento", "email", "estado"]
    df[texto] = df[texto].apply(lambda col: col.str.strip())
    df["numero_documento"] = df["numero_documento"].str.replace(r"[^0-9]", "", regex=True)
    df["nombres"] = df["nombres"].str.title()
    df["apellidos"] = df["apellidos"].str.title()
    df["genero"] = df["genero"].str.upper().str[0]
    df["estado"] = df["estado"].str.capitalize().replace({"Pensionada": "Pensionado"})
    canon = {normalizar_texto(c): c for c in catalogo["ciudad"]}
    df["ciudad"] = df["ciudad"].map(normalizar_texto).replace(ALIAS_CIUDAD).map(canon).fillna(df["ciudad"])
    df["fecha_nacimiento"] = a_fecha(df["fecha_nacimiento"])
    df["fecha_afiliacion"] = a_fecha(df["fecha_afiliacion"])
    sal = pd.to_numeric(df["salario_base"].astype(str).str.replace(".", "", regex=False), errors="coerce")
    df["salario_base"] = sal.where(sal > 0)
    df["email"] = df["email"].str.lower()
    return df


def limpiar_aportes(df):
    """Quita duplicados exactos y convierte la fecha de pago."""
    df = df.drop_duplicates().copy()
    df["fecha_pago"] = pd.to_datetime(df["fecha_pago"], errors="coerce")
    return df


def dias_habiles_pqrs(pq):
    """Días hábiles de respuesta y si fue a tiempo (solo PQRS cerradas con fechas válidas)."""
    pq = pq.copy()
    validas = ((pq["estado"] == "Cerrado") & pq["fecha_respuesta"].notna()
               & (pq["fecha_respuesta"] >= pq["fecha_radicacion"]))
    inicio = pq.loc[validas, "fecha_radicacion"].values.astype("datetime64[D]")
    fin = pq.loc[validas, "fecha_respuesta"].values.astype("datetime64[D]")
    pq["dias_habiles"] = pd.Series(np.busday_count(inicio, fin, holidays=FESTIVOS_2026),
                                   index=pq.index[validas]).astype("Int64")
    pq["a_tiempo"] = (pq["dias_habiles"] <= CONFIG["DIAS_HABILES_RESPUESTA"]).astype("Int64")
    return pq


ALIAS_MUNICIPIO = {   # (departamento, municipio) como lo escribe Colpensiones → código DIVIPOLA
    ("bogota d c", "bogota"): "11001", ("bolivar", "cartagena"): "13001",
    ("bolivar", "mompos"): "13468", ("cauca", "sotara"): "19760",
    ("cordoba", "purisima"): "23586", ("cundinamarca", "ubate"): "25843",
    ("guainia", "barranco minas"): "94343", ("meta", "fuentedeoro"): "50287",
    ("narino", "cuaspud"): "52224", ("narino", "tumaco"): "52835",
    ("norte de santander", "cucuta"): "54001", ("san andres", "providencia"): "88564",
    ("san andres", "san andres"): "88001", ("sucre", "tolu viejo"): "70823",
    ("tolima", "mariquita"): "73443", ("valle del cauca", "cali"): "76001",
    ("sin ciudad", "sin ciudad"): "00000",      # miembro desconocido
    ("guainia", "mapiripana"): "00000",         # área no municipalizada: no tiene código en DIVIPOLA
}


def codificar_municipio(df, divipola):
    """Agrega cod_mpio (DIVIPOLA) a una tabla de Colpensiones: primero por nombre, luego por alias."""
    clave_dane = divipola["dpto"].map(normalizar_texto) + "|" + divipola["nom_mpio"].map(normalizar_texto)
    por_nombre = dict(zip(clave_dane, divipola["cod_mpio"]))
    claves = list(zip(df["departamento"].map(normalizar_texto), df["municipio"].map(normalizar_texto)))
    df = df.copy()
    df["cod_mpio"] = [por_nombre.get(f"{d}|{m}", ALIAS_MUNICIPIO.get((d, m))) for d, m in claves]
    return df


# ----------------------------------------------------------------------------- 3. validar
def regla(n, tabla, nombre, dimension, cumple):
    total = len(cumple)
    ok = int(cumple.sum())
    return {"n": n, "tabla": tabla, "regla": nombre, "dimension": dimension,
            "registros": total, "incumplen": total - ok, "pct_cumplimiento": round(ok / total * 100, 2)}


def evaluar_calidad(af, ap, pq, catalogo, afil_real):
    """8 reglas sobre los datos del curso + 1 sobre los datos reales."""
    return pd.DataFrame([
        regla(1, "afiliados", "Documento con 6 a 10 dígitos", "Validez",
              af["numero_documento"].fillna("").str.fullmatch(r"\d{6,10}")),
        regla(2, "afiliados", "Documento único", "Unicidad",
              ~af["numero_documento"].duplicated(keep=False) & af["numero_documento"].notna()),
        regla(3, "afiliados", "Salario >= SMMLV", "Validez", af["salario_base"] >= CONFIG["SMMLV"]),
        regla(4, "afiliados", "Email con formato válido", "Validez",
              af["email"].fillna("").str.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.]+")),
        regla(5, "afiliados", "Ciudad en catálogo", "Consistencia", af["ciudad"].isin(catalogo["ciudad"])),
        regla(6, "aportes", "Aporte = 16 % del IBC (±1 peso)", "Exactitud",
              (ap["valor_aporte"] - ap["ibc"] * CONFIG["TASA_APORTE"]).abs() <= 1),
        regla(7, "aportes", "El afiliado existe", "Integridad", ap["id_afiliado"].isin(af["id_afiliado"])),
        regla(8, "pqrs", "Fechas coherentes", "Consistencia",
              ~((pq["estado"] == "Cerrado") & pq["fecha_respuesta"].isna())
              & ~(pq["fecha_respuesta"] < pq["fecha_radicacion"])),
        regla(9, "reales", "Municipio real con código DIVIPOLA", "Integridad",
              afil_real["cod_mpio"].notna() & (afil_real["cod_mpio"] != "00000")),
    ])


# ----------------------------------------------------------------------------- 4. modelo formal
DDL = """
CREATE TABLE dim_departamento (
    cod_dpto      TEXT PRIMARY KEY,
    departamento  TEXT NOT NULL
);
CREATE TABLE dim_municipio (
    cod_mpio      TEXT PRIMARY KEY,
    cod_dpto      TEXT NOT NULL REFERENCES dim_departamento (cod_dpto),
    municipio     TEXT NOT NULL,
    latitud       DOUBLE PRECISION,
    longitud      DOUBLE PRECISION
);
CREATE TABLE dim_periodo (
    periodo       TEXT PRIMARY KEY,
    fecha         DATE NOT NULL,
    anio          INTEGER NOT NULL,
    mes           INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    trimestre     INTEGER NOT NULL
);
CREATE TABLE dim_afiliado (
    id_afiliado   TEXT PRIMARY KEY,
    doc_seudo     TEXT,
    genero        TEXT CHECK (genero IN ('F', 'M')),
    anio_nacimiento INTEGER,
    cod_mpio      TEXT REFERENCES dim_municipio (cod_mpio),
    regional      TEXT,
    estado        TEXT,
    salario_base  BIGINT,
    vigente       INTEGER NOT NULL CHECK (vigente IN (0, 1))
);
CREATE TABLE fact_aporte (
    id_aporte     INTEGER PRIMARY KEY,
    id_afiliado   TEXT NOT NULL REFERENCES dim_afiliado (id_afiliado),
    periodo       TEXT NOT NULL REFERENCES dim_periodo (periodo),
    ibc           BIGINT NOT NULL,
    valor_aporte  BIGINT NOT NULL,
    fecha_pago    DATE,
    operador      TEXT,
    aporte_incorrecto INTEGER NOT NULL
);
CREATE TABLE fact_pqrs (
    radicado      TEXT PRIMARY KEY,
    id_afiliado   TEXT NOT NULL REFERENCES dim_afiliado (id_afiliado),
    tipo          TEXT NOT NULL,
    tema          TEXT NOT NULL,
    canal         TEXT NOT NULL,
    fecha_radicacion DATE NOT NULL,
    fecha_respuesta  DATE,
    estado        TEXT NOT NULL,
    dias_habiles  INTEGER,
    a_tiempo      INTEGER
);
CREATE TABLE real_afiliados (
    cod_mpio      TEXT NOT NULL REFERENCES dim_municipio (cod_mpio),
    genero        TEXT NOT NULL,
    cantidad      INTEGER NOT NULL CHECK (cantidad >= 0),
    PRIMARY KEY (cod_mpio, genero)
);
CREATE TABLE real_pensionados (
    cod_mpio      TEXT PRIMARY KEY REFERENCES dim_municipio (cod_mpio),
    cantidad      INTEGER NOT NULL CHECK (cantidad >= 0)
);
CREATE TABLE real_pensionados_edad (
    rango_edad    TEXT NOT NULL,
    rango_salarial TEXT NOT NULL,
    genero        TEXT NOT NULL,
    tipo_pension  TEXT NOT NULL,
    cantidad      INTEGER NOT NULL CHECK (cantidad >= 0),
    PRIMARY KEY (rango_edad, rango_salarial, genero, tipo_pension)
);
CREATE TABLE calidad_regla (
    n             INTEGER PRIMARY KEY,
    tabla         TEXT NOT NULL,
    regla         TEXT NOT NULL,
    dimension     TEXT NOT NULL,
    registros     INTEGER NOT NULL,
    incumplen     INTEGER NOT NULL,
    pct_cumplimiento DOUBLE PRECISION NOT NULL
);
"""

VISTAS = """
CREATE VIEW v_recaudo_mensual AS
SELECT p.periodo, p.fecha,
       SUM(a.valor_aporte)            AS recaudo,
       COUNT(DISTINCT a.id_afiliado)  AS aportantes,
       ROUND(CAST(100.0 * (SUM(a.valor_aporte) - LAG(SUM(a.valor_aporte)) OVER (ORDER BY p.periodo))
             / LAG(SUM(a.valor_aporte)) OVER (ORDER BY p.periodo) AS NUMERIC), 2) AS variacion_pct
FROM fact_aporte a
JOIN dim_periodo p ON p.periodo = a.periodo
GROUP BY p.periodo, p.fecha;

CREATE VIEW v_recaudo_regional AS
SELECT f.regional,
       SUM(a.valor_aporte)            AS recaudo,
       COUNT(DISTINCT a.id_afiliado)  AS aportantes
FROM fact_aporte a
JOIN dim_afiliado f ON f.id_afiliado = a.id_afiliado
GROUP BY f.regional;

CREATE VIEW v_pqrs_tema AS
SELECT tema,
       COUNT(*)                       AS radicadas,
       COUNT(a_tiempo)                AS cerradas_validas,
       ROUND(CAST(AVG(dias_habiles) AS NUMERIC), 1)            AS dias_promedio,
       ROUND(CAST(100.0 * SUM(a_tiempo) / COUNT(a_tiempo) AS NUMERIC), 1) AS pct_a_tiempo
FROM fact_pqrs
GROUP BY tema;

CREATE VIEW v_pqrs_canal AS
SELECT canal,
       COUNT(*)                       AS radicadas,
       ROUND(CAST(100.0 * SUM(a_tiempo) / COUNT(a_tiempo) AS NUMERIC), 1) AS pct_a_tiempo
FROM fact_pqrs
GROUP BY canal;

CREATE VIEW v_mora AS
WITH meses AS (
    SELECT id_afiliado, COUNT(DISTINCT periodo) AS meses_con_aporte
    FROM fact_aporte
    GROUP BY id_afiliado
)
SELECT f.id_afiliado, f.doc_seudo, m.municipio, f.regional,
       COALESCE(x.meses_con_aporte, 0)                                       AS meses_con_aporte,
       (SELECT COUNT(*) FROM dim_periodo) - COALESCE(x.meses_con_aporte, 0)  AS meses_sin_aporte
FROM dim_afiliado f
LEFT JOIN meses x        ON x.id_afiliado = f.id_afiliado
LEFT JOIN dim_municipio m ON m.cod_mpio = f.cod_mpio
WHERE f.vigente = 1
  AND f.estado = 'Activo'
  AND (SELECT COUNT(*) FROM dim_periodo) - COALESCE(x.meses_con_aporte, 0) >= 3;

CREATE VIEW v_kpi_fondo AS
SELECT (SELECT SUM(valor_aporte) FROM fact_aporte)                          AS recaudo_total,
       (SELECT COUNT(*) FROM fact_pqrs)                                     AS pqrs_radicadas,
       (SELECT ROUND(CAST(100.0 * SUM(a_tiempo) / COUNT(a_tiempo) AS NUMERIC), 1)
          FROM fact_pqrs)                                                   AS pct_pqrs_a_tiempo,
       (SELECT ROUND(CAST(AVG(dias_habiles) AS NUMERIC), 1) FROM fact_pqrs) AS dias_habiles_promedio,
       (SELECT COUNT(*) FROM v_mora)                                        AS activos_en_mora,
       (SELECT MIN(pct_cumplimiento) FROM calidad_regla)                    AS peor_regla_pct;

CREATE VIEW v_real_departamento AS
WITH af AS (
    SELECT m.cod_dpto, SUM(r.cantidad) AS afiliados
    FROM real_afiliados r JOIN dim_municipio m ON m.cod_mpio = r.cod_mpio
    GROUP BY m.cod_dpto
), pe AS (
    SELECT m.cod_dpto, SUM(r.cantidad) AS pensionados
    FROM real_pensionados r JOIN dim_municipio m ON m.cod_mpio = r.cod_mpio
    GROUP BY m.cod_dpto
)
SELECT d.cod_dpto, d.departamento,
       af.afiliados,
       COALESCE(pe.pensionados, 0) AS pensionados,
       ROUND(CAST(100.0 * COALESCE(pe.pensionados, 0) / af.afiliados AS NUMERIC), 1) AS pensionados_por_100_afiliados
FROM dim_departamento d
JOIN af      ON af.cod_dpto = d.cod_dpto
LEFT JOIN pe ON pe.cod_dpto = d.cod_dpto;

CREATE VIEW v_real_municipio AS
SELECT m.cod_mpio, m.municipio, d.departamento, m.latitud, m.longitud,
       (SELECT SUM(cantidad) FROM real_afiliados r WHERE r.cod_mpio = m.cod_mpio)   AS afiliados,
       (SELECT SUM(cantidad) FROM real_pensionados r WHERE r.cod_mpio = m.cod_mpio) AS pensionados
FROM dim_municipio m
JOIN dim_departamento d ON d.cod_dpto = m.cod_dpto
WHERE m.cod_mpio <> '00000';

CREATE VIEW v_comparativo_ciudades AS
SELECT m.municipio, f.regional,
       COUNT(*)                                                                   AS afiliados_muestra_curso,
       (SELECT SUM(cantidad) FROM real_afiliados r WHERE r.cod_mpio = m.cod_mpio) AS afiliados_reales_colpensiones
FROM dim_afiliado f
JOIN dim_municipio m ON m.cod_mpio = f.cod_mpio
WHERE f.vigente = 1
GROUP BY m.cod_mpio, m.municipio, f.regional;
"""


def seudonimizar_doc(documento):
    """SHA-256 con sal: mismo documento → mismo código, pero no se puede devolver."""
    if pd.isna(documento) or documento == "":
        return None
    return __import__("hashlib").sha256((CONFIG["SAL"] + str(documento)).encode()).hexdigest()[:12]


def construir_modelo(af, ap, pq, catalogo, afil_real, pens_real, edad_real, divipola, calidad):
    """Arma cada tabla del modelo con exactamente las columnas del DDL."""
    # Dimensiones geográficas (DANE) + miembro desconocido
    dim_departamento = (divipola[["cod_dpto", "dpto"]].drop_duplicates()
                        .rename(columns={"dpto": "departamento"}))
    dim_departamento.loc[len(dim_departamento)] = ["00", "SIN INFORMACIÓN"]
    dim_municipio = divipola.rename(columns={"nom_mpio": "municipio"})[
        ["cod_mpio", "cod_dpto", "municipio", "latitud", "longitud"]].copy()
    for c in ["latitud", "longitud"]:
        dim_municipio[c] = pd.to_numeric(dim_municipio[c].astype(str).str.replace(",", "."))  # coma decimal
    dim_municipio.loc[len(dim_municipio)] = ["00000", "00", "SIN CIUDAD", None, None]

    # Periodos
    fechas = pd.to_datetime([f"2026-{m:02d}-01" for m in CONFIG["MESES"]])
    dim_periodo = pd.DataFrame({"periodo": fechas.strftime("%Y-%m"), "fecha": fechas.date,
                                "anio": fechas.year, "mes": fechas.month, "trimestre": fechas.quarter})

    # Afiliados: seudonimizados (sin nombre, documento, email ni teléfono)
    con_doc = af[af["numero_documento"].fillna("") != ""]
    vigentes = set(con_doc.sort_values("id_afiliado").drop_duplicates("numero_documento")["id_afiliado"])
    cat = catalogo.assign(cod_mpio=catalogo["codigo_dane"].astype(str).str.zfill(5))
    dim_afiliado = af.merge(cat[["ciudad", "cod_mpio", "regional"]], on="ciudad", how="left")
    dim_afiliado = pd.DataFrame({
        "id_afiliado": dim_afiliado["id_afiliado"],
        "doc_seudo": dim_afiliado["numero_documento"].map(seudonimizar_doc),
        "genero": dim_afiliado["genero"].where(dim_afiliado["genero"].isin(["F", "M"])),
        "anio_nacimiento": dim_afiliado["fecha_nacimiento"].dt.year.astype("Int64"),
        "cod_mpio": dim_afiliado["cod_mpio"],
        "regional": dim_afiliado["regional"],
        "estado": dim_afiliado["estado"],
        "salario_base": dim_afiliado["salario_base"].astype("Int64"),
        "vigente": dim_afiliado["id_afiliado"].isin(vigentes).astype(int),
    })

    # Hechos: solo aportes de afiliados que existen (los huérfanos quedan fuera: regla 7)
    validos = ap[ap["id_afiliado"].isin(af["id_afiliado"])].reset_index(drop=True)
    fact_aporte = pd.DataFrame({
        "id_aporte": validos.index + 1,
        "id_afiliado": validos["id_afiliado"], "periodo": validos["periodo"],
        "ibc": validos["ibc"], "valor_aporte": validos["valor_aporte"],
        "fecha_pago": validos["fecha_pago"].dt.date, "operador": validos["operador"],
        "aporte_incorrecto": ((validos["valor_aporte"] - validos["ibc"] * CONFIG["TASA_APORTE"]).abs() > 1).astype(int),
    })
    pq = dias_habiles_pqrs(pq)
    fact_pqrs = pq[["radicado", "id_afiliado", "tipo", "tema", "canal", "fecha_radicacion",
                    "fecha_respuesta", "estado", "dias_habiles", "a_tiempo"]].copy()
    for c in ["fecha_radicacion", "fecha_respuesta"]:
        fact_pqrs[c] = fact_pqrs[c].dt.date

    # Datos reales
    real_afiliados = afil_real.groupby(["cod_mpio", "genero"], as_index=False)["cantidad"].sum()
    real_pensionados = pens_real.groupby("cod_mpio", as_index=False)["cantidad"].sum()
    real_pensionados_edad = edad_real.rename(columns={"rango_salarial_smlv": "rango_salarial",
                                                      "cantidad_personas": "cantidad"})[
        ["rango_edad", "rango_salarial", "genero", "tipo_pension", "cantidad"]]

    calidad_regla = calidad.copy()
    return {"dim_departamento": dim_departamento, "dim_municipio": dim_municipio,
            "dim_periodo": dim_periodo, "dim_afiliado": dim_afiliado,
            "fact_aporte": fact_aporte, "fact_pqrs": fact_pqrs,
            "real_afiliados": real_afiliados, "real_pensionados": real_pensionados,
            "real_pensionados_edad": real_pensionados_edad, "calidad_regla": calidad_regla}


# ----------------------------------------------------------------------------- 5. cargar
def cargar_sqlite(tablas, ruta_db):
    """Crea la base desde cero: DDL → INSERT de cada tabla (en orden de dependencias) → vistas."""
    if os.path.exists(ruta_db):
        os.remove(ruta_db)
    con = sqlite3.connect(ruta_db)
    con.execute("PRAGMA foreign_keys = ON")           # SQLite revisa las llaves foráneas solo si se lo pides
    con.executescript(DDL)
    for nombre, df in tablas.items():                 # el diccionario ya viene en orden: dimensiones primero
        df.to_sql(nombre, con, if_exists="append", index=False)
    con.executescript(VISTAS)
    con.commit()
    return con


def exportar_postgres(tablas, carpeta):
    """Archivos de carga inicial para PostgreSQL (docker-entrypoint-initdb.d)."""
    os.makedirs(os.path.join(carpeta, "csv"), exist_ok=True)
    with open(os.path.join(carpeta, "01_modelo.sql"), "w", encoding="utf-8") as f:
        f.write("-- Generado por pipeline_bodega.py: modelo formal\n" + DDL)
    with open(os.path.join(carpeta, "02_datos.sql"), "w", encoding="utf-8") as f:
        f.write("-- Generado por pipeline_bodega.py: carga de datos\n")
        for nombre, df in tablas.items():
            df.to_csv(os.path.join(carpeta, "csv", f"{nombre}.csv"), index=False)
            columnas = ", ".join(df.columns)
            f.write(f"COPY {nombre} ({columnas}) FROM '/docker-entrypoint-initdb.d/csv/{nombre}.csv' "
                    f"WITH (FORMAT csv, HEADER true);\n")
    with open(os.path.join(carpeta, "03_vistas.sql"), "w", encoding="utf-8") as f:
        f.write("-- Generado por pipeline_bodega.py: vistas para el tablero\n" + VISTAS)


# ----------------------------------------------------------------------------- main
def main(ruta_datos="../datos/", salida="salidas", carpeta_postgres=None):
    log("=== Inicio del pipeline de la bodega ===")
    ruta_datos = ruta_datos.rstrip("/") + "/"
    os.makedirs(salida, exist_ok=True)
    afiliados_raw, pqrs, aportes_raw, catalogo = cargar_curso(ruta_datos)
    afil_real, pens_real, edad_real, divipola = cargar_reales(ruta_datos)
    afiliados = limpiar_afiliados(afiliados_raw, catalogo)
    aportes = limpiar_aportes(aportes_raw)
    afil_real = codificar_municipio(afil_real, divipola)
    pens_real = codificar_municipio(pens_real, divipola)
    calidad = evaluar_calidad(afiliados, aportes, pqrs, catalogo, afil_real)
    tablas = construir_modelo(afiliados, aportes, pqrs, catalogo, afil_real, pens_real,
                              edad_real, divipola, calidad)
    ruta_db = os.path.join(salida, "bodega_pensiones.db")
    con = cargar_sqlite(tablas, ruta_db)
    for nombre in tablas:
        n = con.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
        log(f"  {nombre:<24} {n:>7,} filas")
    kpi = pd.read_sql("SELECT * FROM v_kpi_fondo", con).iloc[0]
    log(f"Recaudo ${kpi['recaudo_total']:,.0f} · PQRS a tiempo {kpi['pct_pqrs_a_tiempo']} % · "
        f"mora {int(kpi['activos_en_mora'])} · peor regla {kpi['peor_regla_pct']} %")
    con.close()
    log(f"Base SQLite: {ruta_db}")
    if carpeta_postgres:
        exportar_postgres(tablas, carpeta_postgres)
        log(f"Carga para PostgreSQL: {carpeta_postgres}")
    log("=== Fin ===")
    return ruta_db


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Bodega de datos del fondo de pensiones (Sesión 5)")
    p.add_argument("--datos", default="../datos", help="carpeta con los datos del curso")
    p.add_argument("--salida", default="salidas", help="carpeta para la base SQLite")
    p.add_argument("--postgres", default=None, help="carpeta para la carga de PostgreSQL (tablero/init)")
    a = p.parse_args()
    main(a.datos, a.salida, a.postgres)
