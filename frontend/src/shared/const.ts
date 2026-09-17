export const COOKIE_NAME = "medicare-session";
export const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;
export const OAUTH_STATE_COOKIE = "medicare-oauth-state";

export function encodeOAuthState(value: Record<string, string>) {
  return btoa(JSON.stringify(value));
}