# drilling-analytics

## Purpose

Penetration-rate metric (m/min), runtime-tunable thresholds, per-rig
z-score normalization, and filtered CSV export for the Streamlit layer.
All business logic MUST live in pure functions in `classification.py` so a
future TypeScript port is a 1:1 translation. Both stacks load the same
golden JSON fixture via the existing parity symlink.

## Pure function contracts (parity-critical)

| Function | Signature (Python and TS identical except `list` ↔ `array`) |
|----------|-------------------------------------------------------------|
| `penetration_rate` | `(depth_m, duration_min) -> float \| None` |
| `classify_with_metric` | `(value, thresholds, metric) -> str` |
| `hardness_index_with_metric` | `(value, thresholds, metric) -> float` |
| `rig_mean_penetration` | `(rates: list[float]) -> float \| None` |
| `rig_normalized_penetration` | `(rate, rig_avg, rig_std) -> float` |

`Thresholds` (TypedDict in Python, `interface` in TS):
`{duration: {soft:16, medium:24, hard:40}, rate: {soft:1.0, medium:0.7, hard:0.4}}`.

## Requirements

### R-1. Penetration rate metric

`classification.penetration_rate(depth_m, duration_min)` MUST return
`None` for non-finite depth, non-finite duration, or `duration_min <= 0`.
`data_processor.load_and_process` MUST add `tasa_penetracion` to every
row; `None` cells render as `—` in the UI.

#### Scenario: Computes rate

- GIVEN `profundidad = 17` (m), `duracion = 19` (min)
- WHEN `penetration_rate(17.0, 19.0)` runs
- THEN it returns `0.8947368421…` within `1e-9`

#### Scenario: Zero or non-finite duration

- GIVEN `penetration_rate(17.0, 0.0)` and `penetration_rate(17.0, inf)`
- WHEN each runs
- THEN both return `None` AND the UI renders `—`

#### Scenario: Missing depth column

- GIVEN a CSV header without `profundidad`
- WHEN `data_processor.load_and_process` runs
- THEN `tasa_penetracion` is `NaN` for every row AND no exception is raised

### R-2. Configurable thresholds

The sidebar MUST expose sliders for duration cutoffs (clamped
`[1, 120]` min) and rate cutoffs (clamped `[0.01, 10.0]` m/min).
Default `Thresholds` MUST equal `{duration:{16,24,40}, rate:{1.0,0.7,0.4}}`
and MUST reproduce pre-change classifications byte-for-byte.

#### Scenario: Slider re-classifies under 1 s

- GIVEN a 5 000-row CSV, default thresholds
- WHEN `medium` slider moves from 24 to 30
- THEN `df["dureza"]` recomputes in under 1 second

#### Scenario: Defaults reproduce current behavior

- GIVEN the default `Thresholds`
- WHEN `pytest tests/test_parity.py -q` runs
- THEN every legacy case in `classification_cases.json` passes against
  `classify_with_metric(v, defaults, "duration")`

#### Scenario: Slider values are clamped

- GIVEN the engineer types `0` into the `soft` rate slider
- WHEN Streamlit validates
- THEN the slider is clamped to `0.01` AND `classify_with_metric` never
  receives `0.0`

### R-3. Per-rig normalization

`tasa_penetracion_normalizada` MUST be a z-score against per-rig mean
and std when `Perforadora` is present. When absent, the column MUST be
omitted silently and per-rig viz MUST NOT render.

#### Scenario: Z-score per rig

- GIVEN rig `R1` mean=0.7, std=0.2
- WHEN `rig_normalized_penetration(0.9, 0.7, 0.2)` runs
- THEN it returns `1.0` within `1e-9`

#### Scenario: Single-sample std guard

- GIVEN `rig_normalized_penetration(0.6, 0.6, 0.0)`
- WHEN it runs
- THEN it returns `0.0` (no `ZeroDivisionError`)

#### Scenario: Missing Perforadora column

- GIVEN a CSV header without `Perforadora`
- WHEN the app processes the file
- THEN `tasa_penetracion_normalizada` is omitted AND per-rig viz silently
  skips without raising

### R-4. CSV export

The app MUST render `st.download_button` whose payload is the active
filtered DataFrame encoded as `utf-8-sig` (UTF-8 BOM, Excel-friendly).

#### Scenario: Export reflects active filters

- GIVEN filters `drill_pattern=["A"]`, date range
  `[2026-01-01, 2026-01-31]`
- WHEN the user clicks "Descargar CSV"
- THEN the file contains exactly the rows in `df_filtrado` AND starts
  with the UTF-8 BOM (`\xef\xbb\xbf`)

#### Scenario: Empty filter set

- GIVEN active filters matching zero rows
- WHEN the user clicks "Descargar CSV"
- THEN the file is valid CSV with headers only AND the UI shows an info
  notice beforehand

### R-5. Parity contract (Python ↔ future TypeScript)

All five parity-critical functions MUST be pure (no pandas/streamlit/
plotly/logging imports), MUST consume and return only primitives, and
MUST each have a golden JSON fixture under
`tests/fixtures/parity/drilling_analytics_cases.json`, loadable verbatim
by both stacks.

#### Scenario: Pure module has zero side-effecting imports

- GIVEN `classification.py` after the change
- WHEN `grep -E "import (streamlit|pandas|plotly|logging)" classification.py` runs
- THEN it returns zero matches

#### Scenario: Golden JSON fixture covers every pure function

- GIVEN `tests/fixtures/parity/drilling_analytics_cases.json`
- WHEN `pytest tests/test_parity.py -q` runs
- THEN every entry is asserted against the corresponding Python function
- AND a TS port MAY load the same file via the existing symlink under
  `webapp/src/utils/__tests__/fixtures/`

#### Scenario: Parity debt markers on Python-only adapters

- GIVEN a DataFrame adapter in `data_processor.py` wrapping a pure
  function
- WHEN it is committed
- THEN it MUST carry a `# PARITY-DEBT:` comment naming the planned TS
  counterpart (e.g. `webapp/src/utils/dataProcessor.ts:processCsvData`)
  and the migration ticket
