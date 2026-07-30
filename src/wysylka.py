import os
import secrets

import httpx

RESEND_URL = 'https://api.resend.com/emails'


def wyslij_potwierdzenie(email: str, kategoria: str | None, temat: str, tresc: str) -> str:
    klucz = os.getenv('RESEND_API_KEY')
    nadawca = os.getenv('RESEND_FROM_EMAIL')
    sprzedawca = os.getenv('DEMO_SPRZEDAWCA_EMAIL')
    if not klucz or not nadawca or not sprzedawca:
        raise RuntimeError(
            'Wysyłka nie jest skonfigurowana, brakuje RESEND_API_KEY, RESEND_FROM_EMAIL lub DEMO_SPRZEDAWCA_EMAIL.'
        )

    ticket = secrets.token_hex(4).upper()
    naglowki = {'Authorization': f'Bearer {klucz}', 'Content-Type': 'application/json'}

    do_sprzedawcy = {
        'from': nadawca,
        'to': sprzedawca,
        'subject': f'[Zgłoszenie {ticket}] {temat}',
        'text': f'Numer zgłoszenia: {ticket}\nKategoria: {kategoria or "brak"}\nAdres klienta: {email}\n\n{tresc}',
    }
    do_klienta = {
        'from': nadawca,
        'to': email,
        'subject': f'Potwierdzenie zgłoszenia {ticket}',
        'text': (
            f'Twoje zgłoszenie zostało przekazane do sprzedawcy.\n\n'
            f'Numer zgłoszenia: {ticket}\n'
            f'Kategoria sprawy: {kategoria or "brak"}\n\n'
            f'Treść wiadomości:\n{tresc}\n\n'
            'Informacja: to demo nie przechowuje Twojego adresu ani treści wiadomości po wysyłce.'
        ),
    }

    with httpx.Client(timeout=10.0) as klient:
        for wiadomosc in (do_sprzedawcy, do_klienta):
            odpowiedz = klient.post(RESEND_URL, headers=naglowki, json=wiadomosc)
            odpowiedz.raise_for_status()

    return ticket
