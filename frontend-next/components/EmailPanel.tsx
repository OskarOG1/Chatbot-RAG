import { useRef } from 'react';
import { useTheme } from '@/lib/theme';
import { TEKSTY, type Lang } from '@/lib/chat';

interface Props {
  lang: Lang;
  open: boolean;
  recipient: string;
  subject: string;
  body: string;
  regenerating: boolean;
  onSubjectChange: (v: string) => void;
  onBodyChange: (v: string) => void;
  onClose: () => void;
  onCopy: () => void;
  onSaveTemplate: () => void;
  onRegenerate: () => void;
  onSend: () => void;
}

export default function EmailPanel({
  lang,
  open,
  recipient,
  subject,
  body,
  regenerating,
  onSubjectChange,
  onBodyChange,
  onClose,
  onCopy,
  onSaveTemplate,
  onRegenerate,
  onSend,
}: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];
  const bodyRef = useRef<HTMLTextAreaElement | null>(null);

  function wrapSelection(before: string, after: string) {
    const el = bodyRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = body.slice(start, end) || 'text';
    const next = body.slice(0, start) + before + selected + after + body.slice(end);
    onBodyChange(next);
    requestAnimationFrame(() => {
      el.focus();
      el.selectionStart = start + before.length;
      el.selectionEnd = start + before.length + selected.length;
    });
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
      {open && (
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
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 15,
                color: th.textSecondary,
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
            <button type="button" onClick={() => wrapSelection('**', '**')} style={toolbarBtn(th, { fontWeight: 800 })}>
              B
            </button>
            <button
              type="button"
              onClick={() => wrapSelection('_', '_')}
              style={toolbarBtn(th, { fontStyle: 'italic', fontWeight: 700 })}
            >
              I
            </button>
            <button type="button" onClick={() => wrapSelection('\n• ', '')} style={toolbarBtn(th, {})}>
              ≡
            </button>
          </div>

          <div style={{ flex: '1 1 auto', padding: '12px 22px 0', minHeight: 0 }}>
            <textarea
              ref={bodyRef}
              value={body}
              onChange={(e) => onBodyChange(e.target.value)}
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
                resize: 'none',
                outline: 'none',
                color: th.textPrimary,
              }}
            />
          </div>

          <div style={{ flex: '0 0 auto', padding: '18px 22px 22px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={onCopy} style={secondaryBtn(th)}>
                {t.copy}
              </button>
              <button type="button" onClick={onSaveTemplate} style={secondaryBtn(th)}>
                {t.saveTemplate}
              </button>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={onRegenerate} disabled={regenerating} style={outlineBtn(th)}>
                {t.regenerate}
              </button>
              <button type="button" onClick={onSend} style={primaryBtn(th)}>
                {t.send}
              </button>
            </div>
          </div>
        </div>
      )}
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
    fontSize: 13,
    cursor: 'pointer',
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

function primaryBtn(th: ReturnType<typeof useTheme>) {
  return {
    flex: 1.4,
    padding: 11,
    borderRadius: 10,
    border: 'none',
    background: th.accent,
    color: 'white',
    fontFamily: 'inherit',
    fontWeight: 700,
    fontSize: 13,
    cursor: 'pointer',
  };
}
