import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTheme } from '@/lib/theme';
import { linkujCytaty, zrodlaZCytatow } from '@/lib/zrodla';
import type { Cytat } from '@/lib/chat';
import SourceList from './SourceList';

interface Props {
  role: 'user' | 'assistant';
  content: string;
  citations?: Cytat[];
  action?: string | null;
  onAction?: (tekst: string) => void;
}

export default function ChatMessage({ role, content, citations = [], action, onAction }: Props) {
  const th = useTheme();
  const isUser = role === 'user';
  const tresc = isUser ? content : linkujCytaty(content, citations);
  const zrodla = zrodlaZCytatow(citations);

  const bubbleStyle = isUser
    ? {
        background: th.bgBubbleUser,
        color: th.accentText,
        padding: '13px 16px',
        borderRadius: '16px 16px 4px 16px',
        fontSize: 14.5,
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap' as const,
      }
    : {
        background: th.bgBubbleBot,
        border: `1px solid ${th.border}`,
        color: th.textPrimary,
        padding: '13px 16px',
        borderRadius: '16px 16px 16px 4px',
        fontSize: 14.5,
        lineHeight: 1.55,
      };

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div
        style={{
          maxWidth: '82%',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          alignItems: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        <div style={bubbleStyle}>
          {isUser ? (
            content
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: th.accent }}>
                      {children}
                    </a>
                  ),
                }}
              >
                {tresc}
              </ReactMarkdown>
            </div>
          )}
        </div>
        {zrodla.length > 0 && <SourceList zrodla={zrodla} />}
        {action && onAction && (
          <button
            type="button"
            onClick={() => onAction(action)}
            style={{
              border: `1.5px solid ${th.accent}`,
              background: th.bgSurface,
              color: th.accentText,
              fontFamily: 'inherit',
              fontWeight: 700,
              fontSize: 13,
              padding: '9px 16px',
              borderRadius: 10,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span
              style={{
                width: 16,
                height: 12,
                border: '1.5px solid currentColor',
                borderRadius: 2,
                flex: '0 0 auto',
              }}
            />
            {action}
          </button>
        )}
      </div>
    </div>
  );
}
