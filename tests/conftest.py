import logging

import pytest


@pytest.fixture(autouse=True)
def _neutralize_logging_basicconfig(monkeypatch):
    monkeypatch.setattr(logging, "basicConfig", lambda *args, **kwargs: None)