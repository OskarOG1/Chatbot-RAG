import sys
from collections import Counter
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def maly_slownik(monkeypatch):
    import spell
    monkeypatch.setattr(spell, 'SLOWNIK_CACHE',
                        Counter({'konto': 100, 'haslo': 40, 'dom': 50, 'zwrot': 30}))
