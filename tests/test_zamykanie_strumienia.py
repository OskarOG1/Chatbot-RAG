import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

STAN_ATRAPY = {'kawalki': 0, 'szybko': False, 'blad': None}


def kawalek_sse():
    payload = {
        'id': 'x', 'object': 'chat.completion.chunk', 'created': 0, 'model': 'atrapa',
        'choices': [{'index': 0, 'delta': {'content': 'slowo '}, 'finish_reason': None}],
    }
    return ('data: ' + json.dumps(payload) + '\n\n').encode()


class HandlerAtrapy(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def wypisz_kawalek(self, dane: bytes):
        self.wfile.write(f'{len(dane):X}\r\n'.encode())
        self.wfile.write(dane)
        self.wfile.write(b'\r\n')

    def do_POST(self):
        dlugosc = int(self.headers.get('Content-Length', 0))
        self.rfile.read(dlugosc)
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        try:
            for _ in range(500):
                self.wypisz_kawalek(kawalek_sse())
                STAN_ATRAPY['kawalki'] += 1
                if not STAN_ATRAPY['szybko']:
                    time.sleep(0.01)
            self.wypisz_kawalek(b'data: [DONE]\n\n')
            self.wfile.write(b'0\r\n\r\n')
        except Exception as e:
            STAN_ATRAPY['blad'] = repr(e)


class SerwerAtrapy(ThreadingHTTPServer):

    def handle_error(self, request, client_address):
        pass


@pytest.fixture(scope='module')
def serwer_atrapy():
    serwer = SerwerAtrapy(('127.0.0.1', 0), HandlerAtrapy)
    port = serwer.server_address[1]
    watek = threading.Thread(target=serwer.serve_forever, daemon=True)
    watek.start()

    import agents_core
    stary_url = agents_core.LLM_BASE_URL
    stary_klucz = agents_core.LLM_API_KEY
    agents_core.LLM_BASE_URL = f'http://127.0.0.1:{port}/v1'
    agents_core.LLM_API_KEY = 'atrapa'

    yield port

    agents_core.LLM_BASE_URL = stary_url
    agents_core.LLM_API_KEY = stary_klucz
    serwer.shutdown()


@pytest.fixture
def stan_czysty(serwer_atrapy):
    STAN_ATRAPY['kawalki'] = 0
    STAN_ATRAPY['szybko'] = False
    STAN_ATRAPY['blad'] = None
    yield


CHUNKI = [({'tekst': 'Treść artykułu pomocy o koncie.', 'tytul': 'Konto Allegro',
            'naglowek': '', 'url': 'https://allegro.pl/pomoc/artykul-konto-1',
            'agent': 'kupujacy'}, 0.9)]


def polaczenia_do_atrapy(port):
    # Pula huggingface_hub jest wspolna dla calego procesu, wiec przy pelnym
    # zestawie testow moze zawierac polaczenia niezwiazane z ta atrapa
    # (np. do huggingface.co z innego testu). Filtrujemy po adresie atrapy.
    from huggingface_hub.utils._http import get_session
    return [c for c in get_session()._transport._pool.connections
            if f'127.0.0.1:{port}' in str(c)]


def test_przerwanie_zamyka_polaczenie(stan_czysty, serwer_atrapy):
    import agents_generacja
    import koszty

    koszty.zacznij()
    strumien = agents_generacja.answer_stream('pytanie testowe', 'konto', CHUNKI)
    odebrane = 0
    for zdarzenie in strumien:
        if zdarzenie['typ'] == 'token':
            odebrane += 1
            if odebrane >= 5:
                break
    assert odebrane == 5
    assert polaczenia_do_atrapy(serwer_atrapy), (
        'pula nie pokazuje polaczenia do atrapy, wiec asercja o jego zamknieciu '
        'nie sprawdzalaby niczego, sprawdz sciezke get_session()._transport._pool')
    kawalki_przed_close = STAN_ATRAPY['kawalki']

    strumien.close()
    koniec = time.monotonic() + 2.0
    while polaczenia_do_atrapy(serwer_atrapy) and time.monotonic() < koniec:
        time.sleep(0.02)

    assert STAN_ATRAPY['kawalki'] <= kawalki_przed_close + 5
    assert polaczenia_do_atrapy(serwer_atrapy) == []
    assert koszty.podsumowanie()['tokeny_wy'] > 0


def test_pelny_przebieg_nie_zostawia_polaczenia(stan_czysty, serwer_atrapy):
    import agents_generacja
    import koszty

    STAN_ATRAPY['szybko'] = True
    koszty.zacznij()
    zdarzenia = list(agents_generacja.answer_stream('inne pytanie testowe', 'konto', CHUNKI))

    assert zdarzenia[-1]['typ'] == 'koniec'
    assert polaczenia_do_atrapy(serwer_atrapy) == []
    assert koszty.podsumowanie()['wywolania'] == 1
