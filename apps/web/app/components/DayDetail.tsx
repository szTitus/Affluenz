"use client";

import { useState } from "react";

type AffluenceScore = {
  id: number;
  score_date: string;
  global_score: number;
  level: "low" | "medium" | "high";
  availability_score: number;
  price_score: number;
  event_score: number;
  weather_score: number;
  confidence_score: number;
};

const LEVEL_CONFIG = {
  low: { label: "Faible", color: "#22c55e", bg: "#14532d" },
  medium: { label: "Modérée", color: "#f59e0b", bg: "#451a03" },
  high: { label: "Élevée", color: "#ef4444", bg: "#450a0a" },
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ background: "#0f172a", borderRadius: 6, height: 8, overflow: "hidden" }}>
      <div
        style={{
          width: `${value}%`,
          height: "100%",
          background: color,
          borderRadius: 6,
          transition: "width 0.4s ease",
        }}
      />
    </div>
  );
}

function DetailRow({ label, value, color }: { label: string; value: number; color: string }) {
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

export default function DayDetail({
  forecast,
  todayDate,
}: {
  forecast: AffluenceScore[];
  todayDate: string | null;
}) {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const selected = forecast.find((d) => d.id === selectedId);

  return (
    <div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {forecast.map((day) => {
          const cfg = LEVEL_CONFIG[day.level] ?? LEVEL_CONFIG.medium;
          const isToday = day.score_date === todayDate;
          const isSelected = day.id === selectedId;

          return (
            <div key={day.id}>
              <div
                onClick={() => setSelectedId(isSelected ? null : day.id)}
                style={{
                  background: isSelected ? "#1e3a5f" : isToday ? "#1e3a5f" : "#1e293b",
                  borderRadius: isSelected ? "10px 10px 0 0" : 10,
                  padding: "12px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  border: isSelected
                    ? "1px solid #3b82f6"
                    : isToday
                    ? "1px solid #3b82f6"
                    : "1px solid transparent",
                  borderBottom: isSelected ? "none" : undefined,
                  cursor: "pointer",
                  userSelect: "none" as const,
                  transition: "background 0.2s",
                }}
              >
                <div style={{ minWidth: 110, fontSize: 13, color: "#94a3b8" }}>
                  {new Date(day.score_date + "T12:00:00").toLocaleDateString("fr-FR", {
                    weekday: "short",
                    day: "numeric",
                    month: "short",
                  })}
                  {isToday && (
                    <span
                      style={{
                        marginLeft: 6,
                        fontSize: 10,
                        background: "#3b82f6",
                        color: "#fff",
                        borderRadius: 4,
                        padding: "1px 5px",
                      }}
                    >
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
                <div
                  style={{
                    minWidth: 72,
                    textAlign: "right",
                    fontSize: 12,
                    background: cfg.bg,
                    color: cfg.color,
                    borderRadius: 6,
                    padding: "2px 8px",
                  }}
                >
                  {cfg.label}
                </div>
                <div style={{ fontSize: 12, color: "#475569", marginLeft: 4 }}>
                  {isSelected ? "▲" : "▼"}
                </div>
              </div>

              {/* Détail dépliable */}
              {isSelected && selected && (
                <div
                  style={{
                    background: "#1e293b",
                    borderRadius: "0 0 10px 10px",
                    border: "1px solid #3b82f6",
                    borderTop: "1px solid #334155",
                    padding: "16px 20px",
                  }}
                >
                  <div style={{ fontSize: 12, color: "#64748b", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Détail du score
                  </div>
                  <DetailRow label="Disponibilité hébergements" value={selected.availability_score} color="#60a5fa" />
                  <DetailRow label="Niveau de prix" value={selected.price_score} color="#a78bfa" />
                  <DetailRow label="Événements" value={selected.event_score} color="#fb923c" />
                  <DetailRow label="Météo" value={selected.weather_score} color="#34d399" />
                  <div style={{ marginTop: 12, fontSize: 12, color: "#475569" }}>
                    Confiance : <strong style={{ color: "#94a3b8" }}>{Math.round(selected.confidence_score * 100)}%</strong>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
