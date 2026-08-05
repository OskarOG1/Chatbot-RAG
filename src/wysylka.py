import os
import secrets

import httpx

from lang_config import LANG

RESEND_URL = 'https://api.resend.com/emails'


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
        odpowiedz.raise_for_status()
        try:
            odpowiedz = klient.post(RESEND_URL, headers=naglowki, json=do_klienta)
            odpowiedz.raise_for_status()
        except httpx.HTTPError as e:
            raise WysylkaCzesciowaError(ticket, e) from e

    return ticket
