import json
from pathlib import Path

import pytest

import classification

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "parity" / "classification_cases.json"


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