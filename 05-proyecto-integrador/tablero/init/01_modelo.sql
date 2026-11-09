-- Generado por pipeline_bodega.py: modelo formal

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
