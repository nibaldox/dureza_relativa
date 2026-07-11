# Delta for cross-stack-parity

## MODIFIED Requirements

### R-5. Fixture governance

Any future change that alters the classification thresholds (`16`, `24`,
`40`, `60`), the per-segment formulas, the `Thresholds` TypedDict shape
(`duration.{soft,medium,hard}` and `rate.{soft,medium,hard}`), or any
pure function signature listed in the `drilling-analytics` spec MUST
update `classification_cases.json` and/or
`tests/fixtures/parity/drilling_analytics_cases.json` in the same change,
before the implementation is merged. The follow-up change `lock-csv-format`
is the precondition for extending this fixture to cover end-to-end CSV
ingestion parity.
(Previously: governance covered only `16/24/40/60` thresholds and the
per-segment formulas of `classify_duracion` and `hardness_index`.)

#### Scenario: S-6. Threshold change requires fixture update

- GIVEN a future change proposes to alter the boundary at `16` minutes or
  the rate threshold at `1.0` m/min
- WHEN that change is reviewed
- THEN every case in `classification_cases.json` and/or
  `drilling_analytics_cases.json` whose expected category depends on the
  boundary has been updated in the same PR
- AND both parity tests still pass

## ADDED Requirements

### R-6. New fixture for parity-critical pure functions

The fixture `tests/fixtures/parity/drilling_analytics_cases.json` MUST
exist at the repository root and MUST hold an object with a `cases` array.
Each case MUST name a pure function from the `drilling-analytics` spec,
provide its inputs as JSON primitives, and declare the expected return
value. The fixture MUST be the only file of its kind; no stack-local copy
is permitted.

#### Scenario: New fixture loads in Python parity test

- GIVEN `tests/fixtures/parity/drilling_analytics_cases.json` with cases
  for all five parity-critical pure functions
- WHEN `pytest tests/test_parity.py -q` runs
- THEN every case in the fixture is asserted against the corresponding
  Python function
- AND the test reports a pass/fail per case

### R-7. TypeScript access via relative symlink for new fixture

`webapp/src/utils/__tests__/fixtures/drilling_analytics_cases.json` MUST
be a relative symlink that resolves to
`tests/fixtures/parity/drilling_analytics_cases.json` at the repo root,
following the same five-level upward traversal pattern as R-2.

#### Scenario: TS parity test loads the new fixture through the symlink

- GIVEN the new symlink resolves to the same bytes as the Python fixture
- WHEN the TS parity test reads the JSON once the port lands
- THEN the parsed content is byte-identical to what the Python test loads
- AND every case is asserted against the TS counterpart

### R-8. Failure message identifies parity divergence in new fixture

If a parity case for `penetration_rate`, `classify_with_metric`,
`hardness_index_with_metric`, `rig_mean_penetration`, or
`rig_normalized_penetration` fails on either stack, the assertion message
MUST include the case index, the function name, the input value(s), the
expected value, and the actual value.

#### Scenario: Diverging new-fixture case is identifiable

- GIVEN a parity case where the TS implementation of
  `rig_normalized_penetration` returns `0.95` but the fixture expects `1.0`
- WHEN the TS parity test fails
- THEN the failure message contains the case index, the function name,
  the rig mean/std inputs, the expected `1.0`, and the actual `0.95`
