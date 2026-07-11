# Tasks: drilling-analytics-enhancements

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 310–360 (classification ~80, data_processor ~30, streamlit ~100, visualizer ~60, tests+fixture ~70) |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Delivery strategy | auto-forecast |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

## Phase A: classification.py pure functions

- [x] A.1 Add `Thresholds`/`MetricThresholds` TypedDict + `Metric` Literal; verify shape via `repr` test.
- [x] A.2 `penetration_rate(depth_m, duration_min)` → `None` on non-finite depth or `duration_min <= 0`; `(17, 19) ≈ 0.8947368421` ±1e-9.
- [x] A.2.p Assert `(17, 0)` and `(17, inf)` return `None`; cover in parity fixture.
- [x] A.3 `classify_with_metric(value, thresholds, metric)`; rate reversed (faster=softer), exact cutoffs → harder.
- [x] A.3.p Golden: `classify_with_metric(v, defaults, "duration") == classify_duracion(v)` for every legacy case in `classification_cases.json`.

- [x] A.4 `hardness_index_with_metric(value, thresholds, metric)`; 16/24/40/60 boundaries = 25/50/75/100.
- [x] A.4.p Parity: `(16, defaults, "duration") == 25.0`; rate-metric segments ±1e-9.
- [x] A.5 `rig_mean_penetration(rates)` (None on empty) + `rig_normalized_penetration(rate, avg, std)` (0.0 when `std <= 1e-9`).
- [x] A.5.p Assert `(0.9, 0.7, 0.2) == 1.0`; std=0 guard: `(0.6, 0.6, 0.0) == 0.0`.
- [x] A.6 `grep -E "import (streamlit|pandas|plotly|logging)" classification.py` → 0.

## Phase B: data_processor.py adapter

- [x] B.1 Add `tasa_penetracion` via `penetration_rate`; NaN when depth column missing.
- [x] B.2 `DataProcessor.classify_with_metric(df, thresholds, metric)` returning copy; tag `# PARITY-DEBT: webapp/src/utils/dataProcessor.ts:processCsvData`.
- [x] B.3 Per-rig mean/std + `tasa_penetracion_normalizada` (z-score) when `perforadora` present; skip silently otherwise.
- [x] B.p Parity: adapter output == pure-function output on 3-row fixture.

## Phase C: UI controls + thresholds (streamlit_app.py)

- [x] C.1 `st.sidebar.expander("Umbrales")` with 6 `st.slider`s: duration [1,120], rate [0.01,10.0]; defaults 16/24/40 and 1.0/0.7/0.4.
- [x] C.2 Build `Thresholds` from sliders on every rerun; pass into `classify_with_metric`; tag `# PARITY-DEBT`.
- [x] C.3 `st.sidebar.multiselect("Perforadoras")` against normalized `perforadora`; `st.info` when absent.
- [x] C.p Default-threshold byte-for-byte: `df_filtrado["dureza"]` matches pre-change `classify_duracion` on `ejemplo_datos.txt`.

## Phase D: Per-rig visualizations (visualizer.py)

- [x] D.1 `Visualizer.plot_penetration_rate_by_rig(df)` box plot by `perforadora`; `None` when absent; `ValueError` for missing non-rig cols.
- [x] D.2 `Visualizer.plot_hardness_by_rig(df)` box plot of `indice_dureza` by `perforadora`; same guards.
- [x] D.p `grep -nE "color_mapping\s*=\s*\{" visualizer.py` → 0; both use `Visualizer.COLOR_MAPPING`.

## Phase E: CSV export (streamlit_app.py)

- [x] E.1 `st.download_button("Descargar CSV", data=df_filtrado.to_csv(index=False).encode("utf-8-sig"), mime="text/csv")` below filter summary.
- [x] E.2 `st.info` when `df_filtrado` empty (headers-only export enabled).
- [x] E.p Bytes start with `\xef\xbb\xbf`; row count == `len(df_filtrado)`.

## Phase F: Golden JSON fixture

- [x] F.1 `tests/fixtures/parity/drilling_analytics_cases.json` with `cases[]` for all 5 pure functions (≥3 pairs each).
- [x] F.2 Symlink `webapp/src/utils/__tests__/fixtures/drilling_analytics_cases.json` → `../../../../../tests/fixtures/parity/drilling_analytics_cases.json`.
- [x] F.3 Extend `tests/test_parity.py` with per-function dispatcher; failure msg includes case index, fn, inputs, expected, actual.

## Phase G: Parity markers + cleanup

- [x] G.1 `# PARITY-DEBT:` comments on every DataFrame/Streamlit adapter naming TS counterpart + migration ticket.
- [x] G.2 Update `README.md` (columns + Umbrales + Descargar CSV); rerun `streamlit run` smoke on `ejemplo_datos.txt`.