# Datos reales · fuentes

Estos archivos son **datos abiertos oficiales**, descargados del portal [datos.gov.co](https://www.datos.gov.co) el
8 de noviembre de 2026. Son cifras agregadas (conteos) y no contienen datos personales.

| Archivo | Conjunto de datos | Publica | Id | Actualizado |
|---|---|---|---|---|
| `colpensiones_afiliados_municipio.csv` | Número de afiliados a Colpensiones desagregado por departamento y municipio | Colpensiones | `xfsi-rqje` | 30 oct 2026 |
| `colpensiones_pensionados_municipio.csv` | Número de pensionados en Colpensiones desagregado por departamento y municipio | Colpensiones | `hdnf-a76p` | 30 oct 2026 |
| `colpensiones_pensionados_edad.csv` | Cantidad de pensionados de Colpensiones por rango de edad | Colpensiones | `np5z-haxm` | 30 oct 2026 |
| `divipola_municipios.csv` | DIVIPOLA · Códigos de municipios (con latitud y longitud) | DANE | `gdxc-w37w` | 24 ene 2025 |

**Licencia:** Creative Commons Atribución-CompartirIgual 4.0 Internacional (CC BY-SA 4.0).

## Descargarlos de nuevo (API Socrata)

```python
import pandas as pd
url = "https://www.datos.gov.co/resource/xfsi-rqje.csv?$limit=50000"
afiliados_reales = pd.read_csv(url)
```

Cambia el id para descargar los demás conjuntos. Si el portal actualiza los datos, las cifras del curso pueden cambiar.

## Lo que hay que limpiar

- **Nombres que no coinciden.** Colpensiones escribe `BOGOTA`, `CALI` o `CUCUTA`. El DANE escribe `BOGOTÁ, D.C.`,
  `SANTIAGO DE CALI` o `SAN JOSÉ DE CÚCUTA`. Se cruzan normalizando el texto y con una tabla de alias.
- **Coordenadas con coma decimal.** `-75,581775` se convierte a `-75.581775`.
- **`SIN CIUDAD`.** Hay afiliados sin municipio. En el modelo se registran como el miembro desconocido `00000`.
