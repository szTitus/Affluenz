"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type DayScore = {
  score_date: string;
  global_score: number;
  level: string;
};

const LEVEL_COLOR: Record<string, string> = {
  low: "#22c55e",
  medium: "#f59e0b",
  high: "#ef4444",
};

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number; payload: DayScore }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const day = payload[0].payload;
  const color = LEVEL_COLOR[day.level] ?? "#94a3b8";
  return (
    <div
      style={{
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: 8,
        padding: "10px 14px",
        fontSize: 13,
      }}
    >
      <div style={{ color: "#94a3b8", marginBottom: 4 }}>{label}</div>
      <div style={{ color, fontWeight: 700, fontSize: 18 }}>
        {payload[0].value}
        <span style={{ fontSize: 12, color: "#64748b" }}> /100</span>
      </div>
    </div>
  );
}

export default function ForecastChart({ forecast }: { forecast: DayScore[] }) {
  const data = forecast.map((d) => ({
    ...d,
    date: new Date(d.score_date + "T12:00:00").toLocaleDateString("fr-FR", {
      weekday: "short",
      day: "numeric",
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#64748b", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: "#64748b", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="global_score"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#scoreGradient)"
          dot={{ fill: "#3b82f6", r: 4 }}
          activeDot={{ r: 6 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
