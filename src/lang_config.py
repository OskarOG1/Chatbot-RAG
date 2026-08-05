import os

MODEL_11B = 'speakleash/Bielik-11B-v3.0-Instruct'
MODEL_DOMYSLNY = 'swiss-ai/apertus-v1.5-8b'

LANG = {
    'pl': {
        'embedder': 'sdadas/mmlw-retrieval-roberta-base',
        'query_prefix': 'zapytanie: ',
        'passage_prefix': '',
        'lemma_lang': 'pl',
        'freq_lang': 'pl',
        'suffix': '',
        'model': os.getenv('MODEL', MODEL_DOMYSLNY),
        'sedzia_model': os.getenv('SEDZIA_MODEL', MODEL_11B),
        'prog_rerank': -4.3,
        'prog_pokrycia': 0.20,
        'brak_wiedzy': (
            'Nie znalazłem tej informacji w bazie pomocy Allegro. '
            'Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc'
        ),
        'nie_zrozumialem': 'Przepraszam, nie zrozumiałem pytania, czy możesz napisać je inaczej?',
        'kroki': {
            'sprawdzam_pytanie': 'Sprawdzam pytanie',
            'poprawiam_literowki': 'Poprawiam literówki',
            'szkic_wiadomosci': 'Przygotowuję szkic wiadomości do sprzedawcy',
            'przepisuje_pytanie': 'Przepisuję pytanie z kontekstu rozmowy',
            'zamieniam_na_wektor': 'Zamieniam pytanie na wektor',
            'przeszukuje_baze': 'Przeszukuję bazę wiedzy i porządkuję wyniki',
            'rozpoznaje_strone': 'Rozpoznaję, czy pytasz jako kupujący, czy sprzedający',
            'wybieram_strone': 'Rozstrzygam stronę pytania: {strona}',
            'poza_zakresem': 'Poza zakresem bazy pomocy, odmawiam',
            'sprawdzam_kontekst': 'Sprawdzam, czy kontekst odpowiada na pytanie',
            'generuje_odpowiedz': 'Generuję odpowiedź (sekcja: {agent})',
        },
        'nazwy_sekcji': {
            'konto': 'konto',
            'zakupy': 'zakupy',
            'platnosci': 'płatności',
            'sprzedaz': 'sprzedaż',
        },
        'nazwy_stron': {
            'kupujacy': 'kupujący',
            'sprzedajacy': 'sprzedający',
        },
        'strona_doprecyzuj': 'Pytasz jako kupujący czy jako sprzedający na Allegro?',
        'guardy': {
            'za_krotkie': 'Napisz proszę pełne pytanie.',
            'za_dlugie': 'Pytanie jest za długie, opisz jeden problem na raz.',
            'nie_rozumiem': 'Nie rozumiem pytania. Czy możesz napisać je inaczej?',
            'zly_alfabet': 'Pomagam w sprawach Allegro po polsku, napisz proszę pytanie po polsku.',
            'injekcja': 'Mogę pomóc tylko w sprawach zakupów, konta i płatności.',
        },
        'bledy': {
            'limit_zapytan': 'Limit zapytań demo osiągnięty, spróbuj później.',
            'model_niedostepny': 'Model chwilowo niedostępny, spróbuj ponownie za chwilę.',
            'limit_wysylek': 'Limit wysyłek demo osiągnięty, spróbuj później.',
            'zly_email': 'Podaj poprawny adres email.',
            'wysylka_nieudana': 'Wysyłka się nie powiodła, spróbuj ponownie.',
        },
        'wysylka': {
            'temat_sprzedawca': '[Zgłoszenie {ticket}] {temat}',
            'temat_sprzedawca_korekta': '[Zgłoszenie {ticket}, korekta] {temat}',
            'tresc_sprzedawca': 'Numer zgłoszenia: {ticket}\nKategoria: {kategoria}\nAdres klienta: {email}\n\n{tresc}',
            'temat_klient': 'Potwierdzenie zgłoszenia {ticket}',
            'temat_klient_korekta': 'Korekta zgłoszenia {ticket}',
            'tresc_klient': (
                'Twoje zgłoszenie zostało przekazane do sprzedawcy.\n\n'
                'Numer zgłoszenia: {ticket}\n'
                'Kategoria sprawy: {kategoria}\n\n'
                'Treść wiadomości:\n{tresc}\n\n'
                '{klauzula}'
            ),
            'klauzula': 'Informacja: to demo nie przechowuje Twojego adresu ani treści wiadomości po wysyłce.',
            'brak_kategorii': 'brak',
        },
        'zaimki': {'to', 'tego', 'tym', 'tam', 'ten', 'ta', 'te', 'nim', 'niej', 'nich'},
        'followup_prefiksy': ('a ',),
        'mail_czasowniki': {'napisz', 'napiszesz', 'napisać', 'przygotuj', 'przygotować',
                            'pomóż', 'pomoz', 'pomożesz'},
        'mail_obiekty': {'mail', 'maila', 'maile', 'mailu', 'meila', 'wiadomość', 'wiadomosc',
                         'wiadomości', 'reklamacja', 'reklamację', 'reklamacje', 'reklamacji',
                         'reklamacyjny', 'reklamacyjnego', 'reklamacyjną', 'zwrot', 'zwrotu',
                         'fakturę', 'fakturze', 'fakturą'},
        'router_model': os.getenv('ROUTER_MODEL', os.getenv('SEDZIA_MODEL', MODEL_11B)),
        'mail_doprecyzuj': (
            'Nie jestem pewien, o jaki rodzaj wiadomości chodzi: reklamację uszkodzonego towaru, '
            'zwrot, prośbę o fakturę czy zgłoszenie braku odpowiedzi sprzedawcy? Napisz proszę dokładniej.'
        ),
        'mail_kategorie': {
            'reklamacja': {
                'artykul': 'jak-rozpoczac-dyskusje-i-wyjasnic-problem-ze-sprzedajacym-WEDKYqnEvik',
                'zapytanie': 'jak rozpocząć dyskusję i wyjaśnić problem ze sprzedającym',
                'oferta': 'Przygotuj proszę szkic maila reklamacyjnego do sprzedawcy.',
                'slowa': {'uszkodzony', 'uszkodzone', 'uszkodzona', 'wadliwy', 'wadliwe', 'wadliwa', 'wada',
                          'zepsuty', 'zepsute', 'zepsuta', 'reklamacja', 'reklamację', 'reklamacje',
                          'reklamacji', 'reklamować', 'oszukany', 'oszukana', 'niezgodny', 'niezgodne'},
                'frazy': ('nie dziala', 'nie działa'),
                'naglowek_ui': 'Szkic maila reklamacyjnego',
            },
            'zwrot': {
                'artykul': 'jak-zwrocic-produkty-kupione-w-ramach-allegro-smart-dykrmbo5qTz',
                'zapytanie': 'jak zwrócić kupiony produkt, odstąpienie od umowy',
                'oferta': 'Przygotuj proszę szkic wiadomości o zwrocie produktu.',
                'slowa': {'zwrot', 'zwrotu', 'zwrócić', 'zwrocic', 'odstąpienie', 'odstapienie', 'odstąpić', 'odstapic'},
                'frazy': ('chce oddac towar', 'chcę oddać towar', 'chce zwrocic', 'chcę zwrócić'),
                'naglowek_ui': 'Szkic wiadomości o zwrocie',
            },
            'faktura': {
                'artykul': 'co-zrobic-aby-dostac-fakture-za-zakupy-LRbW0kGjlS3',
                'zapytanie': 'jak dostać fakturę za zakupy',
                'oferta': 'Przygotuj proszę szkic prośby o fakturę.',
                'slowa': {'faktura', 'fakturę', 'faktury', 'fakturze', 'fakturą', 'fakture'},
                'frazy': (),
                'naglowek_ui': 'Szkic prośby o fakturę',
            },
            'eskalacja': {
                'artykul': 'jak-rozpoczac-dyskusje-i-wyjasnic-problem-ze-sprzedajacym-WEDKYqnEvik',
                'zapytanie': 'sprzedawca nie odpowiada, zaangażowanie Allegro w dyskusję',
                'oferta': 'Przygotuj proszę szkic wiadomości z prośbą o zaangażowanie Allegro.',
                'slowa': set(),
                'frazy': ('nie odpowiada', 'odmawia pomocy', 'odmawia zwrotu',
                          'nie przyszła', 'nie przyszla', 'nie dotarła', 'nie dotarla',
                          'nie dostałem', 'nie dostalem', 'nie dostałam', 'nie dostalam',
                          'zaginęła', 'zaginela'),
                'naglowek_ui': 'Szkic zgłoszenia braku odpowiedzi sprzedawcy',
            },
        },
        'markery_stron': {
            'kupujacy': {
                'slowa': {'kupiłem', 'kupilem', 'kupiłam', 'kupilam', 'zamówiłem', 'zamowilem',
                          'zamówiłam', 'zamowilam', 'zamówienie', 'zamowienie', 'zamówienia', 'zamowienia',
                          'zamówień', 'zamowien', 'przesyłka', 'przesylka', 'przesyłkę', 'przesylke',
                          'przesyłki', 'przesylki', 'paczka', 'paczke', 'paczkę', 'paczki'},
                'frazy': ('moja przesyłka', 'moja przesylka', 'moje zamówienie', 'moje zamowienie',
                          'sprzedawca nie', 'moja paczka'),
            },
            'sprzedajacy': {
                'slowa': {'sprzedaję', 'sprzedaje', 'sprzedajesz', 'wystawiam', 'wystawiłem', 'wystawilem',
                          'wystawić', 'wystawic', 'prowizja', 'prowizję', 'prowizje', 'prowizji',
                          'wypłata', 'wyplata', 'wypłatę', 'wyplate', 'wypłaty', 'wyplaty', 'aukcje',
                          'aukcja', 'aukcji'},
                'frazy': ('moja oferta', 'moje oferty', 'mój kupujący', 'moj kupujacy', 'moi kupujący',
                          'moi kupujacy', 'allegro ads', 'moje aukcje', 'wystawić przedmiot',
                          'wystawic przedmiot', 'moja sprzedaż', 'moja sprzedaz', 'mój sklep', 'moj sklep'),
            },
        },
    },
    'en': {
        'embedder': 'intfloat/multilingual-e5-base',
        'query_prefix': 'query: ',
        'passage_prefix': 'passage: ',
        'lemma_lang': 'en',
        'freq_lang': 'en',
        'suffix': os.getenv('SUFFIX_EN', '_en'),
        'model': os.getenv('MODEL_EN', MODEL_DOMYSLNY),
        'sedzia_model': os.getenv('SEDZIA_MODEL_EN', 'allenai/Olmo-3-7B-Instruct'),
        'prog_rerank': -3.6,
        'prog_pokrycia': 0.35,
        'brak_wiedzy': (
            "I couldn't find this information in Allegro's help base. "
            'Check directly in the Help Center: https://allegro.pl/help'
        ),
        'nie_zrozumialem': "Sorry, I didn't understand the question, could you rephrase it?",
        'kroki': {
            'sprawdzam_pytanie': 'Checking the question',
            'poprawiam_literowki': 'Fixing typos',
            'szkic_wiadomosci': 'Preparing a draft message to the seller',
            'przepisuje_pytanie': 'Rewriting the question from the conversation context',
            'zamieniam_na_wektor': 'Turning the question into a vector',
            'przeszukuje_baze': 'Searching the knowledge base and ranking results',
            'rozpoznaje_strone': "Recognizing whether you're asking as a buyer or a seller",
            'wybieram_strone': 'Deciding the side of the question: {strona}',
            'poza_zakresem': 'Outside the help base scope, declining',
            'sprawdzam_kontekst': 'Checking whether the context answers the question',
            'generuje_odpowiedz': 'Generating the answer (section: {agent})',
        },
        'nazwy_sekcji': {
            'konto': 'account',
            'zakupy': 'shopping',
            'platnosci': 'payments',
            'sprzedaz': 'selling',
        },
        'nazwy_stron': {
            'kupujacy': 'buyer',
            'sprzedajacy': 'seller',
        },
        'strona_doprecyzuj': 'Are you asking as a buyer or as a seller on Allegro?',
        'guardy': {
            'za_krotkie': 'Please write a complete question.',
            'za_dlugie': 'The question is too long, please describe one issue at a time.',
            'nie_rozumiem': "I don't understand the question. Could you phrase it differently?",
            'zly_alfabet': 'I help with Allegro in English, please write your question in English.',
            'injekcja': 'I can only help with shopping, account, and payment questions.',
        },
        'bledy': {
            'limit_zapytan': 'Demo request limit reached, please try again later.',
            'model_niedostepny': 'The model is temporarily unavailable, please try again in a moment.',
            'limit_wysylek': 'Demo sending limit reached, please try again later.',
            'zly_email': 'Please enter a valid email address.',
            'wysylka_nieudana': 'Sending failed, please try again.',
        },
        'wysylka': {
            'temat_sprzedawca': '[Ticket {ticket}] {temat}',
            'temat_sprzedawca_korekta': '[Ticket {ticket}, correction] {temat}',
            'tresc_sprzedawca': 'Ticket number: {ticket}\nCategory: {kategoria}\nCustomer address: {email}\n\n{tresc}',
            'temat_klient': 'Confirmation of ticket {ticket}',
            'temat_klient_korekta': 'Correction to ticket {ticket}',
            'tresc_klient': (
                'Your request has been forwarded to the seller.\n\n'
                'Ticket number: {ticket}\n'
                'Case category: {kategoria}\n\n'
                'Message content:\n{tresc}\n\n'
                '{klauzula}'
            ),
            'klauzula': "Note: this demo doesn't store your address or message content after sending.",
            'brak_kategorii': 'none',
        },
        'zaimki': {'it', 'that', 'this', 'those', 'them', 'one'},
        'followup_prefiksy': ('and ', 'what about', 'how about', 'what if'),
        'mail_czasowniki': {'write', 'draft', 'prepare', 'help'},
        'mail_obiekty': {'email', 'e-mail', 'mail', 'message', 'complaint', 'return', 'invoice', 'receipt'},
        'router_model': os.getenv('ROUTER_MODEL_EN', os.getenv('SEDZIA_MODEL_EN', 'allenai/Olmo-3-7B-Instruct')),
        'mail_doprecyzuj': (
            "I'm not sure which kind of message you need: a complaint about a damaged item, a return, "
            'an invoice request, or a report that the seller is not responding? Please be more specific.'
        ),
        'mail_kategorie': {
            'reklamacja': {
                'artykul': 'jak-rozpoczac-dyskusje-i-wyjasnic-problem-ze-sprzedajacym-WEDKYqnEvik',
                'zapytanie': 'How to start a discussion and resolve a problem with a seller',
                'oferta': 'Please prepare a draft complaint email to the seller.',
                'slowa': {'damaged', 'defective', 'broken', 'faulty', 'complaint', 'complaints',
                          'scam', 'scammed'},
                'frazy': ("isn't working", 'is not working'),
                'naglowek_ui': 'Draft complaint email',
            },
            'zwrot': {
                'artykul': 'jak-zwrocic-produkty-kupione-w-ramach-allegro-smart-dykrmbo5qTz',
                'zapytanie': 'how to return a purchased product, withdrawal from the contract',
                'oferta': 'Please prepare a draft message about returning the product.',
                'slowa': {'return', 'refund', 'withdraw'},
                'frazy': ('want to return', 'want a refund'),
                'naglowek_ui': 'Draft return message',
            },
            'faktura': {
                'artykul': 'co-zrobic-aby-dostac-fakture-za-zakupy-LRbW0kGjlS3',
                'zapytanie': 'how to get an invoice for a purchase',
                'oferta': 'Please prepare a draft invoice request.',
                'slowa': {'invoice', 'receipt'},
                'frazy': (),
                'naglowek_ui': 'Draft invoice request',
            },
            'eskalacja': {
                'artykul': 'jak-rozpoczac-dyskusje-i-wyjasnic-problem-ze-sprzedajacym-WEDKYqnEvik',
                'zapytanie': 'seller not responding, involving Allegro in the discussion',
                'oferta': 'Please prepare a draft message asking Allegro to get involved.',
                'slowa': {'unresponsive'},
                'frazy': ('not responding', 'not responded', 'hasn\'t responded', 'has not responded',
                          'refuses to help', 'refuses a refund',
                          'never arrived', "hasn't arrived", 'has not arrived', 'didn\'t arrive',
                          'did not arrive', 'lost package'),
                'naglowek_ui': 'Draft escalation message',
            },
        },
        'markery_stron': {
            'kupujacy': {
                'slowa': {'bought', 'ordered', 'purchase', 'purchased', 'purchasing'},
                'frazy': ('my package', 'my order', 'my shipment', 'my parcel', 'seller is not',
                          "seller isn't", "seller won't", 'seller refuses', 'seller does not'),
            },
            'sprzedajacy': {
                'slowa': {'sell', 'selling', 'sold', 'sells', 'list', 'listing', 'listed',
                          'commission', 'commissions', 'payout', 'payouts'},
                'frazy': ('my offer', 'my offers', 'my listing', 'my listings', 'my buyer',
                          'my buyers', 'allegro ads', 'my shop', 'my store', 'my payout'),
            },
        },
    },
}

DOMYSLNY_JEZYK = 'pl'
