# Sesión 2 · Procesamiento: limpieza y transformación de datos

**PY-EAN · Python para Procesamiento, Calidad y Automatización de Datos** · Universidad Ean · Mié 4 nov 2026

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hackwy402/python-procesamiento-ean/blob/main/02-limpieza-transformacion/PY-EAN_S02_Lab_alumno.ipynb)

## Objetivos

- Limpiar texto (`str.strip`, `lower`, `title`, quitar tildes) y normalizar categorías con diccionarios de mapeo.
- Convertir tipos: documentos y códigos como texto, salarios con `pd.to_numeric`, fechas con `pd.to_datetime`.
- Decidir qué hacer con los nulos (marcar, imputar o eliminar) y eliminar duplicados exactos y por llave.
- Crear columnas derivadas (`pd.cut`), unir tablas con `merge` (el BUSCARV de pandas) y resumir con
  `groupby` y `pivot_table`.
- Exportar el resultado limpio: `afiliados_limpios.csv` (se usa en la Sesión 3).

## Cómo trabajar

1. Abre el notebook con el botón **Abrir en Colab**.
2. **Archivo → Guardar una copia en Drive**.
3. Ejecuta las celdas en orden (**Shift + Enter**) y resuelve los ejercicios marcados con ✏️.

## Datos usados (carpeta `datos/` del repositorio)

| Archivo | Uso en esta sesión |
|---|---|
| `afiliados.csv` | Archivo a limpiar (~3.120 filas con errores sembrados) |
| `oficinas.xlsx` (hoja `ciudades`) | Catálogo para traer la regional con `merge` |
| `pqrs.csv` | Reto de cierre: días de respuesta por tipo de solicitud |

> Todos los datos son sintéticos: no corresponden a personas reales.
