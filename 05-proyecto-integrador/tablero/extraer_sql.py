#!/usr/bin/env python3
"""
extraer_sql.py — Ejecuta una sentencia SQL a través de la API de Grafana y guarda el resultado en CSV.
Es lo mismo que hace un panel, pero desde un script: así otra herramienta (o un notebook) extrae datos
del tablero sin conectarse directo a la base.

Uso:
    python extraer_sql.py "SELECT * FROM v_kpi_fondo"
    python extraer_sql.py "SELECT * FROM v_mora" --csv mora.csv
"""
import argparse
import csv
import json
import sys
import urllib.error
import urllib.request

GRAFANA = "http://localhost:3300"


def consultar(sql):
    cuerpo = {"queries": [{"refId": "A", "datasource": {"uid": "bodega"}, "rawSql": sql, "format": "table"}],
              "from": "now-1h", "to": "now"}
    req = urllib.request.Request(f"{GRAFANA}/api/ds/query", data=json.dumps(cuerpo).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        respuesta = json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:              # la base rechazó la sentencia
        respuesta = json.load(e)
    resultado = respuesta["results"]["A"]
    if "error" in resultado:
        sys.exit(f"Error de la base: {resultado['error']}")
    marco = resultado["frames"][0]
    columnas = [c["name"] for c in marco["schema"]["fields"]]
    filas = list(zip(*marco["data"]["values"]))
    return columnas, filas


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="SQL → Grafana → CSV")
    p.add_argument("sql")
    p.add_argument("--csv", default=None, help="archivo de salida (si no, imprime en pantalla)")
    a = p.parse_args()
    columnas, filas = consultar(a.sql)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([columnas, *filas])
        print(f"{len(filas)} filas → {a.csv}")
    else:
        print(" | ".join(columnas))
        for fila in filas[:30]:
            print(" | ".join(str(v) for v in fila))
