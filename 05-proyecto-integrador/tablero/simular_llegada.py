#!/usr/bin/env python3
"""
simular_llegada.py — Demo en vivo: "llegan" los archivos de octubre, noviembre y diciembre.

Cada ciclo:
  1. deja un archivo nuevo en datos_vivo/aportes/ (y nuevas PQRS en datos_vivo/pqrs.csv),
  2. ejecuta el pipeline completo (limpiar → validar → modelo formal → modelos → vistas),
  3. recarga el PostgreSQL del tablero en una sola transacción.
Grafana (refresco cada 5 s) muestra el mes nuevo sin que nadie toque nada.

Uso (con el tablero corriendo: docker compose -p tablero-ean up -d):
    python simular_llegada.py --reiniciar            # vuelve a los 9 meses originales
    python simular_llegada.py --cada 30              # un mes nuevo cada 30 s, hasta diciembre
    python simular_llegada.py --un-mes               # solo el siguiente mes (para hacerlo paso a paso)
"""
import argparse
import os
import shutil
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import pipeline_bodega as pb  # noqa: E402

ORIGEN = os.path.join(AQUI, "..", "..", "datos")
VIVO = os.path.join(AQUI, "datos_vivo") + "/"
SALIDA = os.path.join(AQUI, "salidas_vivo")
RETENCION = {10: 0.995, 11: 0.97, 12: 0.95}      # cada mes aporta un poco menos gente: la mora sube


def reiniciar():
    if os.path.exists(VIVO):
        shutil.rmtree(VIVO)
    shutil.copytree(ORIGEN, VIVO)
    pb.log("Datos en vivo reiniciados: enero a septiembre")
    pb.main(VIVO, SALIDA, carpeta_vivo=AQUI)


def llega_un_mes():
    meses = pb.meses_disponibles(VIVO)
    mes = max(meses) + 1
    if mes > 12:
        pb.log("Ya llegó diciembre. Usa --reiniciar para volver a empezar.")
        return False
    _, pqrs, aportes, _ = pb.cargar_curso(VIVO)
    aportes = pb.limpiar_aportes(aportes)
    nuevo, nuevas = pb.simular_mes(aportes, pqrs, mes, retencion=RETENCION.get(mes, 0.98))
    archivo = f"{VIVO}aportes/aportes_2026-{mes:02d}.csv"
    nuevo.to_csv(archivo, index=False)
    nuevas.to_csv(VIVO + "pqrs.csv", mode="a", header=False, index=False)
    pb.log(f">>> LLEGÓ {os.path.basename(archivo)}: {len(nuevo):,} aportes y {len(nuevas)} PQRS nuevas")
    pb.main(VIVO, SALIDA, carpeta_vivo=AQUI)
    return True


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Simula la llegada de meses nuevos al tablero")
    p.add_argument("--reiniciar", action="store_true", help="volver a enero-septiembre")
    p.add_argument("--un-mes", action="store_true", help="entregar solo el siguiente mes")
    p.add_argument("--cada", type=int, default=30, help="segundos entre meses")
    a = p.parse_args()
    if a.reiniciar or not os.path.exists(VIVO):
        reiniciar()
        if a.reiniciar:
            sys.exit(0)
    if a.un_mes:
        llega_un_mes()
    else:
        while llega_un_mes():
            pb.log(f"Esperando {a.cada} s al siguiente archivo… (mira Grafana)")
            time.sleep(a.cada)
