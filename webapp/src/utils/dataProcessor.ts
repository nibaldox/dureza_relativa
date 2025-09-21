import type { ParseResult } from 'papaparse';
import { ProcessedDataResult, RawRecord, WellRecord } from './types';

const REQUIRED_COLUMNS = ['tiempo inicio', 'tiempo final'];

type CsvRow = Record<string, string>;

const normalizeColumnName = (name: string): string => name.trim().toLowerCase();

const toDate = (value: string | number | null | undefined): Date | null => {
  if (value === null || value === undefined) {
    return null;
  }

  const strValue = String(value).trim();
  if (!strValue) {
    return null;
  }

  const parsed = new Date(strValue);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const safeParseNumber = (value: string | number | null | undefined): number | undefined => {
  if (value === null || value === undefined) {
    return undefined;
  }

  const strValue = String(value).replace(',', '.').trim();
  if (!strValue) {
    return undefined;
  }

  const parsed = Number(strValue);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const classifyDuration = (minutes: number): WellRecord['dureza'] => {
  if (minutes < 16) {
    return 'roca suave';
  }
  if (minutes < 24) {
    return 'roca media';
  }
  if (minutes < 40) {
    return 'roca dura';
  }
  return 'roca muy dura';
};

const hardnessIndex = (minutes: number): number => {
  if (minutes < 0) {
    return 0;
  }
  if (minutes <= 16) {
    return 25 * (minutes / 16);
  }
  if (minutes <= 24) {
    return 25 + 25 * ((minutes - 16) / 8);
  }
  if (minutes <= 40) {
    return 50 + 25 * ((minutes - 24) / 16);
  }
  if (minutes <= 60) {
    return 75 + 25 * ((minutes - 40) / 20);
  }
  return 100;
};

const normalizeRow = (row: CsvRow): Record<string, string> => {
  const normalized: Record<string, string> = {};
  Object.entries(row).forEach(([key, value]) => {
    if (!key) {
      return;
    }
    normalized[normalizeColumnName(key)] = value ?? '';
  });
  return normalized;
};

export const processCsvData = (parseResult: ParseResult<CsvRow>): ProcessedDataResult => {
  const warnings: string[] = [];
  const normalizedRows = parseResult.data
    .map(normalizeRow)
    .filter((row) => Object.values(row).some((value) => (value ?? '').toString().trim() !== ''));

  if (normalizedRows.length === 0) {
    return { records: [], warnings: ['El archivo no contiene filas con datos.'] };
  }

  const availableColumns = new Set(Object.keys(normalizedRows[0] ?? {}));
  for (const column of REQUIRED_COLUMNS) {
    if (!availableColumns.has(column)) {
      throw new Error(`El archivo no contiene la columna requerida "${column}".`);
    }
  }

  const records: WellRecord[] = [];

  normalizedRows.forEach((row, index) => {
    const startDate = toDate(row['tiempo inicio']);
    const endDate = toDate(row['tiempo final']);

    if (!startDate || !endDate) {
      warnings.push(`Fila ${index + 1}: valores de fecha no válidos.`);
      return;
    }

    const durationMinutes = (endDate.getTime() - startDate.getTime()) / (1000 * 60);
    if (!Number.isFinite(durationMinutes)) {
      warnings.push(`Fila ${index + 1}: no se pudo calcular la duración.`);
      return;
    }

    const record: WellRecord = {
      tiempoInicio: startDate,
      tiempoFinal: endDate,
      duracion: durationMinutes,
      dureza: classifyDuration(durationMinutes),
      indiceDureza: hardnessIndex(durationMinutes),
      drillPattern: row['drill_pattern']?.toString() ?? undefined,
      pozo: row['pozo']?.toString() ?? undefined,
      materialOperator: row['material_operator']?.toString() ?? undefined,
      profundidadOperador: safeParseNumber(row['prof. por operador']),
      elevacion: safeParseNumber(row['elevacion']),
      este: safeParseNumber(row['este']),
      norte: safeParseNumber(row['norte']),
      raw: row as RawRecord,
    };

    records.push(record);
  });

  if (!records.length) {
    warnings.push('No se pudieron generar registros válidos a partir del archivo.');
  }

  return { records, warnings };
};

export const formatDateInputValue = (date: Date): string => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};
