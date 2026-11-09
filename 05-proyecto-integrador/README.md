# Sesión 5 · Proyecto integrador: base de datos, SQL y tablero

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/05-proyecto-integrador/PY-EAN_S05_Proyecto_alumno.ipynb)

**Presentación de la sesión:** [PDF](PY-EAN_S05_Teoria_Proyecto-Integrador.pdf) · [PowerPoint](PY-EAN_S05_Teoria_Proyecto-Integrador.pptx)

**Caso:** la Dirección de un fondo de pensiones (ficticio) quiere sus datos en una base formal, respuestas en SQL,
un tablero que se actualice solo y saber cómo está frente a los **datos reales de Colpensiones**.

## Objetivos

- Integrar los **datos abiertos reales** de Colpensiones y del DANE (datos.gov.co) con los datos del fondo.
- Cruzar fuentes con **códigos oficiales** (DIVIPOLA) y verificar lo que no cruza.
- Diseñar un **modelo en estrella** con llaves primarias, llaves foráneas y restricciones `CHECK`.
- Responder preguntas de negocio con **SQL**: `WHERE`, `GROUP BY`, `JOIN`, `HAVING`, `WITH` y funciones de ventana.
- Publicar los indicadores como **vistas** y mostrarlos en un **tablero de Grafana**.
- **Integrar modelos** (pronóstico del recaudo y pensionados esperados con datos reales) como tablas de la bodega.
- Ver la **automatización completa**: llega un mes nuevo y la base, los modelos y el tablero se actualizan solos.

## Archivos

| Archivo | Descripción |
|---|---|
| `PY-EAN_S05_Proyecto_alumno.ipynb` | Notebook del laboratorio (SQLite, funciona en Colab) |
| `sql/consultas_clase.sql` | Las sentencias SQL de la clase: SELECT, GROUP BY, JOIN, HAVING, WITH, LAG, vistas y modelos |
| `sql/demo_grafana.sql` | Las sentencias de la demo para pegar en Grafana → Explorar |
| `pipeline_bodega.py` | Versión de producción: genera la base SQLite y la carga de PostgreSQL |
| `tablero/` | PostgreSQL + Grafana con Docker: tablero, simulador de llegada de meses y extracción por SQL |

```bash
python pipeline_bodega.py --datos ../datos --salida salidas --postgres tablero/init
cd tablero && docker compose up -d        # luego abre http://localhost:3300
```

## Datos usados

- Fondo (ficticio): `datos/afiliados.csv`, `datos/aportes/`, `datos/pqrs.csv`, `datos/oficinas.xlsx`.
- Reales (datos.gov.co, CC BY-SA 4.0): `datos/reales/`. Ver [FUENTES.md](../datos/reales/FUENTES.md).
