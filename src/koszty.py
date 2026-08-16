import os
import threading

CENNIK = {'swiss-ai/apertus-v1.5-8b': (0.0, 0.0),
          'speakleash/Bielik-11B-v3.0-Instruct': (0.0, 0.0)}
DOMYSLNA_STAWKA = (0.0, 0.0)
ZNAKI_NA_TOKEN = float(os.getenv('ZNAKI_NA_TOKEN', '3.6'))

_stan = threading.local()


def _zainicjuj_jesli_trzeba() -> None:
    if not hasattr(_stan, 'tokeny_we'):
        _stan.tokeny_we = 0
        _stan.tokeny_wy = 0
        _stan.koszt = 0.0
        _stan.wywolania = 0
        _stan.szacowane = False


def zacznij() -> None:
    _stan.tokeny_we = 0
    _stan.tokeny_wy = 0
    _stan.koszt = 0.0
    _stan.wywolania = 0
    _stan.szacowane = False


def dodaj(model: str, tokeny_we: int, tokeny_wy: int, szacowane: bool = False) -> None:
    _zainicjuj_jesli_trzeba()
    stawka_we, stawka_wy = CENNIK.get(model, DOMYSLNA_STAWKA)
    _stan.tokeny_we += tokeny_we
    _stan.tokeny_wy += tokeny_wy
    _stan.koszt += (tokeny_we / 1_000_000) * stawka_we + (tokeny_wy / 1_000_000) * stawka_wy
    _stan.wywolania += 1
    if szacowane:
        _stan.szacowane = True


def oszacuj(tekst: str) -> int:
    if not tekst:
        return 0
    return max(1, round(len(tekst) / ZNAKI_NA_TOKEN))


def dodaj_z_odpowiedzi(model: str, odp=None, wiadomosci: list[dict] | None = None,
                       tekst: str | None = None) -> None:
    try:
        usage = getattr(odp, 'usage', None)
        we = getattr(usage, 'prompt_tokens', None)
        wy = getattr(usage, 'completion_tokens', None)
        if isinstance(we, int) and isinstance(wy, int):
            dodaj(model, we, wy)
            return
        we = sum(oszacuj(w.get('content') or '') for w in (wiadomosci or []))
        wy = oszacuj(tekst or '')
        dodaj(model, we, wy, szacowane=True)
    except Exception:
        pass


def podsumowanie() -> dict:
    _zainicjuj_jesli_trzeba()
    return {'tokeny_we': _stan.tokeny_we, 'tokeny_wy': _stan.tokeny_wy,
            'koszt_usd': round(_stan.koszt, 6), 'wywolania': _stan.wywolania,
            'szacowane': _stan.szacowane}
