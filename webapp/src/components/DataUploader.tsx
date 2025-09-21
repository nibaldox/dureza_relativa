import { useRef } from 'react';
import Papa, { ParseError } from 'papaparse';
import { processCsvData } from '../utils/dataProcessor';
import type { ProcessedDataResult } from '../utils/types';

interface DataUploaderProps {
  onDataLoaded: (result: ProcessedDataResult) => void;
  onError: (message: string) => void;
}

const DataUploader: React.FC<DataUploaderProps> = ({ onDataLoaded, onError }) => {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = () => {
    const file = inputRef.current?.files?.[0];
    if (!file) {
      return;
    }

    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        try {
          const processed = processCsvData(results);
          onDataLoaded(processed);
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Error desconocido al procesar el archivo.';
          onError(message);
        }
      },
      error: (error: ParseError) => {
        onError(`No se pudo leer el archivo: ${error.message}`);
      },
    });
  };

  return (
    <div className="uploader">
      <label htmlFor="csv-uploader" className="uploader__label">
        <strong>1.</strong> Carga tu archivo CSV
      </label>
      <input id="csv-uploader" ref={inputRef} type="file" accept=".csv" onChange={handleFileChange} />
    </div>
  );
};

export default DataUploader;
