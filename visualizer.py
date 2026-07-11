import logging
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
        # Preparar hover data para incluir drill pattern, profundidad y elevación si existen
        hover_data = []
        if "drill_pattern" in df.columns:
            hover_data.extend(["drill_pattern", "pozo", "duracion", "material_operator"])
        if "prof. por operador" in df.columns:
            hover_data.append("prof. por operador")
        if "elevacion" in df.columns:
            hover_data.append("elevacion")
        # Si no hay columnas adicionales, usar None para mostrar solo las básicas
        if not hover_data:
            hover_data = None

        fig = px.scatter(
            df,
            x='este',
            y='norte',
            color='dureza',
            color_discrete_map=Visualizer.COLOR_MAPPING,
            title="Ubicación Interactiva de Pozos (Este vs Norte)",
            labels={"este": "Este", "norte": "Norte", "dureza": "Dureza"},
            hover_data=hover_data
        )

        # Agregar grilla de 500x500
        fig.update_layout(
            legend_title_text='Dureza',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                dtick=500,  # Espaciado de 500 unidades
                showline=True,
                linewidth=1,
                linecolor='black'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                dtick=500,  # Espaciado de 500 unidades
                showline=True,
                linewidth=1,
                linecolor='black'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        logging.info("Gráfica interactiva de ubicación generada correctamente.")
        return fig

    @staticmethod
    def plot_dureza_count(df):
        # Contar la cantidad de pozos por dureza
        conteo_dureza = df['dureza'].value_counts().reset_index()
        conteo_dureza.columns = ['dureza', 'conteo']

        fig = px.pie(
            conteo_dureza,
            names='dureza',
            values='conteo',
            color='dureza',
            color_discrete_map=Visualizer.COLOR_MAPPING,
            title='Conteo de Pozos por Dureza'
        )
        logging.info("Gráfica de torta de conteo de pozos por dureza generada correctamente.")
        return fig

    @staticmethod
    def plot_duracion_box(df):
        fig = px.box(
            df,
            x="dureza",
            y="duracion",
            color="dureza",
            color_discrete_map=Visualizer.COLOR_MAPPING,
            title="Distribución de Duración por Dureza",
            labels={"duracion": "Duración (minutos)", "dureza": "Dureza"},
            hover_data=["drill_pattern"]
        )
        logging.info("Gráfico box plot de duración por dureza generado correctamente.")
        return fig

    @staticmethod
    def plot_3d_scatter(df):
        required_columns = ['este', 'norte', 'dureza', "elevacion"]
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Falta la columna requerida: {col}")
                raise ValueError(f"El archivo no contiene la columna '{col}' necesaria para la visualización 3D.")
        # Preparar hover data para incluir profundidad y elevación si existen
        hover_data = []
        if "prof. por operador" in df.columns:
            hover_data.append("prof. por operador")
        if "drill_pattern" in df.columns:
            hover_data.append("drill_pattern")
        if "duracion" in df.columns:
            hover_data.append("duracion")
        if "elevacion" in df.columns:
            hover_data.append("elevacion")
        # Si no hay columnas adicionales, usar None para mostrar solo las básicas
        if not hover_data:
            hover_data = None

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
            },
            hover_data=hover_data
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
                ),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                    dtick=500,  # Espaciado de 500 unidades
                    showline=True,
                    linewidth=1,
                    linecolor='black'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                    dtick=500,  # Espaciado de 500 unidades
                    showline=True,
                    linewidth=1,
                    linecolor='black'
                ),
                zaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                    showline=True,
                    linewidth=1,
                    linecolor='black'
                ),
                bgcolor='rgba(0,0,0,0)'
            )
        )

        logging.info("Visualización 3D generada correctamente.")
        return fig

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
                "Índice de Dureza: %{marker.color:.1f}<br>" +
                "Elevación: %{customdata[0]:.1f}" +
                "<extra></extra>"
            ),
            customdata=df[['elevacion']] if 'elevacion' in df.columns else None
        ))

        # Configurar el layout
        fig.update_layout(
            title="Mapa de Dispersión de Índice de Dureza",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                title="Este",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                dtick=500,  # Espaciado de 500 unidades
                showline=True,
                linewidth=1,
                linecolor='black',
                color='black'
            ),
            yaxis=dict(
                title="Norte",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200,200,200,0.3)',  # Gris claro semi-transparente
                dtick=500,  # Espaciado de 500 unidades
                showline=True,
                linewidth=1,
                linecolor='black',
                color='black'
            )
        )

        logging.info("Mapa de dispersión de índice de dureza generado correctamente")
        return fig
