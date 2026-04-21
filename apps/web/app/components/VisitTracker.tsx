"use client";

import { useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Ping silencieux de /api/v1/track au premier rendu client.
 * - 1 seule fois par session (sessionStorage) pour éviter de polluer les stats si l'utilisateur navigue
 * - silencieux : aucune erreur remontée, aucun blocage du rendu
 */
export default function VisitTracker() {
  useEffect(() => {
    try {
      const KEY = "aff_tracked";
      if (typeof window === "undefined") return;
      if (sessionStorage.getItem(KEY)) return;
      sessionStorage.setItem(KEY, "1");

      fetch(`${API}/api/v1/track`, {
        method: "POST",
        keepalive: true,
      }).catch(() => {
        /* noop */
      });
    } catch {
      /* noop – le tracking ne doit jamais casser le rendu */
    }
  }, []);

  return null;
}
