import logging
import math

import pandas as pd

# Workaround: pandas 3.0 defaults to pyarrow-backed string columns
# (future.infer_string=True). Arrow strings trigger SIGSEGV in
# Streamlit's native Plotly rendering pipeline (pyarrow 25.x + plotly
# 6.9 + streamlit 1.59) during reruns with large datasets. Disabling
# Arrow string inference forces plain Python str (object dtype),
# avoiding the native crash without changing observable behavior.
try:
    pd.set_option("future.infer_string", False)
except Exception:
    pass

# PARITY-DEBT: webapp/src/utils/dataProcessor.ts:processCsvData — this
# adapter wraps the pure functions in `classification.py` and the
# migration ticket is tracked in the parity spec. Keep the DataFrame
# logic side-effect-free so a future TS port can mirror it.
from classification import (
    DEFAULT_THRESHOLDS,
    Thresholds,
    Metric,
    classify_duracion,
    classify_with_metric,
    hardness_index,
    hardness_index_with_metric,
    penetration_rate,
    rig_mean_penetration,
    rig_normalized_penetration,
)

# Configuración básica para logging
logging.basicConfig(filename="app.log", level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

# Possible depth column names, in priority order. The app's real CSVs
# use `Prof. por Operador` (normalized to lowercase); the spec also
# mentions the generic `profundidad`. The adapter accepts any of these.
DEPTH_COLUMN_CANDIDATES = (
    "profundidad",
    "prof. por operador",
    "prof. por sensor",
    "mts plan",
)


def _resolve_depth_column(columns):
    """Return the first depth column present in `columns`, else `None`."""
    for candidate in DEPTH_COLUMN_CANDIDATES:
        if candidate in columns:
            return candidate
    return None


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

        # Add the penetration-rate column via the pure function. Missing
        # depth column ⇒ every cell becomes NaN (per R-1 scenario).
        depth_column = _resolve_depth_column(df.columns)
        if depth_column is None:
            df['tasa_penetracion'] = pd.Series(
                [float('nan')] * len(df),
                index=df.index,
                dtype=float,
            )
            logging.info(
                "No se encontró columna de profundidad; "
                "tasa_penetracion queda como NaN."
            )
        else:
            df['tasa_penetracion'] = [
                # PARITY-DEBT: webapp/src/utils/dataProcessor.ts:applyPenetrationRate
                penetration_rate(depth, dur)
                for depth, dur in zip(df[depth_column], df['duracion'])
            ]

        try:
            # Default classification using the legacy boundaries. The
            # downstream UI calls `classify_with_metric` again with the
            # user-tuned thresholds so this default pass only seeds the
            # columns for the very first render.
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

    def classify_with_metric(self, df, thresholds: Thresholds, metric: Metric) -> pd.DataFrame:
        """Reclassify a DataFrame copy using the supplied metric and thresholds.

        Returns a copy — never mutates the cached DataFrame. The
        `dureza` and `indice_dureza` columns are populated by calling
        the pure functions in `classification.py` so this adapter stays
        a thin shim around the parity surface.
        """
        result = df.copy()
        if metric == "duration":
            values = result["duracion"]
        elif metric == "penetration_rate":
            values = result["tasa_penetracion"]
        elif metric == "rig_normalized_penetration":
            if "tasa_penetracion_normalizada" not in result.columns:
                raise ValueError(
                    "rig_normalized_penetration requires the "
                    "'tasa_penetracion_normalizada' column. Call "
                    "add_rig_normalized_rate first."
                )
            values = result["tasa_penetracion_normalizada"]
        else:
            raise ValueError(f"Unknown metric {metric!r}")

        # PARITY-DEBT: webapp/src/utils/dataProcessor.ts:processCsvData —
        # the TS counterpart will read `thresholds[metric]` and apply the
        # same pure helpers. Keep these two call sites in lockstep.
        result["dureza"] = [
            classify_with_metric(v, thresholds, metric) for v in values
        ]
        result["indice_dureza"] = [
            hardness_index_with_metric(v, thresholds, metric) for v in values
        ]
        return result

    def add_rig_normalized_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add `tasa_penetracion_normalizada` per-rig z-score column.

        When the `perforadora` column is absent the result is returned
        unchanged — no exception, no synthetic column. When it is
        present, each row receives a z-score against its own rig's mean
        and standard deviation using the pure
        `rig_normalized_penetration` helper.

        Rows with a missing `tasa_penetracion` value contribute to the
        per-rig statistics as 0.0 weight (the pure helper returns 0.0
        for non-finite inputs anyway, so the aggregate is consistent).
        """
        if "perforadora" not in df.columns:
            return df

        result = df.copy()
        grouped = result.groupby("perforadora")["tasa_penetracion"]

        # PARITY-DEBT: webapp/src/utils/dataProcessor.ts:addRigNormalizedRate
        # — the TS port must mirror this groupby + std+epsilon guard.
        means = grouped.transform(lambda s: rig_mean_penetration(s.tolist()))
        # pandas std with ddof=1 matches the spec's "std <= ε → 0.0" guard
        # because we delegate the epsilon check to the pure helper.
        stds = grouped.transform(lambda s: _safe_std(s.tolist()))

        result["tasa_penetracion_normalizada"] = [
            rig_normalized_penetration(rate, avg, std)
            for rate, avg, std in zip(
                result["tasa_penetracion"], means, stds
            )
        ]
        return result


def _safe_std(values) -> float:
    """Population std of finite values, NaN-free.

    Returns 0.0 when fewer than two finite values exist. We use a small
    helper instead of `pd.Series.std` so the parity contract stays
    explicit about which entries contribute.
    """
    finite = [v for v in values if v is not None and math.isfinite(v)]
    if len(finite) < 2:
        return 0.0
    mean = sum(finite) / len(finite)
    variance = sum((v - mean) ** 2 for v in finite) / (len(finite) - 1)
    return math.sqrt(variance)