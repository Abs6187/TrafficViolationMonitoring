export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api";


export function apiUrl(path) {
  return `${apiBaseUrl}${path}`;
}
