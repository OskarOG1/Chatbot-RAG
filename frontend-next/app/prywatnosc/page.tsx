'use client';

import Link from 'next/link';

export default function PrywatnoscPage() {
  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '48px 24px' }}>
      <Link href="/" style={{ fontSize: 13 }}>&larr; Wróć</Link>
      <h1 style={{ fontSize: 22, marginTop: 24 }}>Jak przetwarzamy dane</h1>
      <p style={{ marginTop: 12, color: '#666' }}>Treść w przygotowaniu.</p>
    </div>
  );
}
