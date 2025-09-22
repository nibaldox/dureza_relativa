export interface RawRecord {
  [key: string]: string | number | null | undefined;
}

export interface WellRecord {
  tiempoInicio: Date;
  tiempoFinal: Date;
  duracion: number;
  dureza: 'roca suave' | 'roca media' | 'roca dura' | 'roca muy dura';
  indiceDureza: number;
  drillPattern?: string;
  pozo?: string;
  materialOperator?: string;
  profundidadOperador?: number;
  elevacion?: number;
  este?: number;
  norte?: number;
  raw: Record<string, string | number | null | undefined>;
}

export interface ProcessedDataResult {
  records: WellRecord[];
  warnings: string[];
}
