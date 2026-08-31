import os
import secrets
import sys

import httpx

from lang_config import LANG

RESEND_URL = 'https://api.resend.com/emails'


def powod_resend(odpowiedz) -> str:
    try:
        dane = odpowiedz.json()
    except Exception:
        return (getattr(odpowiedz, 'text', '') or '')[:200]
    if isinstance(dane, dict):
        opis = ' '.join(str(dane[k]) for k in ('name', 'message') if dane.get(k))
        return opis[:200] if opis else str(dane)[:200]
    return str(dane)[:200]


def sprawdz_wysylke(odpowiedz, do_kogo: str) -> None:
    if odpowiedz.status_code < 400:
        return
    print(f'UWAGA: Resend odrzucil wiadomosc ({do_kogo}): HTTP {odpowiedz.status_code} '
          f'{powod_resend(odpowiedz)}', file=sys.stderr, flush=True)
    odpowiedz.raise_for_status()


class WysylkaCzesciowaError(Exception):
    def __init__(self, ticket: str, oryginalny: Exception):
        super().__init__(str(oryginalny))
        self.ticket = ticket
        self.oryginalny = oryginalny


def wyslij_potwierdzenie(email: str, kategoria: str | None, temat: str, tresc: str, lang: str = 'pl',
                          ticket: str | None = None) -> str:
    klucz = os.getenv('RESEND_API_KEY')
    nadawca = os.getenv('RESEND_FROM_EMAIL')
    sprzedawca = os.getenv('DEMO_SPRZEDAWCA_EMAIL')
    if not klucz or not nadawca or not sprzedawca:
        raise RuntimeError(
            'Wysyłka nie jest skonfigurowana, brakuje RESEND_API_KEY, RESEND_FROM_EMAIL lub DEMO_SPRZEDAWCA_EMAIL.'
        )

    t = LANG[lang]['wysylka']
    temat = temat.replace('\r', ' ').replace('\n', ' ')
    korekta = ticket is not None
    ticket = ticket or secrets.token_hex(4).upper()
    naglowki = {'Authorization': f'Bearer {klucz}', 'Content-Type': 'application/json'}
    kategoria_tekst = kategoria or t['brak_kategorii']
    klucz_temat_sprzedawca = 'temat_sprzedawca_korekta' if korekta else 'temat_sprzedawca'
    klucz_temat_klient = 'temat_klient_korekta' if korekta else 'temat_klient'

    do_sprzedawcy = {
        'from': nadawca,
        'to': sprzedawca,
        'subject': t[klucz_temat_sprzedawca].format(ticket=ticket, temat=temat),
        'text': t['tresc_sprzedawca'].format(ticket=ticket, kategoria=kategoria_tekst, email=email, tresc=tresc),
    }
    do_klienta = {
        'from': nadawca,
        'to': email,
        'subject': t[klucz_temat_klient].format(ticket=ticket),
        'text': t['tresc_klient'].format(ticket=ticket, kategoria=kategoria_tekst, tresc=tresc, klauzula=t['klauzula']),
    }

    with httpx.Client(timeout=10.0) as klient:
        odpowiedz = klient.post(RESEND_URL, headers=naglowki, json=do_sprzedawcy)
        sprawdz_wysylke(odpowiedz, f'kopia dla sprzedawcy, ticket {ticket}')
        try:
            odpowiedz = klient.post(RESEND_URL, headers=naglowki, json=do_klienta)
            sprawdz_wysylke(odpowiedz, f'potwierdzenie dla klienta, ticket {ticket}')
        except httpx.HTTPError as e:
            raise WysylkaCzesciowaError(ticket, e) from e

    return ticket


def wyslij_odpowiedz_operatora(email: str, pytanie: str, odpowiedz: str, zgloszenie: str,
                               lang: str = 'pl') -> str:
    klucz = os.getenv('RESEND_API_KEY')
    nadawca = os.getenv('RESEND_FROM_EMAIL')
    if not klucz or not nadawca:
        raise RuntimeError(
            'Wysyłka nie jest skonfigurowana, brakuje RESEND_API_KEY lub RESEND_FROM_EMAIL.'
        )

    t = LANG[lang]['wysylka']
    ticket = secrets.token_hex(4).upper()
    naglowki = {'Authorization': f'Bearer {klucz}', 'Content-Type': 'application/json'}
    temat = t['temat_odpowiedz'].format(zgloszenie=zgloszenie).replace('\r', ' ').replace('\n', ' ')

    wiadomosc = {
        'from': nadawca,
        'to': email,
        'subject': temat,
        'text': t['tresc_odpowiedz'].format(
            zgloszenie=zgloszenie, pytanie=pytanie, odpowiedz=odpowiedz,
            klauzula=t['klauzula_odpowiedz'],
        ),
    }

    with httpx.Client(timeout=10.0) as klient:
        wynik = klient.post(RESEND_URL, headers=naglowki, json=wiadomosc)
        sprawdz_wysylke(wynik, f'odpowiedz na zgloszenie {zgloszenie}')

    return ticket
