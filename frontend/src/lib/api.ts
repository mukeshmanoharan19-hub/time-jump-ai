const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SESSION_KEY = "timejump_session_token";

export function getSessionToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SESSION_KEY);
}

export function setSessionToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(SESSION_KEY, token);
  else localStorage.removeItem(SESSION_KEY);
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    return JSON.stringify(data.detail ?? data);
  } catch {
    return res.statusText || "Request failed";
  }
}

export async function exchangeMicrosoftToken(
  accessToken: string,
  expiresIn?: number
): Promise<{ session_token: string; user: { id: string; email?: string; display_name?: string } }> {
  const res = await fetch(`${API_URL}/auth/microsoft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: accessToken, expires_in: expiresIn }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchMe(sessionToken: string) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${sessionToken}` },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function logoutSession(sessionToken: string) {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${sessionToken}` },
  });
  setSessionToken(null);
}

export type ResolveResult = {
  normalized_url: string;
  kind: string;
  drive_item_id: string | null;
  drive_id: string | null;
  name: string | null;
  size: number | null;
  mime_type: string | null;
  web_url: string | null;
  can_download: boolean;
  transcript_available: boolean;
  transcript_source: string | null;
  transcript_item_id: string | null;
};

export async function resolveRecording(
  sessionToken: string,
  url: string
): Promise<ResolveResult> {
  const res = await fetch(`${API_URL}/recordings/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${sessionToken}`,
    },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
