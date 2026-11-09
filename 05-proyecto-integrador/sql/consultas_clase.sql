-- =============================================================================
-- Sesión 5 · Sentencias SQL de la clase
-- Bodega del fondo de pensiones + datos reales de Colpensiones y el DANE.
--
-- Corren igual en SQLite (notebook de Colab) y en PostgreSQL (tablero de Grafana).
-- Dónde ejecutarlas:
--   - Notebook:  sql("""...""")
--   - Grafana:   Explorar → modo Code → pegar → Run query
--   - Terminal:  python3 tablero/extraer_sql.py "SELECT ..."
--
-- La estructura (CREATE TABLE con llaves y CHECK) está en tablero/init/01_modelo.sql
-- y las vistas (CREATE VIEW) en tablero/init/03_vistas.sql.
-- =============================================================================


-- 1 · SELECT, WHERE, ORDER BY, LIMIT
-- Los cinco municipios de Antioquia más al norte.
SELECT cod_mpio, municipio, latitud
FROM dim_municipio
WHERE cod_dpto = '05'
ORDER BY latitud DESC
LIMIT 5;


-- 2 · GROUP BY: la tabla dinámica de SQL
-- Recaudo y aportantes únicos por mes.
SELECT periodo,
       SUM(valor_aporte)           AS recaudo,
       COUNT(DISTINCT id_afiliado) AS aportantes
FROM fact_aporte
GROUP BY periodo
ORDER BY periodo;


-- 3 · JOIN sobre datos reales
-- Departamentos con más afiliados a Colpensiones (tres tablas, dos llaves).
SELECT d.departamento, SUM(r.cantidad) AS afiliados
FROM real_afiliados r
JOIN dim_municipio m    ON m.cod_mpio = r.cod_mpio
JOIN dim_departamento d ON d.cod_dpto = m.cod_dpto
GROUP BY d.departamento
ORDER BY afiliados DESC
LIMIT 6;


-- 4 · Un indicador real desde una vista
-- Pensionados por cada 100 afiliados, departamentos con más de 50.000 afiliados.
SELECT departamento, afiliados, pensionados,
       pensionados_por_100_afiliados AS pens_x_100
FROM v_real_departamento
WHERE afiliados > 50000
ORDER BY pens_x_100 DESC
LIMIT 6;


-- 5 · HAVING: filtrar grupos
-- Temas de PQRS por debajo de la meta del 90 % respondidas a tiempo.
SELECT tema,
       COUNT(*)                        AS radicadas,
       ROUND(100.0 * AVG(a_tiempo), 1) AS pct_a_tiempo
FROM fact_pqrs
GROUP BY tema
HAVING 100.0 * AVG(a_tiempo) < 90
ORDER BY pct_a_tiempo;


-- 6 · WITH + LEFT JOIN: la lista de mora
-- Activos con 3 o más meses sin aportar (de 9 meses), por regional.
WITH meses AS (
    SELECT id_afiliado, COUNT(DISTINCT periodo) AS meses_con_aporte
    FROM fact_aporte
    GROUP BY id_afiliado
)
SELECT f.regional, COUNT(*) AS afiliados_en_mora
FROM dim_afiliado f
LEFT JOIN meses x ON x.id_afiliado = f.id_afiliado
WHERE f.vigente = 1 AND f.estado = 'Activo'
  AND 9 - COALESCE(x.meses_con_aporte, 0) >= 3
GROUP BY f.regional
ORDER BY afiliados_en_mora DESC;


-- 7 · Función de ventana: variación mes a mes
-- LAG trae el recaudo del mes anterior.
WITH mensual AS (
    SELECT periodo, SUM(valor_aporte) AS recaudo
    FROM fact_aporte GROUP BY periodo
)
SELECT periodo, recaudo,
       ROUND(100.0 * (recaudo - LAG(recaudo) OVER (ORDER BY periodo))
             / LAG(recaudo) OVER (ORDER BY periodo), 2) AS variacion_pct
FROM mensual
ORDER BY periodo;


-- 8 · Los indicadores de la Dirección en una fila
SELECT * FROM v_kpi_fondo;


-- 9 · Resultado del modelo: municipios con menos pensionados de lo esperado
-- El primero es ARMENIA (ANT): un error de la fuente oficial (ver datos/reales/FUENTES.md).
SELECT m.municipio, d.departamento, p.afiliados, p.pensionados,
       p.pensionados_esperados AS esperados, p.desviacion_pct
FROM modelo_pensionados p
JOIN dim_municipio m    ON m.cod_mpio = p.cod_mpio
JOIN dim_departamento d ON d.cod_dpto = m.cod_dpto
WHERE p.afiliados >= 20000
ORDER BY p.desviacion_pct ASC
LIMIT 5;
