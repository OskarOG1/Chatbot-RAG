import type { Cytat } from './chat';

export interface Zrodlo {
  url: string;
  tytul: string;
  domena: string;
}

function zbudujZrodlo(url: string): Zrodlo {
  try {
    const u = new URL(url);
    const domena = u.hostname.replace(/^www\./, '');
    const segmenty = u.pathname.split('/').filter(Boolean);
    const ostatni = segmenty[segmenty.length - 1] ?? '';
    const bezHash = ostatni.replace(/-[a-zA-Z0-9]{6,}$/, '');
    const slowa = bezHash.split(/[-_]/).filter(Boolean);
    const tytul = slowa.length > 0
      ? slowa.map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')
      : domena;
    return { url, tytul, domena };
  } catch {
    return { url, tytul: url, domena: '' };
  }
}

export function przygotujOdpowiedz(tekst: string, citations: Cytat[]): { tekst: string; zrodla: Zrodlo[] } {
  if (citations.length === 0) return { tekst, zrodla: [] };

  const unikalneUrl: string[] = [];
  const indeksUrl = new Map<string, number>();
  for (const c of citations) {
    if (!indeksUrl.has(c.url)) {
      indeksUrl.set(c.url, unikalneUrl.length);
      unikalneUrl.push(c.url);
    }
  }

  const mapaN = new Map(citations.map((c) => [c.n, indeksUrl.get(c.url) as number]));
  const przepisany = tekst.replace(/\[(\d+)\]/g, (dopasowanie, n) => {
    const indeks = mapaN.get(Number(n));
    return indeks === undefined ? dopasowanie : `[[${indeks + 1}]](${unikalneUrl[indeks]})`;
  });

  return { tekst: przepisany, zrodla: unikalneUrl.map(zbudujZrodlo) };
}
