"use client";

import { useEffect, useState } from "react";
import ForecastChart from "./components/ForecastChart";

type Score = {
  id: number;
  score_date: string;
  zone: string;
  global_score: number;
  level: "low" | "medium" | "high";
  availability_score: number;
  price_score: number;
  event_score: number;
  weather_score: number;
  confidence_score: number;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const L = {
  low:    { label: "Calme",   color: "#34d399", glow: "rgba(52,211,153,0.15)",  ring: "rgba(52,211,153,0.25)"  },
  medium: { label: "Modérée", color: "#fbbf24", glow: "rgba(251,191,36,0.15)",  ring: "rgba(251,191,36,0.25)"  },
  high:   { label: "Élevée",  color: "#f87171", glow: "rgba(248,113,113,0.15)", ring: "rgba(248,113,113,0.25)" },
};

/* ── helpers ──────────────────────────────────────────── */

function fmt(dateStr: string, opts: Intl.DateTimeFormatOptions) {
  return new Date(dateStr + "T12:00:00").toLocaleDateString("fr-FR", opts);
}

/* ── composants ───────────────────────────────────────── */

function Ring({ score, color }: { score: number; color: string }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;

  return (
    <svg width={130} height={130} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={65} cy={65} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={8} />
      <circle
        cx={65} cy={65} r={r}
        fill="none"
        stroke={color}
        strokeWidth={8}
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circ}`}
        style={{ transition: "stroke-dasharray 0.8s ease", filter: `drop-shadow(0 0 6px ${color})` }}
      />
    </svg>
  );
}

function Bar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 99, height: 3, overflow: "hidden" }}>
      <div style={{ width: `${value}%`, height: "100%", background: color, borderRadius: 99 }} />
    </div>
  );
}

function SubScore({ icon, label, value, color }: { icon: string; label: string; value: number; color: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 14 }}>{icon}</span>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }}>{label}</span>
        </div>
        <span style={{ fontSize: 13, fontWeight: 600, color }}>{value}</span>
      </div>
      <Bar value={value} color={color} />
    </div>
  );
}

function TodayCard({ day }: { day: Score }) {
  const cfg = L[day.level] ?? L.medium;
  return (
    <div style={{
      position: "relative",
      background: "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 24,
      padding: "32px 28px",
      marginBottom: 16,
      overflow: "hidden",
    }}>
      {/* Glow bg */}
      <div style={{
        position: "absolute", top: -40, right: -40,
        width: 200, height: 200, borderRadius: "50%",
        background: cfg.glow, filter: "blur(60px)", pointerEvents: "none",
      }} />

      {/* Top row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
        <div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
            Aujourd&apos;hui · {fmt(day.score_date, { weekday: "long", day: "numeric", month: "long" })}
          </div>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.35)" }}>
            Saintes-Maries-de-la-Mer
          </div>
        </div>
        <div style={{
          background: cfg.ring,
          color: cfg.color,
          border: `1px solid ${cfg.color}30`,
          borderRadius: 99,
          padding: "6px 16px",
          fontSize: 13,
          fontWeight: 600,
        }}>
          {cfg.label}
        </div>
      </div>

      {/* Score + ring */}
      <div style={{ display: "flex", alignItems: "center", gap: 28, marginBottom: 32 }}>
        <div style={{ position: "relative", flexShrink: 0 }}>
          <Ring score={day.global_score} color={cfg.color} />
          <div style={{
            position: "absolute", inset: 0,
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
          }}>
            <div style={{ fontSize: 32, fontWeight: 800, color: cfg.color, lineHeight: 1, letterSpacing: "-0.03em" }}>
              {day.global_score}
            </div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", marginTop: 2 }}>/100</div>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", marginBottom: 4 }}>Indice d&apos;affluence</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#e8edf5", letterSpacing: "-0.02em", marginBottom: 8 }}>
            {cfg.label === "Calme" && "Peu de monde"}
            {cfg.label === "Modérée" && "Fréquenté"}
            {cfg.label === "Élevée" && "Très fréquenté"}
          </div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.2)" }}>
            Confiance · {Math.round(day.confidence_score * 100)}%
          </div>
        </div>
      </div>

      {/* Séparateur */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", marginBottom: 24 }} />

      {/* Sous-scores */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <SubScore icon="🏨" label="Disponibilité hébergements" value={day.availability_score} color="#60a5fa" />
        <SubScore icon="💶" label="Niveau de prix"             value={day.price_score}        color="#c084fc" />
        <SubScore icon="🎉" label="Événements"                 value={day.event_score}        color="#fb923c" />
        <SubScore icon="☀️" label="Météo"                      value={day.weather_score}      color="#34d399" />
      </div>
    </div>
  );
}

function DayCard({ day, isToday }: { day: Score; isToday: boolean }) {
  const cfg = L[day.level] ?? L.medium;
  const weekday = fmt(day.score_date, { weekday: "short" });
  const date    = fmt(day.score_date, { day: "numeric" });

  return (
    <div style={{
      flex: "1 0 0",
      minWidth: 80,
      background: isToday ? cfg.ring : "rgba(255,255,255,0.03)",
      border: `1px solid ${isToday ? cfg.color + "40" : "rgba(255,255,255,0.06)"}`,
      borderRadius: 16,
      padding: "16px 12px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 10,
    }}>
      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", textTransform: "capitalize" }}>{weekday}</div>
      <div style={{ fontSize: 13, color: "rgba(255,255,255,0.6)", fontWeight: 500 }}>{date}</div>
      <div style={{
        width: 44, height: 44, borderRadius: "50%",
        background: cfg.ring,
        border: `2px solid ${cfg.color}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 15, fontWeight: 800, color: cfg.color,
        boxShadow: `0 0 12px ${cfg.glow}`,
      }}>
        {day.global_score}
      </div>
      <div style={{
        fontSize: 10, color: cfg.color, fontWeight: 600,
        background: cfg.ring, borderRadius: 99, padding: "2px 8px",
      }}>
        {cfg.label}
      </div>
    </div>
  );
}

/* ── page ─────────────────────────────────────────────── */

export default function HomePage() {
  const [today, setToday] = useState<Score | null>(null);
  const [forecast, setForecast] = useState<Score[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/v1/affluence/today`).then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/api/v1/affluence/forecast`).then((r) => r.ok ? r.json() : []).catch(() => []),
    ]).then(([t, f]) => { setToday(t); setForecast(f); setLoading(false); });
  }, []);

  return (
    <main style={{ maxWidth: 600, margin: "0 auto", padding: "48px 20px 80px" }}>

      {/* VERSION MARKER - TEST DEPLOY */}
      <div style={{
        background: "linear-gradient(90deg, #ec4899, #8b5cf6)",
        color: "white",
        padding: "12px 20px",
        borderRadius: 12,
        marginBottom: 24,
        fontSize: 13,
        fontWeight: 700,
        textAlign: "center",
        letterSpacing: "0.05em",
      }}>
        🚀 BUILD v2 · {new Date().toISOString().slice(0, 16)}
      </div>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 99, padding: "5px 12px 5px 10px", marginBottom: 16 }}>
          <span style={{ fontSize: 14 }}>📍</span>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", fontWeight: 500 }}>Saintes-Maries-de-la-Mer · 13460</span>
        </div>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "#e8edf5", letterSpacing: "-0.02em" }}>
          Indice d&apos;affluence
        </h1>
      </div>

      {/* Carte du jour */}
      {loading ? (
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 24, padding: 32, marginBottom: 16, color: "rgba(255,255,255,0.2)", fontSize: 14 }}>
          Chargement…
        </div>
      ) : today ? (
        <TodayCard day={today} />
      ) : (
        <div style={{ background: "rgba(248,113,113,0.06)", border: "1px solid rgba(248,113,113,0.15)", borderRadius: 16, padding: 20, marginBottom: 16, color: "#f87171", fontSize: 14 }}>
          Impossible de charger les données. Vérifiez que l&apos;API est démarrée.
        </div>
      )}

      {/* Cards 7 jours */}
      {forecast.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12 }}>
            7 prochains jours
          </div>
          <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
            {forecast.map((day) => (
              <DayCard key={day.id} day={day} isToday={day.score_date === today?.score_date} />
            ))}
          </div>
        </div>
      )}

      {/* Graphique */}
      {forecast.length > 0 && (
        <div style={{
          background: "rgba(255,255,255,0.02)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 20,
          padding: "20px 16px 12px",
        }}>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12 }}>
            Tendance
          </div>
          <ForecastChart forecast={forecast} />
        </div>
      )}

      <footer style={{ marginTop: 48, textAlign: "center", fontSize: 11, color: "rgba(255,255,255,0.12)" }}>
        Affluence · Saintes-Maries-de-la-Mer
      </footer>
    </main>
  );
}
