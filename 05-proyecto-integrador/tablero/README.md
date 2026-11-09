# Tablero de la Dirección · PostgreSQL + Grafana

Levanta una base PostgreSQL con el modelo de la Sesión 5 ya cargado y un tablero de Grafana conectado a ella.

## Requisitos

[Docker Desktop](https://www.docker.com/products/docker-desktop/) encendido.

## Uso

```bash
cd 05-proyecto-integrador/tablero
docker compose up -d
```

- **Tablero:** <http://localhost:3300>. Se ve sin iniciar sesión y se refresca cada 5 s. Para editar paneles: usuario
  `admin`, clave `ean2026`.
- **Base de datos:** `localhost:5433`, base `bodega_pensiones`, usuario `analista`, clave `demo-ean-2026`.
  Puedes conectarte con DBeaver, pgAdmin o `psql`.

Grafana se conecta con el usuario `lector_grafana`, de **solo lectura**: puede consultar, pero un `DELETE` o un
`DROP` responden *permission denied*. Las claves son solo para esta demo local. Los puertos quedan abiertos solo en tu computador (`127.0.0.1`).

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

## Automatización en vivo: llegan meses nuevos

```bash
python simular_llegada.py --reiniciar     # punto de partida: enero a septiembre
python simular_llegada.py --un-mes        # llega el siguiente mes (octubre, noviembre, diciembre)
python simular_llegada.py --cada 20       # un mes cada 20 s hasta diciembre
```

Cada llegada deja un archivo nuevo en `datos_vivo/aportes/`, ejecuta `pipeline_bodega.py` completo (limpieza, calidad,
modelo formal, **modelos**) y recarga PostgreSQL en una sola transacción. La fila *Automatización en vivo* del tablero
cambia sola. En producción, el simulador lo reemplaza el Programador de tareas o `cron`.

## Modelos integrados

| Tabla | Modelo |
|---|---|
| `pred_recaudo` | Regresión lineal sobre el tiempo: ajuste y pronóstico del próximo mes, con intervalo |
| `modelo_pensionados` | Regresión log-log con datos reales: pensionados esperados por municipio y su desviación |
| `modelo_metricas` | MAPE del pronóstico y R² del modelo de pensionados, con la fecha de entrenamiento |

Se reentrenan con cada carga.

## SQL desde Grafana y extracción de datos

- **Explore:** menú *Explorar* → modo *Code* → escribe un `SELECT` → *Run query*. *Inspector de consultas* → *Data* →
  *Download CSV* descarga el resultado.
- **Por API:**
  ```bash
  python3 extraer_sql.py "SELECT * FROM v_kpi_fondo"
  python3 extraer_sql.py "SELECT * FROM v_mora" --csv mora.csv
  ```
