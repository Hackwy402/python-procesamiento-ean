# Sesión 5 · Proyecto integrador: pipeline de datos de principio a fin

**Caso:** Informe de PQRS y aportes para la Dirección de un fondo de pensiones (ficticio).

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/05-proyecto-integrador/PY-EAN_S05_Proyecto_alumno.ipynb)

## Objetivos

- Integrar en un solo flujo lo visto en el curso: **ingestar → procesar → validar → automatizar → reportar**.
- Leer los 9 archivos mensuales de aportes de forma robusta (separadores y encabezados distintos).
- Medir la calidad de los datos con 8 reglas y reportar su % de cumplimiento.
- Calcular indicadores de PQRS (oportunidad en días hábiles) y de aportes (recaudo, regionales, mora).
- Proteger datos personales con **seudonimización** (SHA-256 con sal) antes de compartir.
- Exportar un Excel `Informe_Direccion_AAAAMMDD.xlsx` con un solo `main()`.

## Archivos

| Archivo | Descripción |
|---|---|
| `PY-EAN_S05_Proyecto_alumno.ipynb` | Notebook guiado con andamiaje (completa los ✏️) |

Los datos están en [`../datos/`](../datos/). Son **sintéticos**: no corresponden a personas reales.
