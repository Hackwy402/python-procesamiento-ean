# Tablero en Streamlit (público)

El mismo proyecto integrador de la Sesión 5, publicado en la web para que cualquiera pueda usarlo sin instalar nada.

- **Operación del fondo:** recaudo mensual con pronóstico, PQRS frente a la meta del 90 %, mora por regional y
  calidad de los datos. Filtro por regional en la barra lateral.
- **Datos reales de Colpensiones:** mapa por municipio, pensionados por cada 100 afiliados y pirámide de edades.
- **Modelos:** pronóstico del recaudo (MAPE) y pensionados esperados con datos reales (R²), con el hallazgo de Armenia.
- **Consola SQL:** escribe tus propias consultas (`SELECT` y `WITH`) y descarga el resultado en CSV.
  La base es de **solo lectura**: `INSERT`, `UPDATE`, `DELETE` o `DROP` se rechazan.
- **Automatización:** el botón *Llega un mes* simula la llegada de octubre, noviembre y diciembre; el pipeline
  completo vuelve a correr y todo el tablero se actualiza. Solo cambia tu sesión.

Todo sale de `../pipeline_bodega.py`: el mismo código del notebook y de Grafana.

## Correrlo en tu computador

```bash
pip install -r 05-proyecto-integrador/tablero_streamlit/requirements.txt
streamlit run 05-proyecto-integrador/tablero_streamlit/app.py
```

## Publicarlo en Streamlit Community Cloud

1. Entra a <https://share.streamlit.io> con tu cuenta de GitHub.
2. **Create app** → *Deploy a public app from GitHub*.
3. Repositorio `Hackwy402/python-procesamiento-ean`, rama `main`,
   archivo principal `05-proyecto-integrador/tablero_streamlit/app.py`.
4. En *Advanced settings* elige **Python 3.12** y, si quieres, un subdominio fácil de recordar.
5. **Deploy**. Cada `git push` a `main` actualiza la app sola.
