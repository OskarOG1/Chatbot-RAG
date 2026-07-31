import argparse
import json
import shutil
from pathlib import Path
from lang_config import LANG

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / 'RAG'


def wczytaj(sciezka: Path) -> list[dict]:
    with open(sciezka, encoding='utf-8') as r:
        return json.load(r)


def main(lang: str = 'pl') -> None:
    suffix = LANG[lang]['suffix']
    sciezka_kupujacy = RAG_DIR / f'chunks_kupujacy{suffix}.json'
    sciezka_sprzedaz = RAG_DIR / f'chunks_sprzedaz{suffix}.json'
    sciezka_scalona = RAG_DIR / f'chunks{suffix}.json'

    if not sciezka_kupujacy.exists():
        if not sciezka_scalona.exists():
            raise SystemExit(
                f'brak {sciezka_kupujacy} i brak {sciezka_scalona}, nie mam z czego zbudować bazy kupujących'
            )
        shutil.copy2(sciezka_scalona, sciezka_kupujacy)
        print(f'zapisano bazę kupujących: {sciezka_kupujacy}')

    kupujacy = wczytaj(sciezka_kupujacy)
    sprzedaz = wczytaj(sciezka_sprzedaz) if sciezka_sprzedaz.exists() else []

    scalony = kupujacy + sprzedaz

    if scalony[:len(kupujacy)] != kupujacy:
        raise SystemExit('pierwsze pozycje scalonego korpusu nie zgadzają się z bazą kupujących, przerywam')

    if sciezka_scalona.exists():
        shutil.copy2(sciezka_scalona, sciezka_scalona.with_suffix(sciezka_scalona.suffix + '.bak'))

    with open(sciezka_scalona, 'w', encoding='utf-8') as w:
        json.dump(scalony, w, ensure_ascii=False, indent=2)

    print(f'kupujący: {len(kupujacy)} chunków, sprzedaż: {len(sprzedaz)} chunków, razem: {len(scalony)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='pl', choices=list(LANG))
    args = parser.parse_args()
    main(args.lang)
