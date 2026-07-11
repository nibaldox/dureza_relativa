# Delta for python-classification-and-testing

## MODIFIED Requirements

### R-5. Smoke test for extracted module

A test under `tests/test_classification.py` MUST import only `classification`
(never `data_processor`) and MUST assert at least three known input/output
pairs for each of `classify_duracion`, `hardness_index`,
`penetration_rate`, `classify_with_metric`, `hardness_index_with_metric`,
`rig_mean_penetration`, and `rig_normalized_penetration`. The test file
SHOULD exercise the boundary cases `0`, `16`, `24`, `40`, and `60` for the
index function, the category thresholds for the classification function,
and the `(17.0, 19.0)`, `(17.0, 0.0)`, and `(9.9, 0.0, 0.0)` cases for the
new pure functions.
(Previously: smoke coverage limited to `classify_duracion` and
`hardness_index` with one known pair each.)

#### Scenario: S-5. Smoke assertions catch regressions

- GIVEN `tests/test_classification.py`
- WHEN pytest executes it
- THEN for the boundary input `T = 16` the index equals `25.0`
- AND for `T = 24` the index equals `50.0`
- AND for `T = 40` the index equals `75.0`
- AND for `T = 60` the index equals `100.0`
- AND `penetration_rate(17.0, 19.0)` ≈ `0.8947368421`
- AND `classify_with_metric(19.0, defaults, "duration")` equals
  `"roca media"`
- AND `rig_normalized_penetration(0.9, 0.7, 0.2)` equals `1.0`
- AND `rig_normalized_penetration(0.6, 0.6, 0.0)` equals `0.0`

## ADDED Requirements

### R-7. Parity-aware smoke coverage for new pure functions

`tests/test_classification.py` MUST include a smoke test for every
parity-critical pure function added by `drilling-analytics-enhancements`.
Each smoke test MUST (a) call the pure function with at least three known
input/output pairs, (b) load the expected outputs from
`tests/fixtures/parity/drilling_analytics_cases.json` when available, and
(c) carry a `# PARITY-DEBT:` marker when the test exercises a Python-only
DataFrame adapter rather than the bare pure function.

#### Scenario: Smoke test exercises all five new pure functions

- GIVEN the five new pure functions are exported from `classification.py`
- WHEN `pytest tests/test_classification.py -q` runs
- THEN at least one test asserts a known pair for `penetration_rate`
- AND at least one test asserts a known pair for `classify_with_metric`
- AND at least one test asserts a known pair for `hardness_index_with_metric`
- AND at least one test asserts a known pair for `rig_mean_penetration`
- AND at least one test asserts a known pair for `rig_normalized_penetration`
