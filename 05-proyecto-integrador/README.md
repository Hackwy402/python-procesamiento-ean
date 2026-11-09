# Sesión 5 · Proyecto integrador: base de datos, SQL y tablero

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/05-proyecto-integrador/PY-EAN_S05_Proyecto_alumno.ipynb)

**Presentación de la sesión:** [PY-EAN_S05_Teoria_Proyecto-Integrador.pdf](PY-EAN_S05_Teoria_Proyecto-Integrador.pdf)

**Caso:** la Dirección de un fondo de pensiones (ficticio) quiere sus datos en una base formal, respuestas en SQL,
un tablero que se actualice solo y saber cómo está frente a los **datos reales de Colpensiones**.

## Objetivos

- Integrar los **datos abiertos reales** de Colpensiones y del DANE (datos.gov.co) con los datos del fondo.
- Cruzar fuentes con **códigos oficiales** (DIVIPOLA) y verificar lo que no cruza.
- Diseñar un **modelo en estrella** con llaves primarias, llaves foráneas y restricciones `CHECK`.
- Responder preguntas de negocio con **SQL**: `WHERE`, `GROUP BY`, `JOIN`, `HAVING`, `WITH` y funciones de ventana.
- Publicar los indicadores como **vistas** y mostrarlos en un **tablero de Grafana**.

## Archivos

| Archivo | Descripción |
|---|---|
| `PY-EAN_S05_Proyecto_alumno.ipynb` | Notebook del laboratorio (SQLite, funciona en Colab) |
| `pipeline_bodega.py` | Versión de producción: genera la base SQLite y la carga de PostgreSQL |
| `tablero/` | PostgreSQL + Grafana con Docker: el tablero de la Dirección |

```bash
python pipeline_bodega.py --datos ../datos --salida salidas --postgres tablero/init
cd tablero && docker compose up -d        # luego abre http://localhost:3300
```

## Datos usados

- Fondo (ficticio): `datos/afiliados.csv`, `datos/aportes/`, `datos/pqrs.csv`, `datos/oficinas.xlsx`.
- Reales (datos.gov.co, CC BY-SA 4.0): `datos/reales/`. Ver [FUENTES.md](../datos/reales/FUENTES.md).
