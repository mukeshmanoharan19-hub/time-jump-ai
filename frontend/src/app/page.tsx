const API_URL =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

type HealthResponse = {
  status: string;
  services: Record<string, { ok: boolean; detail: string }>;
};

async function getHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const health = await getHealth();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <p className="mb-3 text-sm font-medium uppercase tracking-widest text-[var(--accent)]">
        Phase 0
      </p>
      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
        TimeJump AI
      </h1>
      <p className="mt-4 max-w-xl text-lg text-[var(--muted)]">
        Turn Microsoft Teams recordings into a temporary, searchable knowledge
        base — then jump to the exact moment a topic was discussed.
      </p>

      <div className="mt-10 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-sm font-medium text-[var(--muted)]">API status</h2>
        {health ? (
          <div className="mt-3 space-y-2 text-sm">
            <p>
              Overall:{" "}
              <span
                className={
                  health.status === "healthy"
                    ? "text-emerald-400"
                    : "text-amber-400"
                }
              >
                {health.status}
              </span>
            </p>
            <ul className="space-y-1 text-[var(--muted)]">
              {Object.entries(health.services).map(([name, svc]) => (
                <li key={name}>
                  {name}: {svc.ok ? "ok" : `error (${svc.detail})`}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-3 text-sm text-amber-400">
            Could not reach the API at {API_URL}. Start the stack with{" "}
            <code className="rounded bg-black/30 px-1">docker compose up</code>.
          </p>
        )}
      </div>

      <p className="mt-8 text-sm text-[var(--muted)]">
        Next: Microsoft sign-in, ingest, and semantic search (upcoming phases).
      </p>
    </main>
  );
}
