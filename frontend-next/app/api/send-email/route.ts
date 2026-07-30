import type { NextRequest } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  const body = await request.text();

  const upstream = await fetch(`${FASTAPI_URL}/send-email`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body,
  });

  const dane = await upstream.text();

  return new Response(dane, {
    status: upstream.status,
    headers: { 'content-type': 'application/json' },
  });
}
