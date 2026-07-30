import { useEffect, useRef, type MouseEvent } from 'react';
import { useTheme } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';
import { htmlDoMarkdown, markdownDoHtml } from '@/lib/richtext';

const SZEROKOSCI: Record<'left' | 'center' | 'right', number[]> = {
  left: [16, 11, 14],
  center: [16, 10, 13],
  right: [16, 11, 14],
};

function AlignIcon({ align, color }: { align: 'left' | 'center' | 'right'; color: string }) {
  const justify = align === 'left' ? 'flex-start' : align === 'center' ? 'center' : 'flex-end';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3, width: 16 }}>
      {SZEROKOSCI[align].map((w, i) => (
        <span
          key={i}
          style={{ display: 'flex', justifyContent: justify, width: '100%' }}
        >
          <span style={{ width: w, height: 2, background: color, borderRadius: 1 }} />
        </span>
      ))}
    </div>
  );
}

interface Props {
  lang: Lang;
  open: boolean;
  recipient: string;
  subject: string;
  body: string;
  clientEmail: string;
  emailValid: boolean;
  sending: boolean;
  onSubjectChange: (v: string) => void;
  onBodyChange: (v: string) => void;
  onClientEmailChange: (v: string) => void;
  onClose: () => void;
  onCopy: () => void;
  onUndo: () => void;
  onSend: () => void;
}

export default function EmailPanel({
  lang,
  open,
  recipient,
  subject,
  body,
  clientEmail,
  emailValid,
  sending,
  onSubjectChange,
  onBodyChange,
  onClientEmailChange,
  onClose,
  onCopy,
  onUndo,
  onSend,
}: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const ostatnioZsynchronizowane = useRef<string>('');

  useEffect(() => {
    if (!bodyRef.current) return;
    if (body === ostatnioZsynchronizowane.current) return;
    bodyRef.current.innerHTML = markdownDoHtml(body);
    ostatnioZsynchronizowane.current = body;
  }, [body]);

  function synchronizujBody() {
    if (!bodyRef.current) return;
    const markdown = htmlDoMarkdown(bodyRef.current);
    ostatnioZsynchronizowane.current = markdown;
    onBodyChange(markdown);
  }

  function formatuj(polecenie: string) {
    document.execCommand(polecenie);
    synchronizujBody();
  }

  function zachowajZaznaczenie(e: MouseEvent) {
    e.preventDefault();
  }

  return (
    <div
      style={{
        flex: '0 0 auto',
        width: open ? 440 : 0,
        borderLeft: open ? `1px solid ${th.border}` : 'none',
        background: th.bgSurface,
        overflow: 'hidden',
        transition: 'width 0.28s cubic-bezier(0.22,1,0.36,1), background 0.2s ease',
        animation: open ? 'dcSlideIn 0.3s ease both' : 'none',
      }}
    >
      {
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div
            style={{
              flex: '0 0 auto',
              padding: '20px 22px',
              borderBottom: `1px solid ${th.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: th.textPrimary }}>{t.panelTitle}</div>
              <div style={{ fontSize: 12, color: th.textSecondary, marginTop: 2 }}>
                {t.to} {recipient}
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              style={{
                border: 'none',
                background: th.bgApp,
                width: 30,
                height: 30,
                padding: 0,
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 15,
                lineHeight: 1,
                color: th.textSecondary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ flex: '0 0 auto', padding: '18px 22px 0' }}>
            <label style={labelStyle(th.textSecondary)}>{t.subjectLabel}</label>
            <input
              value={subject}
              onChange={(e) => onSubjectChange(e.target.value)}
              style={{
                width: '100%',
                marginTop: 6,
                border: `1px solid ${th.border}`,
                background: th.inputBg,
                color: th.textPrimary,
                borderRadius: 10,
                padding: '10px 12px',
                fontFamily: 'inherit',
                fontSize: 14,
                fontWeight: 600,
                outline: 'none',
              }}
            />
          </div>

          <div style={{ flex: '0 0 auto', padding: '16px 22px 0', display: 'flex', gap: 6 }}>
            <button
              type="button"
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('bold')}
              style={toolbarBtn(th, { fontWeight: 800 })}
            >
              B
            </button>
            <button
              type="button"
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('italic')}
              style={toolbarBtn(th, { fontStyle: 'italic', fontWeight: 700 })}
            >
              I
            </button>
            <button
              type="button"
              aria-label={t.alignLeft}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('justifyLeft')}
              style={toolbarBtn(th, {})}
            >
              <AlignIcon align="left" color={th.textPrimary} />
            </button>
            <button
              type="button"
              aria-label={t.alignCenter}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('justifyCenter')}
              style={toolbarBtn(th, {})}
            >
              <AlignIcon align="center" color={th.textPrimary} />
            </button>
            <button
              type="button"
              aria-label={t.alignRight}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('justifyRight')}
              style={toolbarBtn(th, {})}
            >
              <AlignIcon align="right" color={th.textPrimary} />
            </button>
          </div>

          <div style={{ flex: '1 1 auto', padding: '12px 22px 0', minHeight: 0 }}>
            <div
              ref={bodyRef}
              contentEditable
              suppressContentEditableWarning
              onInput={synchronizujBody}
              className="email-body-editor"
              style={{
                width: '100%',
                height: '100%',
                border: `1px solid ${th.border}`,
                background: th.inputBg,
                borderRadius: 12,
                padding: 14,
                fontFamily: 'inherit',
                fontSize: 14,
                lineHeight: 1.65,
                overflowY: 'auto',
                outline: 'none',
                color: th.textPrimary,
              }}
            />
          </div>

          <div style={{ flex: '0 0 auto', padding: '18px 22px 0' }}>
            <label style={labelStyle(th.textSecondary)}>{t.emailFieldLabel}</label>
            <input
              type="email"
              value={clientEmail}
              placeholder={t.emailPlaceholder}
              onChange={(e) => onClientEmailChange(e.target.value)}
              style={{
                width: '100%',
                marginTop: 6,
                border: `1px solid ${th.border}`,
                background: th.inputBg,
                color: th.textPrimary,
                borderRadius: 10,
                padding: '10px 12px',
                fontFamily: 'inherit',
                fontSize: 14,
                outline: 'none',
              }}
            />
            <div style={{ fontSize: 11.5, color: th.textSecondary, marginTop: 6 }}>{t.emailPrivacyNote}</div>
          </div>

          <div style={{ flex: '0 0 auto', padding: '18px 22px 22px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={onCopy} style={secondaryBtn(th)}>
                {t.copy}
              </button>
              <button type="button" onClick={onUndo} style={outlineBtn(th)}>
                {t.undoEdits}
              </button>
            </div>
            <button
              type="button"
              onClick={onSend}
              disabled={!emailValid || sending}
              style={primaryBtn(th, !emailValid || sending)}
            >
              {sending ? t.sending : t.send}
            </button>
          </div>
        </div>
      }
    </div>
  );
}

function labelStyle(color: string) {
  return {
    fontSize: 11.5,
    fontWeight: 700,
    color,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.03em',
  };
}

function toolbarBtn(th: ReturnType<typeof useTheme>, extra: Record<string, string | number>) {
  return {
    border: `1px solid ${th.border}`,
    background: th.inputBg,
    color: th.textPrimary,
    borderRadius: 8,
    width: 32,
    height: 32,
    padding: 0,
    fontSize: 13,
    lineHeight: 1,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...extra,
  };
}

function secondaryBtn(th: ReturnType<typeof useTheme>) {
  return {
    flex: 1,
    padding: 11,
    borderRadius: 10,
    border: `1px solid ${th.border}`,
    background: th.inputBg,
    color: th.textPrimary,
    fontFamily: 'inherit',
    fontWeight: 700,
    fontSize: 13,
    cursor: 'pointer',
  };
}

function outlineBtn(th: ReturnType<typeof useTheme>) {
  return {
    flex: 1,
    padding: 11,
    borderRadius: 10,
    border: `1.5px solid ${th.accent}`,
    background: th.inputBg,
    color: th.accentText,
    fontFamily: 'inherit',
    fontWeight: 700,
    fontSize: 13,
    cursor: 'pointer',
  };
}

function primaryBtn(th: ReturnType<typeof useTheme>, disabled = false) {
  return {
    flex: 1.4,
    padding: 11,
    borderRadius: 10,
    border: 'none',
    background: disabled ? th.accentSoft : th.accent,
    color: 'white',
    fontFamily: 'inherit',
    fontWeight: 700,
    fontSize: 13,
    cursor: disabled ? 'not-allowed' : 'pointer',
  };
}
