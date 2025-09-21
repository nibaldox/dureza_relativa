import { useEffect, useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import DataUploader from './components/DataUploader';
import {
  create3DScatterDefinition,
  createBoxPlotDefinition,
  createHardnessHeatmapDefinition,
  createLocationChartDefinition,
  createPieChartDefinition,
  HARDNESS_COLOR_MAPPING,
} from './utils/charts';
import { formatDateInputValue } from './utils/dataProcessor';
import type { ProcessedDataResult, WellRecord } from './utils/types';
import './styles/App.css';

interface DateRange {
  start: string;
  end: string;
}

const App: React.FC = () => {
  const [records, setRecords] = useState<WellRecord[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<DateRange | null>(null);
  const [selectedDrillPatterns, setSelectedDrillPatterns] = useState<string[]>([]);
  const [showBoxPlot, setShowBoxPlot] = useState(true);
  const [showPieChart, setShowPieChart] = useState(true);
  const [showLocation, setShowLocation] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [show3DScatter, setShow3DScatter] = useState(true);
  const [detailLevel, setDetailLevel] = useState(2);

  useEffect(() => {
    if (!records.length) {
      setDateRange(null);
      setSelectedDrillPatterns([]);
      return;
    }

    const sortedByDate = [...records].sort(
      (a, b) => a.tiempoInicio.getTime() - b.tiempoInicio.getTime(),
    );
    const start = formatDateInputValue(sortedByDate[0].tiempoInicio);
    const end = formatDateInputValue(sortedByDate[sortedByDate.length - 1].tiempoInicio);
    setDateRange({ start, end });
    setSelectedDrillPatterns([]);
  }, [records]);

  const availableDrillPatterns = useMemo(() => {
    const patterns = new Set<string>();
    records.forEach((record) => {
      if (record.drillPattern) {
        patterns.add(record.drillPattern.toString());
      }
    });
    return Array.from(patterns).sort((a, b) => b.localeCompare(a));
  }, [records]);

  const filteredRecords = useMemo(() => {
    if (!records.length) {
      return [];
    }

    let filtered = [...records];

    if (dateRange) {
      const startDate = new Date(dateRange.start);
      const endDate = new Date(`${dateRange.end}T23:59:59`);
      filtered = filtered.filter(
        (record) => record.tiempoInicio >= startDate && record.tiempoInicio <= endDate,
      );
    }

    if (selectedDrillPatterns.length) {
      filtered = filtered.filter(
        (record) => record.drillPattern && selectedDrillPatterns.includes(record.drillPattern),
      );
    }

    return filtered;
  }, [records, dateRange, selectedDrillPatterns]);

  const hasLocationData = useMemo(
    () => filteredRecords.some((record) => record.este !== undefined && record.norte !== undefined),
    [filteredRecords],
  );

  const has3DData = useMemo(
    () =>
      filteredRecords.some(
        (record) =>
          record.este !== undefined &&
          record.norte !== undefined &&
          record.elevacion !== undefined,
      ),
    [filteredRecords],
  );

  const handleDataLoaded = (result: ProcessedDataResult) => {
    setRecords(result.records);
    setWarnings(result.warnings);
    setError(null);
    setInfo(`Archivo procesado correctamente. Registros válidos: ${result.records.length}.`);
  };

  const handleError = (message: string) => {
    setError(message);
    setInfo(null);
    setWarnings([]);
    setRecords([]);
  };

  const handleDateChange = (key: keyof DateRange, value: string) => {
    setDateRange((current) => {
      if (!current) {
        return { start: value, end: value };
      }
      return { ...current, [key]: value };
    });
  };

  const handleSelectAllDrillPatterns = () => {
    setSelectedDrillPatterns(availableDrillPatterns);
  };

  const handleClearDrillPatterns = () => {
    setSelectedDrillPatterns([]);
  };

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1>Clasificador de Pozos</h1>
          <p>
            Carga un archivo CSV para procesar los datos, clasificar la dureza de cada pozo y
            visualizar los resultados interactivos.
          </p>
        </div>
        <div className="legend">
          {Object.entries(HARDNESS_COLOR_MAPPING).map(([key, color]) => (
            <span key={key} className="legend__item">
              <span className="legend__color" style={{ backgroundColor: color }} />
              {key}
            </span>
          ))}
        </div>
      </header>

      <section className="app__controls">
        <DataUploader onDataLoaded={handleDataLoaded} onError={handleError} />

        {records.length > 0 && (
          <div className="filters">
            <div className="filters__block">
              <h2>2. Filtros</h2>
              <div className="filters__group">
                <div>
                  <label htmlFor="start-date">Fecha inicio</label>
                  <input
                    id="start-date"
                    type="date"
                    value={dateRange?.start ?? ''}
                    onChange={(event) => handleDateChange('start', event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="end-date">Fecha fin</label>
                  <input
                    id="end-date"
                    type="date"
                    value={dateRange?.end ?? ''}
                    onChange={(event) => handleDateChange('end', event.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="filters__block">
              <h3>Filtro por Drill Pattern</h3>
              <div className="filters__group">
                <select
                  multiple
                  value={selectedDrillPatterns}
                  onChange={(event) =>
                    setSelectedDrillPatterns(
                      Array.from(event.target.selectedOptions, (option) => option.value),
                    )
                  }
                >
                  {availableDrillPatterns.map((pattern) => (
                    <option key={pattern} value={pattern}>
                      {pattern}
                    </option>
                  ))}
                </select>
                <div className="filters__actions">
                  <button type="button" onClick={handleSelectAllDrillPatterns}>
                    Seleccionar todos
                  </button>
                  <button type="button" onClick={handleClearDrillPatterns}>
                    Limpiar selección
                  </button>
                </div>
              </div>
            </div>

            <div className="filters__block">
              <h3>Opciones de visualización</h3>
              <div className="toggles">
                <label>
                  <input
                    type="checkbox"
                    checked={showBoxPlot}
                    onChange={(event) => setShowBoxPlot(event.target.checked)}
                  />
                  Box Plot
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={showPieChart}
                    onChange={(event) => setShowPieChart(event.target.checked)}
                  />
                  Gráfico de Torta
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={showLocation}
                    onChange={(event) => setShowLocation(event.target.checked)}
                  />
                  Ubicación de pozos
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={showHeatmap}
                    onChange={(event) => setShowHeatmap(event.target.checked)}
                  />
                  Mapa de dureza
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={show3DScatter}
                    onChange={(event) => setShow3DScatter(event.target.checked)}
                  />
                  Visualización 3D
                </label>
              </div>
            </div>

            {showHeatmap && (
              <div className="filters__block">
                <h3>Ajustes del mapa de dureza</h3>
                <label htmlFor="detail-level">
                  Nivel de detalle: <strong>{detailLevel.toFixed(1)}</strong>
                </label>
                <input
                  id="detail-level"
                  type="range"
                  min="0.5"
                  max="10"
                  step="0.5"
                  value={detailLevel}
                  onChange={(event) => setDetailLevel(Number(event.target.value))}
                />
              </div>
            )}
          </div>
        )}
      </section>

      <section className="app__feedback">
        {info && <div className="alert alert--success">{info}</div>}
        {error && <div className="alert alert--error">{error}</div>}
        {warnings.length > 0 && (
          <div className="alert alert--warning">
            <strong>Advertencias:</strong>
            <ul>
              {warnings.map((warning, index) => (
                <li key={index}>{warning}</li>
              ))}
            </ul>
          </div>
        )}
        {filteredRecords.length > 0 && dateRange && (
          <div className="alert alert--info">
            Mostrando datos desde <strong>{dateRange.start}</strong> hasta{' '}
            <strong>{dateRange.end}</strong>. Registros visibles: {filteredRecords.length}.
          </div>
        )}
      </section>

      {filteredRecords.length > 0 ? (
        <section className="app__visualizations">
          <div className="grid">
            {showBoxPlot && (
              <div className="grid__item">
                <h2>Distribución de Duración por Dureza (Box Plot)</h2>
                <Plot {...createBoxPlotDefinition(filteredRecords)} useResizeHandler style={{ width: '100%', height: '100%' }} />
              </div>
            )}

            {showPieChart && (
              <div className="grid__item">
                <h2>Tiempo Promedio por Dureza (Torta)</h2>
                <Plot {...createPieChartDefinition(filteredRecords)} useResizeHandler style={{ width: '100%', height: '100%' }} />
              </div>
            )}

            {showLocation && (
              <div className="grid__item">
                <h2>Ubicación de Pozos</h2>
                {hasLocationData ? (
                  <Plot {...createLocationChartDefinition(filteredRecords)} useResizeHandler style={{ width: '100%', height: '100%' }} />
                ) : (
                  <p className="empty-state">Los datos no contienen coordenadas "este" y "norte".</p>
                )}
              </div>
            )}

            {showHeatmap && (
              <div className="grid__item">
                <h2>Mapa de Índice de Dureza</h2>
                {hasLocationData ? (
                  <Plot
                    {...createHardnessHeatmapDefinition(filteredRecords, detailLevel)}
                    useResizeHandler
                    style={{ width: '100%', height: '100%' }}
                  />
                ) : (
                  <p className="empty-state">Se necesitan columnas con coordenadas para dibujar el mapa.</p>
                )}
              </div>
            )}
          </div>

          {show3DScatter && (
            <div className="grid grid--full">
              <div className="grid__item grid__item--full">
                <h2>Visualización 3D de Pozos</h2>
                {has3DData ? (
                  <Plot
                    {...create3DScatterDefinition(filteredRecords)}
                    useResizeHandler
                    style={{ width: '100%', height: '100%' }}
                  />
                ) : (
                  <p className="empty-state">
                    Agrega columnas de coordenadas y elevación para habilitar la visualización 3D.
                  </p>
                )}
              </div>
            </div>
          )}
        </section>
      ) : (
        <section className="app__placeholder">
          <p>Sube un archivo CSV para comenzar a explorar tus datos de perforación.</p>
        </section>
      )}
    </div>
  );
};

export default App;
