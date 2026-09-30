import type { ApiError, Reading, ReadingRequest } from './reading.models';

/**
 * Requests go to the app's own origin, locally and deployed alike: the dev
 * server proxies /api to the FastAPI process, and in production the two are
 * served under one domain. So there is no environment branch here.
 */
const READING_URL = '/api/reading';

const UNREACHABLE =
  'Could not reach the calculation service. It may be waking up from idle, ' +
  'which takes up to a minute on a free instance. Please try again.';

const UNEXPECTED = 'Something went wrong while calculating. Please try again.';

/** Rejects with an ApiError, never with a raw fetch failure. */
export async function getReading(request: ReadingRequest): Promise<Reading> {
  let response: Response;

  try {
    response = await fetch(READING_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
  } catch {
    // fetch only throws for failures that never reached the server: a cold
    // instance, a dropped connection, a CORS refusal. None of those carry a
    // message of their own, so they would otherwise surface as blank.
    throw errorWith(UNREACHABLE);
  }

  if (response.ok) {
    return (await response.json()) as Reading;
  }

  // The backend already flattens its validation failures to {message, field}.
  // The only work left is not assuming it did - an error page from a proxy in
  // front of it would not be JSON at all.
  let body: Partial<ApiError> | null = null;
  try {
    body = (await response.json()) as Partial<ApiError>;
  } catch {
    body = null;
  }

  if (body && typeof body.message === 'string' && body.message) {
    throw errorWith(body.message, body.field ?? null);
  }

  throw errorWith(UNEXPECTED);
}

function errorWith(message: string, field: string | null = null): ApiError {
  return { message, field };
}
