import type { NextRequest } from 'next/server';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.toString();
  const forwardedFor = request.headers.get('x-forwarded-for');
  const naglowkiZadania: Record<string, string> = { 'x-admin-token': request.headers.get('x-admin-token') ?? '' };
  if (forwardedFor) {
    naglowkiZadania['x-forwarded-for'] = forwardedFor;
  }

  const upstream = await fetch(`${FASTAPI_URL}/admin/eksport?${query}`, {
    cache: 'no-store',
    headers: naglowkiZadania,
  });

  const headers: Record<string, string> = { 'cache-control': 'no-store' };
  const contentType = upstream.headers.get('content-type');
  const contentDisposition = upstream.headers.get('content-disposition');
  if (contentType) {
    headers['content-type'] = contentType;
  }
  if (contentDisposition) {
    headers['content-disposition'] = contentDisposition;
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers,
  });
}
