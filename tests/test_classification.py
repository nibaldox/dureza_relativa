import pytest

import classification


CLASSIFY_BOUNDARIES = [
    (15.999, "roca suave"),
    (16.0, "roca media"),
    (23.999, "roca media"),
    (24.0, "roca dura"),
    (39.999, "roca dura"),
    (40.0, "roca muy dura"),
    (60.0, "roca muy dura"),
    (61.0, "roca muy dura"),
]


@pytest.mark.parametrize("minutos,expected", CLASSIFY_BOUNDARIES)
def test_classify_duracion_boundary(minutos, expected):
    assert classification.classify_duracion(minutos) == expected


HARDNESS_SEGMENTS = [
    (0.0, 0.0),
    (8.0, 12.5),
    (15.999, 24.9984375),
    (16.0, 25.0),
    (20.0, 37.5),
    (23.999, 49.996875),
    (24.0, 50.0),
    (32.0, 62.5),
    (39.999, 74.9984375),
    (40.0, 75.0),
    (50.0, 87.5),
    (59.999, 99.99875),
    (60.0, 100.0),
    (61.0, 100.0),
]


@pytest.mark.parametrize("T,expected", HARDNESS_SEGMENTS)
def test_hardness_index_segments(T, expected):
    assert classification.hardness_index(T) == pytest.approx(expected, abs=1e-9)


def test_hardness_index_negative_is_clamped_to_zero():
    assert classification.hardness_index(-1.0) == 0.0
    assert classification.hardness_index(-999.0) == 0.0