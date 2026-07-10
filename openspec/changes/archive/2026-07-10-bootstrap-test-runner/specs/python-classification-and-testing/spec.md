# python-classification-and-testing

## Purpose

This capability defines the Python test runner bootstrap and the extraction of pure
classification logic from `data_processor.py` into a side-effect-free module. It MUST
let `pytest tests/ -q` execute locally with no manual setup beyond installing the dev
extras, MUST preserve the public surface of `data_processor.py` for
`streamlit_app.py:3, 31-32`, and MUST neutralize the `logging.basicConfig` import-time
side effect at `data_processor.py:5-6` so the IO test path remains importable in a
silent harness.

## Requirements

### R-1. Pure-function extraction

The repository MUST expose a new module `classification.py` at the project root that
contains the two pure functions currently inlined at `data_processor.py:47-55` and
`data_processor.py:57-90`. The module MUST NOT import `logging`, `pandas`, or any
side-effecting dependency, and importing it MUST NOT write to disk, configure logging,
or register handlers.

### R-2. Backward-compatible re-export

`data_processor.py` MUST continue to expose the names `classify_duracion` and
`hardness_index` as module-level attributes (re-exported from `classification.py`).
The `DataProcessor.classify_duracion` and `DataProcessor.hardness_index` methods
MUST remain available so that the call sites at `data_processor.py:38-39` and the
`DataProcessor()` instantiation at `streamlit_app.py:31-32` keep working without
modification.

### R-3. Logging side-effect neutralization

`tests/conftest.py` MUST define an `autouse=True` fixture that monkey-patches
`logging.basicConfig` to a no-op before any test module imports `data_processor`.
The fixture MUST NOT itself import `data_processor` or `classification`, so that
the pure-function tests stay free of the logging side effect entirely.

### R-4. pytest runner configuration

The repository MUST declare pytest configuration in `pyproject.toml` under
`[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `python_files = ["test_*.py"]`,
and a minimum pytest version of 9.0. `requirements-dev.txt` MUST pin `pytest>=9.0`,
`pytest-cov>=5.0`, and `pytest-mock>=3.14` so that `python3 -m pytest tests/ -q`
works after `pip install -r requirements-dev.txt` with no other setup.

### R-5. Smoke test for extracted module

A test under `tests/test_classification.py` MUST import only `classification` (never
`data_processor`) and MUST assert at least one known input/output pair for each of
`classify_duracion` and `hardness_index`. The test file SHOULD exercise the boundary
cases `0`, `16`, `24`, `40`, and `60` for the index function, and the category
thresholds for the classification function.

### R-6. Cross-stack parity test

A test under `tests/test_parity.py` MUST load
`tests/fixtures/parity/classification_cases.json` and MUST iterate over every entry,
asserting that `classification.classify_duracion` returns the expected category and
that `classification.hardness_index` returns the expected numeric value within a
documented tolerance.

## Scenarios

#### S-1. Pure module imports cleanly

- GIVEN a fresh Python process with no `app.log` in the working directory
- WHEN `import classification` is executed
- THEN no file named `app.log` is created
- AND no log handlers are attached to the root logger

#### S-2. streamlit_app.py keeps importing

- GIVEN `data_processor.py` after refactor
- WHEN `streamlit run streamlit_app.py` is invoked
- THEN the import `from data_processor import DataProcessor` at `streamlit_app.py:3` succeeds
- AND `DataProcessor().load_and_process(...)` at `streamlit_app.py:31-32` returns the same
  classifications as before the refactor

#### S-3. Logging side-effect suppressed during IO test

- GIVEN `tests/conftest.py` is loaded by pytest
- AND a test under `tests/test_data_processor_io.py` does `import data_processor`
- WHEN the test executes
- THEN `logging.basicConfig` is not invoked with a `filename` argument
- AND no `app.log` file is created in the test working directory

#### S-4. pytest discovers tests

- GIVEN `pyproject.toml` declares `[tool.pytest.ini_options]` with `testpaths = ["tests"]`
- WHEN `python3 -m pytest tests/ -q` is run
- THEN pytest exits with status 0 and reports at least one collected test

#### S-5. Smoke assertions catch regressions

- GIVEN `tests/test_classification.py`
- WHEN pytest executes it
- THEN for the boundary input `T = 16` the index equals `25.0`
- AND for `T = 24` the index equals `50.0`
- AND for `T = 40` the index equals `75.0`
- AND for `T = 60` the index equals `100.0`

#### S-6. Parity fixture drives Python assertions

- GIVEN `tests/fixtures/parity/classification_cases.json` with at least one case
- WHEN `pytest tests/test_parity.py -q` runs
- THEN every case in the fixture is asserted against the extracted functions
- AND a failure message identifies the case index and input that diverged