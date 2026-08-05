import sys
from collections import Counter
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

KORPUS_DOSTEPNY = (SRC.parent / 'RAG' / 'chunks_kupujacy.json').exists()
wymaga_korpusu = pytest.mark.skipif(
    not KORPUS_DOSTEPNY,
    reason='wymaga pelnego korpusu RAG (chunks_kupujacy.json), niedostepnego w CI'
)


@pytest.fixture(autouse=True)
def maly_slownik(monkeypatch):
    import spell
    monkeypatch.setattr(spell, 'SLOWNIK_CACHE',
                        Counter({'konto': 100, 'haslo': 40, 'dom': 50, 'zwrot': 30}))
