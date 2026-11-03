# Sesión 3 · Calidad de datos: perfilado, reglas y métricas

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/03-calidad-de-datos/PY-EAN_S03_Lab_alumno.ipynb)

**Jueves 5 de noviembre de 2026 · 2 horas · Google Colab**

## Objetivos

Al terminar la sesión podrás:

- Explicar las **7 dimensiones de calidad**: completitud, unicidad, validez, consistencia, exactitud, oportunidad e
  integridad referencial.
- **Perfilar** una tabla con pandas (tipos, % de vacíos, valores distintos).
- Escribir **reglas de validación** como máscaras booleanas: expresiones regulares, fechas, reglas de negocio y cruces
  entre tablas.
- Construir un **catálogo de reglas** y un **motor** que genere un reporte de calidad con semáforo, un índice por
  dimensión y un índice global.
- Separar los registros **válidos** de los que van a **cuarentena**, y medir cuánto mejora la calidad después de limpiar.

## Laboratorio

`PY-EAN_S03_Lab_alumno.ipynb`: 17 ejercicios más un reto (~70 min). Ábrelo con el botón **Abrir en Colab** y guarda
una copia en tu Drive.

## Datos usados

| Archivo | Uso |
|---|---|
| `datos/afiliados.csv` | Perfilado, reglas y reporte de calidad |
| `datos/oficinas.xlsx` (hoja `ciudades`) | Catálogo para validar ciudad y departamento |
| `datos/pqrs.csv` | Regla de oportunidad (≤ 15 días hábiles) |
| `datos/aportes/aportes_2026-03.csv` | Exactitud del aporte (16 % del IBC) e integridad referencial |

> Todos los datos son sintéticos y no corresponden a personas reales.
