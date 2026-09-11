const PODPUNKT = /^[ \t]*[a-z][.)][ \t]+\S/;

export function rozdzielPodpunkty(tekst: string): string {
  const linie = tekst.split('\n');
  for (let i = 1; i < linie.length; i++) {
    const poprzednia = linie[i - 1];
    if (PODPUNKT.test(linie[i]) && poprzednia.trim() && !poprzednia.endsWith('\\')) {
      linie[i - 1] = poprzednia.replace(/[ \t]+$/, '') + '\\';
    }
  }
  return linie.join('\n');
}
