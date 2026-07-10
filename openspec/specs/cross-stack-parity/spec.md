# cross-stack-parity

## Purpose

This capability defines the single source of truth that keeps the Python and
TypeScript implementations of the hardness-classification pure functions in lockstep.
It MUST publish a JSON fixture of expected inputs and outputs that both stacks load,
MUST assert exact numeric equality within a documented float tolerance, and MUST name
the diverging case in any failure message so a reviewer can locate the divergence
point without diffing the two stacks by hand.

## Requirements

### R-1. Single JSON source of truth

The fixture `tests/fixtures/parity/classification_cases.json` MUST exist at the
repository root and MUST hold an object with a `cases` array. Each case MUST be an
object with the keys `input` (number, minutes), `expected_dureza` (one of the four
Spanish category strings), and `expected_indice_dureza` (number in `[0, 100]`). The
fixture MUST be the only file of its kind; no stack-local copy is permitted.

### R-2. TypeScript access via relative symlink

`webapp/src/utils/__tests__/fixtures/classification_cases.json` MUST be a relative
symlink that resolves to `tests/fixtures/parity/classification_cases.json` at the
repo root. The relative path MUST traverse five directory levels upward from
`webapp/src/utils/__tests__/fixtures/` to the project root, then descend into
`tests/fixtures/parity/`.

### R-3. Float tolerance on numeric equality

Both parity tests MUST assert that `expected_indice_dureza` matches the computed
value within a tolerance of `1e-9`. The category assertion MUST be an exact string
equality. The chosen tolerance MUST be documented in a comment in each parity test
file.

### R-4. Failure messages identify the diverging case

If a parity case fails on either stack, the assertion message MUST include the case
index, the input value, the expected value, and the actual value. Reviewers MUST be
able to identify the divergence point from the test output alone, without reading
the implementation.

### R-5. Fixture governance

Any future change that alters the classification thresholds (`16`, `24`, `40`, `60`)
or the per-segment formulas MUST update `classification_cases.json` in the same
change, before the implementation is merged. The follow-up change `lock-csv-format`
(see `openspec/changes/bootstrap-test-runner/proposal.md` Follow-ups) is the
precondition for extending this fixture to cover end-to-end CSV ingestion parity.

## Scenarios

#### S-1. Python parity test consumes the fixture

- GIVEN `tests/fixtures/parity/classification_cases.json` with N cases
- WHEN `pytest tests/test_parity.py -q` runs
- THEN every case is asserted
- AND the test reports `N` successful assertions (or one failure per diverging case)

#### S-2. TypeScript parity test consumes the same bytes

- GIVEN the symlink resolves and points at the same file as the Python fixture
- WHEN the TS parity test reads the JSON
- THEN the parsed content is byte-identical to what the Python test loads
- AND every case is asserted against `classifyDuration` and `hardnessIndex`

#### S-3. Float tolerance masks IEEE-754 noise only

- GIVEN a case whose `expected_indice_dureza` is `24.984375`
- WHEN the Python function returns `24.984374999...`
- THEN the assertion passes because the difference is below `1e-9`
- AND a hypothetical case returning `24.99` would fail because the difference is above `1e-9`

#### S-4. Diverging case is identifiable from the failure message

- GIVEN a parity case where the TS implementation returns `"roca media"` but the fixture expects `"roca dura"`
- WHEN the TS parity test fails
- THEN the failure message contains the case index, the input minutes, the expected
  category, and the actual category

#### S-5. Symlink integrity check

- GIVEN the symlink at `webapp/src/utils/__tests__/fixtures/classification_cases.json`
- WHEN the TS test loads the JSON and asserts at least one known sentinel case
- THEN a broken or missing symlink surfaces as a clear test failure rather than an
  empty-array silent pass

#### S-6. Threshold change requires fixture update

- GIVEN a future change proposes to alter the boundary at `16` minutes
- WHEN that change is reviewed
- THEN every case in `classification_cases.json` whose expected category depends on
  the boundary has been updated in the same PR
- AND both parity tests still pass