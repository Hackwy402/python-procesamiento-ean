-- =============================================================================
-- Sesión 5 · Sentencias de la demo en Grafana (PostgreSQL)
-- Grafana → Explorar → modo Code → pegar una sentencia → Run query.
-- Para extraer: Inspector de consultas → Data → Download CSV,
-- o desde la terminal: python3 tablero/extraer_sql.py "SELECT ..." --csv salida.csv
-- =============================================================================


-- 1 · Mora de una regional (vista; sin nombres ni documentos)
SELECT * FROM v_mora WHERE regional = 'Centro';


-- 2 · Qué archivos llegaron y cuándo (bitácora de cargas)
SELECT archivo, periodo, filas, llegada
FROM log_cargas
ORDER BY llegada DESC;


-- 3 · El modelo junto al dato real (el último mes trae el rango probable)
SELECT periodo, recaudo_real, recaudo_modelo, limite_inferior, limite_superior
FROM pred_recaudo
ORDER BY periodo;


-- 4 · Métricas de los modelos y hora del último entrenamiento
SELECT modelo, metrica, valor, entrenado
FROM modelo_metricas;


-- 5 · Lo que llegó en la demo en vivo: recaudo por regional desde octubre
SELECT f.regional,
       COUNT(*)                 AS aportes,
       SUM(a.valor_aporte)      AS recaudo,
       SUM(a.aporte_incorrecto) AS incorrectos
FROM fact_aporte a
JOIN dim_afiliado f ON f.id_afiliado = a.id_afiliado
WHERE a.periodo >= '2026-10'
GROUP BY f.regional
ORDER BY recaudo DESC;


-- 6 · Intento de borrar desde el tablero
-- Respuesta esperada: ERROR: permission denied for table fact_aporte
DELETE FROM fact_aporte;


-- Por qué falla el 6: Grafana entra con un usuario que solo puede leer
-- (tablero/init/04_lector.sql)
--   CREATE ROLE lector_grafana LOGIN PASSWORD '...';
--   GRANT SELECT ON ALL TABLES IN SCHEMA public TO lector_grafana;
