-- Usuario de solo lectura para Grafana: puede consultar (SELECT) pero no modificar ni borrar.
CREATE ROLE lector_grafana LOGIN PASSWORD 'solo-lectura-2026';
GRANT CONNECT ON DATABASE bodega_pensiones TO lector_grafana;
GRANT USAGE ON SCHEMA public TO lector_grafana;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO lector_grafana;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO lector_grafana;
