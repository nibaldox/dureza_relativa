import json
from pathlib import Path

import pytest

import classification

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "parity" / "classification_cases.json"
DRILLING_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "parity" / "drilling_analytics_cases.json"
)


def _load_cases():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    cases = data["cases"]
    assert len(cases) >= 8, f"fixture must have at least 8 cases, got {len(cases)}"
    assert any("sentinel" in c.get("comment", "") for c in cases), (
        "fixture must contain a sentinel-marked case to prove JSON is loaded, not hardcoded"
    )
    return cases


@pytest.mark.parametrize(
    "case",
    _load_cases(),
    ids=[c["comment"] for c in _load_cases()],
)
def test_classify_duracion_parity(case):
    actual = classification.classify_duracion(case["input"])
    expected = case["expected_dureza"]
    assert actual == expected, (
        f"case[{case['comment']}] input={case['input']} expected={expected} actual={actual}"
    )


@pytest.mark.parametrize(
    "case",
    _load_cases(),
    ids=[c["comment"] for c in _load_cases()],
)
def test_hardness_index_parity(case):
    actual = classification.hardness_index(case["input"])
    expected = case["expected_indice_dureza"]
    assert actual == pytest.approx(expected, abs=1e-9), (
        f"case[{case['comment']}] input={case['input']} expected={expected} actual={actual}"
    )


# ---------------------------------------------------------------------------
# Drilling-analytics parity fixture (covers the new pure functions).
# ---------------------------------------------------------------------------


_DISPATCH = {
    "penetration_rate": lambda inp: classification.penetration_rate(
        inp["depth_m"], inp["duration_min"]
    ),
    "classify_with_metric": lambda inp: classification.classify_with_metric(
        inp["value"], inp["thresholds"], inp["metric"]
    ),
    "hardness_index_with_metric": lambda inp: classification.hardness_index_with_metric(
        inp["value"], inp["thresholds"], inp["metric"]
    ),
    "rig_mean_penetration": lambda inp: classification.rig_mean_penetration(
        inp["rates"]
    ),
    "rig_normalized_penetration": lambda inp: classification.rig_normalized_penetration(
        inp["rate"], inp["rig_avg"], inp["rig_std"]
    ),
}


def _load_drilling_cases():
    with DRILLING_FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    cases = data["cases"]
    assert len(cases) >= 15, (
        f"drilling fixture must have at least 15 cases (≥3 per function), "
        f"got {len(cases)}"
    )
    functions = {c["function"] for c in cases}
    expected_functions = set(_DISPATCH.keys())
    missing = expected_functions - functions
    assert not missing, f"drilling fixture missing functions: {missing}"
    return cases


_DRILLING_CASES = _load_drilling_cases()


@pytest.mark.parametrize(
    "case",
    _DRILLING_CASES,
    ids=[c["comment"] for c in _DRILLING_CASES],
)
def test_drilling_analytics_parity(case):
    fn_name = case["function"]
    assert fn_name in _DISPATCH, (
        f"case[{case['comment']}] references unknown function {fn_name!r}"
    )
    actual = _DISPATCH[fn_name](case["inputs"])
    expected = case["expected"]
    tolerance = case.get("tolerance")

    if tolerance is None:
        assert actual == expected, (
            f"case[{case['comment']}] function={fn_name} "
            f"inputs={case['inputs']} expected={expected} actual={actual}"
        )
        return

    # When the expected value is None we still want to know whether the
    # implementation returned a finite number so the failure message is
    # actionable.
    if expected is None:
        assert actual is None, (
            f"case[{case['comment']}] function={fn_name} "
            f"inputs={case['inputs']} expected=None actual={actual}"
        )
        return

    assert actual == pytest.approx(expected, abs=tolerance), (
        f"case[{case['comment']}] function={fn_name} "
        f"inputs={case['inputs']} expected={expected} actual={actual} "
        f"tolerance={tolerance}"
    )