import { useEffect, useRef, useState, type CSSProperties, type MouseEvent } from 'react';
import { useTheme } from '@/lib/theme';
import { OKNO_COFNIECIA_MS, TEKSTY, type Lang } from '@/lib/chat';
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

export type TrybPanelu = 'kolumna' | 'nakladka' | 'ekran';

interface Props {
  lang: Lang;
  open: boolean;
  tryb: TrybPanelu;
  recipient: string;
  subject: string;
  body: string;
  clientEmail: string;
  emailValid: boolean;
  sending: boolean;
  wyslano: { ticket: string; czasTekst: string } | null;
  edytujPoWyslaniu: boolean;
  odliczanieDo: number | null;
  onSubjectChange: (v: string) => void;
  onBodyChange: (v: string) => void;
  onClientEmailChange: (v: string) => void;
  onClose: () => void;
  onDiscard: () => void;
  onCopy: () => void;
  onUndo: () => void;
  onSend: () => void;
  onCancelSend: () => void;
  onStartEdit: () => void;
}

export default function EmailPanel({
  lang,
  open,
  tryb,
  recipient,
  subject,
  body,
  clientEmail,
  emailValid,
  sending,
  wyslano,
  edytujPoWyslaniu,
  odliczanieDo,
  onSubjectChange,
  onBodyChange,
  onClientEmailChange,
  onClose,
  onDiscard,
  onCopy,
  onUndo,
  onSend,
  onCancelSend,
  onStartEdit,
}: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const ostatnioZsynchronizowane = useRef<string>('');
  const readOnly = wyslano !== null && !edytujPoWyslaniu;
  const [teraz, setTeraz] = useState(() => Date.now());

  useEffect(() => {
    if (!bodyRef.current) return;
    if (body === ostatnioZsynchronizowane.current) return;
    bodyRef.current.innerHTML = markdownDoHtml(body);
    ostatnioZsynchronizowane.current = body;
  }, [body]);

  useEffect(() => {
    if (odliczanieDo === null) return undefined;
    const odswiez = () => setTeraz(Date.now());
    const pierwszy = setTimeout(odswiez, 0);
    const iv = setInterval(odswiez, 250);
    return () => {
      clearTimeout(pierwszy);
      clearInterval(iv);
    };
  }, [odliczanieDo]);

  const ekran = tryb === 'ekran';
  const poziomo = ekran ? 14 : 22;
  const fontPola = ekran ? 16 : 14;

  const obudowa: CSSProperties =
    tryb === 'kolumna'
      ? {
          flex: '0 0 auto',
          width: open ? 440 : 0,
          borderLeft: open ? `1px solid ${th.border}` : 'none',
          visibility: open ? 'visible' : 'hidden',
          transition: `width 0.28s cubic-bezier(0.22,1,0.36,1), background 0.2s ease, visibility 0s linear ${open ? '0s' : '0.28s'}`,
          animation: open ? 'dcSlideIn 0.3s ease both' : 'none',
        }
      : tryb === 'nakladka'
        ? {
            position: 'fixed',
            top: 0,
            right: 0,
            bottom: 0,
            zIndex: 80,
            width: 'min(440px, 100vw)',
            display: open ? 'block' : 'none',
            borderLeft: `1px solid ${th.border}`,
            boxShadow: th.shadowLift,
            animation: 'dcPanel 0.28s ease both',
          }
        : {
            position: 'fixed',
            inset: 0,
            zIndex: 80,
            display: open ? 'block' : 'none',
            animation: 'dcRise 0.25s ease both',
          };

  const sekundyDoWyslania =
    odliczanieDo !== null
      ? Math.min(Math.ceil(OKNO_COFNIECIA_MS / 1000), Math.max(0, Math.ceil((odliczanieDo - teraz) / 1000)))
      : null;

  function synchronizujBody() {
    if (!bodyRef.current) return;
    const markdown = htmlDoMarkdown(bodyRef.current);
    ostatnioZsynchronizowane.current = markdown;
    onBodyChange(markdown);
  }

  function formatuj(polecenie: string) {
    if (readOnly) return;
    document.execCommand(polecenie);
    synchronizujBody();
  }

  function zachowajZaznaczenie(e: MouseEvent) {
    e.preventDefault();
  }

  const akcja =
    odliczanieDo !== null ? (
      <div style={{ display: 'flex', gap: 8 }}>
        <div
          style={{
            flex: 1.4,
            padding: 11,
            borderRadius: 10,
            border: `1px solid ${th.border}`,
            background: th.inputBg,
            color: th.textPrimary,
            fontFamily: 'inherit',
            fontWeight: 700,
            fontSize: 13,
            textAlign: 'center',
          }}
        >
          {t.sendingCountdown(sekundyDoWyslania ?? 0)}
        </div>
        <button type="button" onClick={onCancelSend} style={outlineBtn(th)}>
          {t.cancelSend}
        </button>
      </div>
    ) : readOnly ? (
      <button type="button" onClick={onStartEdit} style={primaryBtn(th, false)}>
        {t.editAfterSend}
      </button>
    ) : (
      <button
        type="button"
        onClick={onSend}
        disabled={!emailValid || sending}
        style={primaryBtn(th, !emailValid || sending)}
      >
        {sending ? t.sending : t.send}
      </button>
    );

  return (
    <div
      role={tryb === 'kolumna' ? undefined : 'dialog'}
      aria-label={tryb === 'kolumna' ? undefined : t.panelTitle}
      style={{
        ...obudowa,
        background: th.bgSurface,
        overflow: 'hidden',
      }}
    >
      {
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: tryb === 'kolumna' ? undefined : 'auto' }}>
          <div
            style={{
              flex: '0 0 auto',
              padding: ekran ? '12px 14px' : '20px 22px',
              borderBottom: `1px solid ${th.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10,
            }}
          >
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: th.textPrimary }}>{t.panelTitle}</div>
              <div style={{ fontSize: 12, color: th.textSecondary, marginTop: 2 }}>
                {t.to} {recipient}
              </div>
              {wyslano && (
                <div style={{ fontSize: 11.5, fontWeight: 700, color: th.accentText, marginTop: 4 }}>
                  {t.ticketBadge(wyslano.ticket, wyslano.czasTekst)}
                </div>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '0 0 auto' }}>
              <button type="button" onClick={onDiscard} style={discardBtn(th)}>
                {t.discardDraft}
              </button>
              <button
                type="button"
                onClick={onClose}
                aria-label={t.closePanel}
                style={{
                  border: 'none',
                  background: th.bgApp,
                  width: ekran ? 40 : 30,
                  height: ekran ? 40 : 30,
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
          </div>

          <div style={{ flex: '0 0 auto', padding: `${ekran ? 14 : 18}px ${poziomo}px 0` }}>
            <label style={labelStyle(th.textSecondary)}>{t.subjectLabel}</label>
            <input
              value={subject}
              readOnly={readOnly}
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
                fontSize: fontPola,
                fontWeight: 600,
                outline: 'none',
              }}
            />
          </div>

          <div style={{ flex: '0 0 auto', padding: `${ekran ? 12 : 16}px ${poziomo}px 0`, display: 'flex', gap: 6 }}>
            <button
              type="button"
              disabled={readOnly}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('bold')}
              style={toolbarBtn(th, { fontWeight: 800 }, readOnly, ekran)}
            >
              B
            </button>
            <button
              type="button"
              disabled={readOnly}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('italic')}
              style={toolbarBtn(th, { fontStyle: 'italic', fontWeight: 700 }, readOnly, ekran)}
            >
              I
            </button>
            <button
              type="button"
              disabled={readOnly}
              aria-label={t.alignLeft}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('justifyLeft')}
              style={toolbarBtn(th, {}, readOnly, ekran)}
            >
              <AlignIcon align="left" color={th.textPrimary} />
            </button>
            <button
              type="button"
              disabled={readOnly}
              aria-label={t.alignCenter}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('justifyCenter')}
              style={toolbarBtn(th, {}, readOnly, ekran)}
            >
              <AlignIcon align="center" color={th.textPrimary} />
            </button>
            <button
              type="button"
              disabled={readOnly}
              aria-label={t.alignRight}
              onMouseDown={zachowajZaznaczenie}
              onClick={() => formatuj('justifyRight')}
              style={toolbarBtn(th, {}, readOnly, ekran)}
            >
              <AlignIcon align="right" color={th.textPrimary} />
            </button>
          </div>

          <div
            style={{
              flex: tryb === 'kolumna' ? '1 1 auto' : '1 0 auto',
              padding: `12px ${poziomo}px 0`,
              minHeight: tryb === 'kolumna' ? 0 : 200,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              ref={bodyRef}
              contentEditable={!readOnly}
              suppressContentEditableWarning
              onInput={synchronizujBody}
              className="email-body-editor"
              style={{
                width: '100%',
                flex: '1 1 auto',
                minHeight: 0,
                border: `1px solid ${th.border}`,
                background: th.inputBg,
                borderRadius: 12,
                padding: 14,
                fontFamily: 'inherit',
                fontSize: fontPola,
                lineHeight: 1.65,
                overflowY: 'auto',
                outline: 'none',
                color: th.textPrimary,
              }}
            />
          </div>

          <div style={{ flex: '0 0 auto', padding: `${ekran ? 14 : 18}px ${poziomo}px 0` }}>
            <label style={labelStyle(th.textSecondary)}>{t.emailFieldLabel}</label>
            <input
              type="email"
              value={clientEmail}
              readOnly={readOnly}
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
                fontSize: fontPola,
                outline: 'none',
              }}
            />
            <div style={{ fontSize: 11.5, color: th.textSecondary, marginTop: 6 }}>{t.emailPrivacyNote}</div>
          </div>

          <div
            style={{
              flex: '0 0 auto',
              padding: tryb === 'kolumna' ? '18px 22px 22px' : ekran ? `14px ${poziomo}px 0` : `18px ${poziomo}px 0`,
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={onCopy} style={secondaryBtn(th)}>
                {t.copy}
              </button>
              <button type="button" onClick={onUndo} disabled={readOnly} style={outlineBtn(th)}>
                {t.undoEdits}
              </button>
            </div>
            {tryb === 'kolumna' && akcja}
          </div>
          {tryb !== 'kolumna' && (
            <div
              style={{
                position: 'sticky',
                bottom: 0,
                zIndex: 1,
                flex: '0 0 auto',
                marginTop: 10,
                padding: `10px ${poziomo}px ${ekran ? 14 : 18}px`,
                background: th.bgSurface,
                borderTop: `1px solid ${th.border}`,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {akcja}
            </div>
          )}
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

function toolbarBtn(th: ReturnType<typeof useTheme>, extra: Record<string, string | number>, disabled = false, duzy = false) {
  return {
    border: `1px solid ${th.border}`,
    background: th.inputBg,
    color: th.textPrimary,
    borderRadius: 8,
    width: duzy ? 40 : 32,
    height: duzy ? 40 : 32,
    padding: 0,
    fontSize: 13,
    lineHeight: 1,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.45 : 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    ...extra,
  };
}

function discardBtn(th: ReturnType<typeof useTheme>) {
  return {
    border: `1px solid ${th.border}`,
    background: th.bgApp,
    color: th.textSecondary,
    borderRadius: 100,
    padding: '6px 12px',
    fontFamily: 'inherit',
    fontWeight: 600,
    fontSize: 11.5,
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
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
