import type { Cytat } from './chat';

export interface Zrodlo {
  url: string;
  tytul: string;
  domena: string;
}

function zbudujZrodlo(url: string, tytul: string | null | undefined): Zrodlo {
  try {
    const u = new URL(url);
    const domena = u.hostname.replace(/^www\./, '');
    if (tytul) return { url, tytul, domena };
    const segmenty = u.pathname.split('/').filter(Boolean);
    const ostatni = segmenty[segmenty.length - 1] ?? '';
    const bezHash = ostatni.replace(/-[a-zA-Z0-9]{6,}$/, '');
    const slowa = bezHash.split(/[-_]/).filter(Boolean);
    const tytulZeSlugu = slowa.length > 0
      ? slowa.map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
      : domena;
    return { url, tytul: tytulZeSlugu, domena };
  } catch {
    return { url, tytul: tytul ?? url, domena: '' };
  }
}

export function przygotujOdpowiedz(
  tekst: string,
  citations: Cytat[]
): { tekst: string; zrodla: Zrodlo[]; zacytowano: boolean } {
  if (citations.length === 0) return { tekst, zrodla: [], zacytowano: false };

  const unikalneUrl: string[] = [];
  const tytulyUrl = new Map<string, string | null | undefined>();
  const indeksUrl = new Map<string, number>();
  for (const c of citations) {
    if (!indeksUrl.has(c.url)) {
      indeksUrl.set(c.url, unikalneUrl.length);
      unikalneUrl.push(c.url);
      tytulyUrl.set(c.url, c.tytul);
    }
  }

  let zacytowano = false;
  const uzyteIndeksy = new Set<number>();
  const mapaN = new Map(citations.map((c) => [c.n, indeksUrl.get(c.url) as number]));
  const przepisany = tekst.replace(/\[(\d+)\]/g, (dopasowanie, n) => {
    const indeks = mapaN.get(Number(n));
    if (indeks === undefined) return dopasowanie;
    zacytowano = true;
    uzyteIndeksy.add(indeks);
    return `[[${indeks + 1}]](${unikalneUrl[indeks]})`;
  });

  const widoczneUrl = zacytowano ? unikalneUrl.filter((_, i) => uzyteIndeksy.has(i)) : unikalneUrl;

  return {
    tekst: przepisany,
    zrodla: widoczneUrl.map((url) => zbudujZrodlo(url, tytulyUrl.get(url))),
    zacytowano,
  };
}

const URL_REGEX = /https?:\/\/\S+|\bwww\.\S+/gi;
const NAGLOWEK_ZRODEL =
  /^[ \t]*\**(?:źródła|źródło|zrodla|zrodlo|sources|source|references|bibliografia)\**[ \t]*:?[ \t]*((?:\[\d+\][ \t]*,?[ \t]*)*)$/i;
const LINIA_NUMERU = /^[ \t]*\[\d+\]/;

export function oczyscPodglad(tekst: string): string {
  const bezUrl = tekst.replace(URL_REGEX, '');
  const linie = bezUrl.split('\n');
  for (let i = 0; i < linie.length; i++) {
    if (NAGLOWEK_ZRODEL.test(linie[i])) {
      const reszta = linie.slice(i + 1);
      const samSpis = reszta.every((l) => !l.trim() || LINIA_NUMERU.test(l));
      if (samSpis) return linie.slice(0, i).join('\n').replace(/\s+$/, '');
      return [...linie.slice(0, i), ...reszta].join('\n');
    }
  }
  return bezUrl;
}
