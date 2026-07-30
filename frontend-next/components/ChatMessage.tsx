import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTheme, DISPLAY, BODY } from '@/lib/theme';
import { przygotujOdpowiedz } from '@/lib/zrodla';
import { TEKSTY, type Cytat, type Lang } from '@/lib/chat';
import SourceList from './SourceList';

interface Props {
  role: 'user' | 'assistant';
  content: string;
  lang: Lang;
  citations?: Cytat[];
  action?: string | null;
  onAction?: (tekst: string) => void;
}

export default function ChatMessage({ role, content, lang, citations = [], action, onAction }: Props) {
  const th = useTheme();
  const t = TEKSTY[lang];
  const isUser = role === 'user';

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div
          style={{
            maxWidth: '76%',
            padding: '13px 17px',
            borderRadius: '14px 14px 3px 14px',
            background: th.userBg,
            color: th.userInk,
            fontFamily: BODY,
            fontSize: 14.5,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
          }}
        >
          {content}
        </div>
      </div>
    );
  }

  const { tekst: tresc, zrodla } = przygotujOdpowiedz(content, citations);

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <span
          style={{
            width: 22,
            height: 22,
            borderRadius: 6,
            background: th.accent,
            color: th.markInk,
            fontFamily: DISPLAY,
            fontSize: 14,
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            lineHeight: 1,
            flex: '0 0 auto',
          }}
        >
          a
        </span>
        <span style={{ fontFamily: BODY, fontSize: 12, fontWeight: 600, color: th.ink }}>{t.assistant}</span>
        <span style={{ flex: '1 1 auto', height: 1, background: th.lineSoft }} />
      </div>

      <div
        style={{
          fontFamily: BODY,
          fontSize: 14.5,
          lineHeight: 1.68,
          color: th.ink2,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p style={{ margin: 0 }}>{children}</p>,
            ul: ({ children }) => (
              <ul style={{ margin: 0, paddingLeft: 22, listStyle: 'disc', listStylePosition: 'outside', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol style={{ margin: 0, paddingLeft: 22, listStyle: 'decimal', listStylePosition: 'outside', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {children}
              </ol>
            ),
            li: ({ children }) => <li style={{ margin: 0 }}>{children}</li>,
            strong: ({ children }) => <strong style={{ color: th.ink, fontWeight: 600 }}>{children}</strong>,
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: th.accentInk, textDecoration: 'none', fontWeight: 500 }}
              >
                {children}
              </a>
            ),
          }}
        >
          {tresc}
        </ReactMarkdown>
      </div>

      {zrodla.length > 0 && <SourceList zrodla={zrodla} label={t.sourcesLabel} />}

      {action && onAction && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginTop: 2 }}>
          <button
            type="button"
            onClick={() => onAction(action)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 9,
              padding: '11px 17px',
              borderRadius: 9,
              border: 'none',
              background: th.accent,
              color: '#FFFFFF',
              fontFamily: BODY,
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: th.shadow,
            }}
          >
            <span style={{ width: 15, height: 11, border: '1.5px solid currentColor', borderRadius: 2, flex: '0 0 auto', opacity: 0.9 }} />
            {action}
          </button>
        </div>
      )}
    </div>
  );
}
