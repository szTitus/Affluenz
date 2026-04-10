// React Server Component – données chargées côté serveur au rendu.
// Pour un rafraîchissement dynamique, convertir en Client Component avec fetch + useEffect.
import ForecastChart from "./components/ForecastChart";
import DayDetail from "./components/DayDetail";

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

// API_URL = URL interne Docker (server-side RSC)
// NEXT_PUBLIC_API_URL = URL publique (browser, liens Swagger, footer)
const API = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const PUBLIC_API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getToday(): Promise<AffluenceScore | null> {
  try {
    const res = await fetch(`${API}/api/v1/affluence/today`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function getForecast(): Promise<AffluenceScore[]> {
  try {
    const res = await fetch(`${API}/api/v1/affluence/forecast`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

const LEVEL_CONFIG = {
  low: { label: "Faible", color: "#22c55e", bg: "#14532d" },
  medium: { label: "Modérée", color: "#f59e0b", bg: "#451a03" },
  high: { label: "Élevée", color: "#ef4444", bg: "#450a0a" },
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: 6,
        height: 8,
        overflow: "hidden",
      }}
    >
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

function ComponentRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 4,
          fontSize: 14,
        }}
      >
        <span style={{ color: "#94a3b8" }}>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{value}</span>
      </div>
      <ScoreBar value={value} color={color} />
    </div>
  );
}

export default async function HomePage() {
  const [today, forecast] = await Promise.all([getToday(), getForecast()]);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "32px 16px" }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>
          Indice d&apos;affluence
        </h1>
        <p style={{ color: "#64748b", marginTop: 4, fontSize: 14 }}>
          Village touristique · mis à jour toutes les 5 min
        </p>
      </div>

      {/* Carte du jour */}
      {today ? (
        <TodayCard today={today} />
      ) : (
        <div
          style={{
            background: "#1e293b",
            borderRadius: 12,
            padding: 24,
            marginBottom: 32,
            color: "#f87171",
          }}
        >
          Impossible de charger le score du jour. Vérifiez que l&apos;API est
          démarrée.
        </div>
      )}

      {/* Graphique prévisions */}
      {forecast.length > 0 && (
        <section style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
            Courbe 7 jours
          </h2>
          <div
            style={{
              background: "#1e293b",
              borderRadius: 12,
              padding: "20px 12px 12px",
            }}
          >
            <ForecastChart forecast={forecast} />
          </div>
        </section>
      )}

      {/* Prévisions 7 jours */}
      <section>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
          Prévisions 7 jours
        </h2>
        {forecast.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: 14 }}>
            Aucune prévision disponible.
          </p>
        ) : (
          <DayDetail forecast={forecast} todayDate={today?.score_date ?? null} />
        )}
      </section>

      <footer style={{ marginTop: 48, color: "#334155", fontSize: 12 }}>
        Affluence · Saintes-Maries-de-la-Mer
      </footer>
    </main>
  );
}

function TodayCard({ today }: { today: AffluenceScore }) {
  const cfg = LEVEL_CONFIG[today.level] ?? LEVEL_CONFIG.medium;
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: 16,
        padding: 28,
        marginBottom: 32,
      }}
    >
      {/* Score principal */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 24,
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 13, color: "#64748b", marginBottom: 4 }}>
            Score aujourd&apos;hui ·{" "}
            {new Date(today.score_date + "T12:00:00").toLocaleDateString(
              "fr-FR",
              { weekday: "long", day: "numeric", month: "long" }
            )}
          </div>
          <div
            style={{
              fontSize: 56,
              fontWeight: 800,
              lineHeight: 1,
              color: cfg.color,
            }}
          >
            {today.global_score}
            <span style={{ fontSize: 20, color: "#475569" }}>/100</span>
          </div>
          <div style={{ fontSize: 13, color: "#64748b", marginTop: 4 }}>
            Zone : {today.zone}
          </div>
        </div>
        <div
          style={{
            background: cfg.bg,
            color: cfg.color,
            borderRadius: 12,
            padding: "12px 20px",
            fontSize: 20,
            fontWeight: 700,
          }}
        >
          {cfg.label}
        </div>
      </div>

      {/* Confiance */}
      <div
        style={{
          fontSize: 12,
          color: "#475569",
          marginBottom: 20,
        }}
      >
        Niveau de confiance :{" "}
        <strong style={{ color: "#94a3b8" }}>
          {Math.round(today.confidence_score * 100)} %
        </strong>
      </div>

      {/* Composants */}
      <div>
        <div
          style={{
            fontSize: 13,
            color: "#64748b",
            marginBottom: 12,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Composants
        </div>
        <ComponentRow
          label="Disponibilité hébergements"
          value={today.availability_score}
          color="#60a5fa"
        />
        <ComponentRow
          label="Niveau de prix"
          value={today.price_score}
          color="#a78bfa"
        />
        <ComponentRow
          label="Événements"
          value={today.event_score}
          color="#fb923c"
        />
        <ComponentRow
          label="Météo"
          value={today.weather_score}
          color="#34d399"
        />
      </div>
    </div>
  );
}
