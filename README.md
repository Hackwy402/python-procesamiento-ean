# Python para Procesamiento, Calidad y Automatización de Datos

**Universidad Ean · Educación Continua** · Programa Colpensiones – Ean (Aceptación de Oferta 016-2025)
Docente: Jawy Andrés Romero Pinto · 10 horas · 3 – 9 de noviembre de 2026

Material de laboratorio del programa. Todo se trabaja en **Google Colab**: no necesitas instalar nada.

## Sesiones

| # | Fecha | Tema | Notebook |
|---|---|---|---|
| 1 | Mar 3 nov | Fundamentos de Python y pandas: del Excel al DataFrame | [Abrir en Colab](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/01-fundamentos-python-pandas/PY-EAN_S01_Lab_alumno.ipynb) |
| 2 | Mié 4 nov | Procesamiento: limpieza y transformación de datos | [Abrir en Colab](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/02-limpieza-transformacion/PY-EAN_S02_Lab_alumno.ipynb) |
| 3 | Jue 5 nov | Calidad de datos: perfilado, reglas y métricas | [Abrir en Colab](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/03-calidad-de-datos/PY-EAN_S03_Lab_alumno.ipynb) |
| 4 | Vie 6 nov | Automatización: funciones, pipelines y reportes | [Abrir en Colab](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/04-automatizacion/PY-EAN_S04_Lab_alumno.ipynb) |
| 5 | Lun 9 nov | Proyecto integrador: base de datos, SQL y tablero con datos reales | [Abrir en Colab](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/05-proyecto-integrador/PY-EAN_S05_Proyecto_alumno.ipynb) |

## Presentaciones y material adicional

- Cada carpeta de sesión trae la presentación en **PDF** y en **PowerPoint** (`.pptx`).
- [`05-proyecto-integrador/sql/`](05-proyecto-integrador/sql/): todas las sentencias SQL de la Sesión 5, listas para
  copiar en el notebook, en Grafana o en cualquier cliente SQL.
- [`resueltos-en-clase/`](resueltos-en-clase/): los laboratorios de las Sesiones 1 a 4 tal como se resolvieron en vivo
  en clase. Intenta primero el notebook de alumno y úsalos para comparar.

## Datos

La carpeta [`datos/`](datos/) contiene un escenario **ficticio** de un fondo de pensiones, con errores de calidad
sembrados a propósito:

| Archivo | Contenido |
|---|---|
| `afiliados.csv` | ~3.100 afiliados (documento, nombres, fechas, ciudad, salario, estado…) |
| `oficinas.xlsx` | Catálogo de ciudades y regionales (hojas `ciudades` y `regionales`) |
| `aportes/aportes_2026-MM.csv` | Aportes mensuales enero–septiembre 2026 (un archivo por mes) |
| `pqrs.csv` | ~1.500 peticiones, quejas y reclamos |
| `reales/` | **Datos reales y abiertos** de Colpensiones y del DANE (datos.gov.co), ver [FUENTES.md](datos/reales/FUENTES.md) |

> **Los datos del fondo son sintéticos** (los de `reales/` son cifras oficiales agregadas). Ningún nombre, documento, correo ni teléfono corresponde a una persona real.
> Se regeneran con `python scripts/generar_datos.py` (semilla fija).

Los notebooks leen los datos directamente desde este repositorio. Si no hay internet hacia GitHub, sube
`datos.zip` a Colab y ejecuta `!unzip -o datos.zip`.
