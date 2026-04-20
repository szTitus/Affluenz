import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Affluence – Saintes-Maries-de-la-Mer",
  description: "Indice d'affluence touristique en temps réel",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body style={{
        margin: 0,
        minHeight: "100vh",
        background: "#07090f",
        color: "#e8edf5",
        fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
        WebkitFontSmoothing: "antialiased",
      }}>
        {children}
      </body>
    </html>
  );
}
