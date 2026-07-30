'use client';

import type { CSSProperties } from 'react';
import { useTheme, DISPLAY, BODY, MONO } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';
import type { ThemeName } from '@/lib/theme';

export interface RailItem {
  id: string;
  title: string;
  meta: string;
  active: boolean;
}

interface Props {
  lang: Lang;
  theme: ThemeName;
  items: RailItem[];
  onNew: () => void;
  onSelect: (id: string) => void;
  onSetLang: (lang: Lang) => void;
  onToggleTheme: () => void;
}

export default function Rail({ lang, theme, items, onNew, onSelect, onSetLang, onToggleTheme }: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];

  return (
    <aside
      style={{
        flex: '0 0 256px',
        width: 256,
        minWidth: 0,
        display: 'flex',
        flexDirection: 'column',
        background: th.rail,
        borderRight: `1px solid ${th.line}`,
        overflow: 'hidden',
      }}
    >
      <div style={{ padding: '22px 20px 18px', display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              background: th.accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flex: '0 0 auto',
            }}
          >
            <span style={{ fontFamily: DISPLAY, fontSize: 21, fontWeight: 800, color: th.markInk, lineHeight: 1, marginTop: -2 }}>a</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
            <span style={{ fontFamily: DISPLAY, fontSize: 14.5, fontWeight: 700, letterSpacing: '-0.02em', color: th.ink }}>{t.title}</span>
            <span style={{ fontFamily: MONO, fontSize: 10, color: th.ink3, letterSpacing: '0.02em' }}>{t.brandSub}</span>
          </div>
        </div>
        <button type="button" onClick={onNew} style={newChatBtn(th)}>
          <span style={{ fontFamily: MONO, fontSize: 15, color: th.accent, lineHeight: 1 }}>+</span>
          {t.newChat}
        </button>
      </div>

      <div style={{ flex: '1 1 auto', overflowY: 'auto', paddingBottom: 12 }}>
        <div
          style={{
            fontFamily: BODY,
            fontSize: 10.5,
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: th.ink3,
            padding: '6px 20px 10px',
          }}
        >
          {t.recent}
        </div>
        {items.map((it) => (
          <div
            key={it.id}
            onClick={() => onSelect(it.id)}
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'stretch',
              padding: '10px 20px 10px 0',
              cursor: 'pointer',
              background: it.active ? th.raised : 'transparent',
            }}
          >
            <span style={{ width: 2, borderRadius: '0 2px 2px 0', background: it.active ? th.accent : 'transparent', flex: '0 0 auto' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3, minWidth: 0 }}>
              <span
                style={{
                  fontFamily: BODY,
                  fontSize: 13,
                  fontWeight: it.active ? 600 : 500,
                  color: it.active ? th.ink : th.ink2,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {it.title}
              </span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: th.ink3 }}>{it.meta}</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ flex: '0 0 auto', borderTop: `1px solid ${th.line}`, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', padding: 2, borderRadius: 8, background: th.raised, border: `1px solid ${th.line}` }}>
          <button type="button" onClick={() => onSetLang('pl')} style={segBtn(th, lang === 'pl')}>PL</button>
          <button type="button" onClick={() => onSetLang('en')} style={segBtn(th, lang === 'en')}>EN</button>
        </div>
        <button type="button" onClick={onToggleTheme} style={railGhost(th)}>{t.themeButtonLabel[theme]}</button>
      </div>
    </aside>
  );
}

function newChatBtn(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    width: '100%',
    padding: '10px 12px',
    borderRadius: 9,
    border: `1px solid ${th.line}`,
    background: th.raised,
    color: th.ink,
    fontFamily: BODY,
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    textAlign: 'left',
  };
}

function segBtn(th: ReturnType<typeof useTheme>, active: boolean): CSSProperties {
  return {
    flex: 1,
    padding: 6,
    border: 'none',
    borderRadius: 6,
    fontFamily: MONO,
    fontSize: 11,
    fontWeight: 500,
    cursor: 'pointer',
    background: active ? th.surface : 'transparent',
    color: active ? th.ink : th.ink3,
    boxShadow: active ? th.shadow : 'none',
  };
}

function railGhost(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    padding: '8px 10px',
    borderRadius: 8,
    border: '1px solid transparent',
    background: 'transparent',
    color: th.ink2,
    fontFamily: BODY,
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    textAlign: 'left',
  };
}
