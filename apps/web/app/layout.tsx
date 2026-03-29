import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Affluence – Village touristique",
  description: "Indice d'affluence en temps réel",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          background: "#0f172a",
          color: "#e2e8f0",
          fontFamily: "'Segoe UI', system-ui, sans-serif",
        }}
      >
        {children}
      </body>
    </html>
  );
}
