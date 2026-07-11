# Proposal: streamlit-audit-remediation

**Status:** Draft · **Date:** 2026-07-11 · **Budget:** ~400 LOC

## Intent

Streamlit 1.59.1 audit of `streamlit_app.py` + `visualizer.py` (against the bundled
`developing-with-streamlit` skill) found **18 issues (3 CRIT, 5 HIGH, 6 MED, 4 LOW)**:
inconsistent color mapping across 4 charts, dead error handlers (`ValueError`
re-raised as `Exception`), inert CSS targeting auto-generated hashes with no
`config.toml` backing, deprecated APIs, and a ~100-line `plot_heatmap` nothing calls.
Goal: consistent, current, dead-code-free app — no change to classification semantics
or the `DataProcessor`/`Visualizer` public surface or the React/TypeScript webapp.

## Scope

| WS | Sev | Deliverable |
|----|-----|-------------|
| **WS-1 Color** | CRIT | Single `COLOR_MAPPING`; delete 3 per-method copies; canonicalize `"roca dura"` to `#e74c3c`. |
| **WS-2 Errors** | CRIT | Strip `except Exception → raise Exception`; reactivate `streamlit_app.py:199 except ValueError`. |
| **WS-3 Theme** | CRIT+L | Add `.streamlit/config.toml`; delete `<style>` block; fix `st.get_option("theme.base")` → `st.context.theme.type`. |
| **WS-4 API** | HIGH | Drop `use_container_width=True` (5 sites); stop mutating cached `df_processed`; remove redundant `pd.to_datetime`. |
| **WS-5 Dead code** | HIGH | Delete `plot_heatmap`; fix mid-selection `date_input` with explicit `len == 2` gate. |
| **WS-6 Polish** | M+L | Sentence casing; add `page_title`/`page_icon`; drop unused `bin_size`; remove `if __name__ == "__main__"`. |

**Out of scope:** classification logic (`data_processor.py`, `classification.py` —
threshold rule `config.yaml:48` does not apply); React/TS webapp (no parity audit
requested); tests / `strict_tdd: true` (handled by `bootstrap-test-runner`); unrelated
cleanups (linters, CI, `app.log`).

## Capabilities

Researched `openspec/specs/` (`python-classification-and-testing`, `cross-stack-parity`).
Neither covers the visualization or UI-rendering layer; both stay unchanged.

### New Capabilities
None.

### Modified Capabilities
None.

## Approach

1. **Color** — Use `Visualizer.COLOR_MAPPING` (`visualizer.py:9-14`) as canonical; delete divergent copies at `26-31, 93-98, 117-122`.
2. **Errors** — Strip try/except boilerplate; let `ValueError` reach `streamlit_app.py:199`.
3. **Theme** — Create `.streamlit/config.toml`; delete `st.markdown("<style>...")` at `53-66`; fix theme API call at line 15.
4. **API** — Drop 5× `use_container_width=True` (default = `width="stretch"`); bind `pd.to_datetime(...)` to a fresh var.
5. **Dead code + date** — Delete `plot_heatmap` (0 call sites); replace `len(date_range) != 2` fallback with explicit early-return info.

## Affected Areas

| Area | Impact |
|------|--------|
| `visualizer.py` | Modified: -150 LOC (color dedup, dead code, error cleanup) |
| `streamlit_app.py` | Modified: -30 LOC (CSS, API, date guard, polish) |
| `.streamlit/config.toml` | **New**: ~15 LOC |
| `webapp/`, `data_processor.py`, `classification.py` | None |

## Risks

| Risk | Mitigation |
|------|------------|
| Palette divergence vs webapp | Palette is Streamlit-local; document in PR. |
| `ValueError` re-raise surfaces swallowed errors | Pre-existing `streamlit_app.py:199` handler is landing site; smoke-test malformed CSV. |
| `config.toml` overrides user theme toggle | Use `[theme]` (single mode); user toggle still works. |

## Rollback Plan

`git revert <sha>` restores pre-remediation state. No data migration, no schema change.
Recovery restores the inert `<style>` block, dead `plot_heatmap`, `use_container_width=True`
aliases, and the cached-DataFrame mutation (footgun returns, app still runs).
`config.toml` deletion falls back to Streamlit defaults. **Smoke:** `streamlit run
streamlit_app.py` launches; `ejemplo_datos.txt` renders all 5 charts. Partial revert
(keep `config.toml`) is safe — additive.

## Success Criteria

- [ ] `grep "color_mapping\s*=\s*{" visualizer.py` → 0 matches.
- [ ] `grep -E "plot_heatmap|use_container_width|st\.get_option" streamlit_app.py` → 0 matches each.
- [ ] `.streamlit/config.toml` exists; app launches; visual outcome matches pre-change.
- [ ] CSV missing `elevacion` triggers the previously-dead `except ValueError` branch.
- [ ] `git diff --stat` ≤ 400 LOC.
- [ ] `ejemplo_datos.txt` smoke: 5 charts render; `dureza` colors identical across box/pie/scatter/3D.

## Dependencies

None. Streamlit 1.59.1 installed; `data_processor.py` already produces typed `df_processed`.

## Follow-ups

1. **`streamlit-audit-remediation-webapp`** — symmetric audit of `webapp/src/utils/charts.ts`.
2. **`visualizer-coverage`** — pytest tests for `Visualizer` after a future Strict-TDD flip.
3. **Theme polish** — richer `config.toml` (Material Symbols, `chartCategoricalColors`) using bundled `theme.md` templates.