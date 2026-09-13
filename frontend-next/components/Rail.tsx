'use client';

import type { CSSProperties } from 'react';
import Link from 'next/link';
import { useTheme, DISPLAY, BODY, MONO } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';
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
  items: RailItem[];
  nieaktywny?: boolean;
  waski: boolean;
  otwarte: boolean;
  onZamknij: () => void;
  onNew: () => void;
  onSelect: (id: string) => void;
  onSetLang: (lang: Lang) => void;
  onToggleTheme: () => void;
  selectMode: boolean;
  selectedIds: Set<string>;
  onToggleSelectMode: () => void;
  onToggleSelected: (id: string) => void;
  onDeleteOne: (id: string) => void;
  onDeleteAll: () => void;
  onDeleteSelected: () => void;
}

const CZAS_SZUFLADY_MS = 240;

export default function Rail({
  lang,
  theme,
  items,
  nieaktywny = false,
  waski,
  otwarte,
  onZamknij,
  onNew,
  onSelect,
  onSetLang,
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

  const szuflada: CSSProperties = waski
    ? {
        position: 'fixed',
        top: 0,
        bottom: 0,
        left: 0,
        zIndex: 70,
        width: 'min(304px, 86vw)',
        transform: otwarte ? 'translateX(0)' : 'translateX(-105%)',
        visibility: otwarte ? 'visible' : 'hidden',
        transition: `transform ${CZAS_SZUFLADY_MS}ms cubic-bezier(0.4, 0, 0.2, 1), visibility 0s linear ${otwarte ? 0 : CZAS_SZUFLADY_MS}ms`,
        boxShadow: otwarte ? th.shadowLift : 'none',
      }
    : { flex: '0 0 256px', width: 256 };

  return (
    <aside
      inert={nieaktywny}
      aria-hidden={waski && !otwarte ? true : undefined}
      style={{
        ...szuflada,
        minWidth: 0,
        display: 'flex',
        flexDirection: 'column',
        background: th.rail,
        borderRight: `1px solid ${th.line}`,
        overflow: 'hidden',
      }}
    >
      <div style={{ padding: waski ? '16px 16px 14px' : '22px 20px 18px', display: 'flex', flexDirection: 'column', gap: waski ? 16 : 20 }}>
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0, flex: '1 1 auto' }}>
            <span style={{ fontFamily: DISPLAY, fontSize: 14.5, fontWeight: 700, letterSpacing: '-0.02em', color: th.ink }}>{t.title}</span>
            <span style={{ fontFamily: MONO, fontSize: 10, color: th.ink3, letterSpacing: '0.02em' }}>{t.brandSub}</span>
          </div>
          {waski && (
            <button type="button" aria-label={t.menuClose} onClick={onZamknij} style={closeBtn(th)}>
              ✕
            </button>
          )}
        </div>
        <button type="button" onClick={onNew} style={newChatBtn(th, waski)}>
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
            padding: waski ? '6px 16px 10px' : '6px 20px 10px',
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
          <button type="button" onClick={onToggleSelectMode} style={miniGhost(th, waski)}>
            {selectMode ? t.cancelSelect : t.selectMode}
          </button>
        </div>
        {selectMode && (
          <div style={{ padding: waski ? '0 16px 10px' : '0 20px 10px' }}>
            <button type="button" onClick={onDeleteAll} style={miniGhost(th, waski)}>
              {t.deleteAll}
            </button>
          </div>
        )}
        {items.map((it) => (
          <div
            key={it.id}
            style={{
              display: 'flex',
              gap: 10,
              alignItems: 'stretch',
              padding: waski ? '8px 12px 8px 0' : '10px 20px 10px 0',
              background: it.active && !selectMode ? th.raised : 'transparent',
            }}
          >
            <span style={{ width: 2, borderRadius: '0 2px 2px 0', background: it.active && !selectMode ? th.accent : 'transparent', flex: '0 0 auto' }} />
            {selectMode && (
              <input
                type="checkbox"
                checked={selectedIds.has(it.id)}
                onChange={() => onToggleSelected(it.id)}
                style={{ flex: '0 0 auto', marginTop: 2, cursor: 'pointer', width: waski ? 18 : undefined, height: waski ? 18 : undefined }}
              />
            )}
            <button
              type="button"
              onClick={() => (selectMode ? onToggleSelected(it.id) : onSelect(it.id))}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 3,
                minWidth: 0,
                flex: '1 1 auto',
                textAlign: 'left',
                background: 'none',
                border: 'none',
                padding: waski ? '4px 0' : 0,
                cursor: 'pointer',
              }}
            >
              <span
                style={{
                  maxWidth: '100%',
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
            </button>
            {!selectMode && (
              <button
                type="button"
                aria-label={t.deleteChat}
                onClick={() => onDeleteOne(it.id)}
                style={trashBtn(th, waski)}
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
            <button type="button" onClick={() => onSetLang('pl')} style={segBtn(th, lang === 'pl', waski)}>
              <FlagaPl /> PL
            </button>
            <button type="button" onClick={() => onSetLang('en')} style={segBtn(th, lang === 'en', waski)}>
              <FlagaGb /> EN
            </button>
          </div>
          <button type="button" aria-label={t.themeButtonLabel[theme]} onClick={onToggleTheme} style={themeIconBtn(th, waski)}>
            {theme === 'light' ? <IkonaKsiezyc color={th.ink2} /> : <IkonaSlonce color={th.ink2} />}
          </button>
        </div>
        <Link href="/prywatnosc" style={privacyLink(th)}>
          {lang === 'pl' ? 'Jak przetwarzam dane' : 'How I handle data'}
        </Link>
      </div>
    </aside>
  );
}

function newChatBtn(th: ReturnType<typeof useTheme>, waski: boolean): CSSProperties {
  return {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    width: '100%',
    padding: waski ? '12px 12px' : '10px 12px',
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

function segBtn(th: ReturnType<typeof useTheme>, active: boolean, waski: boolean): CSSProperties {
  return {
    flex: 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: waski ? 10 : 6,
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

function miniGhost(th: ReturnType<typeof useTheme>, waski: boolean): CSSProperties {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    minHeight: waski ? 32 : 24,
    padding: waski ? '4px 12px' : '3px 8px',
    borderRadius: 6,
    border: `1px solid ${th.line}`,
    background: 'transparent',
    color: th.ink2,
    fontFamily: BODY,
    fontSize: waski ? 11.5 : 10.5,
    fontWeight: 600,
    lineHeight: 1.4,
    cursor: 'pointer',
  };
}

function trashBtn(th: ReturnType<typeof useTheme>, waski: boolean): CSSProperties {
  const bok = waski ? 36 : 24;
  return {
    flex: '0 0 auto',
    alignSelf: 'center',
    width: bok,
    height: bok,
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

function closeBtn(th: ReturnType<typeof useTheme>): CSSProperties {
  return {
    flex: '0 0 auto',
    width: 36,
    height: 36,
    borderRadius: 9,
    border: `1px solid ${th.line}`,
    background: th.raised,
    color: th.ink2,
    fontSize: 14,
    lineHeight: 1,
    cursor: 'pointer',
    padding: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
}

function themeIconBtn(th: ReturnType<typeof useTheme>, waski: boolean): CSSProperties {
  const bok = waski ? 38 : 32;
  return {
    flex: '0 0 auto',
    width: bok,
    height: bok,
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
    alignSelf: 'flex-start',
    fontFamily: BODY,
    fontSize: 10.5,
    color: th.ink3,
    textDecoration: 'none',
    padding: '6px 2px 4px',
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
