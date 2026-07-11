# streamlit-visualization

## Purpose

Locks in the post-remediation behavior of the Streamlit app and its Plotly
visualizer: a single canonical color palette, faithful `ValueError` propagation,
theme configuration via `.streamlit/config.toml` (no injected CSS), cache-safe
handling of the processed DataFrame, correct date-range partial-selection
behavior, no deprecated `use_container_width`, and deletion of dead code.
Scope is the Streamlit layer only; classification logic and the React/TS
webapp are untouched, so no TypeScript counterpart is required.

## Requirements

### R-1. Single canonical color palette

`Visualizer` MUST expose exactly one class-level `COLOR_MAPPING` constant that
every chart method reuses. Per-method `color_mapping = {...}` literals MUST NOT
exist. Every chart mapping the `dureza` category MUST apply
`"roca dura": "#e74c3c"`.

### R-2. ValueError fidelity

`Visualizer` chart methods MUST raise `ValueError` (not generic `Exception`)
when a required column is missing or input is invalid. `streamlit_app.py`
`except ValueError` MUST receive these and show a validation message; the
broad `except Exception` MUST NOT intercept them first.

### R-3. Theme via config.toml

`.streamlit/config.toml` MUST exist at the project root with a `[theme]` table.
The app MUST NOT inject widget styling via
`st.markdown("<style>...</style>", unsafe_allow_html=True)`. Runtime theme
introspection MUST use `st.context.theme.type`, not `st.get_option("theme.base")`.

### R-4. Cache safety

The memoized result of `cargar_datos` MUST NOT be mutated in place. Any
column conversion depending on it MUST bind to a fresh local variable.

### R-5. Date-range widget correctness

`st.date_input` used as a range filter MUST handle the partial-selection state
(one endpoint only) without raising `TypeError`. When incomplete, the app MUST
show an info message to pick both endpoints, or apply a documented default —
it MUST NOT propagate to the broad `except Exception`.

### R-6. No deprecated chart API

`streamlit_app.py` MUST NOT call any element with `use_container_width=True`.
The default width behavior (`width="stretch"`) is the contract.

### R-7. No dead code

`Visualizer.plot_heatmap` MUST NOT exist (zero call sites; replaced by
`plot_hardness_heatmap`). Unused parameters, unused imports, and the
module-level `if __name__ == "__main__"` MUST be removed.

### R-8. Per-rig chart methods

`Visualizer` MUST expose two new static methods:
`plot_penetration_rate_by_rig(df)` (box plot of `tasa_penetracion`
grouped by `Perforadora`) and `plot_hardness_by_rig(df)` (box plot of
`indice_dureza` grouped by `Perforadora`). Both MUST reuse the canonical
`COLOR_MAPPING` constant per R-1, MUST silently skip rendering when the
`Perforadora` column is absent, and MUST raise `ValueError` (not generic
`Exception`) when an unrelated required column is missing per R-2.

### R-9. Thresholds expander in sidebar

`streamlit_app.py` MUST render an `st.sidebar.expander("Umbrales")`
containing six sliders (three for `duration` cutoffs clamped to
`[1, 120]` min, three for `rate` cutoffs clamped to `[0.01, 10.0]`
m/min). The default values MUST equal the pre-change thresholds
(16/24/40 for duration; 1.0/0.7/0.4 for rate) and MUST rebuild a
`Thresholds` TypedDict passed to `data_processor.classify_with_metric`
on every rerun. Slider values MUST be clamped by Streamlit, not by
post-hoc validation in pure functions.

### R-10. CSV download button

`streamlit_app.py` MUST render an `st.download_button` labeled
"Descargar CSV" whose payload is `df_filtrado.to_csv(index=False)
.encode("utf-8-sig")`. The button MUST sit below the filter summary
info message and MUST be enabled even when the filter set is empty
(headers-only export).

## Scenarios

#### S-1. Single palette for every chart

- GIVEN `Visualizer.COLOR_MAPPING` as the sole palette definition
- WHEN `plot_duracion_box`, `plot_dureza_count`, `plot_location_interactive`,
  or `plot_3d_scatter` renders a row with `dureza == "roca dura"`
- THEN the figure applies `#e74c3c` for that category
- AND no per-method `color_mapping = {...}` literal exists in `visualizer.py`

#### S-2. Missing column reaches ValueError handler

- GIVEN an uploaded CSV that lacks the `elevacion` column
- WHEN `Visualizer.plot_3d_scatter(df)` runs
- THEN it raises `ValueError` mentioning `elevacion`
- AND `streamlit_app.py` catches it via `except ValueError as ve`
- AND `st.error(f"Error de validación: {ve}")` is shown

#### S-3. Theme via config.toml, no injected CSS

- GIVEN `.streamlit/config.toml` with a `[theme]` table
- WHEN the app launches
- THEN no `st.markdown("<style>...", unsafe_allow_html=True)` block exists
- AND runtime theme introspection uses `st.context.theme.type`

#### S-4. Cached DataFrame is never mutated

- GIVEN `cargar_datos(uploaded_file)` memoized
- WHEN the date-filter sidebar runs
- THEN `df_processed['tiempo inicio'] = pd.to_datetime(...)` does NOT execute
- AND a fresh local variable is used for downstream filtering

#### S-5. Partial date selection does not crash

- GIVEN `st.date_input("Selecciona rango de fechas", value=(min_date, max_date), ...)`
- WHEN the user has only clicked one date (single `datetime.date` returned)
- THEN the app does NOT raise `TypeError`
- AND the user sees an info message or a sensible default is applied

#### S-6. No `use_container_width` anywhere

- GIVEN `streamlit_app.py` after the change
- WHEN `grep -nE "use_container_width" streamlit_app.py` runs
- THEN it returns zero matches
- AND every `st.plotly_chart(...)` uses default width behavior

#### S-7. Dead code removed

- GIVEN `visualizer.py` after the change
- WHEN `grep -nE "def plot_heatmap\b" visualizer.py` runs
- THEN it returns zero matches
- AND `streamlit_app.py` no longer references `plot_heatmap`

#### S-8. Per-rig box plot renders when Perforadora exists

- GIVEN a filtered DataFrame with `Perforadora`, `tasa_penetracion`, and
  `indice_dureza` columns
- WHEN `Visualizer.plot_penetration_rate_by_rig(df)` runs
- THEN a Plotly figure is returned with one box trace per rig
- AND the figure title includes the metric name

#### S-9. Per-rig viz silently skips when Perforadora absent

- GIVEN a filtered DataFrame without `Perforadora`
- WHEN either `plot_penetration_rate_by_rig` or `plot_hardness_by_rig`
  is called
- THEN it returns `None` (or an empty Plotly figure)
- AND no exception is raised

#### S-10. Color palette stays canonical

- GIVEN the new per-rig methods
- WHEN `grep -nE "color_mapping\s*=\s*\{" visualizer.py` runs
- THEN it returns zero matches
- AND every per-rig trace uses `Visualizer.COLOR_MAPPING`

#### S-11. Defaults reproduce current classifications

- GIVEN the `Umbrales` expander is unrendered or untouched
- WHEN the app processes any CSV
- THEN `df["dureza"]` matches the byte-for-byte output of the
  pre-change `classify_duracion(duracion)`

#### S-12. Slider updates trigger reclassification

- GIVEN the engineer drags `medium` from 24 to 30
- WHEN Streamlit reruns the script
- THEN `data_processor.classify_with_metric` receives the new
  `Thresholds`
- AND `df["dureza"]` reflects the new cutoffs in under 1 second for a
  5 000-row CSV

#### S-13. Download reflects active filters

- GIVEN filters `drill_pattern = ["A"]` and date range
  `[2026-01-01, 2026-01-31]`
- WHEN the user clicks "Descargar CSV"
- THEN the downloaded bytes start with the UTF-8 BOM (`\xef\xbb\xbf`)
- AND every row in the file is in `df_filtrado`

#### S-14. Empty filter set yields headers-only CSV

- GIVEN active filters match zero rows
- WHEN the user clicks "Descargar CSV"
- THEN the downloaded file is valid CSV with column headers only
- AND an `st.info` notice precedes the button click

## Notes

- **No cross-stack parity required.** Classification thresholds, CSV schema
  parsing, and other shared business logic are untouched. The React/TS webapp
  is unchanged; its charts in `webapp/src/utils/charts.ts` are audited
  separately under the follow-up `streamlit-audit-remediation-webapp`.