# Jednorazowy skrypt: rozbija zestaw OOD w dane_measure.json na trzy klasy
# (spoza tematu, allegro poza baza, do audytu), zeby kalibracja progu globalnego
# mogla je traktowac osobno. Klucz OOD zostaje nietkniety dla starych skryptow.
import json

SCIEZKA = 'Pomiary/dane_measure.json'

OOD_SPOZA_TEMATU = [
    'ile to jest dwa plus dwa',
    'jaka jest stolica Francji',
    'podaj przepis na pierogi',
    'kto wygral mistrzostwa swiata w pilce noznej',
    'jak zmienic olej w samochodzie',
    'napisz wiersz o jesieni',
    'jaka jest dzisiaj pogoda',
    'przetlumacz dzien dobry na angielski',
    'kto jest prezydentem Polski',
    'opowiedz mi dowcip',
    'jak schudnac dziesiec kilogramow',
    'napisz kod w pythonie sortujacy liste',
    'jak sprzedawac na olx',
    'ile kosztuje najnowszy iphone',
    'jak zalozyc wlasna firme',
    'jaka jest najlepsza karta graficzna do gier',
    'jak ugotowac ryz zeby sie nie kleil',
    'poradz mi cos na przeziebienie',
    'kiedy beda promocje na black friday',
]

OOD_ALLEGRO_POZA_BAZA = [
    'jaki jest numer telefonu do allegro',
    'czy allegro ma sklepy stacjonarne',
    'aplikacja allegro zawiesza sie na moim telefonie',
    'kto jest wlascicielem allegro',
    'czy moge kupic akcje allegro na gieldzie',
    'czy amazon jest tanszy niz allegro',
    'ile zarabia kurier allegro',
]

OOD_DO_AUDYTU = [
    'ile allegro bierze prowizji od sprzedawcy',
    'jak wystawic przedmiot na sprzedaz',
    'jak promowac swoja oferte zeby byla wyzej',
]

with open(SCIEZKA, encoding='utf-8') as f:
    dane = json.load(f)

assert len(dane['OOD']) == 29, f"OOD ma {len(dane['OOD'])} pozycji, oczekiwano 29"

dane['OOD_SPOZA_TEMATU'] = OOD_SPOZA_TEMATU
dane['OOD_ALLEGRO_POZA_BAZA'] = OOD_ALLEGRO_POZA_BAZA
dane['OOD_DO_AUDYTU'] = OOD_DO_AUDYTU

with open(SCIEZKA, 'w', encoding='utf-8') as f:
    json.dump(dane, f, ensure_ascii=False, indent=1)

print(len(OOD_SPOZA_TEMATU), len(OOD_ALLEGRO_POZA_BAZA), len(OOD_DO_AUDYTU))
suma_zbior = set(OOD_SPOZA_TEMATU) | set(OOD_ALLEGRO_POZA_BAZA) | set(OOD_DO_AUDYTU)
print('pokrycie OOD:', suma_zbior == set(dane['OOD']))
print('OOD nietkniety:', len(dane['OOD']) == 29)
