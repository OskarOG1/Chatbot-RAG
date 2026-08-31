ALIASY = {
    'jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP': (
        'Ktoś włamał się na konto, przejął konto, zalogował się bez zgody właściciela. '
        'Nieautoryzowany dostęp do konta, utrata dostępu do konta, obca osoba na koncie, '
        'nieznane zamówienia na koncie.'
    ),
    'jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-AgbzAw2ByF4': (
        'Ktoś włamał się na konto, przejął konto, zalogował się bez zgody właściciela. '
        'Nieautoryzowany dostęp do konta, utrata dostępu do konta, obca osoba na koncie, '
        'nieznane zamówienia na koncie.'
    ),
    'automatic-collection-of-fees-for-our-services-from-the-funds-you-have-from-sales': (
        'Polecenie zapłaty za faktury i opłaty Allegro. Jak złożyć nowe polecenie zapłaty, '
        'jak włączyć automatyczną zapłatę prowizji i opłat za sprzedaż. Automatyczne '
        'rozliczanie z Allegro, zgoda na pobieranie należności z pieniędzy ze sprzedaży, '
        'obciążanie bieżącego salda w zakładce Rozliczenia z Allegro.'
    ),
}


def dla_chunku(chunk: dict) -> str:
    url = chunk.get('url') or ''
    for slug, tekst in ALIASY.items():
        if slug in url:
            return tekst
    return ''


def tekst_do_retrievalu(chunk: dict) -> str:
    tytul = chunk.get('tytul', '')
    tekst = chunk.get('tekst', '')
    alias = dla_chunku(chunk)
    if not alias:
        return f'{tytul}\n{tekst}'
    return f'{tytul}\n{alias}\n{tekst}'
