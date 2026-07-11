import streamlit as st
import pandas as pd
from data_processor import DataProcessor
from visualizer import Visualizer
import plotly.express as px
from typing import Optional
from io import BytesIO

# PARITY-DEBT: webapp/src/utils/dataProcessor.ts:processCsvData — the
# Streamlit UI is a thin shell over the pandas adapter; keep widgets
# stateless and call the adapter on every rerun so the TS port can
# mirror the data flow without re-implementing UI state.
from classification import (
    DEFAULT_THRESHOLDS,
    Thresholds,
    DEFAULT_DURATION_THRESHOLDS,
    DEFAULT_RATE_THRESHOLDS,
)

# Configuración para que la página use todo el ancho
st.set_page_config(layout="wide", page_title="Clasificador de Pozos", page_icon=":material/analytics:")


@st.cache_data
def cargar_datos(uploaded_file: BytesIO) -> pd.DataFrame:
    """
    Carga y procesa los datos desde un archivo CSV.

    Args:
        uploaded_file (BytesIO): Archivo CSV subido por el usuario.

    Returns:
        pd.DataFrame: DataFrame procesado con las clasificaciones de dureza.
    """
    data_processor = DataProcessor()
    df_processed: pd.DataFrame = data_processor.load_and_process(uploaded_file)
    return df_processed


def _build_thresholds_from_widgets(
    duration_soft: float,
    duration_medium: float,
    duration_hard: float,
    rate_soft: float,
    rate_medium: float,
    rate_hard: float,
) -> Thresholds:
    """Assemble a `Thresholds` TypedDict from the sidebar widget state.

    Pulled into a small helper so the Streamlit rerun path stays a
    straight read of widget values — the Streamlit widgets are the
    single source of truth for what the user has tuned.
    """
    return {
        "duration": {
            "soft": float(duration_soft),
            "medium": float(duration_medium),
            "hard": float(duration_hard),
        },
        "rate": {
            "soft": float(rate_soft),
            "medium": float(rate_medium),
            "hard": float(rate_hard),
        },
    }


def main() -> None:
    """
    Función principal que ejecuta la aplicación Streamlit para clasificar y visualizar datos de pozos perforados.
    """
    st.title("Clasificador de Pozos - Aplicación Streamlit")

    st.markdown("""
    Esta aplicación permite cargar un archivo CSV, procesarlo y visualizar gráficos utilizando Streamlit.

    **Funcionalidades:**
    - Cargar archivo CSV y clasificar datos.
    - Visualizar gráficos en una grilla 2x2:
        - Fila 1: Box Plot y Torta.
        - Fila 2: Ubicación de Pozos (con y sin filtro).
    - Filtrar por drill pattern.
    - Ajustar umbrales de dureza (duración y tasa de penetración).
    - Exportar el DataFrame filtrado a CSV.
    """)

    # Subir archivo CSV
    uploaded_file: Optional[BytesIO] = st.file_uploader("Carga tu archivo CSV", type="csv")
    if uploaded_file is not None:
        try:
            # Cargar y procesar datos con caché
            df_processed: pd.DataFrame = cargar_datos(uploaded_file)
            st.success("Archivo CSV cargado y procesado exitosamente.")

            # Inicializar el adapter una sola vez — el resto de los
            # helpers (classify_with_metric, add_rig_normalized_rate)
            # son funciones puras sobre el DataFrame cacheado.
            data_processor = DataProcessor()

            # Filtros en la barra lateral
            with st.sidebar:
                st.header("Filtros")
                
                # Filtro por fecha
                st.subheader("Filtro por fecha")
                # 'tiempo inicio' ya viene tipado como datetime desde data_processor.py:54.
                # No se reasigna aquí porque cargar_datos está memoizado con @st.cache_data
                # y mutar el resultado cacheado corrompe invocaciones futuras.

                # Obtener fechas mínima y máxima
                min_date = df_processed['tiempo inicio'].min().date()
                max_date = df_processed['tiempo inicio'].max().date()

                # Crear selector de rango de fechas
                date_range = st.date_input(
                    "Selecciona rango de fechas",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )

                # Asegurar que tenemos dos fechas para el rango
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    # Convertir a datetime para comparación
                    start_date = pd.to_datetime(start_date)
                    end_date = pd.to_datetime(end_date).replace(hour=23, minute=59, second=59)
                else:
                    # Selección parcial: el usuario solo cliqueó una fecha. Pedimos el rango
                    # completo y detenemos el rerun hasta que se complete; sin esto, el
                    # fallback anterior aplicaba start=end=esa fecha en silencio, mostrando
                    # datos del día único sin avisar al usuario.
                    st.info("Selecciona el rango completo de fechas para continuar.")
                    st.stop()

                # Filtro por perforadora (Phase C.3). Multiselect sobre
                # los rigs normalizados; si la columna no existe en el
                # CSV se muestra un info y se omite sin error.
                if "perforadora" in df_processed.columns:
                    st.subheader("Filtro por perforadora")
                    rigs = sorted(
                        df_processed["perforadora"].dropna().astype(str).unique(),
                        reverse=True,
                    )
                    perforadoras_seleccionadas: list = st.multiselect(
                        "Perforadoras",
                        rigs,
                    )
                else:
                    perforadoras_seleccionadas = []
                    st.info(
                        "No se encontró la columna 'perforadora'. "
                        "Mostrando todas las filas."
                    )

            # Filtro por drill pattern
            if "drill_pattern" in df_processed.columns:
                with st.sidebar:
                    st.subheader("Filtro por drill pattern")
                    # Ordenar la lista de drill patterns en orden descendente
                    drill_patterns: list = sorted(df_processed["drill_pattern"].dropna().astype(str).unique(), reverse=True)
                    drill_pattern_seleccionado: list = st.multiselect("Selecciona drill patterns:", drill_patterns)

                    if drill_pattern_seleccionado:
                        df_filtrado: pd.DataFrame = df_processed[
                            (df_processed["drill_pattern"].isin(drill_pattern_seleccionado)) &
                            (df_processed['tiempo inicio'] >= start_date) &
                            (df_processed['tiempo inicio'] <= end_date)
                        ]
                    else:
                        df_filtrado: pd.DataFrame = df_processed[
                            (df_processed['tiempo inicio'] >= start_date) &
                            (df_processed['tiempo inicio'] <= end_date)
                        ]
                        st.sidebar.info("Mostrando todos los Drill Patterns.")
            else:
                df_filtrado: pd.DataFrame = df_processed[
                    (df_processed['tiempo inicio'] >= start_date) &
                    (df_processed['tiempo inicio'] <= end_date)
                ]
                st.sidebar.info("No se encontró la columna 'drill_pattern'. Mostrando todos los datos.")

            # Aplicar filtro por perforadora sobre el set ya filtrado.
            if perforadoras_seleccionadas and "perforadora" in df_filtrado.columns:
                df_filtrado = df_filtrado[
                    df_filtrado["perforadora"].isin(perforadoras_seleccionadas)
                ]

            # Mostrar información sobre el filtro de fecha aplicado
            st.info(f"Mostrando datos desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")

            # --- Phase C.1 / C.2: Umbrales expander with 6 sliders ---
            with st.sidebar:
                with st.expander("Umbrales", expanded=False):
                    st.caption(
                        "Ajusta los límites de clasificación. Los defaults "
                        "reproducen las clasificaciones previas."
                    )
                    duration_soft = st.slider(
                        "Duration soft (min)",
                        min_value=1.0,
                        max_value=120.0,
                        value=float(DEFAULT_DURATION_THRESHOLDS["soft"]),
                        step=0.5,
                        key="threshold_duration_soft",
                    )
                    duration_medium = st.slider(
                        "Duration medium (min)",
                        min_value=1.0,
                        max_value=120.0,
                        value=float(DEFAULT_DURATION_THRESHOLDS["medium"]),
                        step=0.5,
                        key="threshold_duration_medium",
                    )
                    duration_hard = st.slider(
                        "Duration hard (min)",
                        min_value=1.0,
                        max_value=120.0,
                        value=float(DEFAULT_DURATION_THRESHOLDS["hard"]),
                        step=0.5,
                        key="threshold_duration_hard",
                    )
                    rate_soft = st.slider(
                        "Rate soft (m/min)",
                        min_value=0.01,
                        max_value=10.0,
                        value=float(DEFAULT_RATE_THRESHOLDS["soft"]),
                        step=0.05,
                        key="threshold_rate_soft",
                    )
                    rate_medium = st.slider(
                        "Rate medium (m/min)",
                        min_value=0.01,
                        max_value=10.0,
                        value=float(DEFAULT_RATE_THRESHOLDS["medium"]),
                        step=0.05,
                        key="threshold_rate_medium",
                    )
                    rate_hard = st.slider(
                        "Rate hard (m/min)",
                        min_value=0.01,
                        max_value=10.0,
                        value=float(DEFAULT_RATE_THRESHOLDS["hard"]),
                        step=0.05,
                        key="threshold_rate_hard",
                    )

            # Build the Thresholds dict on every rerun so any slider
            # movement re-classifies. The data_processor adapter copies
            # the cached DataFrame so the cache stays intact.
            thresholds: Thresholds = _build_thresholds_from_widgets(
                duration_soft=duration_soft,
                duration_medium=duration_medium,
                duration_hard=duration_hard,
                rate_soft=rate_soft,
                rate_medium=rate_medium,
                rate_hard=rate_hard,
            )

            # Reclasifica usando los umbrales actuales. Por defecto se
            # usa la métrica "duration" para preservar el contrato
            # pre-cambio.
            df_clasificado: pd.DataFrame = data_processor.classify_with_metric(
                df_filtrado, thresholds, "duration"
            )

            # Per-rig normalization column (Phase B.3 + Phase D.1). When
            # the rig column is present we add it so the per-rig plots
            # have something to box against.
            if "perforadora" in df_clasificado.columns:
                df_clasificado = data_processor.add_rig_normalized_rate(
                    df_clasificado
                )

            # Mostrar información sobre el filtro de fecha aplicado
            st.info(
                f"Mostrando datos desde {start_date.strftime('%Y-%m-%d')} "
                f"hasta {end_date.strftime('%Y-%m-%d')} "
                f"({len(df_clasificado)} filas)"
            )

            # --- Phase E.1 / E.2: CSV download button ---
            csv_bytes: bytes = df_clasificado.to_csv(index=False).encode("utf-8-sig")
            if df_clasificado.empty:
                st.info(
                    "El conjunto filtrado está vacío; el botón descarga "
                    "un CSV con solo los encabezados."
                )
            st.download_button(
                "Descargar CSV",
                data=csv_bytes,
                file_name="dureza_filtrada.csv",
                mime="text/csv",
                key="download_csv",
            )

            # Opciones de visualización
            st.sidebar.header("Opciones de visualización")
            mostrar_box_plot: bool = st.sidebar.checkbox("Mostrar box plot", value=True)
            mostrar_torta: bool = st.sidebar.checkbox("Mostrar gráfico de torta", value=True)
            mostrar_ubicacion_equipo: bool = st.sidebar.checkbox("Mostrar gráficos de ubicación", value=True)
            mostrar_mapa_dureza: bool = st.sidebar.checkbox("Mostrar mapa de dureza", value=True)
            mostrar_3d_scatter: bool = st.sidebar.checkbox("Mostrar visualización 3D", value=True)
            mostrar_per_rig: bool = st.sidebar.checkbox(
                "Mostrar gráficos por perforadora", value=True
            )

            # Crear la grilla de 2x2
            col1, col2 = st.columns(2)

            # Gráfico Box Plot (col1, fila 1)
            if mostrar_box_plot:
                with col1:
                    st.subheader("Distribución de duración por dureza (box plot)")
                    fig_box: px.Figure = Visualizer.plot_duracion_box(df_clasificado)
                    st.plotly_chart(fig_box, key="box_plot")

            # Gráfico Torta (col2, fila 1)
            if mostrar_torta:
                with col2:
                    st.subheader("Tiempo promedio por dureza (torta)")
                    fig_pie: px.Figure = Visualizer.plot_dureza_count(df_clasificado)
                    st.plotly_chart(fig_pie, key="pie_chart")

            # Gráfico de Ubicación y Mapa de Densidad (fila 2)
            col1, col2 = st.columns(2)
            if mostrar_ubicacion_equipo:
                with col1:
                    st.subheader("Ubicación de pozos")
                    fig_ubicacion_filtrado: px.Figure = Visualizer.plot_location_interactive(df_clasificado)
                    st.plotly_chart(fig_ubicacion_filtrado, key="filtered_location")

            # Mapa de Dureza 3D
            if mostrar_mapa_dureza:
                with col2:
                    st.subheader("Mapa de índice de dureza 3D")
                    fig_hardness: px.Figure = Visualizer.plot_hardness_heatmap(df_clasificado)
                    st.plotly_chart(fig_hardness, key="hardness_map")

            # Visualización 3D a ancho completo
            if mostrar_3d_scatter:
                st.subheader("Visualización 3D de pozos")
                fig_3d_scatter: px.Figure = Visualizer.plot_3d_scatter(df_clasificado)
                # Usar el ancho completo de la pantalla
                st.plotly_chart(fig_3d_scatter, key="3d_scatter")

            # --- Phase D: per-rig box plots ---
            if mostrar_per_rig:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Tasa de penetración por perforadora")
                    fig_rate_rig = Visualizer.plot_penetration_rate_by_rig(
                        df_clasificado
                    )
                    if fig_rate_rig is None:
                        st.info(
                            "No se encontró la columna 'perforadora'. "
                            "Se omite el box plot por perforadora."
                        )
                    else:
                        st.plotly_chart(fig_rate_rig, key="penetration_rate_by_rig")
                with col2:
                    st.subheader("Índice de dureza por perforadora")
                    fig_hardness_rig = Visualizer.plot_hardness_by_rig(
                        df_clasificado
                    )
                    if fig_hardness_rig is None:
                        st.info(
                            "No se encontró la columna 'perforadora'. "
                            "Se omite el box plot por perforadora."
                        )
                    else:
                        st.plotly_chart(fig_hardness_rig, key="hardness_by_rig")

        except ValueError as ve:
            st.error(f"Error de validación: {ve}")
        except Exception as e:
            st.error(f"Error al procesar o visualizar los datos: {e}")
    else:
        st.info("Esperando que se suba un archivo CSV.")


main()