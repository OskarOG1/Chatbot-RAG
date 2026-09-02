const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

export async function POST(request: Request) {
  const body = await request.text();
  const forwardedFor = request.headers.get('x-forwarded-for');
  const headers: Record<string, string> = {
    'content-type': 'application/json',
    'x-admin-token': request.headers.get('x-admin-token') ?? '',
  };
  if (forwardedFor) {
    headers['x-forwarded-for'] = forwardedFor;
  }

  const upstream = await fetch(`${FASTAPI_URL}/admin/kolejka/odpowiedz`, {
    method: 'POST',
    cache: 'no-store',
    headers,
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
