import os

MODEL_11B = 'speakleash/Bielik-11B-v3.0-Instruct'

LANG = {
    'pl': {
        'embedder': 'sdadas/mmlw-retrieval-roberta-base',
        'query_prefix': 'zapytanie: ',
        'passage_prefix': '',
        'lemma_lang': 'pl',
        'freq_lang': 'pl',
        'suffix': '',
        'model': os.getenv('MODEL', MODEL_11B),
        'sedzia_model': os.getenv('SEDZIA_MODEL', os.getenv('MODEL', MODEL_11B)),
        'prog_rerank': -4.3,
        'prog_pokrycia': 0.20,
        'brak_wiedzy': (
            'Nie znalazłem tej informacji w bazie pomocy Allegro. '
            'Sprawdź bezpośrednio w Centrum Pomocy: https://allegro.pl/pomoc'
        ),
        'nie_zrozumialem': 'Przepraszam, nie zrozumiałem pytania — czy możesz napisać je inaczej?',
        'zaimki': {'to', 'tego', 'tym', 'tam', 'ten', 'ta', 'te', 'nim', 'niej', 'nich'},
        'followup_prefiksy': ('a ',),
        'mail_czasowniki': {'napisz', 'napiszesz', 'napisać', 'przygotuj', 'przygotować',
                            'pomóż', 'pomoz', 'pomożesz'},
        'mail_obiekty': {'mail', 'maila', 'maile', 'mailu', 'meila', 'wiadomość', 'wiadomosc',
                         'wiadomości', 'reklamacja', 'reklamację', 'reklamacje', 'reklamacji',
                         'reklamacyjny', 'reklamacyjnego', 'reklamacyjną', 'zwrot', 'zwrotu',
                         'fakturę', 'fakturze', 'fakturą'},
        'router_model': os.getenv('ROUTER_MODEL', os.getenv('SEDZIA_MODEL', os.getenv('MODEL', MODEL_11B))),
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
                'frazy': ('nie odpowiada', 'odmawia pomocy', 'odmawia zwrotu'),
                'naglowek_ui': 'Szkic zgłoszenia braku odpowiedzi sprzedawcy',
            },
        },
    },
    'en': {
        'embedder': 'intfloat/multilingual-e5-base',
        'query_prefix': 'query: ',
        'passage_prefix': 'passage: ',
        'lemma_lang': 'en',
        'freq_lang': 'en',
        'suffix': '_en',
        'model': os.getenv('MODEL_EN', 'allenai/Olmo-3-7B-Instruct'),
        'sedzia_model': os.getenv('SEDZIA_MODEL_EN', os.getenv('MODEL_EN', 'allenai/Olmo-3-7B-Instruct')),
        'prog_rerank': -3.6,
        'prog_pokrycia': 0.35,
        'brak_wiedzy': (
            "I couldn't find this information in Allegro's help base. "
            'Check directly in the Help Center: https://allegro.pl/help'
        ),
        'nie_zrozumialem': "Sorry, I didn't understand the question — could you rephrase it?",
        'zaimki': {'it', 'that', 'this', 'those', 'them', 'one'},
        'followup_prefiksy': ('and ', 'what about', 'how about', 'what if'),
        'mail_czasowniki': {'write', 'draft', 'prepare', 'help'},
        'mail_obiekty': {'email', 'e-mail', 'mail', 'message', 'complaint', 'return', 'invoice', 'receipt'},
        'router_model': os.getenv('ROUTER_MODEL_EN', os.getenv('SEDZIA_MODEL_EN', os.getenv('MODEL_EN', 'allenai/Olmo-3-7B-Instruct'))),
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
                          'refuses to help', 'refuses a refund'),
                'naglowek_ui': 'Draft escalation message',
            },
        },
    },
}

DOMYSLNY_JEZYK = 'pl'
