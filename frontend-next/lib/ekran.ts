import { useSyncExternalStore } from 'react';

interface ZapytanieMedia {
  subskrybuj: (zmiana: () => void) => () => void;
  stan: () => boolean;
}

function zapytanieMedia(zapytanie: string): ZapytanieMedia {
  return {
    subskrybuj: (zmiana) => {
      const lista = window.matchMedia(zapytanie);
      lista.addEventListener('change', zmiana);
      return () => lista.removeEventListener('change', zmiana);
    },
    stan: () => window.matchMedia(zapytanie).matches,
  };
}

const WASKI = zapytanieMedia('(max-width: 767px)');
const PANEL_NAKLADKA = zapytanieMedia('(max-width: 1099px)');

function stanSerwera(): boolean {
  return false;
}

export function useWaskiEkran(): boolean {
  return useSyncExternalStore(WASKI.subskrybuj, WASKI.stan, stanSerwera);
}

export function usePanelJakoNakladka(): boolean {
  return useSyncExternalStore(PANEL_NAKLADKA.subskrybuj, PANEL_NAKLADKA.stan, stanSerwera);
}
