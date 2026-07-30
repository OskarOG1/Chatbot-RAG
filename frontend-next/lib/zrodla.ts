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

export function zrodlaZCytatow(citations: Cytat[]): Zrodlo[] {
  const unikalne = new Map<string, Cytat>();
  for (const c of citations) {
    if (!unikalne.has(c.url)) unikalne.set(c.url, c);
  }
  return Array.from(unikalne.values()).map((c) => zbudujZrodlo(c.url));
}

export function linkujCytaty(tekst: string, citations: Cytat[]): string {
  if (citations.length === 0) return tekst;
  const mapa = new Map(citations.map((c) => [c.n, c.url]));
  return tekst.replace(/\[(\d+)\]/g, (dopasowanie, n) => {
    const url = mapa.get(Number(n));
    return url ? `[[${n}]](${url})` : dopasowanie;
  });
}
