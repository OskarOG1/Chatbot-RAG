const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function POST(request: Request) {
  const body = await request.text();

  const upstream = await fetch(`${FASTAPI_URL}/admin/kolejka/odpowiedz`, {
    method: 'POST',
    cache: 'no-store',
    headers: {
      'content-type': 'application/json',
      'x-admin-token': request.headers.get('x-admin-token') ?? '',
    },
    body,
  });

  const tresc = await upstream.text();

  return new Response(tresc, {
    status: upstream.status,
    headers: {
      'content-type': 'application/json',
      'cache-control': 'no-store',
    },
  });
}
