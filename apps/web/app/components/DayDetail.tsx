"use client";

import { useState } from "react";

type Score = {
  id: number;
  score_date: string;
  global_score: number;
  level: string;
  availability_score: number;
  price_score: number;
  event_score: number;
  weather_score: number;
  confidence_score: number;
};

const COLORS: Record<string, { label: string; color: string; bg: string }> = {
  low:    { label: "Faible",   color: "#22c55e", bg: "#14532d" },
  medium: { label: "Modérée",  color: "#f59e0b", bg: "#451a03" },
  high:   { label: "Élevée",   color: "#ef4444", bg: "#450a0a" },
};

function Bar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ background: "#0f172a", borderRadius: 6, height: 8, overflow: "hidden" }}>
      <div style={{ width: `${value}%`, height: "100%", background: color, borderRadius: 6 }} />
    </div>
  );
}

function Row({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 13 }}>
        <span style={{ color: "#94a3b8" }}>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{value}</span>
      </div>
      <Bar value={value} color={color} />
    </div>
  );
}

export default function DayDetail({
  forecast,
  todayDate,
}: {
  forecast: Score[];
  todayDate: string | null;
}) {
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {forecast.map((day) => {
        const cfg = COLORS[day.level] ?? COLORS.medium;
        const isToday = day.score_date === todayDate;
        const isOpen = day.id === openId;

        return (
          <div key={day.id}>
            {/* Ligne cliquable */}
            <button
              onClick={() => setOpenId(isOpen ? null : day.id)}
              style={{
                width: "100%",
                background: isOpen || isToday ? "#1e3a5f" : "#1e293b",
                border: isOpen || isToday ? "1px solid #3b82f6" : "1px solid transparent",
                borderBottom: isOpen ? "1px solid #334155" : undefined,
                borderRadius: isOpen ? "10px 10px 0 0" : 10,
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: 16,
                cursor: "pointer",
                textAlign: "left",
                appearance: "none",
                WebkitAppearance: "none",
                color: "inherit",
                font: "inherit",
                outline: "none",
              }}
            >
              <div style={{ minWidth: 110, fontSize: 13, color: "#94a3b8" }}>
                {new Date(day.score_date + "T12:00:00").toLocaleDateString("fr-FR", {
                  weekday: "short", day: "numeric", month: "short",
                })}
                {isToday && (
                  <span style={{
                    marginLeft: 6, fontSize: 10, background: "#3b82f6",
                    color: "#fff", borderRadius: 4, padding: "1px 5px",
                  }}>
                    Auj.
                  </span>
                )}
              </div>
              <div style={{ flex: 1 }}>
                <Bar value={day.global_score} color={cfg.color} />
              </div>
              <div style={{ minWidth: 36, textAlign: "right", fontWeight: 700, color: cfg.color }}>
                {day.global_score}
              </div>
              <div style={{
                minWidth: 72, textAlign: "right", fontSize: 12,
                background: cfg.bg, color: cfg.color, borderRadius: 6, padding: "2px 8px",
              }}>
                {cfg.label}
              </div>
              <div style={{ fontSize: 11, color: "#475569" }}>{isOpen ? "▲" : "▼"}</div>
            </button>

            {/* Détail dépliable */}
            {isOpen && (
              <div style={{
                background: "#1e293b",
                border: "1px solid #3b82f6",
                borderTop: "none",
                borderRadius: "0 0 10px 10px",
                padding: "16px 20px",
              }}>
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Détail du score
                </div>
                <Row label="Disponibilité hébergements" value={day.availability_score} color="#60a5fa" />
                <Row label="Niveau de prix"             value={day.price_score}        color="#a78bfa" />
                <Row label="Événements"                 value={day.event_score}        color="#fb923c" />
                <Row label="Météo"                      value={day.weather_score}      color="#34d399" />
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
