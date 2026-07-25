"use client";

import { useCallback, useEffect, useState } from "react";
import {
  exchangeMicrosoftToken,
  getSessionToken,
  logoutSession,
  resolveRecording,
  ResolveResult,
  setSessionToken,
} from "@/lib/api";
import {
  isMsalConfigured,
  loginAndGetAccessToken,
  logoutMicrosoft,
} from "@/lib/msal";

type UserInfo = { id: string; email?: string; display_name?: string };

export default function Phase1Panel() {
  const [sessionToken, setLocalSession] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResolveResult | null>(null);

  useEffect(() => {
    setLocalSession(getSessionToken());
  }, []);

  const signIn = useCallback(async () => {
    if (!isMsalConfigured) {
      setError("Set NEXT_PUBLIC_AZURE_AD_CLIENT_ID and TENANT_ID in .env");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const token = await loginAndGetAccessToken();
      const exchanged = await exchangeMicrosoftToken(
        token.accessToken,
        token.expiresOn
          ? Math.max(60, Math.floor((token.expiresOn.getTime() - Date.now()) / 1000))
          : undefined
      );
      setSessionToken(exchanged.session_token);
      setLocalSession(exchanged.session_token);
      setUser(exchanged.user);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    if (sessionToken) {
      try {
        await logoutSession(sessionToken);
      } catch {
        setSessionToken(null);
      }
    }
    setLocalSession(null);
    setUser(null);
    setResult(null);
    try {
      await logoutMicrosoft();
    } catch {
      /* ignore popup dismissal */
    }
  }, [sessionToken]);

  const onResolve = useCallback(async () => {
    if (!sessionToken) {
      setError("Sign in with Microsoft first");
      return;
    }
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const resolved = await resolveRecording(sessionToken, url.trim());
      setResult(resolved);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Resolve failed");
    } finally {
      setBusy(false);
    }
  }, [sessionToken, url]);

  return (
    <div className="mt-10 space-y-6">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-sm font-medium text-[var(--muted)]">Microsoft account</h2>
        {!isMsalConfigured && (
          <p className="mt-3 text-sm text-amber-400">
            Configure <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_AZURE_AD_CLIENT_ID</code>{" "}
            and <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_AZURE_AD_TENANT_ID</code> in{" "}
            <code className="rounded bg-black/30 px-1">.env</code>, then restart the web service.
          </p>
        )}
        {sessionToken ? (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <p className="text-sm">
              Signed in{user?.display_name ? ` as ${user.display_name}` : ""}
              {user?.email ? ` (${user.email})` : ""}
            </p>
            <button
              type="button"
              onClick={signOut}
              className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-white/5"
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={signIn}
            disabled={busy || !isMsalConfigured}
            className="mt-3 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in with Microsoft"}
          </button>
        )}
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-sm font-medium text-[var(--muted)]">Resolve recording URL</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Paste a Teams / SharePoint / Stream recording link. Phase 1 resolves metadata via Graph
          (ingest comes in Phase 2).
        </p>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://….sharepoint.com/…/stream.aspx?id=…"
          className="mt-4 w-full rounded-lg border border-[var(--border)] bg-black/20 px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
        />
        <button
          type="button"
          onClick={onResolve}
          disabled={busy || !sessionToken || !url.trim()}
          className="mt-3 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "Resolving…" : "Resolve"}
        </button>

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

        {result && (
          <dl className="mt-4 grid gap-2 text-sm">
            <div>
              <dt className="text-[var(--muted)]">Name</dt>
              <dd>{result.name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Kind</dt>
              <dd>{result.kind}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Can download</dt>
              <dd>{result.can_download ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Transcript nearby</dt>
              <dd>
                {result.transcript_available
                  ? `yes (${result.transcript_source})`
                  : "not found (Whisper fallback in Phase 2)"}
              </dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Normalized URL</dt>
              <dd className="break-all text-[var(--muted)]">{result.normalized_url}</dd>
            </div>
          </dl>
        )}
      </div>
    </div>
  );
}
