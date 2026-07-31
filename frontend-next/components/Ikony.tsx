export function FlagaPl() {
  return (
    <svg width={18} height={13} viewBox="0 0 20 14" aria-hidden focusable="false">
      <defs>
        <clipPath id="flagaPlRamka">
          <rect width="20" height="14" rx="2" />
        </clipPath>
      </defs>
      <g clipPath="url(#flagaPlRamka)">
        <rect width="20" height="7" fill="#FFFFFF" />
        <rect y="7" width="20" height="7" fill="#D4213D" />
      </g>
      <rect width="20" height="14" rx="2" fill="none" stroke="rgba(0,0,0,0.18)" />
    </svg>
  );
}

export function FlagaGb() {
  return (
    <svg width={18} height={13} viewBox="0 0 20 14" aria-hidden focusable="false">
      <defs>
        <clipPath id="flagaGbRamka">
          <rect width="20" height="14" rx="2" />
        </clipPath>
      </defs>
      <g clipPath="url(#flagaGbRamka)">
        <rect width="20" height="14" fill="#012169" />
        <path d="M0 0 L20 14 M20 0 L0 14" stroke="#FFFFFF" strokeWidth={3} />
        <path d="M0 0 L20 14 M20 0 L0 14" stroke="#C8102E" strokeWidth={1.4} />
        <path d="M10 0 V14 M0 7 H20" stroke="#FFFFFF" strokeWidth={4.6} />
        <path d="M10 0 V14 M0 7 H20" stroke="#C8102E" strokeWidth={2.6} />
      </g>
      <rect width="20" height="14" rx="2" fill="none" stroke="rgba(0,0,0,0.18)" />
    </svg>
  );
}

export function IkonaKosz({ color = 'currentColor' }: { color?: string }) {
  return (
    <svg width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden focusable="false">
      <path
        d="M2.5 4.5h11M6 4.5V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1.5M6.7 7.5v4.2M9.3 7.5v4.2M3.6 4.5l.6 8a1 1 0 0 0 1 .93h5.6a1 1 0 0 0 1-.93l.6-8"
        stroke={color}
        strokeWidth={1.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function IkonaSlonce({ color = 'currentColor' }: { color?: string }) {
  return (
    <svg width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden focusable="false">
      <circle cx="8" cy="8" r="3.2" stroke={color} strokeWidth={1.4} />
      <path
        d="M8 1.3v1.6M8 13.1v1.6M14.7 8h-1.6M2.9 8H1.3M12.7 3.3l-1.1 1.1M4.4 11.6l-1.1 1.1M12.7 12.7l-1.1-1.1M4.4 4.4 3.3 3.3"
        stroke={color}
        strokeWidth={1.4}
        strokeLinecap="round"
      />
    </svg>
  );
}

export function IkonaKsiezyc({ color = 'currentColor' }: { color?: string }) {
  return (
    <svg width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden focusable="false">
      <path
        d="M13.2 9.7A5.6 5.6 0 0 1 6.3 2.8a5.6 5.6 0 1 0 6.9 6.9Z"
        stroke={color}
        strokeWidth={1.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function IkonaWyslij({ color = 'currentColor' }: { color?: string }) {
  return (
    <svg width={14} height={14} viewBox="0 0 16 16" fill="none" aria-hidden focusable="false">
      <path d="M8 13V3M8 3 3.5 7.5M8 3l4.5 4.5" stroke={color} strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
