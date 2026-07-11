# Delta for streamlit-visualization

## ADDED Requirements

### R-8. Per-rig chart methods

`Visualizer` MUST expose two new static methods:
`plot_penetration_rate_by_rig(df)` (box plot of `tasa_penetracion`
grouped by `Perforadora`) and `plot_hardness_by_rig(df)` (box plot of
`indice_dureza` grouped by `Perforadora`). Both MUST reuse the canonical
`COLOR_MAPPING` constant per R-1, MUST silently skip rendering when the
`Perforadora` column is absent, and MUST raise `ValueError` (not generic
`Exception`) when an unrelated required column is missing per R-2.

#### Scenario: Per-rig box plot renders when Perforadora exists

- GIVEN a filtered DataFrame with `Perforadora`, `tasa_penetracion`, and
  `indice_dureza` columns
- WHEN `Visualizer.plot_penetration_rate_by_rig(df)` runs
- THEN a Plotly figure is returned with one box trace per rig
- AND the figure title includes the metric name

#### Scenario: Per-rig viz silently skips when Perforadora absent

- GIVEN a filtered DataFrame without `Perforadora`
- WHEN either `plot_penetration_rate_by_rig` or `plot_hardness_by_rig`
  is called
- THEN it returns `None` (or an empty Plotly figure)
- AND no exception is raised

#### Scenario: Color palette stays canonical

- GIVEN the new per-rig methods
- WHEN `grep -nE "color_mapping\s*=\s*\{" visualizer.py` runs
- THEN it returns zero matches
- AND every per-rig trace uses `Visualizer.COLOR_MAPPING`

### R-9. Thresholds expander in sidebar

`streamlit_app.py` MUST render an `st.sidebar.expander("Umbrales")`
containing six sliders (three for `duration` cutoffs clamped to
`[1, 120]` min, three for `rate` cutoffs clamped to `[0.01, 10.0]`
m/min). The default values MUST equal the pre-change thresholds
(16/24/40 for duration; 1.0/0.7/0.4 for rate) and MUST rebuild a
`Thresholds` TypedDict passed to `data_processor.classify_with_metric`
on every rerun. Slider values MUST be clamped by Streamlit, not by
post-hoc validation in pure functions.

#### Scenario: Defaults reproduce current classifications

- GIVEN the `Umbrales` expander is unrendered or untouched
- WHEN the app processes any CSV
- THEN `df["dureza"]` matches the byte-for-byte output of the
  pre-change `classify_duracion(duracion)`

#### Scenario: Slider updates trigger reclassification

- GIVEN the engineer drags `medium` from 24 to 30
- WHEN Streamlit reruns the script
- THEN `data_processor.classify_with_metric` receives the new
  `Thresholds`
- AND `df["dureza"]` reflects the new cutoffs in under 1 second for a
  5 000-row CSV

### R-10. CSV download button

`streamlit_app.py` MUST render an `st.download_button` labeled
"Descargar CSV" whose payload is `df_filtrado.to_csv(index=False)
.encode("utf-8-sig")`. The button MUST sit below the filter summary
info message and MUST be enabled even when the filter set is empty
(headers-only export).

#### Scenario: Download reflects active filters

- GIVEN filters `drill_pattern = ["A"]` and date range
  `[2026-01-01, 2026-01-31]`
- WHEN the user clicks "Descargar CSV"
- THEN the downloaded bytes start with the UTF-8 BOM (`\xef\xbb\xbf`)
- AND every row in the file is in `df_filtrado`

#### Scenario: Empty filter set yields headers-only CSV

- GIVEN active filters match zero rows
- WHEN the user clicks "Descargar CSV"
- THEN the downloaded file is valid CSV with column headers only
- AND an `st.info` notice precedes the button click
