-- Generado por pipeline_bodega.py: carga de datos
COPY dim_departamento (cod_dpto, departamento) FROM '/docker-entrypoint-initdb.d/csv/dim_departamento.csv' WITH (FORMAT csv, HEADER true);
COPY dim_municipio (cod_mpio, cod_dpto, municipio, latitud, longitud) FROM '/docker-entrypoint-initdb.d/csv/dim_municipio.csv' WITH (FORMAT csv, HEADER true);
COPY dim_periodo (periodo, fecha, anio, mes, trimestre) FROM '/docker-entrypoint-initdb.d/csv/dim_periodo.csv' WITH (FORMAT csv, HEADER true);
COPY dim_afiliado (id_afiliado, doc_seudo, genero, anio_nacimiento, cod_mpio, regional, estado, salario_base, vigente) FROM '/docker-entrypoint-initdb.d/csv/dim_afiliado.csv' WITH (FORMAT csv, HEADER true);
COPY fact_aporte (id_aporte, id_afiliado, periodo, ibc, valor_aporte, fecha_pago, operador, aporte_incorrecto) FROM '/docker-entrypoint-initdb.d/csv/fact_aporte.csv' WITH (FORMAT csv, HEADER true);
COPY fact_pqrs (radicado, id_afiliado, tipo, tema, canal, fecha_radicacion, fecha_respuesta, estado, dias_habiles, a_tiempo) FROM '/docker-entrypoint-initdb.d/csv/fact_pqrs.csv' WITH (FORMAT csv, HEADER true);
COPY real_afiliados (cod_mpio, genero, cantidad) FROM '/docker-entrypoint-initdb.d/csv/real_afiliados.csv' WITH (FORMAT csv, HEADER true);
COPY real_pensionados (cod_mpio, cantidad) FROM '/docker-entrypoint-initdb.d/csv/real_pensionados.csv' WITH (FORMAT csv, HEADER true);
COPY real_pensionados_edad (rango_edad, rango_salarial, genero, tipo_pension, cantidad) FROM '/docker-entrypoint-initdb.d/csv/real_pensionados_edad.csv' WITH (FORMAT csv, HEADER true);
COPY calidad_regla (n, tabla, regla, dimension, registros, incumplen, pct_cumplimiento) FROM '/docker-entrypoint-initdb.d/csv/calidad_regla.csv' WITH (FORMAT csv, HEADER true);
COPY log_cargas (archivo, periodo, filas, llegada) FROM '/docker-entrypoint-initdb.d/csv/log_cargas.csv' WITH (FORMAT csv, HEADER true);
COPY pred_recaudo (periodo, fecha, recaudo_real, recaudo_modelo, limite_inferior, limite_superior) FROM '/docker-entrypoint-initdb.d/csv/pred_recaudo.csv' WITH (FORMAT csv, HEADER true);
COPY modelo_pensionados (cod_mpio, afiliados, pensionados, pensionados_esperados, desviacion_pct) FROM '/docker-entrypoint-initdb.d/csv/modelo_pensionados.csv' WITH (FORMAT csv, HEADER true);
COPY modelo_metricas (modelo, tipo, metrica, valor, observaciones, entrenado) FROM '/docker-entrypoint-initdb.d/csv/modelo_metricas.csv' WITH (FORMAT csv, HEADER true);
