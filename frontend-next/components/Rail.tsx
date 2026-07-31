'use client';

import type { CSSProperties } from 'react';
import Link from 'next/link';
import { useTheme, DISPLAY, BODY, MONO } from '@/lib/theme';
import { TEKSTY, type Lang, type Strona } from '@/lib/chat';
import type { ThemeName } from '@/lib/theme';
import { FlagaPl, FlagaGb, IkonaKosz, IkonaSlonce, IkonaKsiezyc } from './Ikony';

export interface RailItem {
  id: string;
  title: string;
  meta: string;
  active: boolean;
}

interface Props {
  lang: Lang;
  theme: ThemeName;
  strona: Strona;
  items: RailItem[];
  onNew: () => void;
  onSelect: (id: string) => void;
  onSetLang: (lang: Lang) => void;
  onSetStrona: (strona: Strona) => void;
  onToggleTheme: () => void;
  selectMode: boolean;
  selectedIds: Set<string>;
  onToggleSelectMode: () => void;
  onToggleSelected: (id: string) => void;
  onDeleteOne: (id: string) => void;
  onDeleteAll: () => void;
  onDeleteSelected: () => void;
}

export default function Rail({
  lang,
  theme,
  strona,
  items,
  onNew,
  onSelect,
  onSetLang,
  onSetStrona,
  onToggleTheme,
  selectMode,
  selectedIds,
  onToggleSelectMode,
  onToggleSelected,
  onDeleteOne,
  onDeleteAll,
  onDeleteSelected,
}: Props) {
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
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
            padding: '6px 20px 10px',
          }}
        >
          <span
            style={{
              fontFamily: BODY,
              fontSize: 10.5,
              fontWeight: 600,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: th.ink3,
            }}
          >
            {t.recent}
          </span>
          <button type="button" onClick={onToggleSelectMode} style={miniGhost(th)}>
            {selectMode ? t.cancelSelect : t.selectMode}
          </button>
        </div>
        {selectMode && (
          <div style={{ padding: '0 20px 10px' }}>
            <button type="button" onClick={onDeleteAll} style={miniGhost(th)}>
              {t.deleteAll}
            </button>
          </div>
        )}
        {items.map((it) => (
          <div
            key={it.id}
            onClick={() => (selectMode ? onToggleSelected(it.id) : onSelect(it.id))}
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'stretch',
              padding: '10px 20px 10px 0',
              cursor: 'pointer',
              background: it.active && !selectMode ? th.raised : 'transparent',
            }}
          >
            <span style={{ width: 2, borderRadius: '0 2px 2px 0', background: it.active && !selectMode ? th.accent : 'transparent', flex: '0 0 auto' }} />
            {selectMode && (
              <input
                type="checkbox"
                checked={selectedIds.has(it.id)}
                onChange={() => onToggleSelected(it.id)}
                onClick={(e) => e.stopPropagation()}
                style={{ flex: '0 0 auto', marginTop: 2, cursor: 'pointer' }}
              />
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3, minWidth: 0, flex: '1 1 auto' }}>
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
            {!selectMode && (
              <button
                type="button"
                aria-label={t.deleteChat}
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteOne(it.id);
                }}
                style={trashBtn(th)}
              >
                <IkonaKosz color={th.ink3} />
              </button>
            )}
          </div>
        ))}
      </div>

      {selectMode && (
        <div style={{ flex: '0 0 auto', borderTop: `1px solid ${th.line}`, padding: '12px 16px', display: 'flex', gap: 8 }}>
          <button type="button" onClick={onDeleteSelected} disabled={selectedIds.size === 0} style={dangerBtn(th, selectedIds.size === 0)}>
            {selectedIds.size > 0 ? `${t.deleteSelected} (${selectedIds.size})` : t.deleteSelected}
          </button>
          <button type="button" onClick={onToggleSelectMode} style={railGhost(th)}>
            {t.cancelSelect}
          </button>
        </div>
      )}

      <div style={{ flex: '0 0 auto', borderTop: `1px solid ${th.line}`, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ flex: '1 1 auto', display: 'flex', padding: 2, borderRadius: 8, background: th.raised, border: `1px solid ${th.line}` }}>
            <button type="button" onClick={() => onSetLang('pl')} style={segBtn(th, lang === 'pl')}>
              <FlagaPl /> PL
            </button>
            <button type="button" onClick={() => onSetLang('en')} style={segBtn(th, lang === 'en')}>
              <FlagaGb /> EN
            </button>
          </div>
          <button type="button" aria-label={t.themeButtonLabel[theme]} onClick={onToggleTheme} style={themeIconBtn(th)}>
            {theme === 'light' ? <IkonaKsiezyc color={th.ink2} /> : <IkonaSlonce color={th.ink2} />}
          </button>
        </div>
        <div style={{ display: 'flex', padding: 2, borderRadius: 8, background: th.raised, border: `1px solid ${th.line}` }}>
          <button type="button" onClick={() => onSetStrona('auto')} style={segBtn(th, strona === 'auto')}>
            {t.sideAuto}
          </button>
          <button type="button" onClick={() => onSetStrona('kupujacy')} style={segBtn(th, strona === 'kupujacy')}>
            {t.sideBuying}
          </button>
          <button type="button" onClick={() => onSetStrona('sprzedajacy')} style={segBtn(th, strona === 'sprzedajacy')}>
            {t.sideSelling}
          </button>
        </div>
        <Link href="/prywatnosc" style={privacyLink(th)}>
          {lang === 'pl' ? 'Jak przetwarzam dane' : 'How I handle data'}
        </Link>
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
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 6,
    border: 'none',
    borderRadius: 6,
    fontFamily: MONO,
    fontSize: 11,
    fontWeight: 500,
    lineHeight: 1,
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

function miniGhost(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 8px',
    borderRadius: 6,
    border: `1px solid ${th.line}`,
    background: 'transparent',
    color: th.ink2,
    fontFamily: BODY,
    fontSize: 10.5,
    fontWeight: 600,
    lineHeight: 1.4,
    cursor: 'pointer',
  };
}

function trashBtn(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    flex: '0 0 auto',
    alignSelf: 'center',
    width: 22,
    height: 22,
    borderRadius: 6,
    border: 'none',
    background: 'transparent',
    color: th.ink3,
    cursor: 'pointer',
    padding: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
}

function themeIconBtn(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    flex: '0 0 auto',
    width: 32,
    height: 32,
    borderRadius: 8,
    border: `1px solid ${th.line}`,
    background: th.raised,
    cursor: 'pointer',
    padding: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
}

function privacyLink(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    fontFamily: BODY,
    fontSize: 10.5,
    color: th.ink3,
    textDecoration: 'none',
    padding: '2px 2px 0',
  };
}

function dangerBtn(th: ReturnType<typeof useTheme>, disabled: boolean): CSSProperties {
  return {
    flex: '1 1 auto',
    padding: '8px 10px',
    borderRadius: 8,
    border: `1px solid ${th.accentLine}`,
    background: disabled ? th.raised : th.accentSoft,
    color: disabled ? th.ink3 : th.accentInk,
    fontFamily: BODY,
    fontSize: 12,
    fontWeight: 600,
    cursor: disabled ? 'default' : 'pointer',
  };
}
