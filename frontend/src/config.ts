/// <reference types="vite/client" />

export function getApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  const value = configured ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : undefined);
  if (!value) {
    throw new Error('Set VITE_API_BASE_URL to a loopback API URL. Production builds require an explicit value.');
  }
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error('VITE_API_BASE_URL must be a well-formed absolute HTTP or HTTPS URL.');
  }
  const loopback = url.hostname === 'localhost' || url.hostname === '[::1]' ||
    /^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(url.hostname);
  if (!['http:', 'https:'].includes(url.protocol) || !loopback || url.username || url.password || url.search || url.hash) {
    throw new Error('VITE_API_BASE_URL must use HTTP or HTTPS on a loopback host, without credentials, query parameters, or a fragment.');
  }
  return url.href.replace(/\/$/, '');
}
