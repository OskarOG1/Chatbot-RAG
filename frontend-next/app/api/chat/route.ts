import type { NextRequest } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  const body = await request.text();
  const forwardedFor = request.headers.get('x-forwarded-for');
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  if (forwardedFor) {
    headers['x-forwarded-for'] = forwardedFor;
  }

  const upstream = await fetch(`${FASTAPI_URL}/chat/stream`, {
    method: 'POST',
    headers,
    body,
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache',
    },
  });
}
