const PODPUNKT = /^[ \t]*[a-z][.)][ \t]+\S/;
const PUNKT = /^(\d+[.)][ \t]+)\S/;
const PLYTKI_WYPUNKTOWANY = /^ {1,2}([-*+][ \t]+\S.*)$/;

export function rozdzielPodpunkty(tekst: string): string {
  const linie = tekst.split('\n');
  let wciecie: number | null = null;
  for (let i = 0; i < linie.length; i++) {
    const punkt = PUNKT.exec(linie[i]);
    const wypunktowany = PLYTKI_WYPUNKTOWANY.exec(linie[i]);
    if (punkt) {
      wciecie = punkt[1].length;
    } else if (wypunktowany && wciecie !== null) {
      linie[i] = ' '.repeat(wciecie) + wypunktowany[1];
    } else if (!linie[i].trim()) {
      wciecie = null;
    }
    const poprzednia = i > 0 ? linie[i - 1] : '';
    if (PODPUNKT.test(linie[i]) && poprzednia.trim() && !poprzednia.endsWith('\\')) {
      linie[i - 1] = poprzednia.replace(/[ \t]+$/, '') + '\\';
    }
  }
  return linie.join('\n');
}
