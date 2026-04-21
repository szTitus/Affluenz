"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SECRET_KEY = "aff_stats_secret";

type DayRow = { date: string; views: number; unique: number };
type Stats = {
  range_days: number;
  since: string;
  total_views: number;
  total_unique_visitors: number;
  all_time_views: number;
  all_time_unique_visitors: number;
  days: DayRow[];
};

export default function StatsPage() {
  const [secret, setSecret] = useState<string>("");
  const [authed, setAuthed] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rangeDays, setRangeDays] = useState(30);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem(SECRET_KEY) : null;
    if (stored) {
      setSecret(stored);
      setAuthed(true);
    }
  }, []);

  useEffect(() => {
    if (!authed || !secret) return;
    setLoading(true);
    setError(null);
    fetch(`${API}/api/v1/stats?days=${rangeDays}`, {
      headers: { "X-Stats-Secret": secret },
    })
      .then(async (r) => {
        if (r.status === 401) {
          setError("Secret invalide");
          setAuthed(false);
          localStorage.removeItem(SECRET_KEY);
          return null;
        }
        if (!r.ok) {
          setError(`Erreur ${r.status}`);
          return null;
        }
        return r.json();
      })
      .then((data) => {
        if (data) setStats(data);
      })
      .catch(() => setError("Impossible de joindre l'API"))
      .finally(() => setLoading(false));
  }, [authed, secret, rangeDays]);

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;
    localStorage.setItem(SECRET_KEY, secret.trim());
    setAuthed(true);
  }

  function handleLogout() {
    localStorage.removeItem(SECRET_KEY);
    setSecret("");
    setAuthed(false);
    setStats(null);
  }

  // ── Login screen ────────────────────────────────────────────────
  if (!authed) {
    return (
      <main style={{ maxWidth: 420, margin: "120px auto", padding: "0 20px" }}>
        <h1 style={{
          fontSize: 22, fontWeight: 700, color: "#e8edf5",
          letterSpacing: "-0.02em", marginBottom: 8,
        }}>
          Statistiques · Admin
        </h1>
        <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", marginBottom: 24 }}>
          Entre le secret admin pour afficher les statistiques de visite.
        </p>

        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input
            type="password"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
            placeholder="Secret admin"
            autoFocus
            style={{
              padding: "12px 14px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.08)",
              background: "rgba(255,255,255,0.04)",
              color: "#e8edf5",
              fontSize: 14,
              fontFamily: "inherit",
              outline: "none",
            }}
          />
          <button
            type="submit"
            style={{
              padding: "12px 14px",
              borderRadius: 10,
              border: "none",
              background: "#6366f1",
              color: "white",
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            Afficher les stats
          </button>
          {error && (
            <div style={{ fontSize: 12, color: "#f87171", marginTop: 4 }}>{error}</div>
          )}
        </form>
      </main>
    );
  }

  // ── Dashboard ───────────────────────────────────────────────────
  const maxViews = Math.max(1, ...(stats?.days ?? []).map((d) => d.views));

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 20px 80px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#e8edf5", letterSpacing: "-0.02em" }}>
            Statistiques
          </h1>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.35)", marginTop: 4 }}>
            Affluence · tableau de bord admin
          </div>
        </div>
        <button
          onClick={handleLogout}
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.1)",
            color: "rgba(255,255,255,0.6)",
            padding: "6px 14px",
            borderRadius: 99,
            fontSize: 12,
            cursor: "pointer",
            fontFamily: "inherit",
          }}
        >
          Déconnexion
        </button>
      </div>

      {/* Range selector */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {[7, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setRangeDays(d)}
            style={{
              padding: "6px 14px",
              borderRadius: 99,
              border: "1px solid rgba(255,255,255,0.08)",
              background: rangeDays === d ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.03)",
              color: rangeDays === d ? "#a5b4fc" : "rgba(255,255,255,0.5)",
              fontSize: 12,
              fontWeight: 500,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            {d} jours
          </button>
        ))}
      </div>

      {loading && !stats && (
        <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 14 }}>Chargement…</div>
      )}

      {error && (
        <div style={{
          background: "rgba(248,113,113,0.08)",
          border: "1px solid rgba(248,113,113,0.2)",
          color: "#f87171",
          padding: 16,
          borderRadius: 12,
          fontSize: 14,
          marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {stats && (
        <>
          {/* KPIs */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 24 }}>
            <KPI label="Vues (période)" value={stats.total_views} accent="#6366f1" />
            <KPI label="Visiteurs uniques" value={stats.total_unique_visitors} accent="#34d399" />
            <KPI label="Vues totales" value={stats.all_time_views} accent="#fbbf24" />
            <KPI label="Uniques totaux" value={stats.all_time_unique_visitors} accent="#c084fc" />
          </div>

          {/* Bars */}
          <div style={{
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 16,
            padding: 20,
          }}>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 14 }}>
              Détail par jour
            </div>
            {stats.days.length === 0 ? (
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.3)" }}>Aucune visite enregistrée sur cette période.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {[...stats.days].reverse().map((d) => {
                  const pct = Math.round((d.views / maxViews) * 100);
                  return (
                    <div key={d.date} style={{ display: "grid", gridTemplateColumns: "100px 1fr 90px", gap: 12, alignItems: "center" }}>
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>
                        {new Date(d.date + "T12:00:00").toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" })}
                      </div>
                      <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 4, height: 20, position: "relative", overflow: "hidden" }}>
                        <div style={{
                          width: `${pct}%`, height: "100%",
                          background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
                          borderRadius: 4, transition: "width 0.3s",
                        }} />
                      </div>
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", textAlign: "right" }}>
                        <b style={{ color: "#e8edf5" }}>{d.views}</b> · {d.unique} uniq.
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </main>
  );
}

function KPI({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.06)",
      borderRadius: 14,
      padding: "16px 18px",
    }}>
      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 6, letterSpacing: "0.03em" }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, color: accent, letterSpacing: "-0.02em" }}>
        {value.toLocaleString("fr-FR")}
      </div>
    </div>
  );
}
