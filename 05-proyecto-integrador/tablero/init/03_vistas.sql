-- Generado por pipeline_bodega.py: vistas para el tablero

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
