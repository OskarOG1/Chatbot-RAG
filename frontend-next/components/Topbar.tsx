'use client';

import type { CSSProperties } from 'react';
import { useTheme, type ThemeName } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';

interface Props {
  lang: Lang;
  theme: ThemeName;
  onSetLang: (lang: Lang) => void;
  onToggleTheme: () => void;
}

export default function Topbar({ lang, theme, onSetLang, onToggleTheme }: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];

  return (
    <div
      style={{
        height: 64,
        flex: '0 0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        borderBottom: `1px solid ${th.border}`,
        background: th.bgSurface,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 10,
            background: th.accent,
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: 15,
            flex: '0 0 auto',
          }}
        >
          A
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: th.textPrimary }}>{t.title}</span>
          <span style={{ fontSize: 12, color: th.textSecondary }}>{t.subtitle}</span>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 12,
            color: th.textSecondary,
          }}
        >
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: th.success }} />
          {t.connected}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            padding: 3,
            border: `1px solid ${th.border}`,
            borderRadius: 11,
          }}
        >
          <LangPill active={lang === 'pl'} onClick={() => onSetLang('pl')} th={th} src="/flags/pl.png" label="PL" />
          <LangPill active={lang === 'en'} onClick={() => onSetLang('en')} th={th} src="/flags/gb.svg" label="EN" />
        </div>
        <button type="button" onClick={onToggleTheme} style={ghostBtn(th)}>
          {t.themeButtonLabel[theme]}
        </button>
      </div>
    </div>
  );
}

function LangPill({
  active,
  onClick,
  th,
  src,
  label,
}: {
  active: boolean;
  onClick: () => void;
  th: ReturnType<typeof useTheme>;
  src: string;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        border: 'none',
        borderRadius: 8,
        padding: '5px 10px 5px 6px',
        fontFamily: 'inherit',
        fontWeight: 700,
        fontSize: 12,
        cursor: 'pointer',
        background: active ? th.accentSoft : 'transparent',
        color: active ? th.accentText : th.textSecondary,
        transition: 'background 0.15s ease, color 0.15s ease',
      }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt=""
        width={16}
        height={16}
        style={{ borderRadius: 4, objectFit: 'cover', boxShadow: `0 0 0 1px ${th.border}` }}
      />
      {label}
    </button>
  );
}

function ghostBtn(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    border: `1px solid ${th.border}`,
    background: 'transparent',
    color: th.textPrimary,
    fontFamily: 'inherit',
    fontWeight: 700,
    fontSize: 12,
    padding: '8px 14px',
    borderRadius: 9,
    cursor: 'pointer',
  };
}
