# Design: streamlit-audit-remediation

## Technical Approach

Behavior-preserving refactor + bug-fix of `visualizer.py` and `streamlit_app.py` covering the 6 WS in `proposal.md`. Applied in dependency order — each step's surface shrinks before the next fans out. No data-flow, classification, or React/TS changes.

## Architecture Decisions

### Decision: WS ordering — (1) Theme → (2) Dead code → (3) Errors → (4) Color → (5) API → (6) Polish

| Option | Tradeoff | Decision |
|---|---|---|
| Spec-driven 1:1 with WS-1..WS-6 | AUD-02 (errors) lands AFTER color dedup → dead `ValueError` handler never validates the fix | **Rejected** |
| Dependency-driven | AUD-02 precedes AUD-01 testing; AUD-08 (`plot_heatmap` delete, ~100 LOC) shrinks the color-dedup diff | **Chosen** |

### Decision: Strip `try/except Exception → raise Exception` wrappers (not domain-exception mapping)

The 5 `Visualizer.plot_*` methods catch `ValueError` and re-raise as `Exception(f"...: {e}")`, dropping dynamic type so `streamlit_app.py:199 except ValueError` is dead. The `required_columns` loops already raise `ValueError` (`visualizer.py:23, 146, 249, 344`) — the contracts we want propagate. A `VisualizationError` domain class adds ceremony for zero new caller logic. **Choice**: delete wrappers, keep the `logging.info(...)` statements plain. Other exceptions still bubble to Streamlit's default handler.

### Decision: Single source of color = `Visualizer.COLOR_MAPPING`, "roca dura" = `#e74c3c`

Delete local copies at `visualizer.py:26-31`, `:93-98`, `:117-122`. `plot_3d_scatter:271` already passes the class-level map (correct). `#e74c3c` matches class declaration AND `plot_location_interactive`'s copy; `#8B0000` (`:96`) and `#FFA07A` (`:120`) are drift bugs.

### Decision: `.streamlit/config.toml` — single light mode (locks user toggle)

```toml
[theme]
base = "light"
primaryColor = "#1f6feb"
backgroundColor = "#f0f2f6"
secondaryBackgroundColor = "#e6e9ef"
textColor = "#333333"
font = "sans-serif"
```

Mirrors `streamlit_app.py:54-66`'s hardcoded CSS exactly. Per `theme.md` §Light and dark modes, a single `[theme]` block locks to one mode — acceptable since the app previously rendered a single fixed style. Replace `st.get_option("theme.base")` (line 15) with `st.context.theme.type`; delete the now-dead `streamlit_theme` var.

### Decision: Drop `use_container_width=True` (5 sites)

Removed from `st.plotly_chart` (lines 168, 175, 183, 190, 197). Deprecated in 1.59 per bundled `SKILL.md`; default already stretches to container width.

### Decision: Stop mutating cached `df_processed`

Delete `streamlit_app.py:83` (`df_processed['tiempo inicio'] = pd.to_datetime(...)`). `data_processor.py:54` already types it; the assignment is redundant AND a `@st.cache_data` footgun.

### Decision: `date_input` len-gate

Keep `len == 2` branch (lines 98-102). Replace lines 103-106 (`start = end = date_range[0]`) with `else: st.info("Selecciona el rango completo..."); st.stop()`. Old fallback is silent wrong behavior.

## Data Flow

Unchanged — no new ingestion, classification, or persistence. Only delta: `ValueError` now surfaces visibly in `streamlit_app.py:199` instead of being absorbed and re-wrapped.

```
file_uploader → cargar_datos (cached) → DataProcessor.load_and_process
   → df_processed → date+drill_pattern filter → df_filtrado
   → Visualizer.plot_{box,pie,location,heatmap,3d}  (raises ValueError → caller)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `.streamlit/config.toml` | **Create** | Single light-mode theme, ~15 LOC |
| `streamlit_app.py` | Modify | -30 LOC: drop `<style>`, 5× `use_container_width`, cache mutation, theme lookup, `if __name__`, add `page_title`/`page_icon`, add `st.info`+`st.stop` on mid-selection, sentence-case subheaders |
| `visualizer.py` | Modify | -150 LOC: 3 local `color_mapping` dicts deleted, `plot_heatmap` deleted, 5× `try/except` wrappers stripped |

Total: -165 LOC (within 400-LOC budget).

## Interfaces / Contracts

| Contract | Shape |
|---|---|
| `Visualizer.COLOR_MAPPING` | class-level `dict[str,str]`, single source for all 4 remaining charts |
| `Visualizer.plot_*(df, ...)` | may raise `ValueError` (validation) or pandas `KeyError`/`TypeError`; no `Exception` wrapping |
| `streamlit_app.py` outer `try` | `except ValueError` at line 199 becomes live; `except Exception` at 201 stays as safety net |
| `.streamlit/config.toml` | light-mode lock; `st.context.theme.type` always `"light"` |

No new types; public surface strictly reduced.

## Testing Strategy

Per `openspec/config.yaml`: `strict_tdd: false`, pytest not installed.

| Layer | What | How |
|---|---|---|
| Unit | none | pytest absent (config.yaml:26-30) |
| Smoke | `python -m streamlit run streamlit_app.py` | upload `ejemplo_datos.txt`; verify 4 charts render post-`plot_heatmap` deletion |
| Error path | `streamlit_app.py:199 except ValueError` | inject malformed CSV → branch fires with `st.error("Error de validación: ...")` (previously dead) |
| Acceptance grep | `grep "color_mapping\s*=\s*{" visualizer.py` → 0 · `grep -E "plot_heatmap\|use_container_width\|st\.get_option" streamlit_app.py` → 0 each · `git diff --stat` ≤ 400 LOC |

## Migration / Rollout

No migration. Per `proposal.md §Rollback Plan`: `git revert <sha>` restores inert `<style>`, dead `plot_heatmap`, `use_container_width` aliases, cached-DataFrame mutation. `config.toml` deletion falls back to Streamlit's built-in light theme (close visual match). Partial revert (keep `config.toml`) is safe — additive.

## No Parity Impact (per `config.yaml:rules.design`)

This change does NOT modify `data_processor.py`, `classification.py`, `webapp/`, or any classification threshold (`config.yaml:48` rollback rule does not apply). The sequence-diagram and parity-test requirements are conditionally scoped to changes that touch classification logic or shared cross-stack code — this change does neither, so both relax. CSV ingestion flow unchanged; classification thresholds unchanged; React/TS webapp audit is deferred to follow-up `streamlit-audit-remediation-webapp`.

## Open Questions

None.
