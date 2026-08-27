from contextvars import ContextVar
import os
import sys

CENNIK = {'swiss-ai/apertus-8b-instruct': (0.0, 0.0),
          'speakleash/Bielik-11B-v3.0-Instruct': (0.0, 0.0),
          'google/gemini-2.5-flash': (0.30, 2.50),
          'openai/gpt-4o-mini': (0.15, 0.60),
          'anthropic/claude-haiku-4.5': (1.00, 5.00)}
DOMYSLNA_STAWKA = (0.0, 0.0)
ZNAKI_NA_TOKEN = float(os.getenv('ZNAKI_NA_TOKEN', '3.6'))

ZUZYCIE: ContextVar = ContextVar('zuzycie', default=None)
OSTRZEZONO_O_KOSZTACH = False


def zacznij() -> dict:
    akumulator = {'tokeny_we': 0, 'tokeny_wy': 0, 'koszt': 0.0,
                  'wywolania': 0, 'szacowane': False}
    ZUZYCIE.set(akumulator)
    return akumulator


def dodaj(model: str, tokeny_we: int, tokeny_wy: int, szacowane: bool = False) -> None:
    akumulator = ZUZYCIE.get()
    if akumulator is None:
        return
    stawka_we, stawka_wy = CENNIK.get(model, DOMYSLNA_STAWKA)
    akumulator['tokeny_we'] += tokeny_we
    akumulator['tokeny_wy'] += tokeny_wy
    akumulator['koszt'] += (tokeny_we / 1_000_000) * stawka_we + (tokeny_wy / 1_000_000) * stawka_wy
    akumulator['wywolania'] += 1
    if szacowane:
        akumulator['szacowane'] = True


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
        dodaj(model, we, oszacuj(tekst or ''), szacowane=True)
    except Exception as e:
        global OSTRZEZONO_O_KOSZTACH
        if not OSTRZEZONO_O_KOSZTACH:
            print(f'UWAGA: licznik kosztow zawiodl ({type(e).__name__}: {e})',
                  file=sys.stderr, flush=True)
            OSTRZEZONO_O_KOSZTACH = True


def podsumowanie() -> dict:
    akumulator = ZUZYCIE.get()
    if akumulator is None:
        return {'tokeny_we': 0, 'tokeny_wy': 0, 'koszt_usd': 0.0,
                'wywolania': 0, 'szacowane': False}
    return {'tokeny_we': akumulator['tokeny_we'], 'tokeny_wy': akumulator['tokeny_wy'],
            'koszt_usd': round(akumulator['koszt'], 6), 'wywolania': akumulator['wywolania'],
            'szacowane': akumulator['szacowane']}
