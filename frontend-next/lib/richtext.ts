function escapujHtml(tekst: string): string {
  return tekst.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function inlineDoHtml(tekst: string): string {
  let wynik = escapujHtml(tekst);
  wynik = wynik.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  wynik = wynik.replace(/_(.+?)_/g, '<i>$1</i>');
  return wynik;
}

export function markdownDoHtml(tekst: string): string {
  const linie = tekst.split('\n');
  const czesci: string[] = [];
  let wLiscie = false;

  for (const linia of linie) {
    const dopasowanie = /^[•\-]\s+(.*)$/.exec(linia);
    if (dopasowanie) {
      if (!wLiscie) {
        czesci.push('<ul>');
        wLiscie = true;
      }
      czesci.push(`<li>${inlineDoHtml(dopasowanie[1])}</li>`);
      continue;
    }
    if (wLiscie) {
      czesci.push('</ul>');
      wLiscie = false;
    }
    czesci.push(`<div>${linia ? inlineDoHtml(linia) : '<br>'}</div>`);
  }
  if (wLiscie) czesci.push('</ul>');
  return czesci.join('');
}

function inlineDzieci(wezel: Node): string {
  let wynik = '';
  wezel.childNodes.forEach((dziecko) => {
    wynik += inlineWezel(dziecko);
  });
  return wynik;
}

function inlineWezel(wezel: Node): string {
  if (wezel.nodeType === Node.TEXT_NODE) return wezel.textContent ?? '';
  if (wezel.nodeType !== Node.ELEMENT_NODE) return '';
  const el = wezel as HTMLElement;
  const tag = el.tagName.toLowerCase();
  if (tag === 'br') return '\n';
  if (tag === 'b' || tag === 'strong') return `**${inlineDzieci(el)}**`;
  if (tag === 'i' || tag === 'em') return `_${inlineDzieci(el)}_`;
  return inlineDzieci(el);
}

function jestSamymBr(el: HTMLElement): boolean {
  return (
    el.childNodes.length === 1 &&
    el.firstChild !== null &&
    el.firstChild.nodeType === Node.ELEMENT_NODE &&
    (el.firstChild as HTMLElement).tagName.toLowerCase() === 'br'
  );
}

export function htmlDoMarkdown(root: HTMLElement): string {
  const linie: string[] = [];

  root.childNodes.forEach((dziecko) => {
    if (dziecko.nodeType === Node.TEXT_NODE) {
      linie.push(dziecko.textContent ?? '');
      return;
    }
    if (dziecko.nodeType !== Node.ELEMENT_NODE) return;
    const el = dziecko as HTMLElement;
    const tag = el.tagName.toLowerCase();
    if (tag === 'ul' || tag === 'ol') {
      Array.from(el.children).forEach((li) => {
        if (li.tagName.toLowerCase() === 'li') {
          linie.push(`• ${inlineDzieci(li)}`);
        }
      });
      return;
    }
    if (tag === 'br' || jestSamymBr(el)) {
      linie.push('');
      return;
    }
    inlineWezel(el)
      .split('\n')
      .forEach((l) => linie.push(l));
  });

  return linie.join('\n');
}
