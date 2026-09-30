/**
 * Where the API lives.
 *
 * Angular's static build inlines this at compile time, so the deployed
 * bundle needs the production URL baked in. Vercel sets it via the
 * build-time replacement in environments, but for local development the
 * Angular dev server proxies /api to localhost:8000 (see proxy.conf.json),
 * which is why an empty base works here: requests go to the same origin and
 * the proxy forwards them.
 */
export const API_BASE_URL = '';
