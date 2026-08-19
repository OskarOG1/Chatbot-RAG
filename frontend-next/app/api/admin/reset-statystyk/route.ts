const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function POST(request: Request) {
  const upstream = await fetch(`${FASTAPI_URL}/admin/resetuj-statystyki`, {
    method: 'POST',
    cache: 'no-store',
    headers: { 'x-admin-token': request.headers.get('x-admin-token') ?? '' },
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
