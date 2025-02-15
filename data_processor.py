import logging
import pandas as pd

# Configuración básica para logging
logging.basicConfig(filename="app.log", level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

class DataProcessor:
    REQUIRED_COLUMNS = ['tiempo inicio', 'tiempo final']

    def load_and_process(self, file_path):
        logging.info(f"Iniciando carga del archivo: {file_path}")
        try:
            df = pd.read_csv(file_path)
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
        if minutos < 16:
            return "roca suave"
        elif minutos < 24:
            return "roca media"
        elif minutos < 40:
            return "roca dura"
        else:
            return "roca muy dura"

    def hardness_index(self, T):
        """
        Calcula el Índice de Dureza (HI) en función del tiempo de perforación (T, en minutos).
        HI varía de 0 a 100 según los siguientes tramos:
          - 0 <= T <= 16  -> [0, 25]
          - 16 < T <= 24  -> [25, 50]
          - 24 < T <= 40  -> [50, 75]
          - 40 < T <= 60  -> [75, 100]
          - T > 60        -> 100 (saturado)
        
        Parámetros:
        ----------
        T : float
            Tiempo de perforación en minutos (no debe ser negativo).
        
        Retorna:
        --------
        float
            Valor del índice de dureza (entre 0 y 100).
        """
        if T < 0:
            # Manejo básico de casos "atípicos" o inválidos
            return 0.0
        elif T <= 16:
            return 25.0 * (T / 16.0)
        elif T <= 24:
            return 25.0 + 25.0 * ((T - 16.0) / 8.0)
        elif T <= 40:
            return 50.0 + 25.0 * ((T - 24.0) / 16.0)
        elif T <= 60:
            return 75.0 + 25.0 * ((T - 40.0) / 20.0)
        else:
            # Para T > 60, se fija en 100
            return 100.0
