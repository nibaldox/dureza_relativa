# Design: Drilling Analytics Enhancements

## Technical Approach

Add a parity-critical pure API in `classification.py` first, then adapt pandas and Streamlit around it. The Python UI ships now; the TypeScript port is deferred, but the callable shapes below are the contract. `classification.py` MUST NOT import pandas, Streamlit, Plotly, or logging. This follows the proposal and current specs: classification logic stays side-effect free, Streamlit stays a thin UI, and parity fixtures protect Python/TS drift.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Parity boundary | `classification.py` owns all metric math, thresholds, category/index functions, and rig-normalization formulas. | Put formulas in `data_processor.py` or `streamlit_app.py`. | Pure primitive-in/primitive-out functions are easiest to port 1:1 to TS and test with shared fixtures. |
| Threshold contract | Use one `Thresholds` TypedDict/interface with primitive numeric leaf fields: `duration.{soft,medium,hard}` and `rate.{soft,medium,hard}`. | Keep hardcoded constants or separate configs per metric. | A single shape prevents UI/adapter/TS drift; duration defaults remain `16/24/40`, rate defaults start at `1.0/0.7/0.4`. |
| Invalid rate inputs | `penetration_rate` returns `0.0` for non-positive duration and `NaN` for missing/non-finite depth. | Raise inside pure functions. | Keeps Streamlit reruns from crashing; pandas adapter handles NaN display/filtering at the boundary. |
| Cache safety | Cache CSV parsing/base derived columns, then classify a copy after widgets resolve thresholds. | Cache threshold-specific results. | Threshold sliders rerun cheaply without mutating `@st.cache_data` output. |

## Data Flow

```text
streamlit_app.py (UI/widgets/export) ──calls──> data_processor.py (pandas adapter) ──calls──> classification.py (pure)
classification.py (pure, parity-critical) ← data_processor.py ← streamlit_app.py
```

CSV ingestion/classification sequence:

```text
CSV → normalize columns → duracion + tasa_penetracion
UI widgets → Thresholds + metric
filtered copy → classify_with_metric → dureza + indice_dureza → charts/export
```

`Perforadora` is checked as `perforadora` after existing lowercase normalization. If absent, rig filters, rig box plots, and normalized columns are skipped silently.

## File Changes

| File | Action | Description |
|---|---|---|
| `classification.py` | Modify | Add `Thresholds`, `penetration_rate`, `classify_with_metric`, `hardness_index_with_metric`, `rig_mean_penetration`, `rig_normalized_penetration`; keep `classify_duracion`/`hardness_index`. |
| `data_processor.py` | Modify | Add `tasa_penetracion`; add adapter method to classify copies by selected metric and optional rig-normalized rate. Group by normalized `perforadora` for rig mean/std. |
| `streamlit_app.py` | Modify | Sidebar metric selector plus `st.number_input`/slider cutoffs; optional rig filter; `st.download_button` exports `df_filtrado.to_csv(index=False).encode("utf-8-sig")` after date, drill-pattern, and rig filters. |
| `visualizer.py` | Modify | Add per-rig penetration-rate box plot and normalized-hardness plot guards. |
| `tests/*`, `tests/fixtures/parity/classification_cases.json` | Modify | Add pure-function and parity cases for new contracts. |
| `webapp/` | No change | TS signatures documented only; implementation deferred. |

## Interfaces / Contracts

```python
class MetricThresholds(TypedDict):
    soft: float
    medium: float
    hard: float

class Thresholds(TypedDict):
    duration: MetricThresholds
    rate: MetricThresholds

Metric = Literal["duration", "penetration_rate", "rig_normalized_penetration"]
def classify_duracion(minutos: float) -> str: ...
def hardness_index(T: float) -> float: ...
def penetration_rate(depth_m: float, duration_min: float) -> float: ...
def classify_with_metric(value: float, thresholds: Thresholds, metric: Metric) -> str: ...
def hardness_index_with_metric(value: float, thresholds: Thresholds, metric: Metric) -> float: ...
def rig_mean_penetration(rates: list[float]) -> float: ...
def rig_normalized_penetration(rate: float, rig_avg: float, rig_std: float) -> float: ...
```

Expected TypeScript:

```ts
export interface MetricThresholds { soft: number; medium: number; hard: number }
export interface Thresholds { duration: MetricThresholds; rate: MetricThresholds }
export type Metric = 'duration' | 'penetration_rate' | 'rig_normalized_penetration'
export function classifyDuration(minutes: number): HardnessCategory
export function hardnessIndex(minutes: number): number
export function penetrationRate(depthM: number, durationMin: number): number
export function classifyWithMetric(value: number, thresholds: Thresholds, metric: Metric): HardnessCategory
export function hardnessIndexWithMetric(value: number, thresholds: Thresholds, metric: Metric): number
export function rigMeanPenetration(rates: number[]): number
export function rigNormalizedPenetration(rate: number, rigAvg: number, rigStd: number): number
```

Duration comparisons preserve current strict boundaries. Rate comparisons are reversed: faster means softer; exact cutoffs move to the harder bucket. Rig-normalized rate is `(rate - rig_avg) / rig_std`, returning `0.0` when `rig_std <= ε`.

Parity-critical: `classification.py` contracts and parity fixtures. Python-only: Streamlit widgets/export, pandas DataFrame adaptation, and Plotly visualizations. Any divergence from the future TS implementation must be justified in the relevant spec/design update.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Pure functions, edge rates, threshold boundaries, std=0 normalization. | Extend `tests/test_classification.py`. |
| Parity | Shared fixture shape and TS-ready expected outputs. | Extend `classification_cases.json`; Python asserts now, TS later. |
| Integration | DataFrame columns, optional `prof. por operador`/`perforadora`, filtered export source. | Extend `tests/test_data_processor_io.py` where feasible. |
| Smoke | Streamlit upload, sliders, filters, export. | Manual `streamlit run streamlit_app.py`. |

## Migration / Rollout

No data migration required. Implementation sequence: (1) pure `classification.py`; (2) `data_processor.py` adapter; (3) Streamlit metric/threshold widgets; (4) per-rig visuals; (5) filtered CSV export.

## Open Questions

None.
