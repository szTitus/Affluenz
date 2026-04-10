"use client";

import { useEffect, useState } from "react";
import ForecastChart from "./components/ForecastChart";

type AffluenceScore = {
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
  created_at: string;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const LEVEL = {
  low:    { label: "Calme",   color: "#4ade80", dim: "rgba(74,222,128,0.12)" },
  medium: { label: "Modérée", color: "#fb923c", dim: "rgba(251,146,60,0.12)" },
  high:   { label: "Élevée",  color: "#f87171", dim: "rgba(248,113,113,0.12)" },
};

function Bar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 99, height: 4, overflow: "hidden" }}>
      <div style={{ width: `${value}%`, height: "100%", background: color, borderRadius: 99, transition: "width 0.5s ease" }} />
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ fontSize: 13, color: "rgba(255,255,255,0.45)" }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color, fontVariantNumeric: "tabular-nums" }}>{value}</span>
      </div>
      <Bar value={value} color={color} />
    </div>
  );
}

function TodayCard({ day }: { day: AffluenceScore }) {
  const cfg = LEVEL[day.level] ?? LEVEL.medium;
  const date = new Date(day.score_date + "T12:00:00").toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long",
  });

  return (
    <div style={{
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 20,
      padding: "28px 28px 24px",
      marginBottom: 24,
    }}>
      {/* Date + badge */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
            Aujourd&apos;hui
          </div>
          <div style={{ fontSize: 15, color: "rgba(255,255,255,0.7)", textTransform: "capitalize" }}>{date}</div>
        </div>
        <div style={{
          background: cfg.dim,
          color: cfg.color,
          borderRadius: 99,
          padding: "5px 14px",
          fontSize: 13,
          fontWeight: 600,
          letterSpacing: "0.02em",
        }}>
          {cfg.label}
        </div>
      </div>

      {/* Score */}
      <div style={{ display: "flex", alignItems: "flex-end", gap: 8, marginBottom: 28 }}>
        <div style={{ fontSize: 72, fontWeight: 800, lineHeight: 1, color: cfg.color, letterSpacing: "-0.03em" }}>
          {day.global_score}
        </div>
        <div style={{ fontSize: 18, color: "rgba(255,255,255,0.2)", marginBottom: 8 }}>/100</div>
      </div>

      {/* Barre principale */}
      <div style={{ marginBottom: 28 }}>
        <Bar value={day.global_score} color={cfg.color} />
      </div>

      {/* Séparateur */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", marginBottom: 20 }} />

      {/* Sous-scores */}
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <Stat label="Disponibilité hébergements" value={day.availability_score} color="#60a5fa" />
        <Stat label="Niveau de prix"             value={day.price_score}        color="#c084fc" />
        <Stat label="Événements"                 value={day.event_score}        color="#fb923c" />
        <Stat label="Météo"                      value={day.weather_score}      color="#34d399" />
      </div>

      {/* Confiance */}
      <div style={{ marginTop: 20, fontSize: 12, color: "rgba(255,255,255,0.25)" }}>
        Indice de confiance · {Math.round(day.confidence_score * 100)}%
      </div>
    </div>
  );
}

function ForecastRow({ day, isToday }: { day: AffluenceScore; isToday: boolean }) {
  const cfg = LEVEL[day.level] ?? LEVEL.medium;
  const label = new Date(day.score_date + "T12:00:00").toLocaleDateString("fr-FR", {
    weekday: "short", day: "numeric", month: "short",
  });

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "120px 1fr 48px 80px",
      alignItems: "center",
      gap: 16,
      padding: "14px 20px",
      background: isToday ? "rgba(96,165,250,0.06)" : "rgba(255,255,255,0.02)",
      border: `1px solid ${isToday ? "rgba(96,165,250,0.2)" : "rgba(255,255,255,0.05)"}`,
      borderRadius: 12,
    }}>
      <div style={{ fontSize: 13, color: isToday ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.45)" }}>
        {label}
        {isToday && (
          <span style={{ marginLeft: 8, fontSize: 10, color: "#60a5fa", fontWeight: 600 }}>auj.</span>
        )}
      </div>
      <Bar value={day.global_score} color={cfg.color} />
      <div style={{ textAlign: "right", fontWeight: 700, fontSize: 15, color: cfg.color, fontVariantNumeric: "tabular-nums" }}>
        {day.global_score}
      </div>
      <div style={{
        textAlign: "center",
        fontSize: 12,
        fontWeight: 500,
        color: cfg.color,
        background: cfg.dim,
        borderRadius: 99,
        padding: "3px 10px",
      }}>
        {cfg.label}
      </div>
    </div>
  );
}

export default function HomePage() {
  const [today, setToday] = useState<AffluenceScore | null>(null);
  const [forecast, setForecast] = useState<AffluenceScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/v1/affluence/today`).then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/api/v1/affluence/forecast`).then((r) => r.ok ? r.json() : []).catch(() => []),
    ]).then(([t, f]) => {
      setToday(t);
      setForecast(f);
      setLoading(false);
    });
  }, []);

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "48px 20px 64px" }}>

      {/* Header */}
      <div style={{ marginBottom: 40 }}>
        <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
          Saintes-Maries-de-la-Mer
        </div>
        <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700, color: "rgba(255,255,255,0.9)", letterSpacing: "-0.02em" }}>
          Indice d&apos;affluence
        </h1>
      </div>

      {/* Carte aujourd'hui */}
      {loading ? (
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 20, padding: 28, marginBottom: 24, color: "rgba(255,255,255,0.25)", fontSize: 14 }}>
          Chargement…
        </div>
      ) : today ? (
        <TodayCard day={today} />
      ) : (
        <div style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: 16, padding: 20, marginBottom: 24, color: "#f87171", fontSize: 14 }}>
          Impossible de charger le score du jour.
        </div>
      )}

      {/* Graphique */}
      {forecast.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>
            Courbe 7 jours
          </div>
          <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 16, padding: "20px 16px 12px" }}>
            <ForecastChart forecast={forecast} />
          </div>
        </div>
      )}

      {/* Prévisions */}
      {forecast.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>
            Prévisions 7 jours
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {forecast.map((day) => (
              <ForecastRow
                key={day.id}
                day={day}
                isToday={day.score_date === today?.score_date}
              />
            ))}
          </div>
        </div>
      )}

      <footer style={{ marginTop: 48, fontSize: 12, color: "rgba(255,255,255,0.15)", textAlign: "center" }}>
        Affluence · Saintes-Maries-de-la-Mer
      </footer>
    </main>
  );
}
