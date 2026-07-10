from pathlib import Path

import pytest


def test_data_processor_import_does_not_create_app_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from data_processor import DataProcessor

    assert DataProcessor().classify_duracion(15.99) == "roca suave"
    assert DataProcessor().hardness_index(16.0) == pytest.approx(25.0, abs=1e-9)
    assert not (tmp_path / "app.log").exists()


def test_data_processor_hardness_wrapper_delegates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from data_processor import DataProcessor

    dp = DataProcessor()
    assert dp.hardness_index(40.0) == pytest.approx(75.0, abs=1e-9)
    assert dp.classify_duracion(30.0) == "roca dura"
    assert not Path("app.log").exists()