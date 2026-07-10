# Exploration: Bootstrap Test Runner (pytest + Vitest)

**Change:** `bootstrap-test-runner`
**Date:** 2026-07-10
**Artifact store:** openspec
**Current state:** zero automated tests; `strict_tdd: false`
**Review budget:** 400 lines

## 0. Verified Environment

Verified at exploration time (read-only — no installs):

| Probe | Result | Evidence |
| --- | --- | --- |
| `python3 --version` | 3.14.6 | shell output |
| `python3 -m pytest --version` | `ModuleNotFoundError: No module named pytest` | shell output, also `config.yaml:30` |
| `pip` in PATH | not found (also `python3 -c "import pandas; ..."` -> `ModuleNotFoundError`) | shell output |
| `node --version` | 26.4.0 | shell output |
| `npm --version` | 12.0.0 | shell output |
| `webapp/node_modules/` | absent | `ls webapp/` |
| `data_processor.py` line 5 | `logging.basicConfig(filename="app.log", ...)` runs at **import time** | `data_processor.py:5-6` |
| `app.log` | 212 KB, committed despite `.gitignore` listing it | `ls -la app.log`, `.gitignore:42` |

Webapp `package.json:1-27` declares `vite@^4.4.9`, `react@^18.2.0`, `typescript@^5.2.2`, `papaparse@^5.4.1`, `react-plotly.js@^2.6.0`. No `vitest`, no `@testing-library/*`.

`README.md:77` explicitly warns that the environment has no internet access and `npm install` "may fail" — same environment is in use here. Vitest + testing-library are pure-JS (no native bindings) so the dependency footprint is lighter than pandas; still, **the bootstrap cannot self-verify with `npm test` in this offline box**.

## 1. Pure Entry Points (the "smoke test" surface)

Both stacks classify rock hardness from duration in minutes. The purest, dependency-free entry points are:

**Python (`data_processor.py`)**:

- `DataProcessor.classify_duracion(minutos)` — lines 47-55. Pure function, no `pandas`/`logging`/`IO`. Categorical: `roca suave` <16, `roca media` <24, `roca dura` <40, `roca muy dura` >=40.
- `DataProcessor.hardness_index(T)` — lines 57-90. Pure function. Returns 0 for T<0, linear 0..100 across four segments, saturates at 100 above T=60.
- These are **already correctly testable in isolation** if we can import the module without triggering `logging.basicConfig` (see risks).

**TypeScript (`webapp/src/utils/dataProcessor.ts`)**:

- `classifyDuration` — lines 38-49. **Module-private** (declared `const`, not exported).
- `hardnessIndex` — lines 51-68. **Module-private** (declared `const`, not exported).
- `normalizeColumnName` — line 8, also module-private.
- Exported: `processCsvData` (line 81), `formatDateInputValue` (line 141).

Python and TS algorithms are **byte-for-byte equivalent on the inputs that matter** (same boundaries, same formulas). Verified by reading both files: identical branch order, identical `<` vs `<=`, identical constants `[16, 24, 40, 60]`. The risk is **future drift**, not present divergence.

## 2. Runner Choice — Python: pytest

**Recommendation: pytest 8.x or 9.x.**

Evidence:
- `pytest` is the de-facto Python runner; alternatives (`unittest`, `nox`, `tox`) are either too verbose (`unittest`) or task-orchestrators (`nox`/`tox`) that wrap `pytest` underneath.
- pytest 9.0 docs explicitly support `[tool.pytest.ini_options]` in `pyproject.toml` since 6.0, and `tool.pytest` (native TOML) since 9.0. Source: `https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/customize.rst` via context7.
- "Pytest configuration options can be defined in pytest.ini, .pytest.ini, pyproject.toml, tox.ini, or setup.cfg." Source: `https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/reference.rst` via context7.
- Streaming CachyOS / Arch 3.14.6 is bleeding-edge; **pytest 9.x is required for native 3.14 wheels** (pytest 7.x/8.x were built against <=3.12). Verified published pytest version: 9.0.0 (context7).

Companion plugins to pin in `requirements-dev.txt`:
- `pytest>=9.0` (test runner).
- `pytest-cov>=5.0` (coverage; `coverage` provider is the standard).
- `pytest-mock>=3.14` (only if we need monkeypatching beyond `monkeypatch` fixture).
- `pytest-asyncio>=0.23` (not needed; Streamlit app is sync, no async paths yet).

Skip: `nox`, `tox`, `hypothesis` (out of scope; can revisit in a future change).

## 3. Runner Choice — TypeScript: Vitest

**Recommendation: Vitest (latest).**

Evidence:
- Vitest's docs explicitly recommend `defineConfig` from `'vitest/config'` and a `test: { environment, setupFiles }` block. Source: `https://github.com/vitest-dev/vitest/blob/main/docs/guide/features.md` via context7.
- Vite is already in the project (`webapp/package.json:25`, `vite@^4.4.9`). Vitest reuses the Vite config — no Babel/Jest transformer pipeline to maintain.
- React Testing Library interop: `import '@testing-library/jest-dom/vitest'` in setup file (canonical pattern).
- DOM environment: `happy-dom` is faster than `jsdom` and recommended unless the code uses DOM APIs not yet supported (file upload, FileReader, etc.). For this project the heaviest DOM user is `DataUploader.tsx` which uses a `<input type="file">` event — both `jsdom` and `happy-dom` support that; `happy-dom` will be lighter. Source: `https://github.com/vitest-dev/vitest/blob/main/docs/guide/features.md` via context7.

Alternatives considered:
- **Jest** — works with Vite via `vite-jest`, but adds a transformer that drifts from the production build. Vitest uses the same Vite plugins as `npm run dev` (Vite docs confirm this); this means component tests exercise the **same** transform as the runtime. Higher fidelity, fewer config drift bugs.
- **Node `node:test`** — built-in but lacks a watch mode that respects the Vite config; would force manual path mapping. Not a runner for React component tests with the current toolchain.

Companion packages:
- `vitest` (test runner, devDep).
- `@testing-library/react` (component testing).
- `@testing-library/jest-dom` (extended matchers, devDep only).
- `@testing-library/user-event` (user interaction simulation, for `DataUploader`).
- `happy-dom` (lighter DOM; install once). Source: `https://github.com/vitest-dev/vitest/blob/main/docs/guide/features.md` confirms `npm i -D happy-dom`.
- `@vitest/coverage-v8` (V8-native coverage, no Babel).

## 4. Configuration Files (exact paths and minimal contents)

### Python side

- **`pyproject.toml`** (new, at repo root):
  ```toml
  [project]
  name = "dureza_relativa"
  version = "0.1.0"
  requires-python = ">=3.13"

  [project.optional-dependencies]
  dev = [
    "pytest>=9.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.14",
  ]

  [tool.pytest.ini_options]
  minversion = "9.0"
  testpaths = ["tests"]
  python_files = ["test_*.py"]
  addopts = "-ra -q --strict-markers --strict-config"
  ```
  Source for the INI-options section shape: pytest docs via context7 (`https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/customize.rst`).

- **`requirements-dev.txt`** (new, sibling of `requirements.txt`): mirror the `[project.optional-dependencies].dev` block above for pip-tool/uv users. Lets `pip install -r requirements-dev.txt` work without `pyproject.toml`-aware tooling.

- **`tests/__init__.py`**: empty. Keeps the tests root importable when running with `pytest tests/`.

- **`tests/conftest.py`** (new): two responsibilities:
  1. Disable the side-effectful `logging.basicConfig` at module import time. Cleanest pattern: do NOT import `data_processor` from `conftest.py` (collect-only is fine). For tests that DO import it, use a fixture that monkey-patches `logging.basicConfig` to a no-op before the first import in the test process — see Section 9 Risks.
  2. Add the path for shared fixture JSON (`tests/fixtures/`) so parity tests can locate it.

### TypeScript side

- **`webapp/vitest.config.ts`** (new):
  ```ts
  import { defineConfig } from 'vitest/config';

  export default defineConfig({
    test: {
      environment: 'happy-dom',
      globals: false,
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html'],
        include: ['src/utils/**'],
      },
    },
  });
  ```
  Source for `defineConfig` + `environment` + `setupFiles`: `https://github.com/vitest-dev/vitest/blob/main/examples/projects/packages/client/vitest.config.ts` via context7.

- **`webapp/src/test/setup.ts`** (new, single import):
  ```ts
  import '@testing-library/jest-dom/vitest';
  ```

- **`webapp/package.json`** patches:
  - `scripts`: add `"test": "vitest"`, `"test:run": "vitest run"`, `"coverage": "vitest run --coverage"`.
  - `devDependencies`: add `vitest@^2`, `@testing-library/react@^16`, `@testing-library/jest-dom@^6`, `@testing-library/user-event@^14`, `happy-dom@^15`, `@vitest/coverage-v8@^2`.

## 5. Test Directory Layout

Mirror the source tree. Clean, no surprises:

```
.
├── pyproject.toml
├── requirements-dev.txt
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_classification.py               # pure functions only
│   ├── test_data_processor_io.py            # IO + CSV edge cases
│   └── fixtures/
│       └── parity/
│           └── classification_cases.json    # shared Python/TS fixture (see Section 6)
│
└── webapp/
    └── src/
        ├── test/
        │   └── setup.ts
        └── utils/
            ├── dataProcessor.ts
            ├── types.ts
            └── __tests__/
                ├── dataProcessor.test.ts
                └── fixtures/
                    └── classification_cases.json   # symlink OR duplicate OR shared import path
```

Symlink the TS fixture to the Python one via `webapp/src/utils/__tests__/fixtures/classification_cases.json -> ../../../../tests/fixtures/parity/classification_cases.json`. Allows **one source of truth** for parity inputs; the JSON itself is loaded by both runners with relative-path resolution.

## 6. Minimum Smoke Tests — what ships in the first slice

**Two pure-function tests per stack, ~70 LOC each.**

### Python — `tests/test_classification.py`

Smoke goal: prove pytest works, exercise the categorical boundaries, exercise the continuous index at segment joints.

1. `test_classify_duracion_boundaries` — table-driven:
   - Inputs and expected outputs (Python uses strict `<`, so `16` belongs to "roca media"):
     - `0` -> "roca suave", `15.999` -> "roca suave", `16` -> "roca media",
     - `23.999` -> "roca media", `24` -> "roca dura", `39.999` -> "roca dura",
     - `40` -> "roca muy dura", `60` -> "roca muy dura", `1e6` -> "roca muy dura".
   - 9 cases, parameterized via `pytest.mark.parametrize`.

2. `test_hardness_index_segments` — table-driven:
   - Inputs and expected outputs (formulas derived from `data_processor.py:57-90`):
     - `-1` -> 0.0 (negative guard), `0` -> 0.0, `8` -> 12.5 (`25 * 8/16`),
     - `16` -> 25.0, `20` -> 37.5 (`25 + 25 * 4/8`), `24` -> 50.0,
     - `32` -> 62.5 (`50 + 25 * 8/16`), `40` -> 75.0,
     - `50` -> 87.5 (`75 + 25 * 10/20`), `60` -> 100.0, `90` -> 100.0.
   - 11 cases.

Both tests must import only `classification` (the extracted module). **NOT** `data_processor`, to avoid `logging.basicConfig` (see Section 9).

### TypeScript — `webapp/src/utils/__tests__/dataProcessor.test.ts`

Same shape. Steps:

1. **Export the two pure functions** from `webapp/src/utils/dataProcessor.ts` by adding `export` keyword in front of `const classifyDuration = ...` and `const hardnessIndex = ...` (lines 38, 51). This is a 2-character change per function and does not alter runtime behavior — the only call sites are inside the same module (`processCsvData` at lines 119-120). Alternative: re-export via a barrel `webapp/src/utils/index.ts`. The 2-character change is simpler and stays in this slice.

2. **Smoke tests** (Vitest's `it(...)` + `describe(...)`):
   - `describe('classifyDuration')`: same 9 boundary inputs as Python.
   - `describe('hardnessIndex')`: same 11 segment inputs as Python.
   - Fixture-driven via the shared `classification_cases.json` (see next section).

This satisfies "at least one runnable test per stack that exercises shared business logic at its purest entry point" — both smoke tests target the same algorithm surface, with the same inputs, expecting the same outputs.

## 7. Cross-Stack Parity Strategy

**Recommended: shared JSON contract + parameterized equality test in both runners.**

Shape: `tests/fixtures/parity/classification_cases.json` (a single file, ~30 LOC):
```json
{
  "cases": [
    { "input": 0.0,    "expected_dureza": "roca suave",       "expected_indice_dureza": 0.0 },
    { "input": 15.999, "expected_dureza": "roca suave",       "expected_indice_dureza": 24.984375 },
    { "input": 16.0,   "expected_dureza": "roca media",       "expected_indice_dureza": 25.0 },
    ... (one row per smoke-test case, ~15 cases total) ...
  ]
}
```

Both test runners load this JSON at test time:

- Python `test_parity` test: `json.loads(...)` -> iterate cases -> call `classify_duracion` and `hardness_index` -> assert exact match for `expected_dureza`, `pytest.approx` for `expected_indice_dureza` (avoids float-rounding false positives).
- TS `parity` test: `import json from '...'; JSON.parse(...)` -> iterate -> call `classifyDuration` and `hardnessIndex` -> same assertions.

**Why this and not the alternatives:**

| Strategy | Effort | Drift detection | Maintenance |
| --- | --- | --- | --- |
| **Shared JSON contract (RECOMMENDED)** | Low — 1 file + 2 tests, ~50 LOC total | Catches divergence at the unit level (fastest feedback) | One source of truth for thresholds; reviewable in PRs |
| Snapshot tests (`toMatchSnapshot`) | Medium | Catches drift but the snapshot is **regenerated** on changes, hiding intentional deviations | Fragile; second-best for this use case |
| Property-based (Hypothesis + fast-check) | High — new runtime deps in both ecosystems, more schemas | Excellent, but overkill for ~10 boundary values | Excessive complexity for finite algorithm |
| End-to-end "same CSV -> same JSON outputs" | High — requires shared CSV format, agreed output schema, harness to run both processes | Catches all parity issues (including date-format drift) | Real, but blocked by Section 9 Risk #5 (CSV/date format disagreement); defer to a follow-up slice |

End-to-end CSV-in/JSON-out parity is the **right long-term answer** but blocked on a concrete obstacle: Python `pd.to_datetime("2024/05/10 08:30")` accepts slash-separated dates (verified manually against the example data — `ejemplo_datos.txt` uses that format), while JavaScript `new Date("2024/05/10 08:30")` is **locale-dependent and unreliable**. Until both stacks agree on a CSV dialect (ISO 8601 recommended), end-to-end parity tests will produce false-positive failures. Lock the date format in a follow-up change; for the bootstrap, JSON-level parity is sufficient and self-contained.

## 8. CI Readiness — split into a follow-up slice

Recommendation: **defer GitHub Actions to a follow-up change (`bootstrap-ci`)**. Rationale:

- The README's test plan (`README.md:114-119`) explicitly names two GH jobs. Bootstrap is already large enough at ~250 LOC.
- GH workflow yaml requires reviewers to grok matrix strategy, caching, Python 3.14 wheel availability, and Node version pinning — separate discussion.
- The smoke tests have **value even without CI** during the bootstrap window: local `pytest tests/ -q` and `npm run test:run` become the developer's contract. CI is the enforcement layer, but the tests can land first.
- Bootstrapping tests creates a clean baseline; CI on top of failing-then-passing tests avoids chasing merged failures.

When CI lands, ~50 LOC for `.github/workflows/tests.yml` with two jobs (`python-tests` matrix Python 3.13/3.14, `webapp-tests` on Node 20 LTS). Bootstrap should NOT include this.

## 9. Order of Work & Parallelization

```
PHASE 1 — config + scaffolding (parallel)
   A1. Create pyproject.toml + requirements-dev.txt
   A2. Create webapp/vitest.config.ts + webapp/src/test/setup.ts
       Add vitest/RTL/happy-dom to webapp/package.json devDependencies
       Add npm scripts (test, test:run, coverage)

PHASE 2 — make logic testable (parallel)
   B1. Refactor data_processor.py — extract classify_duracion + hardness_index
       into a new classification.py module. Keep DataProcessor as the
       IO orchestrator. data_processor.py keeps the logging.basicConfig
       line so run-time behavior is unchanged. (Alternative: skip the
       refactor and instead drop a conftest.py that monkey-patches
       logging.basicConfig before import; log file gets nuked between
       test runs. See Risks #1 for the trade.)
   B2. Add `export` keyword to classifyDuration and hardnessIndex in
       webapp/src/utils/dataProcessor.ts (lines 38 and 51). No logic change.

PHASE 3 — smoke tests (parallel)
   C1. Write tests/test_classification.py (parametrized classification +
       hardness_index tests against the new classification.py module).
   C2. Write webapp/src/utils/__tests__/dataProcessor.test.ts (mirror of C1).
       Both should `pip install -r requirements-dev.txt` and
       `npm install` (vitest/RTL/happy-dom).

PHASE 4 — parity (parallel)
   D1. Author tests/fixtures/parity/classification_cases.json.
   D2. Add tests/test_parity.py — loads JSON, asserts both functions
       equal expected.
   D3. Add webapp/src/utils/__tests__/parity.test.ts — mirrors D2.
   D4. Symlink the JSON into webapp/src/utils/__tests__/fixtures/.

PHASE 5 — verification (single)
   E1. Run `python -m pytest tests/ -q` locally. Run
       `cd webapp && npm run test:run`. Capture results.

PHASE 6 (separate change) — CI
   F1. New change `bootstrap-ci` adds .github/workflows/tests.yml.
```

Per-phase size estimate (changed/added LOC):

| Phase | Files | New LOC | Notes |
| --- | --- | --- | --- |
| 1 | 4 files | ~40 | pyproject + requirements-dev + vitest.config + setup.ts |
| 2 | 1 file modified, 1 new | ~40 | refactor + 2 keywords |
| 3 | 2 files | ~80 | smoke tests in both stacks |
| 4 | 1 fixture + 2 tests | ~60 | parity JSON + 2 parity tests |
| 5 | — | 0 | verification only |
| **TOTAL bootstrap slice** | ~9 files | **~220** | comfortably under 400 |

CI (separate change) would add another ~50 LOC and is independently reviewable.

## 10. Risks & Open Questions

1. **`logging.basicConfig` runs at module import** (`data_processor.py:5-6`). Any test that imports `data_processor` will create or overwrite `app.log`. Two resolutions:
   - **(a) Refactor:** extract pure functions into `classification.py`. `data_processor.py` becomes the IO orchestrator. Cleanest. ~30 LOC move, no behavioral change at runtime (logging still configures when the orchestrator is imported).
   - **(b) Patch in conftest.py:** add `conftest.py` with `import logging; logging.basicConfig = lambda *a, **k: None` BEFORE any test imports `data_processor`. Works in-process; brittle if pytest ever splits import collection. ~5 LOC.
   - **(c) Use `tmp_path`:** write to `capsys`-captured stream — but `basicConfig` only honors the filename arg, so this doesn't redirect; the log file is still created.
   Recommended: (a). It also kills two latent bugs: `basicConfig` is a no-op if the root logger is already configured, and tests are sensitive to import order. Extracting pure functions is good architecture, not just testability.

2. **`app.log` is committed (212 KB)** despite `.gitignore:42`. Cleanup commit is out of scope for this slice (separate, one-liner: `git rm --cached app.log`). Calling it out so the change does not silently mix concerns.

3. **Python 3.14 wheel availability.** Confirmed pytest 9.0 supports Python 3.14 (context7 lookup). `pandas 3.x` should support 3.14 as of mid-2026 (unverified — flag in task list). If `pip install pandas` fails on Python 3.14, fall back to the upstream `uv` workflow: `uv venv && uv pip install -r requirements-dev.txt`. `uv` was not found in PATH during exploration; bootstrap may need to install it first.

4. **`pip` is not in PATH** on this box. Bootstrap will need `python3 -m ensurepip --upgrade` or a venv (`python3 -m venv .venv`). Verify before the apply phase; if `ensurepip` is missing on the system image, the apply step ships an explicit `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` recipe.

5. **CSV/date format divergence between stacks.** Python's `pd.to_datetime` accepts `2024/05/10 08:30` (the example's format). JS `new Date("2024/05/10 08:30")` is implementation-defined (Safari historically rejects). This blocks end-to-end CSV parity. **Defer to a follow-up change** (`lock-csv-format` or migrate `ejemplo_datos.txt` to ISO 8601). For the bootstrap slice, parity is at the classification-function level only (numeric minutes in, categorical + scalar out), so this is **not a blocker**.

6. **Offline network.** `README.md:77` warns of no-internet `npm install`. Vitest/RTL/happy-dom are pure JS — lighter than pandas. Still, on this box: bootstrapping cannot be verified by the orchestrator. Recommend the user runs the apply on a machine with internet, OR have the bootstrap step also include `package-lock.json` / `pip freeze > constraints.txt` commit conventions so that offline repro is possible later.

7. **TS classification functions are private.** Currently `const classifyDuration` and `const hardnessIndex` (`webapp/src/utils/dataProcessor.ts:38, 51`). Adding `export` is a contract change — flagged in Phase 2 step B2. Alternative (extracting to a separate `classification.ts` module) is more invasive but more architecturally pure; flagged as a follow-up choice.

8. **`strict_tdd: false` will remain false** until Vitest+RTL also produce at least one passing test. Bootstrap pins pytest+Vitest with passing smoke tests; flipping the flag is a one-line config change in `openspec/config.yaml` after the verify phase passes.

9. **CI matrix Python version.** GitHub's `actions/setup-python` does not yet have a verified 3.14 stable release on every image — when CI lands, pin `python-version: ["3.13", "3.14"]` and confirm 3.14 wheels exist for `pandas`, `streamlit`, `plotly`. Out of scope here but called out for the CI slice.

### Open questions for the orchestrator / user

- **(Q1)** Approve Option (a) for Risk #1 (refactor `data_processor.py` into `classification.py` + IO orchestrator) vs. Option (b) (conftest patch)? Prefer (a) — it improves testability AND architecture.
- **(Q2)** Should the parity fixture live at repo root (`tests/fixtures/parity/`) symlinked into `webapp/src/utils/__tests__/fixtures/`, OR duplicated for simpler off-repo CI caching? Recommend symlinked single-source.
- **(Q3)** Should we commit `package-lock.json` and a `pip freeze constraints.txt` even though this dev box has no internet — to enable later offline repro? Out of strict scope but cheap.
- **(Q4)** Is CI in this slice or the next? Recommended: next.

## Sources

- pytest docs via context7:
  - `https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/customize.rst` — `[tool.pytest.ini_options]` shape, `testpaths`, `addopts`.
  - `https://github.com/pytest-dev/pytest/blob/main/doc/en/reference/reference.rst` — config file precedence.
  - Library ID `/pytest-dev/pytest` (v9.0.0).
- Vitest docs via context7:
  - `https://github.com/vitest-dev/vitest/blob/main/docs/guide/features.md` — `environment`, `setupFiles`, `npm i -D happy-dom` / `jsdom`.
  - `https://github.com/vitest-dev/vitest/blob/main/examples/projects/packages/client/vitest.config.ts` — `defineConfig` example.
  - Library ID `/vitest-dev/vitest` (v4.1.6).
- Repo evidence:
  - `data_processor.py:1-90` — current Python implementation; pure functions at lines 47-55, 57-90.
  - `webapp/src/utils/dataProcessor.ts:1-146` — current TS implementation; pure functions at lines 38-49, 51-68 (both currently unexported).
  - `webapp/package.json:1-27` — current dependencies; vitest/RTL absent.
  - `requirements.txt:1-13` — current Python deps; pytest not listed.
  - `README.md:86-119` — explicitly documented test plan referencing pytest, Vitest+RTL, GitHub Actions.
  - `openspec/config.yaml:25-36` — testing capabilities (none).
  - `openspec/project-context.md:1-138` — project context and risks.
  - `.gitignore:42` — declares `app.log`, which is nevertheless committed (212 KB).
