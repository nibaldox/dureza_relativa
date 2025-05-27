# Archivo de Ejemplo para Clasificador de Pozos

Este directorio contiene un archivo de ejemplo (`ejemplo_datos.txt`) que puedes utilizar para probar la aplicación de Clasificador de Pozos. Este archivo contiene datos ficticios pero realistas que cumplen con el formato requerido por la aplicación.

## Estructura del Archivo de Ejemplo

El archivo `ejemplo_datos.txt` contiene las siguientes columnas:

- **tiempo inicio**: Fecha y hora de inicio de la perforación
- **tiempo final**: Fecha y hora de finalización de la perforación
- **este**: Coordenada Este del pozo
- **norte**: Coordenada Norte del pozo
- **elevacion**: Elevación o cota del pozo
- **drill_pattern**: Patrón de perforación (opcional, usado para filtrado)

## Cómo Usar el Archivo de Ejemplo

Para utilizar este archivo con la aplicación:

1. Cambia la extensión del archivo de `.txt` a `.csv`:
   ```
   ejemplo_datos.txt → ejemplo_datos.csv
   ```

2. Inicia la aplicación Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```

3. En la interfaz de la aplicación, sube el archivo `ejemplo_datos.csv` usando el selector de archivos.

4. Explora las diferentes visualizaciones y filtros disponibles en la aplicación.

## Características de los Datos de Ejemplo

Los datos de ejemplo incluyen:

- 25 registros de pozos ficticios
- 5 patrones de perforación diferentes (PW30, PW31, PW32, PW33, PW34)
- Variedad de tiempos de perforación que cubren todas las categorías de dureza:
  - Roca suave (< 16 minutos)
  - Roca media (16-24 minutos)
  - Roca dura (24-40 minutos)
  - Roca muy dura (> 40 minutos)
- Coordenadas espaciales distribuidas para visualizar patrones geográficos

## Notas

- El archivo se proporciona en formato `.txt` para evitar que sea ignorado por el control de versiones (según las reglas del `.gitignore`).
- Para usarlo con la aplicación, debes cambiar la extensión a `.csv`.
- Puedes modificar este archivo o crear tus propios archivos CSV siguiendo el mismo formato para probar diferentes escenarios.
