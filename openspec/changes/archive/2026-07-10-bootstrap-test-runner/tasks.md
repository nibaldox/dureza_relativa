# Tasks: bootstrap-test-runner

## Forecast

**Total estimate: ~340 LOC changed/added** (under the 400-line review budget by ~60 lines). S-3 coverage gap closed by injecting A.5 (~30 LOC).

| Task | Estimate (LOC) | Phase |
|------|---------------:|-------|
| A.1 pytest config + dev deps | 25 | A — Python foundation |
| A.2 Extract `classification.py` + re-export shim | 50 | A |
| A.3 `tests/conftest.py` logging neutralization | 12 | A |
| A.4 `tests/test_classification.py` smoke test | 45 | A |
| **A.5 `tests/test_data_processor_io.py` (S-3 closure)** | **30** | **A** |
| B.1 Parity JSON fixture (curated cases) | 30 | B — Parity contract |
| C.1 `tests/test_parity.py` | 25 | C — Python parity |
| D.1 Vitest config + npm scripts | 27 | D — TS foundation |
| D.2 Export `classifyDuration` / `hardnessIndex` | 2 | D |
| D.3 Symlink fixture (drift-corrected path) | 0 | D |
| E.1 `dataProcessor.test.ts` smoke | 45 | E — TS parity |
| E.2 `parity.test.ts` (TS consumer) | 25 | E |
| F.1 README "How to run tests" | 20 | F — Docs |
| F.2 Local smoke recipe (doc-only) | 0 | F |
| **Total** | **~340** | — |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: single-pr  (confirmed by user, resolves Open Question 2)
400-line budget risk: Low  (~340 / 400)
S-3 coverage gap: closed by A.5  (resolves Open Question 1)

### Work units (one PR; six commits inside)

| Unit | Goal | Commit type | Notes |
|------|------|-------------|-------|
| 1 | Python extraction + re-export | `refactor+test` | Pure-function move; tests gate it |
| 2 | pytest config + dev deps | `chore` | No logic change |
| 3 | Parity fixture (single source of truth) | `test` | JSON only |
| 4 | Python parity test | `test` | Consumes unit 3 |
| 5 | Python IO test - S-3 closure (A.5) | `test` | Imports data_processor; asserts no app.log |
| 6 | TS export + Vitest config + smoke | `feat+test` | One PR slice |
| 7 | TS parity test + symlink + README | `test+docs` | Final slice; drift fix baked in |

---

## Phase A — Python runner foundation

### A.1 Add pytest config and dev dependency manifest

- **Title:** Declare pytest 9.x runner config and dev-only pip manifest.
- **Spec linkage:** python-classification-and-testing R-4, S-4.
- **Parity-paired:** N (foundation only).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/pyproject.toml` (NEW)
  - `/home/xod/Documentos/Code/dureza_relativa/requirements-dev.txt` (NEW)
- **Estimate:** ~25 LOC.
- **Commit:** `chore(python): add pytest 9 config and dev deps manifest` — touches `pyproject.toml`, `requirements-dev.txt`.
- **Done when:** `python3 -m pytest --collect-only -q` exits 0 once `tests/test_*.py` files exist; `pyproject.toml` declares `[tool.pytest.ini_options]` with `testpaths=["tests"]`, `python_files=["test_*.py"]`, `minversion="9.0"`; `requirements-dev.txt` pins `pytest>=9.0`, `pytest-cov>=5.0`, `pytest-mock>=3.14`. Spec python S-4 satisfied once A.4 lands.

### A.2 Extract pure classification functions into `classification.py`

- **Title:** Move `classify_duracion` and `hardness_index` out of `data_processor.py` into a side-effect-free module; keep `DataProcessor` methods as one-line wrappers.
- **Spec linkage:** python-classification-and-testing R-1, R-2, S-1, S-2.
- **Parity-paired:** Y (mirrors D.2; C.1 consumes this).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/classification.py` (NEW) — pure functions verbatim from `data_processor.py:47-55, 57-90`, no `logging`/`pandas` imports.
  - `/home/xod/Documentos/Code/dureza_relativa/data_processor.py` (MODIFIED) — replace method bodies at `:47-55, 57-90` with `return classify_duracion(minutos)` / `return hardness_index(t)`; add module-level `from classification import classify_duracion, hardness_index` (re-export for any future caller). The `logging.basicConfig(filename="app.log", ...)` at `:5-6` MUST stay.
  - `/home/xod/Documentos/Code/dureza_relativa/streamlit_app.py` (UNTOUCHED) — verify after refactor that `from data_processor import DataProcessor` (`streamlit_app.py:3`) and `DataProcessor().load_and_process(...)` (`:31-32`) still resolve.
- **Estimate:** ~50 LOC (45 new in `classification.py`, ~5 net delta in `data_processor.py`).
- **Commit:** `refactor(python): extract pure classification into classification.py with re-export shim` — touches `classification.py`, `data_processor.py`.
- **Done when:** `python3 -c "import classification; assert classification.classify_duracion(15.99)=='roca suave'"` exits 0; `python3 -c "import classification; assert classification.hardness_index(16)==25.0"` exits 0; `python3 -c "from data_processor import DataProcessor; assert DataProcessor().classify_duracion(15.99)=='roca suave'"` exits 0; no `app.log` is created by importing `classification` alone. Spec python S-1, S-2 satisfied. `pandas.DataFrame.apply` call shape at `data_processor.py:38-39` byte-equivalent.

### A.3 Add `tests/conftest.py` to neutralize `logging.basicConfig`

- **Title:** Install an autouse fixture that no-ops `logging.basicConfig` before any test imports `data_processor`, so the IO test path stays silent.
- **Spec linkage:** python-classification-and-testing R-3, S-3.
- **Parity-paired:** N indirectly (gate for any future `data_processor` import in tests; pure-function tests in A.4 do not depend on this).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/tests/__init__.py` (NEW, empty marker).
  - `/home/xod/Documentos/Code/dureza_relativa/tests/conftest.py` (NEW).
- **Estimate:** ~12 LOC.
- **Commit:** `test(python): add conftest that neutralizes logging.basicConfig` — touches `tests/__init__.py`, `tests/conftest.py`.
- **Done when:** `python3 -m pytest tests/test_classification.py -q` runs and `import classification` alone does NOT create `app.log` (already true without conftest; conftest is the gate for any IO test). Conftest fixture is `autouse=True` and monkey-patches `logging.basicConfig` to a no-op BEFORE any test module imports `data_processor`. Conftest itself imports neither `data_processor` nor `classification`. Spec python R-3 satisfied; spec python S-3 is explicitly exercised by A.5 (`tests/test_data_processor_io.py`).

### A.4 Add smoke test for the extracted `classification` module

- **Title:** Parametrized pytest asserting boundary cases for `classify_duracion` and segment cases for `hardness_index`.
- **Spec linkage:** python-classification-and-testing R-5, S-5.
- **Parity-paired:** Y (mirrors E.1; same boundary inputs on both stacks).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/tests/test_classification.py` (NEW).
- **Estimate:** ~45 LOC (9 boundary + 11 segment cases via `pytest.mark.parametrize`).
- **Commit:** `test(python): add classification smoke test with boundary + segment cases` — touches `tests/test_classification.py`.
- **Done when:** `python3 -m pytest tests/test_classification.py -q` exits 0; tests import only `classification` (never `data_processor`); asserts `hardness_index(16)==25.0`, `hardness_index(24)==50.0`, `hardness_index(40)==75.0`, `hardness_index(60)==100.0`; asserts at least one `classify_duracion` boundary pair per category. Spec python S-5 satisfied.

### A.5 Add IO test that imports `data_processor` under conftest-suppressed logging

- **Title:** Close the `python-classification-and-testing S-3` coverage gap by importing `data_processor` from inside a test and asserting the conftest neutralized the `logging.basicConfig` side effect.
- **Spec linkage:** python-classification-and-testing R-3, S-3.
- **Parity-paired:** N (Py-specific IO verification).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/tests/test_data_processor_io.py` (NEW).
- **Estimate:** ~30 LOC.
- **Commit:** `test(python): assert data_processor import does not write app.log under conftest` — touches `tests/test_data_processor_io.py`.
- **Done when:** `python3 -m pytest tests/test_data_processor_io.py -q` exits 0; the test uses the `tmp_path` fixture to redirect cwd into an empty directory; then `from data_processor import DataProcessor` succeeds and `DataProcessor().classify_duracion(15.99)=='roca suave'` holds (proves the re-export at `R-2` works through the IO path), and `not (tmp_path / 'app.log').exists()` holds (proves `logging.basicConfig(filename='app.log', ...)` at `data_processor.py:5-6` was no-op'd by the conftest). A `logging.basicConfig`-call recorder installed by the test shows zero calls with a `filename` keyword. Conftest `A.3` MUST already be active for this test to pass. Spec python S-3 satisfied.

---

## Phase B — Parity contract

### B.1 Curate the shared JSON parity fixture

- **Title:** Hand-curate the boundary + segment cases that lock the contract between Python and TypeScript implementations.
- **Spec linkage:** cross-stack-parity R-1, R-5, S-1, S-2, S-6.
- **Parity-paired:** Y (single source of truth for C.1 and E.2).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/tests/fixtures/parity/classification_cases.json` (NEW).
- **Estimate:** ~30 LOC (at least 8 boundary + segment cases derived from thresholds `16/24/40/60` and formulas in `data_processor.py:47-90` and `webapp/src/utils/dataProcessor.ts:38-68`).
- **Commit:** `test(parity): add shared classification_cases.json fixture` — touches `tests/fixtures/parity/classification_cases.json`.
- **Done when:** JSON parses as `{"cases": [{"input": <num>, "expected_dureza": "<str>", "expected_indice_dureza": <num>}, ...]}` with at least 8 entries; covers boundary values `0`, `15.999`, `16`, `23.999`, `24`, `39.999`, `40`, `59.999`, `60`, `61` (or equivalent exhaustive set); at least one entry uses a synthetic sentinel `expected_dureza` value (e.g., a placeholder string the parity tests can pattern-match on to confirm `expected_dureza` was loaded from JSON, not hardcoded). Spec cross-stack R-1, R-5 satisfied.

---

## Phase C — Python parity test

### C.1 Add `tests/test_parity.py`

- **Title:** Load the JSON fixture and assert every case against `classification.classify_duracion` / `classification.hardness_index`.
- **Spec linkage:** cross-stack-parity R-3, R-4, S-1, S-3, S-4; python-classification-and-testing R-6.
- **Parity-paired:** Y (the Python consumer of B.1).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/tests/test_parity.py` (NEW).
- **Estimate:** ~25 LOC.
- **Commit:** `test(python): add parity test consuming shared fixture` — touches `tests/test_parity.py`.
- **Done when:** `python3 -m pytest tests/test_parity.py -q` exits 0; every entry in `tests/fixtures/parity/classification_cases.json` is asserted; `expected_indice_dureza` uses `pytest.approx(abs=1e-9)` with a comment documenting the tolerance; failure message format is `case[{index}] input={input} expected={expected} actual={actual}` (covers spec S-4). Spec cross-stack S-1, S-3, S-4 satisfied.

---

## Phase D — TypeScript runner foundation

### D.1 Add Vitest config and npm scripts

- **Title:** Wire Vitest through the existing Vite config; declare npm scripts.
- **Spec linkage:** typescript-classification-and-testing R-2, R-5, S-3, S-6.
- **Parity-paired:** N (foundation).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/vitest.config.ts` (NEW) — `defineConfig` from `vitest/config`; merges the existing Vite plugin chain (`react()`); `test.environment='happy-dom'`, `setupFiles=['./src/test/setup.ts']`, `include=['src/**/*.{test,spec}.{ts,tsx}']`, `coverage.provider='v8'`.
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/src/test/setup.ts` (NEW, 1 LOC) — `import '@testing-library/jest-dom/vitest';`.
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/package.json` (MODIFIED) — add `scripts.test="vitest"`, `scripts.test:run="vitest run"`, `scripts.coverage="vitest run --coverage"`; add devDependencies `vitest@^2`, `@testing-library/react@^16`, `@testing-library/jest-dom@^6`, `@testing-library/user-event@^14`, `happy-dom@^15`, `@vitest/coverage-v8@^2`. Existing `vite`/`@vitejs/plugin-react` stay untouched.
- **Estimate:** ~27 LOC.
- **Commit:** `feat(webapp): add vitest config and npm test scripts` — touches `webapp/vitest.config.ts`, `webapp/src/test/setup.ts`, `webapp/package.json`.
- **Done when:** `cd webapp && npm install` completes; `cd webapp && npm run test:run` exits 0 with at least one collected test (after E.1 lands); `cd webapp && npm run build` still succeeds (existing Vite pipeline reused, no parallel transformer). Spec ts R-2, R-5 satisfied.

### D.2 Export `classifyDuration` and `hardnessIndex`

- **Title:** Add the `export` keyword to the two pure functions; no body changes.
- **Spec linkage:** typescript-classification-and-testing R-1, S-1, S-2.
- **Parity-paired:** Y (mirrors A.2; E.1 imports these).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/src/utils/dataProcessor.ts` (MODIFIED) — line 38 prefix `const` → `export const`; line 51 prefix `const` → `export const`. Bodies unchanged. Call sites at `dataProcessor.ts:119-120` unchanged.
- **Estimate:** ~2 LOC net.
- **Commit:** `feat(webapp): export classifyDuration and hardnessIndex for tests` — touches `webapp/src/utils/dataProcessor.ts`.
- **Done when:** `cd webapp && npx tsc --noEmit` exits 0; `cd webapp && npm run build` exits 0; `import { classifyDuration, hardnessIndex } from '../utils/dataProcessor'` resolves in E.1. Spec ts S-1, S-2 satisfied.

### D.3 Create the relative symlink to the shared fixture (DRIFT CORRECTION)

- **Title:** Symlink the TS-side fixture path to the Python canonical file at repo root.
- **Spec linkage:** cross-stack-parity R-2, S-2, S-5.
- **Parity-paired:** Y (consumer path for E.2).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/src/utils/__tests__/fixtures/classification_cases.json` (NEW — relative symlink).
- **Estimate:** 0 LOC (file metadata only).
- **Commit:** `test(parity): symlink ts fixture to canonical python fixture` — touches `webapp/src/utils/__tests__/fixtures/classification_cases.json`.
- **Done when:** `readlink webapp/src/utils/__tests__/fixtures/classification_cases.json` prints `../../../../../tests/fixtures/parity/classification_cases.json` (FIVE `../` levels); `cat` of the symlinked path returns the same bytes as `cat tests/fixtures/parity/classification_cases.json`.
- **DRIFT CORRECTION (mandatory):** `proposal.md:147` illustrates the symlink with FOUR `../` levels, but `cross-stack-parity R-2` and `design.md:119` mandate FIVE. **The spec is the source of truth.** Apply MUST use:
  ```
  ../../../../../tests/fixtures/parity/classification_cases.json
  ```
  Symlink math: `fixtures/` → `__tests__/` → `utils/` → `src/` → `webapp/` → `<repo root>` = five directory levels upward. Four `../` would resolve to `webapp/tests/...` and break. This drift is in `proposal.md` illustrative text only — no spec edit required; apply must use the correct five-level string.

---

## Phase E — TypeScript parity test

### E.1 Add smoke test for the exported TS functions

- **Title:** Vitest `describe`/`it` exercising boundary cases on the now-exported `classifyDuration` / `hardnessIndex`.
- **Spec linkage:** typescript-classification-and-testing R-3, S-3, S-4.
- **Parity-paired:** Y (mirrors A.4; same boundary inputs).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/src/utils/__tests__/dataProcessor.test.ts` (NEW).
- **Estimate:** ~45 LOC.
- **Commit:** `test(webapp): add dataProcessor smoke test with boundary + segment cases` — touches `webapp/src/utils/__tests__/dataProcessor.test.ts`.
- **Done when:** `cd webapp && npm run test:run` exits 0; the test file imports `{ classifyDuration, hardnessIndex } from '../dataProcessor'`; asserts `hardnessIndex(16)≈25`, `hardnessIndex(24)≈50`, `hardnessIndex(40)≈75`, `hardnessIndex(60)≈100` within `1e-9`; at least one `classifyDuration` boundary pair per category. Spec ts S-1, S-3, S-4 satisfied.

### E.2 Add TS parity test consuming the symlinked fixture

- **Title:** Load the JSON fixture through the symlink and assert every case against the exported functions.
- **Spec linkage:** cross-stack-parity R-3, R-4, R-5, S-2, S-3, S-4, S-5; typescript-classification-and-testing R-4, S-5.
- **Parity-paired:** Y (the TS consumer of B.1).
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/webapp/src/utils/__tests__/parity.test.ts` (NEW).
- **Estimate:** ~25 LOC.
- **Commit:** `test(webapp): add parity test consuming shared fixture via symlink` — touches `webapp/src/utils/__tests__/parity.test.ts`.
- **Done when:** `cd webapp && npm run test:run parity` exits 0; every entry from the symlinked JSON is asserted; `expected_indice_dureza` is compared with `Math.abs(a-b) < 1e-9` and the tolerance is documented in a comment; failure message includes `case[${index}] input=${input} expected=${expected} actual=${actual}`; the test asserts at least one known sentinel case (`input: 0.0` → `roca suave`, `0.0`) so a broken symlink fails loudly instead of silently passing with an empty array. Spec cross-stack S-2, S-3, S-4, S-5 satisfied.

---

## Phase F — Documentation and verification

### F.1 Document how to run tests in the README

- **Title:** Add a "How to run tests" section covering both stacks and a note that CI ships separately.
- **Spec linkage:** implicit (developer contract from `proposal.md:21-23`); supports verify-phase reproducibility.
- **Parity-paired:** N.
- **Files:**
  - `/home/xod/Documentos/Code/dureza_relativa/README.md` (MODIFIED) — append a new section after the existing test plan (`README.md:86-119`).
- **Estimate:** ~20 LOC.
- **Commit:** `docs(readme): add how-to-run-tests for python and webapp` — touches `README.md`.
- **Done when:** README contains a "How to run tests" section with: (a) Python recipe `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pytest -q`; (b) TypeScript recipe `cd webapp && npm install && npm test`; (c) an explicit note that GitHub Actions CI ships in the follow-up `bootstrap-ci` change. Existing test-plan section (`README.md:86-119`) stays untouched or is cross-referenced.

### F.2 Document the local verification recipe (doc-only)

- **Title:** Capture the local smoke commands so the apply and verify phases have a single source for "what to run".
- **Spec linkage:** supports apply-phase contract (per orchestrator preflight) and verify phase.
- **Parity-paired:** N.
- **Files:** no new files; captured inline in this tasks.md and referenced from F.1.
- **Estimate:** 0 LOC (documentation only — already in this file and in F.1).
- **Commit:** none (folded into F.1).
- **Done when:** the recipes below are listed in F.1's README section AND in the verify-phase preflight. Apply runs them when env is available; if env is unavailable, apply fails gracefully with this explicit command list:
  - Python: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pytest -q`
  - TypeScript: `cd webapp && npm install && npm test`
  - Both MUST pass before the change ships. Acceptance criteria AC-1..AC-10 from `proposal.md:202-214` map directly.

---

## Open questions raised by this task list

1. ✅ Resolved: **`tests/test_data_processor_io.py` injected as A.5** (~30 LOC). `python-classification-and-testing S-3` is now explicitly exercised by a test that imports `data_processor` under conftest-suppressed logging and asserts no `app.log` is created. Net delta: ~340 LOC, still under the 400-LOC budget.

2. ✅ Resolved: **Single-PR confirmed by user.** Orchestrator preflight `chained_pr_strategy: ask-always` honored; forecast ~340 LOC comfortably under budget; user confirmed `single-pr`. Apply may proceed without re-slicing.

---

## Verification preflight (for apply + verify)

Run in order. Both stacks must pass before this change ships.

```bash
# Python
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q

# TypeScript
cd webapp
npm install
npm run test:run
```

Spec coverage by command:

| Command | Spec scenarios satisfied |
|---------|--------------------------|
| `.venv/bin/pytest tests/test_classification.py -q` | python S-5 |
| `.venv/bin/pytest tests/test_parity.py -q` | cross-stack S-1, S-3, S-4; python R-6 |
| `.venv/bin/pytest tests/test_data_processor_io.py -q` | python S-3 |
| `cd webapp && npm run test:run` | ts S-1, S-2, S-3, S-4 |
| `cd webapp && npm run test:run parity` | cross-stack S-2, S-3, S-4, S-5 |
| `cd webapp && npm run build` | ts S-2 |
| `python3 -c "import classification"` (no `app.log` written) | python S-1 |
| `python3 -c "from data_processor import DataProcessor; DataProcessor().classify_duracion(15.99)"` | python S-2 |