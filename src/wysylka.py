import os
import secrets

import httpx

from lang_config import LANG

RESEND_URL = 'https://api.resend.com/emails'


def wyslij_potwierdzenie(email: str, kategoria: str | None, temat: str, tresc: str, lang: str = 'pl') -> str:
    klucz = os.getenv('RESEND_API_KEY')
    nadawca = os.getenv('RESEND_FROM_EMAIL')
    sprzedawca = os.getenv('DEMO_SPRZEDAWCA_EMAIL')
    if not klucz or not nadawca or not sprzedawca:
        raise RuntimeError(
            'Wysyłka nie jest skonfigurowana, brakuje RESEND_API_KEY, RESEND_FROM_EMAIL lub DEMO_SPRZEDAWCA_EMAIL.'
        )

    t = LANG[lang]['wysylka']
    ticket = secrets.token_hex(4).upper()
    naglowki = {'Authorization': f'Bearer {klucz}', 'Content-Type': 'application/json'}
    kategoria_tekst = kategoria or t['brak_kategorii']

    do_sprzedawcy = {
        'from': nadawca,
        'to': sprzedawca,
        'subject': t['temat_sprzedawca'].format(ticket=ticket, temat=temat),
        'text': t['tresc_sprzedawca'].format(ticket=ticket, kategoria=kategoria_tekst, email=email, tresc=tresc),
    }
    do_klienta = {
        'from': nadawca,
        'to': email,
        'subject': t['temat_klient'].format(ticket=ticket),
        'text': t['tresc_klient'].format(ticket=ticket, kategoria=kategoria_tekst, tresc=tresc, klauzula=t['klauzula']),
    }

    with httpx.Client(timeout=10.0) as klient:
        for wiadomosc in (do_sprzedawcy, do_klienta):
            odpowiedz = klient.post(RESEND_URL, headers=naglowki, json=wiadomosc)
            odpowiedz.raise_for_status()

    return ticket
