"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";

type DayScore = {
  score_date: string;
  global_score: number;
  level: string;
};

function CustomTooltip({ active, payload }: {
  active?: boolean;
  payload?: { value: number; payload: DayScore }[];
}) {
  if (!active || !payload?.length) return null;
  const val = payload[0].value;
  const level = payload[0].payload.level;
  const color = level === "high" ? "#f87171" : level === "medium" ? "#fbbf24" : "#34d399";
  return (
    <div style={{
      background: "rgba(14,18,28,0.95)",
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: 10,
      padding: "10px 16px",
      backdropFilter: "blur(12px)",
    }}>
      <div style={{ fontSize: 22, fontWeight: 800, color }}>{val}</div>
      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginTop: 2 }}>/100</div>
    </div>
  );
}

export default function ForecastChart({ forecast }: { forecast: DayScore[] }) {
  const data = forecast.map((d) => ({
    ...d,
    date: new Date(d.score_date + "T12:00:00").toLocaleDateString("fr-FR", {
      weekday: "short", day: "numeric",
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={140}>
      <AreaChart data={data} margin={{ top: 8, right: 4, left: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.1)", strokeWidth: 1 }} />
        <Area
          type="monotone"
          dataKey="global_score"
          stroke="#6366f1"
          strokeWidth={2}
          fill="url(#g)"
          dot={false}
          activeDot={{ r: 4, fill: "#6366f1", strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
