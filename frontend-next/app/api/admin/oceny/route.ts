import type { NextRequest } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.toString();
  const forwardedFor = request.headers.get('x-forwarded-for');
  const headers: Record<string, string> = { 'x-admin-token': request.headers.get('x-admin-token') ?? '' };
  if (forwardedFor) {
    headers['x-forwarded-for'] = forwardedFor;
  }

  const upstream = await fetch(`${FASTAPI_URL}/admin/oceny?${query}`, {
    cache: 'no-store',
    headers,
  });

  const body = await upstream.text();

  return new Response(body, {
    status: upstream.status,
    headers: {
      'content-type': 'application/json',
      'cache-control': 'no-store',
    },
  });
}
