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

## Notes

- **No cross-stack parity required.** Classification thresholds, CSV schema
  parsing, and other shared business logic are untouched. The React/TS webapp
  is unchanged; its charts in `webapp/src/utils/charts.ts` are audited
  separately under the follow-up `streamlit-audit-remediation-webapp`.