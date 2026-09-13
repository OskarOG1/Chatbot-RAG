import { useTheme } from '@/lib/theme';

interface Props {
  tekst: string | null;
  waski?: boolean;
}

export default function Toast({ tekst, waski = false }: Props) {
  const th = useTheme();
  if (!tekst) return null;

  return (
    <div
      role="status"
      style={{
        position: 'fixed',
        ...(waski ? { top: 64 } : { bottom: 24 }),
        left: 0,
        right: 0,
        margin: '0 auto',
        width: 'fit-content',
        maxWidth: 'calc(100vw - 32px)',
        background: th.toastBg,
        color: th.toastInk,
        padding: '11px 20px',
        borderRadius: 10,
        fontSize: 13,
        fontWeight: 600,
        textAlign: 'center',
        animation: 'dcFadeUp 0.25s ease both',
        boxShadow: th.shadowLift,
        pointerEvents: 'none',
        zIndex: 95,
      }}
    >
      {tekst}
    </div>
  );
}
