ALIASY = {
    'jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-0KvwX8YAocP': (
        'Ktoś włamał się na konto, przejął konto, zalogował się bez zgody właściciela. '
        'Nieautoryzowany dostęp do konta, utrata dostępu do konta, obca osoba na koncie, '
        'nieznane zamówienia na koncie. '
        'Zapomniałem loginu, nie pamiętam loginu, nie pamiętam nazwy użytkownika, '
        'zapomniałem adresu mejlowego do logowania, nie wiem na jaki login się logowałem.'
    ),
    'jak-odzyskac-dostep-do-konta-gdy-nie-mozesz-sie-zalogowac-AgbzAw2ByF4': (
        'Ktoś włamał się na konto, przejął konto, zalogował się bez zgody właściciela. '
        'Nieautoryzowany dostęp do konta, utrata dostępu do konta, obca osoba na koncie, '
        'nieznane zamówienia na koncie. '
        'Zapomniałem loginu, nie pamiętam loginu, nie pamiętam nazwy użytkownika, '
        'zapomniałem adresu mejlowego do logowania, nie wiem na jaki login się logowałem.'
    ),
    'czy-mozna-uzywac-kilku-kont-na-allegro-mGwAg1dKEtr': (
        'Czy mogę mieć dwa konta na Allegro, drugie konto, kolejne konto, jeszcze jedno konto. '
        'Więcej niż jedno konto na jedną osobę, dwa konta na ten sam adres mejlowy, '
        'zakładanie osobnego konta firmowego obok prywatnego.'
    ),
    'czym-jest-i-jak-zalozyc-konto-junior-4GDdXn8qXt3': (
        'Konto dla dziecka, czy dziecko może mieć swoje konto, konto dla nastolatka, '
        'konto dla osoby niepełnoletniej, czy dziecko może samo kupować, '
        'zakupy nastolatka pod kontrolą rodzica.'
    ),
    'jak-aktywowac-allegro-pay-bEoD02GdGij': (
        'Jak włączyć Allegro Pay, jak uruchomić Allegro Pay, jak zacząć korzystać z Allegro Pay, '
        'gdzie włącza się odroczoną płatność, aktywacja płatności odroczonej na koncie.'
    ),
    'jak-zwrocic-zakup-i-odeslac-produkt-do-sprzedajacego-GDeq5VeKRHD': (
        'Ile mam czasu na zwrot, ile dni na zwrot towaru, jak długo mam na zwrot, '
        'do kiedy mogę zwrócić zakup, czy zdążę jeszcze zwrócić towar. '
        'Termin na odstąpienie od umowy, czternaście dni na odesłanie produktu, '
        'czas na odesłanie przesyłki zwrotnej, do kiedy trzeba nadać zwrot.',
        '14 dni',
    ),
    'co-mozesz-zrobic-gdy-czekasz-na-przesylke-zbyt-dlugo-xG71gn36qC4': (
        'Paczka nie przyszła, nie dostałem paczki, przesyłka nie dotarła, zamówienie nie przyszło, '
        'towar nie dotarł, produkt nie dotarł, nie dostałem towaru, nie dostałem zamówienia, '
        'sprzedawca nie wysłał paczki, brak dostawy przesyłki, zaginęła paczka, '
        'czekam za długo na przesyłkę i nie wiem co robić.',
        'nie otrzymałem produktu',
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
    for slug, wpis in ALIASY.items():
        if slug not in url:
            continue
        if isinstance(wpis, tuple):
            tekst, kotwica = wpis
            return tekst if kotwica in (chunk.get('tekst') or '') else ''
        return wpis
    return ''


def tekst_do_retrievalu(chunk: dict) -> str:
    tytul = chunk.get('tytul', '')
    tekst = chunk.get('tekst', '')
    alias = dla_chunku(chunk)
    if not alias:
        return f'{tytul}\n{tekst}'
    return f'{tytul}\n{alias}\n{tekst}'
