# Sesión 4 · Automatización: funciones, pipelines y reportes

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/04-automatizacion/PY-EAN_S04_Lab_alumno.ipynb)

**Presentación de la sesión:** [PDF](PY-EAN_S04_Teoria_Automatizacion.pdf) · [PowerPoint](PY-EAN_S04_Teoria_Automatizacion.pptx)

## Objetivos

- Convertir pasos sueltos en **funciones** reutilizables (una función = una responsabilidad).
- Procesar **muchos archivos** con un bucle y consolidarlos con `pd.concat`.
- **Validar la estructura** de cada archivo, manejar errores con `try/except` y llevar una **bitácora**.
- Generar un **reporte Excel** con varias hojas, formato y gráfico, nombrado con la fecha.
- Unir todo en un **pipeline** y conocer cómo llevarlo a producción.

## Archivos

| Archivo | Descripción |
|---|---|
| `PY-EAN_S04_Lab_alumno.ipynb` | Notebook del laboratorio (ábrelo en Colab con el botón de arriba). |
| `pipeline_aportes.py` | Versión “de producción” del pipeline, ejecutable desde la terminal. |

```bash
python pipeline_aportes.py --help
python pipeline_aportes.py --datos ../datos --salida salidas --meses 1-9
```

## Datos usados

- `datos/aportes/aportes_2026-01.csv` … `aportes_2026-09.csv` (un archivo por mes).
- `datos/afiliados.csv` (reto de aportes huérfanos).

> Todos los datos son sintéticos. No corresponden a personas reales.
