# typescript-classification-and-testing

## Purpose

This capability defines the TypeScript test runner bootstrap for the webapp and the
export of the two pure classification functions so they can be asserted under Vitest.
It MUST let `npm run test:run` execute locally after `npm install` with zero tests
failing, MUST add `export` to `classifyDuration` and `hardnessIndex` at
`webapp/src/utils/dataProcessor.ts:38, 51` without altering runtime behavior at the
existing call sites (`webapp/src/utils/dataProcessor.ts:119-120`), and MUST consume
the shared parity fixture via a relative symlink.

## Requirements

### R-1. Export the pure classification functions

`webapp/src/utils/dataProcessor.ts` MUST declare `classifyDuration` (currently at
line 38) and `hardnessIndex` (currently at line 51) as `export const`. The body of
each function MUST remain byte-equivalent to its current implementation; only the
`export` keyword is added. The two in-module call sites at lines 119-120 of
`processCsvData` MUST continue to resolve without change.

### R-2. Vitest configuration via the existing Vite config

The repository MUST add `webapp/vitest.config.ts` that imports `defineConfig` from
`vitest/config` and merges Vitest's `test` options into the existing Vite setup. The
`test` block MUST set `environment: 'happy-dom'`, declare `setupFiles:
['./src/test/setup.ts']`, and `include: ['src/**/*.{test,spec}.{ts,tsx}']`. The
Vite build path (`npm run build`) MUST keep working through the same config.

### R-3. Smoke test for the exported functions

A test file MUST exist under `webapp/src/utils/__tests__/dataProcessor.test.ts`
(or the Vitest-conventional sibling location). The test MUST import `classifyDuration`
and `hardnessIndex` directly from the module under test and MUST assert at least one
known input/output pair for each. The test SHOULD cover the same boundary inputs as
the Python smoke test (`0`, `16`, `24`, `40`, `60`).

### R-4. Cross-stack parity test

A test file MUST exist under
`webapp/src/utils/__tests__/parity.test.ts`. It MUST load
`webapp/src/utils/__tests__/fixtures/classification_cases.json` (a relative symlink
to `tests/fixtures/parity/classification_cases.json` at the repo root), MUST iterate
over every entry, and MUST assert that the exported TS functions return the expected
category and numeric value within a documented tolerance.

### R-5. NPM scripts for the runner

`webapp/package.json` MUST expose `scripts.test = "vitest"`,
`scripts.test:run = "vitest run"`, and `scripts.coverage = "vitest run --coverage"`.
The dev dependencies MUST include `vitest@^2`, `@testing-library/react@^16`,
`@testing-library/jest-dom@^6`, `@testing-library/user-event@^14`,
`happy-dom@^15`, and `@vitest/coverage-v8@^2`.

## Scenarios

#### S-1. Exported functions resolve from a test file

- GIVEN `webapp/src/utils/dataProcessor.ts` with `export` on `classifyDuration` and `hardnessIndex`
- WHEN a Vitest test file does `import { classifyDuration, hardnessIndex } from '../dataProcessor'`
- THEN the import compiles under `tsc --noEmit`
- AND each function is callable

#### S-2. Existing call sites still work

- GIVEN `processCsvData` references `classifyDuration` and `hardnessIndex` at lines 119-120
- WHEN `npm run build` runs
- THEN the build succeeds with no TypeScript errors
- AND the produced bundle behaves identically at runtime

#### S-3. Vitest discovers the smoke test

- GIVEN `webapp/vitest.config.ts` declares `include: ['src/**/*.{test,spec}.{ts,tsx}']`
- WHEN `npm run test:run` is executed
- THEN Vitest reports at least one passing test
- AND the exit code is 0

#### S-4. Smoke assertions match boundary cases

- GIVEN the smoke test in `webapp/src/utils/__tests__/dataProcessor.test.ts`
- WHEN the test executes
- THEN `hardnessIndex(16)` equals `25` within tolerance
- AND `hardnessIndex(24)` equals `50` within tolerance
- AND `hardnessIndex(40)` equals `75` within tolerance
- AND `hardnessIndex(60)` equals `100` within tolerance

#### S-5. Parity fixture loads through the symlink

- GIVEN the symlink at `webapp/src/utils/__tests__/fixtures/classification_cases.json`
- WHEN the parity test reads and parses the JSON
- THEN the loaded object has at least one case
- AND every case is asserted against `classifyDuration` and `hardnessIndex`

#### S-6. Coverage script executes

- GIVEN `@vitest/coverage-v8@^2` is installed
- WHEN `npm run coverage` runs
- THEN Vitest executes all tests with the v8 coverage provider
- AND exits with code 0 if all tests pass