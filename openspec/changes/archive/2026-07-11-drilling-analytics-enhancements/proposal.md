# Proposal: drilling-analytics-enhancements

## Intent

Classification keys on raw drilling duration — but 19 min for a 17 m hole is not
the same rock as 19 min for a 30 m hole, and the engineer cannot tune the hardcoded
16/24/40 thresholds for local geology or equipment. Add a penetration-rate metric,
runtime thresholds, per-rig normalization, and CSV export. Python ships now;
classification is locked behind pure functions so a future TypeScript port is a
1:1 translation.

## Scope

### In Scope

| # | Deliverable | Layer |
|---|-------------|-------|
| F1 | `tasa_penetracion` (m/min) derived column; `classification.py` gains `penetration_rate` + rate-aware classify/index variants | Python |
| F2 | Sidebar sliders for 3 thresholds × 2 metrics, defaulting to 16/24/40; `Thresholds` struct flows into pure functions | Python UI |
| F3 | `Perforadora` (rig) grouping: per-rig box plot + per-rig normalized hardness (z-score vs rig mean). Columns optional | Python + viz |
| F4 | `st.download_button` exporting filtered + classified DataFrame to CSV (UTF-8 BOM). Reflects active filters | Python UI |

### Out of Scope

- TypeScript / React implementation — pure signatures ARE the contract; TS port deferred.
- Changing default thresholds — 16/24/40 stay default; engineer adjusts at runtime.
- Webapp CSV upload parity; pytest / parity-fixture bootstrap (provided by `bootstrap-test-runner`).

## Capabilities

Researched `openspec/specs/`: `python-classification-and-testing`,
`cross-stack-parity`, `streamlit-visualization`.

### New Capabilities

- `drilling-analytics`: penetration-rate metric + configurable thresholds +
  per-rig normalization + CSV export. One spec.md, four ADDED Requirements.

### Modified Capabilities

- `python-classification-and-testing`: `classification.py` extends with rate-aware
  parity-critical functions; smoke tests cover each (R-5 additive).
- `cross-stack-parity`: `classification_cases.json` extends with cases for
  `penetration_rate` and `rig_normalized_penetration`; tolerance / governance rules unchanged.
- `streamlit-visualization`: two new chart methods
  (`plot_penetration_rate_by_rig`, `plot_hardness_by_rig`); sidebar gains "Umbrales"
  expander. Palette / cache / theme requirements unchanged.

## Approach

1. **Parity-isolation first.** All business logic in `classification.py` (no
   streamlit / pandas / logging imports). Thresholds travel as a `Thresholds`
   TypedDict through function args.
2. **UI thin.** `streamlit_app.py` reads sliders, builds `Thresholds`, calls
   `data_processor.classify_with_metric(df, thresholds, metric)`. DataFrame
   ops stay in `data_processor.py`.
3. **Metric-as-input.** Classifier becomes `classify(value, thresholds,
   metric)`. Per-rig mean & std on `tasa_penetracion`;
   `rig_normalized_penetration` returns z-score; UI toggle for raw vs
   normalized. Export: `st.download_button` emits
   `df_filtrado.to_csv(index=False).encode("utf-8-sig")`.

## Parity-Aware Architecture

| Function | Python signature | Planned TS signature |
|----------|------------------|----------------------|
| `penetration_rate` | `(depth_m: float, duration_min: float) -> float \| None` | `(depthM, durationMin) => number \| null` |
| `classify_with_metric` | `(value: float, thresholds: Thresholds, metric: "duration"\|"penetration_rate") -> str` | `(value, thresholds, metric) => HardnessCategory` |
| `hardness_index_with_metric` | `(value: float, thresholds: Thresholds, metric: ...) -> float` | `(value, thresholds, metric) => number` |
| `rig_mean_penetration` | `(rates: list[float]) -> float \| None` | `(rates: number[]) => number \| null` |
| `rig_normalized_penetration` | `(rate: float, rig_avg: float, rig_std: float) -> float` | `(rate, rigAvg, rigStd) => number` |

`Thresholds` is a TypedDict in Python, interface in TS, same shape:
`{ duration: {soft:16, medium:24, hard:40}, rate: {soft:1.0, medium:0.7, hard:0.4} }`.
Pure modules MUST NOT import streamlit/pandas/plotly/logging. Both stacks load the
same JSON fixture via `tests/test_parity.py` once the TS port lands.

## Affected Areas

| Area | Impact |
|------|--------|
| `classification.py` | Modified: +~80 LOC (5 new pure fns, Thresholds TypedDict) |
| `data_processor.py` | Modified: +~30 LOC (rate-aware classification, optional rig col) |
| `streamlit_app.py` | Modified: +~60 LOC (sidebar thresholds, export, viz toggles) |
| `visualizer.py` | Modified: +~60 LOC (per-rig viz methods) |
| `tests/test_classification.py` | Modified: +~20 LOC (smoke tests) |
| `tests/fixtures/parity/classification_cases.json` | Modified: +~15 cases |
| `webapp/` | None |

## Risks

| Risk | Lik | Mitigation |
|------|-----|------------|
| Threshold struct drifts Python ↔ TS | Med | Typed shape; shared JSON schema |
| Engineer picks nonsensical thresholds | Low | Sliders clamp `[1,120]` min / `[0.01,10]` m/min |
| `tasa_penetracion` NaN/Inf on depth=0 or dur=0 | Med | Pure fn returns `None`; UI renders "—" |
| Per-rig std=0 single-sample divide-by-zero | Med | Returns 0.0 when std ≤ ε |
| Parity fixture staleness on threshold tweak | Med | cross-stack-parity R-5 mandates same-change update |
| Per-rig viz crashes when `Perforadora` absent | Low | New viz methods guard `if col not in df.columns` |

## Rollback Plan

`git revert <sha>` per file. Existing `classify_duracion` and `hardness_index`
signatures stay byte-identical — `bootstrap-test-runner` smoke tests keep
passing. New widgets sit behind new controls; disabling them reverts user
behavior without touching classification math. Default `Thresholds` match
current 16/24/40; rolling back sidebars returns to hardcoded behavior. No
data migration, no schema change. **Smoke:** sidebar at defaults reproduces
pre-change classifications byte-for-byte; `ejemplo_datos.txt` renders.

## Dependencies

- `streamlit>=1.57` (`st.download_button` since 0.88); `pandas`, `plotly` present.
- `tests/fixtures/parity/classification_cases.json` exists (from `bootstrap-test-runner`).

## Success Criteria

- [ ] `grep -E "import (streamlit|pandas|plotly|logging)" classification.py` → 0 matches.
- [ ] Default thresholds reproduce current classifications byte-for-byte.
- [ ] Slider movement updates `dureza` in <1 s on 5k-row CSV.
- [ ] CSV download reflects active filters (date + drill_pattern + rig).
- [ ] Smoke tests cover each new pure function with ≥3 known pairs.
- [ ] Parity fixture extended; `pytest tests/test_parity.py -q` green.
- [ ] Per-rig viz silently skips when `Perforadora` absent.
- [ ] `git diff --stat` ≤ 400 LOC across all Python files.
