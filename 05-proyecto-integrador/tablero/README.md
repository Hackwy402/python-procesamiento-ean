# Tablero de la Dirección · PostgreSQL + Grafana

Levanta una base PostgreSQL con el modelo de la Sesión 5 ya cargado y un tablero de Grafana conectado a ella.

## Requisitos

[Docker Desktop](https://www.docker.com/products/docker-desktop/) encendido.

## Uso

```bash
cd 05-proyecto-integrador/tablero
docker compose up -d
```

- **Tablero:** <http://localhost:3300>. Se ve sin iniciar sesión. Para editar paneles: usuario `admin`, clave `ean2026`.
- **Base de datos:** `localhost:5433`, base `bodega_pensiones`, usuario `analista`, clave `demo-ean-2026`.
  Puedes conectarte con DBeaver, pgAdmin o `psql`.

Las claves son solo para esta demo local. Los puertos quedan abiertos solo en tu computador (`127.0.0.1`).

## Cómo funciona

| Carpeta | Qué hace |
|---|---|
| `init/` | Generada por `pipeline_bodega.py`: `01_modelo.sql` (tablas y llaves), `02_datos.sql` + `csv/` (carga) y `03_vistas.sql` (vistas). PostgreSQL la ejecuta al crear la base. |
| `grafana/provisioning/` | Conecta Grafana a la base y registra el tablero. |
| `grafana/dashboards/` | El tablero: cada panel es una consulta SQL sobre las vistas. |

## Recargar con datos nuevos

```bash
cd ..
python pipeline_bodega.py --datos ../datos --salida salidas --postgres tablero/init
cd tablero
docker compose down -v      # borra la base anterior
docker compose up -d        # la vuelve a crear desde init/
```
