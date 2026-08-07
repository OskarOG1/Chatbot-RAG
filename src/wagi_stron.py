# Wygenerowano przez Pomiary/ucz_wagi_stron.py, 2026-08-07T12:59:41.562715+00:00 UTC, na 3896
# przykladach z RAG/pytania_realne.jsonl (cala baza). TAU_MOCNY/TAU_SLABY/Z_SILNY to
# srednia z 5 foldow walidacji krzyzowej. Patrz Pomiary/PLAN_WAGI_STRON.md,
# Pomiary/PLAN_KALIBRACJA_R9.md i Pomiary/POMIAR_WAGI_STRON.md. Nie edytowac recznie,
# ponowne uruchomienie skryptu nadpisuje ten plik.

import math
import simplemma
from spell import tokenize_words, MIN_DLUGOSC
from strony import prior_strony

TAU_MOCNY = 7.8616
TAU_SLABY = 6.8341
Z_SILNY = 3.5

WAGI = {
    'zakup': -7.853431281287691,
    'sprzedaż': 7.749943708678513,
    'zwrot': -7.238399418479116,
    'wośp': 5.487320408460488,
    'klient': 5.452081061576384,
    'oferta': 4.949568466227157,
    'towar': -4.713794885662829,
    'aukcja': 4.708988837760196,
    'inpost': 4.695835755842054,
    'moneta': -4.5555966136890795,
    'link': -4.5509187492066046,
    'zakupić': -4.290405719247932,
    'podjazd': 4.289042297817092,
    'chcieć': -4.218099947066148,
    'wysyłka': 4.148740293557672,
    'płatność': -4.115300140825465,
    'zakupy': -4.008584486916558,
    'kurier': 3.9975246044893096,
    'wystawić': 3.9721092295790377,
    'sprzedający': -3.9632502027226955,
    'kupić': -3.9297225976474697,
    'przekierować': -3.8955498614464985,
    'etykieta': 3.870906331002621,
    'odesłać': -3.813362059421378,
    'sprzedać': 3.7798944954384934,
    'otrzymać': -3.741828140114862,
    'nadanie': 3.697384112389943,
    'opłata': 3.6376611068243943,
    'jakość': 3.633703266040977,
    'kupon': -3.6035711608790555,
    'zwrócić': -3.5731704806570233,
    'allegro': 3.469414571725966,
    'kupować': 3.4445446388300915,
    'pieniądz': -3.399406841766008,
    'prowizja': 3.324737147546062,
    'wystawiać': 3.272717976034725,
    'blokada': 3.216411465177108,
    'wypłata': 3.2041915262173375,
    'paczek': 3.1310333337258234,
    'inny': -2.878912242680595,
    'moja': -2.867252329619464,
    'ochrona': -2.8643545465853295,
    'zrobić': -2.8588441847424026,
    'Orlen': 2.7252964371392925,
    'weryfikacja': 2.7239782919551714,
    'zapłacić': -2.7160004512270906,
    'alegro': -2.698618963373498,
    'kod': -2.5923566138641916,
    'błąd': 2.569871751903968,
    'paczka': -2.566834375840159,
    'kiedy': -2.547200454016417,
    'przedmiot': 2.5245794681226776,
    'prywatny': 2.503182767924085,
    'nadać': 2.4341465245268776,
    'wygenerować': 2.4258945260141376,
    'zablokować': 2.417404404679838,
    'automatyczny': 2.412688408118599,
    'pobrać': -2.3690571077477753,
    'tylko': -2.355868744289666,
    'zostać': -2.3364003987030886,
    'skrytka': -2.2425055044281375,
    'kupujący': 2.2245093400493863,
    'działać': -2.1886009746631148,
    'móc': -2.183953230910873,
    'sprzedawać': 2.1592454911957626,
    'sprzedawca': -2.1516759673401804,
    'przesylka': -2.1460994655552312,
    'oszustwo': -2.108953508432444,
    'odzyskać': -2.09548461348179,
    'gdzie': -2.055678775430642,
    'dana': 2.013444086817716,
    'konto': 2.0102415078292832,
    'witać': -1.9796495851551712,
    'adres': -1.9723225420451118,
    'zamowilem': -1.96,
    'sprzedaj': 1.8275298637765198,
    'zamowienia': -1.433085483542546,
    'kupilem': -1.1698769022847064,
    'wystawic': 0.9180859808166432,
    'wyplatać': 0.9180859808166432,
    'zamowilam': -0.8270635866427202,
    'kupilam': -0.8270635866427202,
    'przesylke': -0.7239296035263163,
    'wyplaty': 0.6490667778021496,
    'wystawilem': 0.6490667778021496,
    'wyplate': 0.6490667778021496,
    'paczke': -0.46579627775187765,
}


def ocena_pytania(lematy_pytania: set, tabela: dict) -> dict:
    """P3: suma znormalizowana przez sqrt(k), k = liczba dopasowanych lematow, zeby dlugie
    pytanie nie przekraczalo progu samym nazbieraniem slabych wag. P2: dowod to |z| pojedynczego
    najmocniejszego dopasowanego lematu, osobno od sumy, bo suma wybiera strone, a dowod
    rozstrzyga, czy w ogole wolno miec zdanie."""
    dopasowane = [tabela[t] for t in lematy_pytania if t in tabela]
    if not dopasowane:
        return {'suma_norm': 0.0, 'dowod': 0.0, 'k': 0}
    suma = sum(dopasowane)
    return {'suma_norm': suma / math.sqrt(len(dopasowane)),
            'dowod': max(abs(w) for w in dopasowane), 'k': len(dopasowane)}


def przewidziana_strona(suma_norm: float) -> str | None:
    if suma_norm > 0:
        return 'sprzedajacy'
    if suma_norm < 0:
        return 'kupujacy'
    return None


def zdecyduj_r9(suma_norm: float, dowod: float, tau_mocny: float, tau_slaby: float,
                 z_silny: float, agent_poprzedni: str | None,
                 czy_followup: bool) -> tuple[str | None, str | None]:
    strona = przewidziana_strona(suma_norm)
    ma_dowod = strona is not None and dowod >= z_silny
    if ma_dowod and abs(suma_norm) >= tau_mocny:
        return strona, 'leksykalna'
    if agent_poprzedni and czy_followup:
        return ('sprzedajacy' if agent_poprzedni == 'sprzedaz' else 'kupujacy'), 'lepka'
    if ma_dowod and abs(suma_norm) >= tau_slaby:
        return strona, 'leksykalna_slaba'
    return None, None


def prior_wazony(query, agent_poprzedni, lang, czy_followup):
    if lang != 'pl':
        return prior_strony(query, agent_poprzedni, lang, czy_followup)
    tokeny = [t for t in tokenize_words(query) if len(t) >= MIN_DLUGOSC]
    lematy_pytania = {simplemma.lemmatize(t, lang='pl') for t in tokeny}
    ocena = ocena_pytania(lematy_pytania, WAGI)
    return zdecyduj_r9(ocena['suma_norm'], ocena['dowod'], TAU_MOCNY, TAU_SLABY, Z_SILNY, agent_poprzedni, czy_followup)
