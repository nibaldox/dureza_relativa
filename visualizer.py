import logging
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import numpy as np  # Agregando numpy para cálculos de histograma

class Visualizer:
    # Color mapping definition at class level
    COLOR_MAPPING = {
        "roca suave": "#98FB98",    # verde menta pastel
        "roca media": "#FFD700",    # amarillo más cercano al original
        "roca dura": "#e74c3c",     # rojo más oscuro
        "roca muy dura": "#BA55D3"  # lavanda más brillante
    }

    @staticmethod
    def plot_location_interactive(df):
        # Validar columnas necesarias
        required_columns = ['este', 'norte', 'dureza']
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Falta la columna requerida: {col}")
                raise ValueError(f"El archivo no contiene la columna '{col}' necesaria para la visualización interactiva.")
        try:
            # Definir mapeo de colores desaturados para Plotly
            color_mapping = {
                "roca suave": "#98FB98",    # verde menta pastel
                "roca media": "#FFD700",    # amarillo más cercano al original
                "roca dura": "#e74c3c",      # rojo más oscuro
                "roca muy dura": "#BA55D3"   # lavanda más brillante, cercano al original
            }
            # Preparar hover data para incluir drill pattern si existe
            hover_data = None
            if "drill_pattern" in df.columns:
                hover_data = ["drill_pattern", "pozo","duracion", "material_operator"]

            fig = px.scatter(
                df,
                x='este',
                y='norte',
                color='dureza',
                color_discrete_map=color_mapping,
                title="Ubicación Interactiva de Pozos (Este vs Norte)",
                labels={"este": "Este", "norte": "Norte", "dureza": "Dureza"},
                hover_data=hover_data
            )
            fig.update_layout(legend_title_text='Dureza')
            logging.info("Gráfica interactiva de ubicación generada correctamente.")
            return fig
        except Exception as e:
            logging.exception("Error generando gráfica interactiva de ubicación")
            raise Exception(f"Error al generar la gráfica interactiva de ubicación: {e}")

    @staticmethod
    def plot_dureza_count(df):
        try:
            # Contar la cantidad de pozos por dureza
            conteo_dureza = df['dureza'].value_counts().reset_index()
            conteo_dureza.columns = ['dureza', 'conteo']

            # Mapeo de colores desaturados para Plotly
            color_mapping = {
                "roca suave": "#98FB98",    # verde menta pastel
                "roca media": "#FFD700",    # amarillo más cercano al original
                "roca dura": "#8B0000",      # rojo pastel
                "roca muy dura": "#BA55D3"   # lavanda más brillante, cercano al original
            }
            fig = px.pie(
                conteo_dureza,
                names='dureza',
                values='conteo',
                color='dureza',
                color_discrete_map=color_mapping,
                title='Conteo de Pozos por Dureza'
            )
            logging.info("Gráfica de torta de conteo de pozos por dureza generada correctamente.")
            return fig
        except Exception as e:
            logging.exception("Error generando gráfica de torta de conteo de pozos por dureza")
            raise Exception(f"Error al generar la gráfica de torta de conteo de pozos por dureza: {e}")

    @staticmethod
    def plot_duracion_box(df):
        try:
            # Definir mapeo de colores desaturados para Plotly
            color_mapping = {
                "roca suave": "#98FB98",    # verde menta pastel
                "roca media": "#FFD700",    # amarillo más cercano al original
                "roca dura": "#FFA07A",      # rojo pastel
                "roca muy dura": "#BA55D3"   # lavanda más brillante, cercano al original
            }

            fig = px.box(
                df,
                x="dureza",
                y="duracion",
                color="dureza",
                color_discrete_map=color_mapping,
                title="Distribución de Duración por Dureza",
                labels={"duracion": "Duración (minutos)", "dureza": "Dureza"},
                hover_data=["drill_pattern"]
            )
            logging.info("Gráfico box plot de duración por dureza generado correctamente.")
            return fig
        except Exception as e:
            logging.exception("Error generando gráfico box plot")
            raise Exception(f"Error al generar el gráfico box plot: {e}")

    @staticmethod
    def plot_heatmap(df, bin_size: float = 2.0):
        required_columns = ['este', 'norte', 'dureza']
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Falta la columna requerida: {col}")
                raise ValueError(f"El archivo no contiene la columna '{col}' necesaria para el mapa de calor.")
        try:
            # Crear una figura con subplots para cada tipo de dureza
            fig = go.Figure()
            
            # Calcular el número óptimo de bins basado en los datos
            range_este = df['este'].max() - df['este'].min()
            range_norte = df['norte'].max() - df['norte'].min()
            nbins = max(10, int(min(range_este, range_norte) / bin_size))  # Asegurar un mínimo de bins
            
            # Iterar sobre cada tipo de dureza
            for dureza, color in Visualizer.COLOR_MAPPING.items():
                # Filtrar datos para esta dureza y eliminar NaN
                df_dureza = df[df['dureza'] == dureza].dropna(subset=['este', 'norte'])
                
                if not df_dureza.empty:
                    # Crear histograma 2D para obtener los valores de densidad
                    try:
                        H, x_edges, y_edges = np.histogram2d(
                            df_dureza['este'].values,  # Asegurar que usamos arrays numpy
                            df_dureza['norte'].values,
                            bins=nbins,
                            range=[[df_dureza['este'].min(), df_dureza['este'].max()],
                                  [df_dureza['norte'].min(), df_dureza['norte'].max()]]
                        )
                        
                        # Verificar que tenemos datos válidos
                        if np.isfinite(H).any():  # Verificar si hay valores finitos
                            # Crear las coordenadas para la malla 3D
                            x_centers = (x_edges[:-1] + x_edges[1:]) / 2
                            y_centers = (y_edges[:-1] + y_edges[1:]) / 2
                            x_mesh, y_mesh = np.meshgrid(x_centers, y_centers)
                            
                            # Reemplazar valores NaN con 0
                            H = np.nan_to_num(H, nan=0.0)
                            
                            # Crear la visualización 3D de densidad
                            fig.add_trace(go.Surface(
                                x=x_mesh,
                                y=y_mesh,
                                z=H.T,  # Transponer H para que coincida con la malla
                                name=dureza,
                                colorscale=[[0, 'rgba(0,0,0,0)'], [0.5, color.replace('1)', '0.3)')], [1, color]],
                                showscale=True,
                                opacity=0.95,
                                hovertemplate=(
                                    "Este: %{x}<br>" +
                                    "Norte: %{y}<br>" +
                                    "Densidad: %{z}<br>" +
                                    "Tipo: " + dureza +
                                    "<extra></extra>"
                                )
                            ))
                    except Exception as e:
                        logging.warning(f"Error procesando datos para dureza {dureza}: {str(e)}")
                        continue

            # Configurar el layout para visualización 3D
            fig.update_layout(
                title=f"Mapa de Densidad 3D por Tipo de Dureza (Detalle: {bin_size}m)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend_title_text="Tipos de Dureza",
                scene=dict(
                    xaxis=dict(
                        title="Este",
                        showgrid=False,
                        zeroline=False,
                        color='white'
                    ),
                    yaxis=dict(
                        title="Norte",
                        showgrid=False,
                        zeroline=False,
                        color='white'
                    ),
                    zaxis=dict(
                        title="Densidad",
                        showgrid=False,
                        zeroline=False,
                        color='white'
                    ),
                    camera=dict(
                        up=dict(x=0, y=0, z=1),
                        center=dict(x=0, y=0, z=0),
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                )
            )
            
            logging.info(f"Mapa de densidad 3D generado correctamente con tamaño de bin: {bin_size}")
            return fig
        except Exception as e:
            logging.exception("Error generando el mapa de densidad 3D")
            raise Exception(f"Error al generar el mapa de densidad 3D: {e}")

    @staticmethod
    def plot_3d_scatter(df):
        required_columns = ['este', 'norte', 'mts plan', 'dureza', "elevacion"]
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Falta la columna requerida: {col}")
                raise ValueError(f"El archivo no contiene la columna '{col}' necesaria para la visualización 3D.")
        try:
            fig = px.scatter_3d(
                df, 
                x='este', 
                y='norte', 
                z='elevacion', 
                color='dureza',
                color_discrete_map=Visualizer.COLOR_MAPPING,
                title="Visualización 3D de Pozos",
                labels={
                    "este": "Este", 
                    "norte": "Norte", 
                    "elevacion": "Cota", 
                    "dureza": "Dureza"
                }
            )
            
            # Mejorar la visualización 3D con puntos más pequeños
            fig.update_traces(marker=dict(size=3))
            fig.update_layout(
                scene=dict(
                    aspectmode='data',
                    camera=dict(
                        up=dict(x=0, y=0, z=1),
                        center=dict(x=0, y=0, z=0),
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                )
            )
            
            logging.info("Visualización 3D generada correctamente.")
            return fig
        except Exception as e:
            logging.exception("Error generando la visualización 3D")
            raise Exception(f"Error al generar la visualización 3D: {e}")

    @staticmethod
    def plot_hardness_heatmap(df, bin_size: float = 2.0):
        """
        Genera un mapa de dispersión 2D basado en el índice de dureza.
        
        Args:
            df (pd.DataFrame): DataFrame con las columnas 'este', 'norte' y 'indice_dureza'
            bin_size (float): No se usa en esta versión pero se mantiene por compatibilidad
            
        Returns:
            go.Figure: Figura de Plotly con el mapa de dispersión 2D
        """
        required_columns = ['este', 'norte', 'indice_dureza']
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Falta la columna requerida: {col}")
                raise ValueError(f"El archivo no contiene la columna '{col}' necesaria para el mapa de dureza.")
        try:
            fig = go.Figure()

            # Crear el scatter plot con índice de dureza
            fig.add_trace(go.Scatter(
                x=df['este'],
                y=df['norte'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=df['indice_dureza'],
                    colorscale=[
                        [0, 'rgb(0,255,0)'],      # Verde para dureza baja
                        [0.25, 'rgb(255,255,0)'],  # Amarillo para dureza media-baja
                        [0.5, 'rgb(255,165,0)'],   # Naranja para dureza media
                        [0.75, 'rgb(255,69,0)'],   # Naranja-rojo para dureza media-alta
                        [1, 'rgb(255,0,0)']        # Rojo para dureza alta
                    ],
                    colorbar=dict(
                        title="Índice de Dureza",
                        ticktext=['Muy Suave (0)', 'Suave (25)', 'Media (50)', 'Dura (75)', 'Muy Dura (100)'],
                        tickvals=[0, 25, 50, 75, 100],
                        tickmode="array"
                    ),
                    showscale=True
                ),
                hovertemplate=(
                    "Este: %{x:.1f}<br>" +
                    "Norte: %{y:.1f}<br>" +
                    "Índice de Dureza: %{marker.color:.1f}" +
                    "<extra></extra>"
                )
            ))

            # Configurar el layout
            fig.update_layout(
                title="Mapa de Dispersión de Índice de Dureza",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    title="Este",
                    showgrid=False,
                    zeroline=False,
                    color='white'
                ),
                yaxis=dict(
                    title="Norte",
                    showgrid=False,
                    zeroline=False,
                    color='white'
                )
            )
            
            logging.info("Mapa de dispersión de índice de dureza generado correctamente")
            return fig
        except Exception as e:
            logging.exception("Error generando el mapa de dispersión de índice de dureza")
            raise Exception(f"Error al generar el mapa de dispersión de índice de dureza: {e}")
