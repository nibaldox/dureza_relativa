# Tiempos de Perforación - Clasificador de Pozos

Este proyecto es una aplicación desarrollada en Python para procesar y clasificar datos de pozos perforados, y para visualizar dicha información de forma gráfica. La aplicación utiliza Streamlit para la interfaz de usuario, y herramientas de visualización (Plotly) para mostrar resultados de clasificación y ubicación.

## Requisitos de Datos

### Columnas Requeridas del CSV
El archivo CSV de entrada debe contener las siguientes columnas obligatorias:
- **tiempo inicio**: Fecha y hora de inicio de la perforación (formato datetime o string convertible a datetime)
- **tiempo final**: Fecha y hora de finalización de la perforación (formato datetime o string convertible a datetime)
- **este**: Coordenada Este del pozo (valor numérico)
- **norte**: Coordenada Norte del pozo (valor numérico)
- **elevacion**: Elevación o cota del pozo (valor numérico)

### Columnas Opcionales
- **drill_pattern**: Patrón de perforación (string) - Utilizado para filtrado de datos

### Columnas Calculadas
Las siguientes columnas son calculadas automáticamente por el script:
- **duracion**: Calculada como la diferencia entre tiempo final y tiempo inicio (en minutos)
- **dureza**: Clasificación categórica según la duración:
  - Roca suave: < 16 minutos
  - Roca media: 16-24 minutos
  - Roca dura: 24-40 minutos
  - Roca muy dura: > 40 minutos
- **indice_dureza**: Valor numérico entre 0 y 100 que representa la dureza del pozo:
  - 0-25: Para tiempos entre 0 y 16 minutos (pendiente lineal)
  - 25-50: Para tiempos entre 16 y 24 minutos (pendiente lineal)
  - 50-75: Para tiempos entre 24 y 40 minutos (pendiente lineal)
  - 75-100: Para tiempos entre 40 y 60 minutos (pendiente lineal)
  - 100: Para tiempos mayores a 60 minutos (valor máximo)

## Estructura del Proyecto

El proyecto se encuentra organizado en módulos separados que facilitan el mantenimiento y escalabilidad del código:

- **streamlit_app.py**  
  Contiene la aplicación principal de Streamlit, que gestiona la interfaz de usuario, la carga de datos, el procesamiento y la visualización.

- **data_processor.py**  
  Contiene la clase `DataProcessor`, encargada de cargar, procesar y clasificar los datos de entrada (archivos CSV).
  - Convierte columnas de tiempo a formato datetime.
  - Calcula la duración en minutos entre "tiempo inicio" y "tiempo final".
  - Clasifica la dureza del pozo (roca suave, roca media, roca dura, roca muy dura) basándose en la duración.

- **visualizer.py**  
  Contiene la clase `Visualizer`, la cual genera gráficos a partir de los datos procesados.
  - `plot_location_interactive`: Genera un scatter plot interactivo para visualizar la ubicación de los pozos.
  - `plot_dureza_count`: Crea un gráfico de torta para mostrar el conteo de pozos por dureza.
  - `plot_duracion_box`: Crea un gráfico box plot para la distribución de duración por dureza.
  - `plot_hardness_heatmap`: Genera un mapa de dispersión 2D que muestra el índice de dureza mediante una escala de colores continua.
  - `plot_3d_scatter`: Visualiza los pozos en un espacio tridimensional.

- **logs/**  
  Carpeta (crearse manualmente si no existe) para almacenar el archivo de logging `app.log`, donde se registran eventos y errores.


## Requisitos

- Python 3.x
- Bibliotecas:
  - pandas
  - plotly
  - streamlit
  - numpy

## Cómo Ejecutar la Aplicación

1. Asegúrate de tener instaladas las dependencias necesarias:

```bash
pip install pandas plotly streamlit numpy
```

2. Prepara tu archivo CSV asegurándote de que contenga las columnas requeridas con los nombres exactos:
   - tiempo inicio
   - tiempo final
   - este
   - norte
   - elevacion
   - drill_pattern (opcional)

3. Coloca tu archivo CSV en el directorio **input-data/** (o en cualquier ubicación a la que apuntes durante la ejecución).

4. Ejecuta la aplicación desde la terminal:

```bash
streamlit run streamlit_app.py
```

5. Usa la interfaz de Streamlit para:
   - **Cargar CSV:** Selecciona el archivo CSV que contiene las columnas requeridas.
   - **Visualizar gráficos:** Explora los datos a través de los gráficos interactivos disponibles.
   - **Filtro por Drill Pattern:** Filtra los resultados por el valor de la columna "drill_pattern" si está disponible.
   - **Ajuste de Detalle:** Controla el nivel de detalle del mapa de densidad 3D en tiempo real.
   - **Visualización 3D:** Explora la distribución espacial de los pozos en tres dimensiones.

## Características de Visualización

### Mapa de Índice de Dureza
- Visualización 2D con escala de colores continua
- Escala de colores intuitiva:
  - Verde: Roca muy suave (0-25)
  - Amarillo: Roca suave (25-50)
  - Naranja: Roca media (50-75)
  - Rojo: Roca dura (75-100)
- Información detallada al pasar el cursor sobre los puntos
- Barra de escala con etiquetas descriptivas
- Fondo transparente para mejor visualización

### Mapa de Densidad 3D
- Visualiza la concentración de pozos por tipo de dureza en un espacio tridimensional.
- Control deslizante para ajustar el nivel de detalle en tiempo real.
- Colores distintivos para cada tipo de dureza.
- Interactividad completa para rotar, hacer zoom y explorar los datos.

### Visualización 3D de Pozos
- Representa cada pozo en el espacio usando coordenadas este, norte y elevación.
- Puntos coloreados según la dureza del pozo.
- Tamaño de puntos optimizado para mejor visualización.
- Controles interactivos para explorar la distribución espacial.

## Notas

- Asegúrate de que los nombres de las columnas del CSV coincidan exactamente con los nombres requeridos (tiempo inicio, tiempo final, este, norte, elevacion).
- Los nombres de las columnas se convertirán automáticamente a minúsculas durante el procesamiento.
- La aplicación realiza validación de columnas y manejo de errores para ayudar a identificar problemas con el archivo de entrada.
- El índice de dureza proporciona una medida continua y más precisa de la dureza que la clasificación categórica.
- Los mapas de densidad 3D pueden requerir más recursos del sistema dependiendo del nivel de detalle seleccionado.
- Las visualizaciones son completamente interactivas y permiten una exploración detallada de los datos.

## Ejemplo de Formato CSV
```csv
tiempo inicio,tiempo final,este,norte,elevacion,drill_pattern
2024/09/06 19:52,2024/09/06 20:10,648.705,175.765,38.38,PW30
```

## Licencia

Este proyecto se distribuye bajo licencia MIT.
