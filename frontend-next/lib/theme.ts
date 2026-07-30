import { createContext, useContext } from 'react';

export type ThemeName = 'light' | 'dark';

export const DISPLAY = "var(--font-bricolage), 'Plus Jakarta Sans', system-ui, sans-serif";
export const BODY = "var(--font-plex-sans), system-ui, sans-serif";
export const MONO = "var(--font-plex-mono), ui-monospace, monospace";

export const ACCENT = '#FF5A00';

export interface ThemeTokens {
  canvas: string;
  rail: string;
  surface: string;
  raised: string;
  ink: string;
  ink2: string;
  ink3: string;
  line: string;
  lineSoft: string;
  userBg: string;
  userInk: string;
  accent: string;
  accentSoft: string;
  accentLine: string;
  accentInk: string;
  shadow: string;
  shadowLift: string;
  dot: string;
  markInk: string;
  bgApp: string;
  bgSurface: string;
  bgBubbleBot: string;
  bgBubbleUser: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
  accentHover: string;
  accentSoft2: string;
  accentSoftHover: string;
  accentText: string;
  success: string;
  toastBg: string;
  toastInk: string;
  inputBg: string;
}

const light = {
  canvas: '#F6F4F1',
  rail: '#FFFFFF',
  surface: '#FFFFFF',
  raised: '#FCFBF9',
  ink: '#1A1614',
  ink2: '#5C534D',
  ink3: '#8B8177',
  line: '#E6E1DB',
  lineSoft: '#EFEBE6',
  userBg: '#EDE9E3',
  userInk: '#332C27',
  accent: ACCENT,
  accentSoft: '#FFF0E8',
  accentLine: '#FFD3BC',
  accentInk: '#C43E00',
  shadow: '0 1px 2px rgba(26,22,20,0.04), 0 8px 24px -12px rgba(26,22,20,0.10)',
  shadowLift: '0 2px 4px rgba(26,22,20,0.05), 0 20px 44px -20px rgba(26,22,20,0.22)',
  dot: '#1F9D55',
  markInk: '#FFFFFF',
};

const dark = {
  canvas: '#141110',
  rail: '#1A1615',
  surface: '#1F1B19',
  raised: '#26211E',
  ink: '#F5F1EE',
  ink2: '#A79D96',
  ink3: '#7C726B',
  line: '#302A27',
  lineSoft: '#282221',
  userBg: '#2A2422',
  userInk: '#EDE7E3',
  accent: ACCENT,
  accentSoft: '#2E1B11',
  accentLine: '#4A2A18',
  accentInk: '#FF8A50',
  shadow: '0 1px 2px rgba(0,0,0,0.4), 0 8px 24px -12px rgba(0,0,0,0.6)',
  shadowLift: '0 2px 6px rgba(0,0,0,0.5), 0 24px 48px -20px rgba(0,0,0,0.75)',
  dot: '#3FBF77',
  markInk: '#FFFFFF',
};

function zbuduj(p: typeof light): ThemeTokens {
  return {
    ...p,
    bgApp: p.canvas,
    bgSurface: p.surface,
    bgBubbleBot: p.raised,
    bgBubbleUser: p.userBg,
    textPrimary: p.ink,
    textSecondary: p.ink2,
    border: p.line,
    accentHover: p.accentInk,
    accentSoft2: p.accentSoft,
    accentSoftHover: p.raised,
    accentText: p.accentInk,
    success: p.dot,
    toastBg: p.ink,
    toastInk: p.canvas,
    inputBg: p.surface,
  };
}

export const THEMES: Record<ThemeName, ThemeTokens> = {
  light: zbuduj(light),
  dark: zbuduj(dark),
};

export const ThemeContext = createContext<ThemeTokens>(THEMES.light);

export function useTheme(): ThemeTokens {
  return useContext(ThemeContext);
}
