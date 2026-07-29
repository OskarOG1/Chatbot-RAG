import { createContext, useContext } from 'react';

export type ThemeName = 'light' | 'dark';

export interface ThemeTokens {
  bgApp: string;
  bgSurface: string;
  bgBubbleBot: string;
  bgBubbleUser: string;
  textPrimary: string;
  textSecondary: string;
  border: string;
  accent: string;
  accentHover: string;
  accentSoft: string;
  accentSoftHover: string;
  accentText: string;
  success: string;
  toastBg: string;
  inputBg: string;
}

export const THEMES: Record<ThemeName, ThemeTokens> = {
  light: {
    bgApp: 'oklch(0.955 0.006 70)',
    bgSurface: 'oklch(0.985 0.003 70)',
    bgBubbleBot: 'oklch(0.99 0.002 70)',
    bgBubbleUser: 'oklch(0.91 0.045 45)',
    textPrimary: 'oklch(0.2 0.012 60)',
    textSecondary: 'oklch(0.48 0.012 60)',
    border: 'oklch(0.85 0.01 60)',
    accent: 'oklch(0.58 0.15 45)',
    accentHover: 'oklch(0.52 0.15 45)',
    accentSoft: 'oklch(0.91 0.035 45)',
    accentSoftHover: 'oklch(0.87 0.045 45)',
    accentText: 'oklch(0.4 0.1 45)',
    success: 'oklch(0.52 0.12 150)',
    toastBg: 'oklch(0.18 0.012 60)',
    inputBg: 'oklch(0.99 0.002 70)',
  },
  dark: {
    bgApp: 'oklch(0.2 0.01 60)',
    bgSurface: 'oklch(0.24 0.01 60)',
    bgBubbleBot: 'oklch(0.27 0.01 60)',
    bgBubbleUser: 'oklch(0.34 0.05 45)',
    textPrimary: 'oklch(0.93 0.006 70)',
    textSecondary: 'oklch(0.66 0.012 60)',
    border: 'oklch(0.34 0.012 60)',
    accent: 'oklch(0.68 0.14 45)',
    accentHover: 'oklch(0.74 0.14 45)',
    accentSoft: 'oklch(0.32 0.05 45)',
    accentSoftHover: 'oklch(0.37 0.06 45)',
    accentText: 'oklch(0.83 0.07 45)',
    success: 'oklch(0.62 0.12 150)',
    toastBg: 'oklch(0.1 0.01 60)',
    inputBg: 'oklch(0.24 0.01 60)',
  },
};

export const ThemeContext = createContext<ThemeTokens>(THEMES.light);

export function useTheme(): ThemeTokens {
  return useContext(ThemeContext);
}
