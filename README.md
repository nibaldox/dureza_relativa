# Plataforma de Clasificación de Dureza Relativa

Este repositorio contiene dos implementaciones complementarias para analizar los tiempos de perforación de pozos y clasificarlos según su dureza:

1. **Aplicación Streamlit (Python):** la versión original con la que se procesan archivos CSV y se generan visualizaciones interactivas en Plotly.
2. **WebApp React (TypeScript):** una interfaz web moderna que replica y extiende las funcionalidades de la app de Streamlit directamente en el navegador.

Ambas experiencias comparten la misma lógica de negocio: normalizar la información de perforación, calcular métricas temporales y presentar gráficos que faciliten la toma de decisiones en terreno.

---

## Requisitos de Datos

Para garantizar que el procesamiento funcione correctamente, cualquier CSV que se cargue (ya sea en la aplicación de Streamlit o en la WebApp) debe respetar la siguiente estructura:

| Columna         | Tipo esperado            | Descripción                                                                 |
|-----------------|--------------------------|-----------------------------------------------------------------------------|
| `tiempo inicio` | Fecha/hora (string o ISO) | Momento en el que inicia la perforación.                                   |
| `tiempo final`  | Fecha/hora (string o ISO) | Momento en el que termina la perforación.                                  |
| `este`          | Numérico                  | Coordenada Este del pozo.                                                  |
| `norte`         | Numérico                  | Coordenada Norte del pozo.                                                 |
| `elevacion`     | Numérico                  | Elevación (cota) del pozo.                                                 |
| `drill_pattern` | String (opcional)         | Patrón de perforación utilizado. Se emplea para filtros y agrupaciones.    |

Durante el procesamiento se calculan automáticamente:

- **`duracion`**: diferencia en minutos entre `tiempo final` y `tiempo inicio`.
- **`dureza`**: etiqueta categórica (roca suave, media, dura o muy dura) basada en la duración.
- **`indice_dureza`**: valor entre 0 y 100 que describe la dureza en escala continua para facilitar comparaciones finas.

---

## Estructura del Proyecto

```text
├── data_processor.py          # Lógica de normalización y clasificación (Python)
├── streamlit_app.py           # UI original construida con Streamlit
├── visualizer.py              # Gráficos Plotly reutilizables
├── webapp/                    # Nuevo frontend en React + TypeScript + Vite
│   ├── src/
│   │   ├── components/        # Componentes reutilizables (ej. cargador de CSV)
│   │   ├── styles/            # Hojas de estilo CSS
│   │   └── utils/             # Procesamiento de datos y generación de gráficos
│   ├── index.html             # Punto de entrada HTML
│   └── package.json           # Scripts de desarrollo y dependencias
└── requirements.txt           # Dependencias Python para la app Streamlit
```

---

## Guía Rápida de Uso

### 1. Aplicación Streamlit

1. Crear y activar un entorno virtual de Python (opcional pero recomendado).
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la interfaz:
   ```bash
   streamlit run streamlit_app.py
   ```
4. Cargar el CSV con la estructura descrita y explorar los gráficos interactivos:
   - Conteo por dureza.
   - Dispersión espacial (2D y 3D).
   - Boxplot de duración.
   - Heatmap de índices de dureza.

### 2. WebApp React

1. Instalar dependencias de Node.js (se requiere Node 18+):
   ```bash
   cd webapp
   npm install
   ```
   > Nota: En este entorno de ejecución no se dispone de acceso a internet, por lo que la instalación puede fallar. Para trabajar localmente, ejecutar el comando en un entorno con conexión.
2. Ejecutar servidor de desarrollo:
   ```bash
   npm run dev
   ```
3. Abrir el navegador en la URL indicada por Vite y utilizar la interfaz para cargar y analizar los CSV.

---

## Plan de Pruebas

El proyecto aún no cuenta con pruebas automatizadas. A continuación se describe el plan para incorporarlas de forma incremental.

### Python / Streamlit

1. **Pruebas unitarias (pytest):**
   - Verificar la correcta lectura de CSVs válidos e inválidos en `DataProcessor`.
   - Asegurar el cálculo correcto de `duracion`, `dureza` e `indice_dureza` para distintos escenarios límite (ej. tiempos negativos, datos faltantes).
   - Confirmar que los filtros por `drill_pattern` funcionen y que el resultado preserve la estructura esperada.
2. **Pruebas de integración ligera:**
   - Utilizar `streamlit.testing` o `pytest` con `requests` para simular la carga de archivos y validar que los gráficos se generan sin excepciones.
3. **Validación de regresión de datos:**
   - Mantener un conjunto pequeño de CSVs de ejemplo en `tests/fixtures` y comparar salidas agregadas (conteos, promedios, rangos) contra snapshots aprobados.

### React / TypeScript

1. **Configuración de Vitest + React Testing Library:**
   - Ejecutar `npm install -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom`.
2. **Pruebas unitarias de utilidades (`src/utils`):**
   - Validar que `dataProcessor` transforme los datasets y calcule métricas igual que la versión Python.
   - Comprobar que los generadores de gráficas (`charts.ts`) produzcan configuraciones de Plotly coherentes (ejes, títulos, escalas de color).
3. **Pruebas de componentes:**
   - Testear `DataUploader` para asegurar que maneje archivos correctos e inválidos, y que propague eventos al `App`.
   - Simular la interacción completa de carga y filtrado para detectar regresiones en la UI.
4. **Pruebas end-to-end (opcional):**
   - Integrar Playwright o Cypress para automatizar un flujo básico: cargar CSV, ajustar filtros y verificar la presencia de gráficos clave.

### Automatización y CI

- Configurar GitHub Actions con dos jobs:
  1. `python-tests`: instala dependencias, ejecuta `pytest` y reporta cobertura.
  2. `webapp-tests`: usa Node 18, instala paquetes, corre `npm run lint` y `npm test` (Vitest) en modo `--run`.
- Agregar validaciones de formato (por ejemplo, `ruff` para Python y `eslint`/`prettier` para TypeScript) para mantener un estilo consistente.

---

## Recursos Adicionales

- `EJEMPLO_README.md`: versión previa del README con información detallada sobre visualizaciones disponibles.
- `ejemplo_datos.txt`: ejemplo mínimo de archivo CSV.
- `app.log`: archivo de logs generado por la ejecución de la app de Streamlit (se crea automáticamente si se habilita el logging).

---

## Próximos Pasos

- Migrar la lógica de procesamiento compartido a un paquete común reutilizable (por ejemplo, publicar una librería Python/TypeScript con cálculos idénticos).
- Implementar el plan de pruebas descrito y activar la integración continua.
- Documentar decisiones de diseño y criterios de aceptación en un `CONTRIBUTING.md` para facilitar aportes externos.
