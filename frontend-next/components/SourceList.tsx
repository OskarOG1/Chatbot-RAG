import { useTheme } from '@/lib/theme';

interface Props {
  zrodla: string[];
}

export default function SourceList({ zrodla }: Props) {
  const th = useTheme();
  if (zrodla.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
      {zrodla.map((url) => (
        <a
          key={url}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            borderRadius: 10,
            background: th.accentSoft,
            color: th.accentText,
            fontSize: 12.5,
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: th.accent, flex: '0 0 auto' }} />
          <span style={{ flex: '1 1 auto', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {url}
          </span>
          <span style={{ flex: '0 0 auto', opacity: 0.6 }}>↗</span>
        </a>
      ))}
    </div>
  );
}
