#!/usr/bin/env python3
"""
pipeline_aportes.py — Versión "de producción" del laboratorio de la Sesión 4
Universidad Ean · PY-EAN · Python para Procesamiento, Calidad y Automatización de Datos

Lee los archivos mensuales de aportes, valida su estructura, consolida, marca alertas
y genera un reporte Excel con formato y gráfico. Deja una bitácora en un archivo .log.

Uso:
    python pipeline_aportes.py --datos ../datos --salida salidas
    python pipeline_aportes.py --datos ../datos --salida salidas --meses 1-3
    python pipeline_aportes.py --help

Programarlo (ejemplos):
    Windows → Programador de tareas: acción "python C:\\ruta\\pipeline_aportes.py --datos ... --salida ..."
    Linux/Mac → cron (día 5 de cada mes, 6:00 a. m.):
        0 6 5 * * /usr/bin/python3 /ruta/pipeline_aportes.py --datos /ruta/datos --salida /ruta/salidas
"""
import argparse
import logging
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")                     # sin ventanas: sirve en servidores y tareas programadas
import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, PatternFill

# ----------------------------------------------------------------- configuración
SMMLV = 1_750_905                         # salario mínimo 2026 (verificar valor vigente)
TASA = 0.16                               # aporte a pensión = 16 % del IBC
ANIO = 2026
COLUMNAS = ["id_afiliado", "periodo", "ibc", "valor_aporte", "fecha_pago", "operador"]

log = logging.getLogger("pipeline_aportes")


# ----------------------------------------------------------------- etapas
def ruta_mes(ruta_datos, mes):
    return os.path.join(ruta_datos, "aportes", f"aportes_{ANIO}-{mes:02d}.csv")


def leer_aportes(ruta):
    """Lee un archivo detectando el separador y normalizando nombres de columnas."""
    df = pd.read_csv(ruta, sep=None, engine="python")
    df.columns = df.columns.str.strip().str.lower()
    return df


def validar_estructura(df, esperadas=COLUMNAS):
    return [c for c in esperadas if c not in df.columns]


def cargar_aportes(ruta_datos, meses):
    partes = []
    for m in meses:
        ruta = ruta_mes(ruta_datos, m)
        nombre = os.path.basename(ruta)
        try:
            df = leer_aportes(ruta)
            faltan = validar_estructura(df)
            if faltan:
                raise ValueError(f"faltan columnas {faltan}")
            df["archivo_origen"] = nombre
            partes.append(df)
            log.info("%s OK (%d filas)", nombre, len(df))
        except Exception as e:
            log.error("%s ERROR: %s", nombre, e)
    if not partes:
        raise RuntimeError("No se pudo cargar ningún archivo de aportes.")
    return pd.concat(partes, ignore_index=True)


def limpiar_aportes(df):
    antes = len(df)
    df = df.drop_duplicates(subset=COLUMNAS).copy()
    df["fecha_pago"] = pd.to_datetime(df["fecha_pago"], errors="coerce")
    log.info("Duplicados eliminados: %d", antes - len(df))
    return df


def marcar_alertas(df):
    esperado = (df["ibc"] * TASA).round()
    df["aporte_incorrecto"] = (df["valor_aporte"] - esperado).abs() > 1
    limite = pd.to_datetime(df["periodo"] + "-01") + pd.offsets.MonthEnd(2)
    df["pago_tardio"] = df["fecha_pago"] > limite
    df["ibc_bajo_minimo"] = df["ibc"] < SMMLV
    df["tiene_alerta"] = df[["aporte_incorrecto", "pago_tardio", "ibc_bajo_minimo"]].any(axis=1)
    log.info("Alertas: %d filas con al menos una alerta", df["tiene_alerta"].sum())
    return df


def resumir(df):
    return (df.groupby("periodo")
              .agg(aportantes=("id_afiliado", "nunique"),
                   recaudo=("valor_aporte", "sum"),
                   aportes_incorrectos=("aporte_incorrecto", "sum"),
                   pagos_tardios=("pago_tardio", "sum"),
                   ibc_bajo_minimo=("ibc_bajo_minimo", "sum"))
              .reset_index())


def graficar_recaudo(resumen, ruta_png):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(resumen["periodo"], resumen["recaudo"] / 1e6, color="#1F4E9C")
    ax.set_title(f"Recaudo mensual de aportes {ANIO} (millones de $)")
    ax.set_ylabel("Millones de $")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta_png, dpi=120)
    plt.close(fig)
    return ruta_png


def exportar_reporte(df, resumen, carpeta, ruta_log):
    ruta_xlsx = os.path.join(carpeta, f"reporte_aportes_{datetime.now():%Y-%m-%d}.xlsx")
    por_operador = df.groupby("operador").agg(aportes=("valor_aporte", "count"),
                                              recaudo=("valor_aporte", "sum"))
    matriz = df.pivot_table(index="periodo", columns="operador", values="valor_aporte", aggfunc="sum")
    alertas = df[df["tiene_alerta"]].copy()
    alertas["fecha_pago"] = alertas["fecha_pago"].dt.date
    with open(ruta_log, encoding="utf-8") as f:
        bitacora = pd.DataFrame({"evento": f.read().splitlines()})
    with pd.ExcelWriter(ruta_xlsx, engine="openpyxl") as w:
        resumen.to_excel(w, sheet_name="resumen_mensual", index=False)
        por_operador.to_excel(w, sheet_name="por_operador")
        matriz.to_excel(w, sheet_name="periodo_x_operador")
        alertas.to_excel(w, sheet_name="alertas", index=False)
        bitacora.to_excel(w, sheet_name="bitacora", index=False)
    return ruta_xlsx


def dar_formato(ruta_xlsx, ruta_png):
    wb = load_workbook(ruta_xlsx)
    for ws in wb.worksheets:
        for celda in ws[1]:
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor="1F3864")
        for col in ws.columns:
            ancho = max(len(str(c.value)) for c in col[:200] if c.value is not None) + 2
            ws.column_dimensions[col[0].column_letter].width = min(max(ancho, 10), 60)
            for c in col[1:]:
                if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                    c.number_format = "#,##0"
        ws.freeze_panes = "A2"
    wb["resumen_mensual"].add_image(XLImage(ruta_png), "H2")
    wb.save(ruta_xlsx)


def ejecutar_pipeline(ruta_datos, carpeta_salida, meses):
    """Cargar → validar → limpiar → alertas → resumir → exportar."""
    os.makedirs(carpeta_salida, exist_ok=True)
    ruta_log = os.path.join(carpeta_salida, f"bitacora_{datetime.now():%Y-%m-%d}.log")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
                        handlers=[logging.FileHandler(ruta_log, mode="w", encoding="utf-8"),
                                  logging.StreamHandler()])
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    log.info("Inicio del pipeline · datos=%s · meses=%s", ruta_datos, list(meses))
    df = marcar_alertas(limpiar_aportes(cargar_aportes(ruta_datos, meses)))
    resumen = resumir(df)
    ruta_png = graficar_recaudo(resumen, os.path.join(carpeta_salida, "recaudo_mensual.png"))
    ruta_xlsx = exportar_reporte(df, resumen, carpeta_salida, ruta_log)
    dar_formato(ruta_xlsx, ruta_png)
    log.info("Reporte generado: %s (%d aportes, recaudo $%s)",
             ruta_xlsx, len(df), f"{resumen['recaudo'].sum():,.0f}")
    return ruta_xlsx


def parse_meses(texto):
    """'1-9' → range(1, 10) ;  '1,3,5' → [1, 3, 5]"""
    if "-" in texto:
        a, b = texto.split("-")
        return range(int(a), int(b) + 1)
    return [int(x) for x in texto.split(",")]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pipeline de consolidación y reporte de aportes.")
    ap.add_argument("--datos", default="../datos", help="carpeta que contiene aportes/ (por defecto ../datos)")
    ap.add_argument("--salida", default="salidas", help="carpeta donde se guarda el reporte")
    ap.add_argument("--meses", default="1-9", help="rango '1-9' o lista '1,2,3' (por defecto 1-9)")
    args = ap.parse_args()
    ejecutar_pipeline(args.datos, args.salida, parse_meses(args.meses))
