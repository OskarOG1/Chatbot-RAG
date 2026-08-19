import type { NextRequest } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.toString();

  const upstream = await fetch(`${FASTAPI_URL}/admin/oceny?${query}`, {
    cache: 'no-store',
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
