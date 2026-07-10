import logging
import pandas as pd

from classification import classify_duracion, hardness_index

# Configuración básica para logging
logging.basicConfig(filename="app.log", level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

class DataProcessor:
    REQUIRED_COLUMNS = ['tiempo inicio', 'tiempo final']

    def load_and_process(self, file_path):
        logging.info(f"Iniciando carga del archivo: {file_path}")
        try:
            try:
                df = pd.read_csv(file_path)
            except pd.errors.ParserError:
                import warnings as _warnings

                with _warnings.catch_warnings(record=True) as captured:
                    _warnings.simplefilter("always")
                    df = pd.read_csv(
                        file_path,
                        engine="python",
                        on_bad_lines="warn",
                    )
                bad_lines = sum(
                    1
                    for w in captured
                    if "Skipping" in str(w.message)
                )
                if bad_lines:
                    logging.warning(
                        "Se descartaron %d filas con esquema inválido "
                        "(campos extra o faltantes respecto al header).",
                        bad_lines,
                    )
        except Exception as e:
            logging.exception("Error leyendo el archivo")
            raise Exception(f"Error al leer el archivo: {e}")

        # Estandarizar nombres de columnas a minúsculas y sin espacios extremos.
        df.columns = [col.strip().lower() for col in df.columns]
        logging.debug(f"Columnas del archivo: {df.columns.tolist()}")

        # Validar columnas requeridas
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                logging.error(f"Falta la columna requerida: {col}")
                raise ValueError(f"El archivo no contiene la columna requerida '{col}'.")

        try:
            df['tiempo inicio'] = pd.to_datetime(df['tiempo inicio'])
            df['tiempo final'] = pd.to_datetime(df['tiempo final'])
            df['duracion'] = (df['tiempo final'] - df['tiempo inicio']).dt.total_seconds() / 60.0
        except Exception as e:
            logging.exception("Error en el cálculo de la duración")
            raise Exception(f"Error al procesar los tiempos: {e}")

        try:
            df['dureza'] = df['duracion'].apply(self.classify_duracion)
            df['indice_dureza'] = df['duracion'].apply(self.hardness_index)
        except Exception as e:
            logging.exception("Error al clasificar la duración y calcular el índice de dureza")
            raise Exception(f"Error al procesar los índices: {e}")

        logging.info("Archivo procesado exitosamente.")
        return df

    def classify_duracion(self, minutos):
        return classify_duracion(minutos)

    def hardness_index(self, T):
        return hardness_index(T)
