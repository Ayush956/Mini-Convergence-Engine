import type { ApiError, Reading } from './reading.models';

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
  source: 'model' | 'unavailable';
}

const CHAT_URL = '/api/chat';

const UNREACHABLE =
  'Could not reach the assistant. The backend may be waking from idle — please try again.';

export async function sendChatMessage(
  message: string,
  reading: Reading | null,
  history: ChatTurn[],
): Promise<ChatResponse> {
  let response: Response;

  try {
    response = await fetch(CHAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, reading: reading ?? null, history }),
    });
  } catch {
    throw errorWith(UNREACHABLE);
  }

  if (response.ok) {
    return (await response.json()) as ChatResponse;
  }

  let body: Partial<ApiError> | null = null;
  try {
    body = (await response.json()) as Partial<ApiError>;
  } catch {
    body = null;
  }

  if (body && typeof body.message === 'string' && body.message) {
    throw errorWith(body.message);
  }

  throw errorWith('Something went wrong while asking the assistant.');
}

function errorWith(message: string): ApiError {
  return { message, field: null };
}
