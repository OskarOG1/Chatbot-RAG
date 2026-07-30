'use client';

import type { CSSProperties } from 'react';
import { useTheme, type ThemeName } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';

interface Props {
  lang: Lang;
  theme: ThemeName;
  onToggleLang: () => void;
  onToggleTheme: () => void;
}

export default function Topbar({ lang, theme, onToggleLang, onToggleTheme }: Props) {
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
        <button type="button" onClick={onToggleLang} style={ghostBtn(th)}>
          <span style={{ marginRight: 6 }}>{lang === 'pl' ? '🇬🇧' : '🇵🇱'}</span>
          {t.langButtonLabel}
        </button>
        <button type="button" onClick={onToggleTheme} style={ghostBtn(th)}>
          {t.themeButtonLabel[theme]}
        </button>
      </div>
    </div>
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
