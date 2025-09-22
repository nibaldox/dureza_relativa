import type { Config, Data, Layout } from 'plotly.js';
import { WellRecord } from './types';

export interface ChartDefinition {
  data: Data[];
  layout: Partial<Layout>;
  config?: Partial<Config>;
}

export const HARDNESS_COLOR_MAPPING: Record<WellRecord['dureza'], string> = {
  'roca suave': '#98FB98',
  'roca media': '#FFD700',
  'roca dura': '#e74c3c',
  'roca muy dura': '#BA55D3',
};

export const createBoxPlotDefinition = (records: WellRecord[]): ChartDefinition => {
  const traces: Data[] = Object.entries(HARDNESS_COLOR_MAPPING).map(([hardness, color]) => {
    const hardnessRecords = records.filter((record) => record.dureza === hardness);
    return {
      type: 'box',
      name: hardness,
      marker: { color },
      y: hardnessRecords.map((record) => record.duracion),
      boxmean: true,
      hovertemplate: 'Duración: %{y:.2f} minutos<extra></extra>',
    } as Data;
  });

  const layout: Partial<Layout> = {
    title: 'Distribución de Duración por Dureza',
    yaxis: {
      title: 'Duración (minutos)',
      zeroline: false,
    },
    boxmode: 'group',
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  return { data: traces, layout };
};

export const createPieChartDefinition = (records: WellRecord[]): ChartDefinition => {
  const counts = Object.keys(HARDNESS_COLOR_MAPPING).map((hardness) => ({
    hardness,
    count: records.filter((record) => record.dureza === hardness).length,
  }));

  const data: Data[] = [
    {
      type: 'pie',
      labels: counts.map((item) => item.hardness),
      values: counts.map((item) => item.count),
      marker: {
        colors: counts.map((item) => HARDNESS_COLOR_MAPPING[item.hardness as WellRecord['dureza']]),
      },
      hole: 0.2,
      hovertemplate: '%{label}: %{value} pozos<extra></extra>',
    } as Data,
  ];

  const layout: Partial<Layout> = {
    title: 'Conteo de Pozos por Dureza',
    showlegend: true,
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  return { data, layout };
};

const filterByCoordinates = (records: WellRecord[]): WellRecord[] =>
  records.filter((record) => record.este !== undefined && record.norte !== undefined);

export const createLocationChartDefinition = (records: WellRecord[]): ChartDefinition => {
  const withCoordinates = filterByCoordinates(records);

  const data: Data[] = [
    {
      type: 'scatter',
      mode: 'markers',
      x: withCoordinates.map((record) => record.este ?? null),
      y: withCoordinates.map((record) => record.norte ?? null),
      marker: {
        color: withCoordinates.map((record) => HARDNESS_COLOR_MAPPING[record.dureza]),
        size: 10,
        line: { color: '#1f2933', width: 0.5 },
      },
      hovertemplate:
        'Este: %{x}<br>Norte: %{y}<br>Dureza: %{customdata[0]}<extra></extra>',
      customdata: withCoordinates.map((record) => [record.dureza]),
    } as Data,
  ];

  const layout: Partial<Layout> = {
    title: 'Ubicación Interactiva de Pozos (Este vs Norte)',
    xaxis: {
      title: 'Este',
      dtick: 500,
      gridwidth: 1,
      gridcolor: 'rgba(200,200,200,0.3)',
      showline: true,
      linecolor: 'black',
    },
    yaxis: {
      title: 'Norte',
      dtick: 500,
      gridwidth: 1,
      gridcolor: 'rgba(200,200,200,0.3)',
      showline: true,
      linecolor: 'black',
    },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  return { data, layout };
};

export const createHardnessHeatmapDefinition = (
  records: WellRecord[],
  detailLevel: number,
): ChartDefinition => {
  const withCoordinates = filterByCoordinates(records);
  const markerSize = Math.max(4, 16 - detailLevel);

  const data: Data[] = [
    {
      type: 'scatter',
      mode: 'markers',
      x: withCoordinates.map((record) => record.este ?? null),
      y: withCoordinates.map((record) => record.norte ?? null),
      marker: {
        size: markerSize,
        color: withCoordinates.map((record) => record.indiceDureza),
        colorscale: [
          [0, 'rgb(0,255,0)'],
          [0.25, 'rgb(255,255,0)'],
          [0.5, 'rgb(255,165,0)'],
          [0.75, 'rgb(255,69,0)'],
          [1, 'rgb(255,0,0)'],
        ],
        colorbar: {
          title: 'Índice de Dureza',
          ticktext: ['Muy Suave (0)', 'Suave (25)', 'Media (50)', 'Dura (75)', 'Muy Dura (100)'],
          tickvals: [0, 25, 50, 75, 100],
        },
      },
      hovertemplate:
        'Este: %{x:.1f}<br>Norte: %{y:.1f}<br>Índice de dureza: %{marker.color:.1f}<extra></extra>',
    } as Data,
  ];

  const layout: Partial<Layout> = {
    title: 'Mapa de Dispersión de Índice de Dureza',
    xaxis: {
      title: 'Este',
      dtick: 500,
      gridwidth: 1,
      gridcolor: 'rgba(200,200,200,0.3)',
      showline: true,
      linecolor: 'black',
    },
    yaxis: {
      title: 'Norte',
      dtick: 500,
      gridwidth: 1,
      gridcolor: 'rgba(200,200,200,0.3)',
      showline: true,
      linecolor: 'black',
    },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  return { data, layout };
};

export const create3DScatterDefinition = (records: WellRecord[]): ChartDefinition => {
  const withCoordinates = records.filter(
    (record) =>
      record.este !== undefined && record.norte !== undefined && record.elevacion !== undefined,
  );

  const data: Data[] = [
    {
      type: 'scatter3d',
      mode: 'markers',
      x: withCoordinates.map((record) => record.este ?? null),
      y: withCoordinates.map((record) => record.norte ?? null),
      z: withCoordinates.map((record) => record.elevacion ?? null),
      marker: {
        size: 3,
        color: withCoordinates.map((record) => HARDNESS_COLOR_MAPPING[record.dureza]),
      },
      hovertemplate:
        'Este: %{x}<br>Norte: %{y}<br>Cota: %{z}<br>Dureza: %{customdata[0]}<extra></extra>',
      customdata: withCoordinates.map((record) => [record.dureza]),
    } as Data,
  ];

  const layout: Partial<Layout> = {
    title: 'Visualización 3D de Pozos',
    scene: {
      aspectmode: 'data',
      xaxis: {
        title: 'Este',
        dtick: 500,
        showgrid: true,
        gridcolor: 'rgba(200,200,200,0.3)',
        showline: true,
        linecolor: 'black',
      },
      yaxis: {
        title: 'Norte',
        dtick: 500,
        showgrid: true,
        gridcolor: 'rgba(200,200,200,0.3)',
        showline: true,
        linecolor: 'black',
      },
      zaxis: {
        title: 'Cota',
        showgrid: true,
        gridcolor: 'rgba(200,200,200,0.3)',
        showline: true,
        linecolor: 'black',
      },
      camera: {
        up: { x: 0, y: 0, z: 1 },
        center: { x: 0, y: 0, z: 0 },
        eye: { x: 1.5, y: 1.5, z: 1.5 },
      },
      bgcolor: 'rgba(0,0,0,0)',
    },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  const config: Partial<Config> = {
    responsive: true,
  };

  return { data, layout, config };
};
