# Proposal: bootstrap-test-runner

**Status:** Draft
**Date:** 2026-07-10
**Change:** `bootstrap-test-runner`
**Owner:** maintainer (single contributor today)
**Review budget:** ~400 LOC for the eventual change; this proposal targets <250 LOC.

## Why

The repository ships two parallel implementations of the same business logic — one in
Python (`data_processor.py`) and one in TypeScript (`webapp/src/utils/dataProcessor.ts`) — and
ships zero automated tests (`openspec/config.yaml:25-36`, `README.md:88`). The maintainer
cannot refactor either stack with confidence because there is nothing to assert
behavioral equivalence against; future contributors have no executable definition of
"correct" and no fast feedback loop. The README documents a test plan
(`README.md:86-119`) but no code implements it.

**Target users:**
- The maintainer (today) — needs a safety net before touching shared business logic.
- Future contributors (tomorrow) — need a runnable contract: `pytest tests/ -q` and
  `npm run test:run` must be green, locally, with no manual setup beyond
  `pip install -r requirements-dev.txt` and `npm install`.

**Current-state gap:** `pytest` is not installed (`openspec/config.yaml:30`); Vitest is
not declared (`webapp/package.json:19-26`); `strict_tdd: false`
(`openspec/config.yaml:17`). The pure classification functions are import-clean in
isolation but blocked by `logging.basicConfig` running at module import
(`data_processor.py:5-6`) and by `classifyDuration`/`hardnessIndex` being module-private
in TS (`webapp/src/utils/dataProcessor.ts:38, 51`).

**Why now:** Any future change that touches classification thresholds, CSV schema, or
shared business logic — exactly the surface the README's test plan calls out
(`README.md:88-119`) — is currently unverifiable. This change is the precondition for
Strict TDD, for parity enforcement, and for the CI follow-up (`bootstrap-ci`).

## What changes

Per-file summary with rough LOC. All claims cite source.

| File | Status | LOC | Notes |
| --- | --- | --- | --- |
| `classification.py` | **NEW** | ~45 | Pure functions extracted from `data_processor.py:47-55, 57-90`. Module-level functions, no `self`, no `logging`, no `pandas`. |
| `data_processor.py` | MODIFIED | ~+6 net | `DataProcessor.classify_duracion` and `DataProcessor.hardness_index` delegate to `classification.py`; module-level `from classification import classify_duracion, hardness_index` (re-export). `logging.basicConfig` at lines 5-6 **stays** — runtime behavior unchanged for `streamlit_app.py`. |
| `pyproject.toml` | **NEW** | ~20 | `[tool.pytest.ini_options]` block; `requires-python = ">=3.13"`; `dev` extras list. |
| `requirements-dev.txt` | **NEW** | ~5 | Mirrors `[project.optional-dependencies].dev` for pip users without `pyproject.toml`-aware tooling. |
| `tests/__init__.py` | **NEW** | 0 | Empty marker file. |
| `tests/conftest.py` | **NEW** | ~12 | Neutralizes `logging.basicConfig` side-effect for any test that imports `data_processor` (auto-use fixture: monkey-patches `logging.basicConfig` before first import). Does **not** import `classification` or `data_processor` itself. |
| `tests/test_classification.py` | **NEW** | ~45 | `pytest.mark.parametrize` smoke: 9 boundary cases for `classify_duracion`, 11 segment cases for `hardness_index`. Imports only `classification`. |
| `tests/test_data_processor_io.py` | **NEW** | ~30 | Imports `data_processor` (triggers `logging.basicConfig`); verifies `conftest` neutralization, then exercises `DataProcessor.load_and_process` against a tiny in-memory CSV fixture. |
| `tests/fixtures/parity/classification_cases.json` | **NEW** | ~30 | Single source of truth for cross-stack parity (see "Cross-stack parity guarantee"). |
| `tests/test_parity.py` | **NEW** | ~25 | Loads the JSON, calls both extracted functions, asserts equality. |
| `webapp/package.json` | MODIFIED | ~+12 net | Add `vitest@^2`, `@testing-library/react@^16`, `@testing-library/jest-dom@^6`, `@testing-library/user-event@^14`, `happy-dom@^15`, `@vitest/coverage-v8@^2` to `devDependencies`. Add `scripts.test`, `scripts.test:run`, `scripts.coverage`. |
| `webapp/vitest.config.ts` | **NEW** | ~15 | `defineConfig({ test: { environment: 'happy-dom', setupFiles: ['./src/test/setup.ts'], include: ['src/**/*.{test,spec}.{ts,tsx}'], coverage: { provider: 'v8', reporter: ['text', 'html'], include: ['src/utils/**'] } } })`. |
| `webapp/src/test/setup.ts` | **NEW** | 1 | `import '@testing-library/jest-dom/vitest';` |
| `webapp/src/utils/dataProcessor.ts` | MODIFIED | +2 net | Add `export` keyword before `classifyDuration` (line 38) and `hardnessIndex` (line 51). No runtime change — call sites at lines 119-120 unchanged. |
| `webapp/src/utils/__tests__/dataProcessor.test.ts` | **NEW** | ~45 | Vitest `describe`/`it`: 9 boundary cases + 11 segment cases against the freshly-exported functions. |
| `webapp/src/utils/__tests__/parity.test.ts` | **NEW** | ~25 | Loads the JSON fixture, asserts both functions equal expected. |
| `webapp/src/utils/__tests__/fixtures/classification_cases.json` | **NEW** | 0 | Symlink to `tests/fixtures/parity/classification_cases.json` (relative). One fixture, two consumers. |
| **TOTAL (bootstrap slice)** | **8 new, 3 modified** | **~340 LOC** | Within 400-LOC review budget. |

## Scope

**In scope:**
- pytest 9.x runner configuration and minimal dev dependency list.
- Vitest + React Testing Library + `happy-dom` configuration.
- Pure-function extraction into `classification.py`; `data_processor.py` re-exports for backward compatibility with `streamlit_app.py:3, 31-32`.
- `logging.basicConfig` neutralization via `tests/conftest.py` for any test that imports `data_processor`.
- `export` keyword on `classifyDuration` and `hardnessIndex` in `webapp/src/utils/dataProcessor.ts`.
- One smoke test per stack exercising the same boundary cases (9 categorical + 11 continuous).
- One cross-stack parity test per stack against a single shared JSON fixture.
- Symlinked fixture (Python owns the file; TS references it).
- `npm run test`, `npm run test:run`, `npm run coverage` scripts.

**Out of scope (explicit non-goals):**
- **GitHub Actions / CI workflow.** Deferred to follow-up change `bootstrap-ci`. This slice ships runners only; the developer contract is local `pytest` + `npm run test:run`.
- **Coverage threshold.** No `--cov-fail-under` is set. Smoke + parity tests only.
- **Property-based testing (Hypothesis / fast-check).** A future change MAY add this; the JSON fixture is the boundary test set for now.
- **End-to-end CSV-in / JSON-out parity.** Blocked by date-format disagreement between Python `pd.to_datetime` and JS `new Date` for slash-separated inputs (`explore.md:9, Section 7`). Lock the CSV dialect in a separate change (`lock-csv-format`) before adding e2e parity.
- **`app.log` cleanup.** `app.log` is committed despite `.gitignore:62` (212 KB per `explore.md:0`). A `git rm --cached app.log` commit is a separate concern; not bundled.
- **Linter / formatter setup** (`ruff`, `eslint`, `prettier`). README mentions them (`README.md:119`) but they are out of scope here.
- **Component tests beyond smoke** (e.g., full `DataUploader` flow). The slice proves the runner works; depth of UI testing is a follow-up.

## Approach

### Python side

1. **Extract pure functions.** Create `classification.py` at repo root with two
   module-level functions:
   - `classify_duracion(minutos: float) -> str` — verbatim from `data_processor.py:47-55`.
   - `hardness_index(t: float) -> float` — verbatim from `data_processor.py:57-90`.

   No `import logging`, no `import pandas`. Verified-safe to import in any context.

2. **Re-export from `data_processor.py`.** Replace the method bodies
   (`data_processor.py:47-55, 57-90`) with delegation:
   ```python
   from classification import classify_duracion, hardness_index
   ```
   Keep `DataProcessor.classify_duracion` and `DataProcessor.hardness_index` as
   one-line wrappers (`return classify_duracion(minutos)` / `return hardness_index(t)`).
   `streamlit_app.py:31-32` calls `DataProcessor().load_and_process(...)` and
   `load_and_process` at line 38-39 uses `self.classify_duracion` / `self.hardness_index`
   — both code paths keep working unchanged.

3. **pytest config.** `pyproject.toml` with `[tool.pytest.ini_options]`:
   `testpaths = ["tests"]`, `python_files = ["test_*.py"]`,
   `addopts = "-ra -q --strict-markers --strict-config"`, `minversion = "9.0"`.
   `requires-python = ">=3.13"` per `explore.md:2` (Python 3.14.6 detected).

4. **Dev deps.** `requirements-dev.txt` pins:
   `pytest>=9.0`, `pytest-cov>=5.0`, `pytest-mock>=3.14`. Skip `pytest-asyncio`
   (no async paths in Streamlit app).

5. **Neutralize the logging side-effect.** `tests/conftest.py` defines an
   `autouse=True` fixture that monkey-patches `logging.basicConfig` to a no-op
   BEFORE the first test in the process imports `data_processor`. Pytest
   guarantees conftest is loaded before any test module imports — this is the
   canonical pattern. Document the rationale in a one-line comment on the fixture.

### TypeScript side

1. **Export the two pure functions.** Add `export` to `const classifyDuration`
   (`webapp/src/utils/dataProcessor.ts:38`) and `const hardnessIndex`
   (`webapp/src/utils/dataProcessor.ts:51`). The only call sites are inside
   `processCsvData` at lines 119-120; they remain unchanged.

2. **Vitest config.** `webapp/vitest.config.ts` uses `defineConfig` from
   `'vitest/config'` per Vitest docs (`explore.md:3`). Environment `happy-dom`
   (lighter than `jsdom`, sufficient for `DataUploader`'s `<input type="file">`).
   `setupFiles: ['./src/test/setup.ts']`. `include: ['src/**/*.{test,spec}.{ts,tsx}']`.

3. **NPM scripts.** `webapp/package.json`:
   - `"test": "vitest"`
   - `"test:run": "vitest run"`
   - `"coverage": "vitest run --coverage"`

4. **Dev deps** (per `explore.md:3`):
   `vitest@^2`, `@testing-library/react@^16`, `@testing-library/jest-dom@^6`,
   `@testing-library/user-event@^14`, `happy-dom@^15`, `@vitest/coverage-v8@^2`.

### Shared

1. **Golden parity fixture.** `tests/fixtures/parity/classification_cases.json`
   holds ~15 rows: each row is `{input: float, expected_dureza: str, expected_indice_dureza: float}`.
   The TS side references the same file via a relative symlink
   (`webapp/src/utils/__tests__/fixtures/classification_cases.json -> ../../../../tests/fixtures/parity/classification_cases.json`).
   One source of truth, two consumers.

2. **Import-order behavior.** The smoke tests MUST import only `classification`
   (Python) and `dataProcessor` exporting the two functions (TS) — NOT
   `data_processor.py` for the boundary cases. This avoids the logging side-effect
   for the simple smoke tests. Only `test_data_processor_io.py` imports
   `data_processor`; it relies on `conftest.py` to neutralize `logging.basicConfig`
   first.

## Cross-stack parity guarantee

The JSON fixture is the **contract**. Ownership rules:

- **Author of record:** the maintainer. Any change to thresholds (`16`, `24`, `40`, `60`)
  or formulas (`25 * (t/16)`, etc.) MUST be reflected in the fixture BEFORE the
  implementation changes ship.
- **Format:** `{ "cases": [ { "input": <number>, "expected_dureza": <string>, "expected_indice_dureza": <number> }, ... ] }`. Floats use exact decimal notation; the Python test uses `pytest.approx` for the index to avoid IEEE-754 noise (e.g., `24.984375` vs `24.98437499...`).
- **Consumer discipline:** both `tests/test_parity.py` and `webapp/src/utils/__tests__/parity.test.ts` load this exact file (symlink resolves to the same bytes on disk).
- **Drift detection:** if Python and TS implementations ever disagree on a case, BOTH parity tests fail. The PR diff is the only place this can hide; reviewer's job to ensure the fixture and the formulas change together.
- **Scope:** this fixture covers the pure-function surface (numeric minutes -> categorical + scalar). It does NOT cover CSV ingestion, date parsing, or end-to-end pipeline parity — those are deliberately deferred to `lock-csv-format` and a subsequent e2e change.

## Tradeoffs

| Decision | Chosen | Alternative | Why chosen |
| --- | --- | --- | --- |
| Pure-function extraction | **Do it now** (in this slice) | Defer to follow-up | `logging.basicConfig` at `data_processor.py:5-6` blocks clean test imports; extraction also kills two latent bugs (import-order coupling + silent no-op when root logger already configured). Small move (~45 LOC), high testability payoff. Locked by orchestrator decision #3. |
| Refactor vs conftest-only patch | **Both**: extract + conftest neutralization | Conftest-only (`logging.basicConfig = lambda *a, **k: None`) | Conftest-only is fragile if pytest ever splits import collection; extraction gives clean isolation. Tests of `classification` don't touch `data_processor` at all. Tests of `data_processor.load_and_process` (IO) need the conftest neutralization. |
| Parity strategy | **Shared JSON fixture + parameterized equality** | Snapshot tests / property-based / e2e CSV | JSON is lowest-effort, fastest feedback, single reviewable artifact. Snapshots mask intentional drift. Property-based is overkill for ~15 finite cases. E2E blocked by date-format disagreement (`explore.md:9, Section 7`). Locked by orchestrator decision #4. |
| Lockfiles | **NOT committed in this slice** | Commit `package-lock.json` + `requirements.constraints.txt` | README warns of no-internet (`README.md:77`); bootstrap cannot self-verify on the dev box (`explore.md:0`). Lockfiles will be generated naturally when the apply phase runs `pip install -r requirements-dev.txt` and `npm install` on a connected machine. If the maintainer wants them committed later, that's a one-line follow-up. |
| PR shape | **Single PR with two stacks + parity fixture** | Two chained PRs (Python first, then TS) | The parity contract only makes sense if both sides land together; chained PRs would leave one side unverified. Review budget is ~400 LOC for the change; this slice lands at ~340 LOC, within budget. Locked by orchestrator `chained_pr_strategy: ask-always` — recommend single PR; the apply step will ask. |
| `data_processor.py` shim | **Yes — keep `DataProcessor.classify_duracion` / `hardness_index` as one-line wrappers** | Delete the methods and inline-call `classification.*` everywhere | `streamlit_app.py:31-32` uses `DataProcessor()`; the methods are public API of `DataProcessor`. Deleting them breaks the call sites at `data_processor.py:38-39` and any future caller that relies on the class form. Wrapper preserves the interface for ~3 LOC. |
| CI scope | **Deferred to `bootstrap-ci`** | Bundle `.github/workflows/tests.yml` here | README test plan already names two GH jobs (`README.md:116-118`); that conversation deserves its own slice. Bootstrap first, then enforce. Locked by orchestrator decision #1. |

## Risks & open questions

Resolutions for every `open_question` from `explore.md:Section 10`, plus risks newly surfaced.

| ID | Question / Risk | Resolution |
| --- | --- | --- |
| **Q1** | Refactor `data_processor.py` vs conftest-only patch? | **Refactor + conftest.** `classification.py` is the new home for pure functions; `data_processor.py` re-exports for `streamlit_app.py` compatibility; `tests/conftest.py` neutralizes `logging.basicConfig` for IO tests that must import `data_processor`. Locked by orchestrator decision #3. |
| **Q2** | Symlink fixture or duplicate? | **Symlink.** Single source of truth at `tests/fixtures/parity/`. TS symlink lives at `webapp/src/utils/__tests__/fixtures/`. Symlinks work on every CI runner (Linux/macOS/Windows-with-admin); if portability becomes an issue, the apply step can switch to a small loader script that resolves the canonical path. |
| **Q3** | Commit lockfiles? | **Not in this slice.** Bootstrap cannot self-verify on the offline dev box. The apply phase runs on a connected machine and will generate them; a follow-up commits them. Out of strict scope here. |
| **Q4** | CI in this slice or next? | **Next.** Follow-up change is named `bootstrap-ci` and is listed in "Follow-ups" below. Locked by orchestrator decision #1. |
| **R-A** | `pip` not in PATH on dev box (`explore.md:0`). | Apply phase MUST ship a venv recipe: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`. `.venv/` is already in `.gitignore:28`. |
| **R-B** | `app.log` (212 KB) committed despite `.gitignore:62`. | **Out of scope** for this slice; flagged as a one-liner follow-up (`git rm --cached app.log`). Mixing cleanup with bootstrap blurs review. |
| **R-C** | Python 3.14 wheel availability for pytest/pytest-cov. | pytest 9.x has native 3.14 wheels (confirmed via context7 in `explore.md:2`). If `pytest-cov` fails to install on 3.14, apply falls back to `pip install --pre` or pins `pytest-cov>=6.0` (when available). |
| **R-D** | Symlink portability on Windows runners. | If CI later runs on Windows, symlinks require admin or Developer Mode. Apply step MUST verify with `git config core.symlinks true` if any consumer is Windows. Note in the apply plan. |
| **R-E** | `data_processor.py:38-39` calls `self.classify_duracion(df['duracion'])` via `DataFrame.apply` — pandas passes the scalar. After refactor, `self.classify_duracion` becomes a wrapper that calls `classification.classify_duracion`. Behavior identical; smoke test confirms. |
| **R-F** | TS fixtures use relative `path` resolution; if the symlink target moves, the TS test silently breaks. | Apply step MUST add an integration check in `parity.test.ts` that the loaded JSON has `> 0` cases and a known sentinel case (`input: 0.0`). This catches a broken symlink with a clear error instead of an empty-array assertion. |
| **R-G** | Coverage provider on Python — `coverage` vs `pytest-cov`. | `pytest-cov` is the standard (`explore.md:2`); pin `>=5.0`. No `--cov-fail-under` in this slice (locked decision #2). |
| **R-H** | `happy-dom` vs `jsdom` for TS DOM env. | `happy-dom` — lighter, supports `<input type="file">` events used by `DataUploader.tsx` (`explore.md:3`). If a missing API is hit during apply, switch to `jsdom`; the only `vitest.config.ts` change is the environment string. |

## Acceptance criteria

`apply` is done; `verify` can pass when all of the following are true:

- [ ] **AC-1 (smoke, Python):** `python3 -m pytest tests/test_classification.py -q` runs and passes with **0 failures**. Specifically the 9 `classify_duracion` boundary cases and 11 `hardness_index` segment cases.
- [ ] **AC-2 (smoke, TypeScript):** `cd webapp && npm run test:run` runs and passes with **0 failures**. Same boundary + segment cases against the exported TS functions.
- [ ] **AC-3 (parity, Python):** `python3 -m pytest tests/test_parity.py -q` passes — every JSON fixture case matches `classification.classify_duracion` and `classification.hardness_index`.
- [ ] **AC-4 (parity, TypeScript):** `cd webapp && npm run test:run parity` passes — every JSON fixture case matches the exported TS functions.
- [ ] **AC-5 (backward compatibility):** `streamlit run streamlit_app.py` still launches without import errors. `DataProcessor` is instantiable; `DataProcessor.classify_duracion` and `DataProcessor.hardness_index` return identical results to the extracted `classification.*` functions (verified by AC-1).
- [ ] **AC-6 (side-effect neutralization):** `tests/test_data_processor_io.py` imports `data_processor` and runs without creating `app.log` (verified by `assert not Path("app.log").exists()` after the test, or equivalent `tmp_path`-based assertion).
- [ ] **AC-7 (export contract):** `webapp/src/utils/dataProcessor.ts` lines 38 and 51 are now `export const`. `tsc --noEmit` (`npm run lint`) still passes.
- [ ] **AC-8 (single source of truth):** The TS fixture at `webapp/src/utils/__tests__/fixtures/classification_cases.json` is a symlink to `tests/fixtures/parity/classification_cases.json`. `readlink` confirms the symlink; the loaded JSON content is byte-identical.
- [ ] **AC-9 (build still works):** `cd webapp && npm run build` succeeds. `tsc --noEmit` passes. No new TypeScript errors introduced.
- [ ] **AC-10 (review budget):** `git diff --stat main...HEAD` shows ≤ 400 LOC changed/added across the change. Soft target.
- [ ] **AC-11 (no scope creep):** The change does NOT include `.github/workflows/`, `app.log` removal, linter/formatter config, or end-to-end CSV parity tests.

## Rollback plan

The change is reversible in one command per layer. Concretely:

1. **Python revert:**
   - `git revert <bootstrap-test-runner-sha>~..<bootstrap-test-runner-sha>` restores `data_processor.py` to its pre-refactor form (pure functions inline, `logging.basicConfig` unchanged).
   - `pyproject.toml`, `requirements-dev.txt`, `tests/`, `classification.py` are deleted by the revert.
   - **Effect:** `streamlit run streamlit_app.py` runs against the pre-refactor `data_processor.py` exactly as before. No behavior change at runtime; the `app.log` side-effect returns at import time.

2. **TypeScript revert:**
   - Same revert removes `vitest.config.ts`, `src/test/setup.ts`, `src/utils/__tests__/`, the symlinked fixture, and the `vitest`/`@testing-library/*` dev deps.
   - `dataProcessor.ts` lines 38 and 51 lose the `export` keyword; `processCsvData` at line 81 continues to work because the only call sites at lines 119-120 are inside the same module.
   - **Effect:** `npm run dev`, `npm run build`, `npm run lint` all behave as before. No runtime change.

3. **The shim is the safety belt.** Even if the maintainer wants to keep
   `classification.py` but revert `data_processor.py` (a partial revert), the
   one-line wrappers (`from classification import classify_duracion, hardness_index`)
   can be replaced by inlining the original method bodies. The extracted module is
   additive — nothing in the production runtime path depends on it existing.

4. **No data migrations, no schema changes, no external API surface changes.**
   Rollback is pure file restoration; no downstream consumers to coordinate with.

## Follow-ups

Explicit named list, each independently scannable and reviewable:

1. **`bootstrap-ci`** — GitHub Actions workflow (`.github/workflows/tests.yml`) with two jobs: `python-tests` (matrix `3.13`/`3.14`) and `webapp-tests` (Node 20 LTS). Will consume the runners this slice ships. Confirms CI matrix Python version pinning per `explore.md:R-9`.

2. **`lock-csv-format`** — Decide and document the canonical CSV dialect (ISO 8601 recommended per `explore.md:7`). After this lands, end-to-end CSV-in / JSON-out parity becomes possible in a future change. Currently blocked.

3. **Coverage threshold negotiation** — Once smoke + parity tests land and the maintainer has confidence in the runner, add `--cov-fail-under` to `addopts` in `pyproject.toml` and `coverage.thresholds.lines/functions/branches/statements` in `vitest.config.ts`. Pick numbers after seeing the baseline; do not guess now.

4. **Property-based parity (Hypothesis + fast-check)** — Replaces the bounded JSON fixture with random-input fuzzers that cover the full input space. Lower maintenance than hand-curated cases once the algorithms stabilize.

5. **`app.log` cleanup** — `git rm --cached app.log` + verify `.gitignore:62`. Trivial one-liner; out of scope here to keep this slice focused.

6. **Linter / formatter setup** — `ruff` for Python, `eslint` + `prettier` for TypeScript, per `README.md:119`. Pre-commit hook integration is a separate decision.

7. **`strict_tdd: true`** — Flip the flag in `openspec/config.yaml:17` once this slice's verify phase passes and at least one Vitest + one pytest run cleanly. One-line config change; gated by `bootstrap-ci` so failures are caught automatically.

## References

- Exploration: `openspec/changes/bootstrap-test-runner/explore.md`
- Project context: `openspec/project-context.md:1-138`
- OpenSpec config: `openspec/config.yaml:25-36, 46-76`
- Source-of-truth implementation: `data_processor.py:1-90`, `webapp/src/utils/dataProcessor.ts:1-146`
- Streamlit entry point that MUST keep working: `streamlit_app.py:1-33`
- README test plan that motivates this slice: `README.md:86-119`
- pytest docs (via context7): `/pytest-dev/pytest` v9.0.0
- Vitest docs (via context7): `/vitest-dev/vitest` v4.1.6
