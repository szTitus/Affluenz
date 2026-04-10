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

const LEVEL_CONFIG = {
  low:    { label: "Faible",   color: "#22c55e", bg: "#14532d" },
  medium: { label: "Modérée",  color: "#f59e0b", bg: "#451a03" },
  high:   { label: "Élevée",   color: "#ef4444", bg: "#450a0a" },
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ background: "#0f172a", borderRadius: 6, height: 8, overflow: "hidden" }}>
      <div style={{ width: `${value}%`, height: "100%", background: color, borderRadius: 6, transition: "width 0.4s ease" }} />
    </div>
  );
}

function ComponentRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 13 }}>
        <span style={{ color: "#94a3b8" }}>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{value}</span>
      </div>
      <ScoreBar value={value} color={color} />
    </div>
  );
}

function TodayCard({ today }: { today: AffluenceScore }) {
  const cfg = LEVEL_CONFIG[today.level] ?? LEVEL_CONFIG.medium;
  return (
    <div style={{ background: "#1e293b", borderRadius: 16, padding: 28, marginBottom: 32 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ fontSize: 13, color: "#64748b", marginBottom: 4 }}>
            Score aujourd&apos;hui ·{" "}
            {new Date(today.score_date + "T12:00:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}
          </div>
          <div style={{ fontSize: 56, fontWeight: 800, lineHeight: 1, color: cfg.color }}>
            {today.global_score}
            <span style={{ fontSize: 20, color: "#475569" }}>/100</span>
          </div>
          <div style={{ fontSize: 13, color: "#64748b", marginTop: 4 }}>Zone : {today.zone}</div>
        </div>
        <div style={{ background: cfg.bg, color: cfg.color, borderRadius: 12, padding: "12px 20px", fontSize: 20, fontWeight: 700 }}>
          {cfg.label}
        </div>
      </div>
      <div style={{ fontSize: 12, color: "#475569", marginBottom: 20 }}>
        Niveau de confiance : <strong style={{ color: "#94a3b8" }}>{Math.round(today.confidence_score * 100)} %</strong>
      </div>
      <div>
        <div style={{ fontSize: 13, color: "#64748b", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>Composants</div>
        <ComponentRow label="Disponibilité hébergements" value={today.availability_score} color="#60a5fa" />
        <ComponentRow label="Niveau de prix"             value={today.price_score}        color="#a78bfa" />
        <ComponentRow label="Événements"                 value={today.event_score}        color="#fb923c" />
        <ComponentRow label="Météo"                      value={today.weather_score}      color="#34d399" />
      </div>
    </div>
  );
}

function ForecastList({ forecast, todayDate }: { forecast: AffluenceScore[]; todayDate: string | null }) {
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {forecast.map((day) => {
        const cfg = LEVEL_CONFIG[day.level] ?? LEVEL_CONFIG.medium;
        const isToday = day.score_date === todayDate;
        const isOpen = day.id === openId;

        return (
          <div key={day.id}>
            <button
              onClick={() => setOpenId(isOpen ? null : day.id)}
              style={{
                width: "100%",
                background: isOpen || isToday ? "#1e3a5f" : "#1e293b",
                border: `1px solid ${isOpen || isToday ? "#3b82f6" : "transparent"}`,
                borderBottom: isOpen ? "1px solid #334155" : undefined,
                borderRadius: isOpen ? "10px 10px 0 0" : 10,
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: 16,
                cursor: "pointer",
                color: "inherit",
                font: "inherit",
                textAlign: "left",
              }}
            >
              <div style={{ minWidth: 110, fontSize: 13, color: "#94a3b8" }}>
                {new Date(day.score_date + "T12:00:00").toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" })}
                {isToday && (
                  <span style={{ marginLeft: 6, fontSize: 10, background: "#3b82f6", color: "#fff", borderRadius: 4, padding: "1px 5px" }}>
                    Auj.
                  </span>
                )}
              </div>
              <div style={{ flex: 1 }}>
                <ScoreBar value={day.global_score} color={cfg.color} />
              </div>
              <div style={{ minWidth: 36, textAlign: "right", fontWeight: 700, color: cfg.color }}>
                {day.global_score}
              </div>
              <div style={{ minWidth: 72, textAlign: "right", fontSize: 12, background: cfg.bg, color: cfg.color, borderRadius: 6, padding: "2px 8px" }}>
                {cfg.label}
              </div>
              <div style={{ fontSize: 11, color: "#475569" }}>{isOpen ? "▲" : "▼"}</div>
            </button>

            {isOpen && (
              <div style={{ background: "#1e293b", border: "1px solid #3b82f6", borderTop: "none", borderRadius: "0 0 10px 10px", padding: "16px 20px" }}>
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Détail du score
                </div>
                <ComponentRow label="Disponibilité hébergements" value={day.availability_score} color="#60a5fa" />
                <ComponentRow label="Niveau de prix"             value={day.price_score}        color="#a78bfa" />
                <ComponentRow label="Événements"                 value={day.event_score}        color="#fb923c" />
                <ComponentRow label="Météo"                      value={day.weather_score}      color="#34d399" />
                <div style={{ marginTop: 12, fontSize: 12, color: "#475569" }}>
                  Confiance : <strong style={{ color: "#94a3b8" }}>{Math.round(day.confidence_score * 100)}%</strong>
                </div>
              </div>
            )}
          </div>
        );
      })}
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
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>Indice d&apos;affluence</h1>
        <p style={{ color: "#64748b", marginTop: 4, fontSize: 14 }}>Village touristique · mis à jour toutes les heures</p>
      </div>

      {loading ? (
        <div style={{ background: "#1e293b", borderRadius: 16, padding: 28, marginBottom: 32, color: "#64748b" }}>
          Chargement…
        </div>
      ) : today ? (
        <TodayCard today={today} />
      ) : (
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 24, marginBottom: 32, color: "#f87171" }}>
          Impossible de charger le score du jour. Vérifiez que l&apos;API est démarrée.
        </div>
      )}

      {forecast.length > 0 && (
        <section style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Courbe 7 jours</h2>
          <div style={{ background: "#1e293b", borderRadius: 12, padding: "20px 12px 12px" }}>
            <ForecastChart forecast={forecast} />
          </div>
        </section>
      )}

      <section>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Prévisions 7 jours</h2>
        {loading ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>Chargement…</p>
        ) : forecast.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>Aucune prévision disponible.</p>
        ) : (
          <ForecastList forecast={forecast} todayDate={today?.score_date ?? null} />
        )}
      </section>

      <footer style={{ marginTop: 48, color: "#334155", fontSize: 12 }}>
        Affluence · Saintes-Maries-de-la-Mer
      </footer>
    </main>
  );
}
