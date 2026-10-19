import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "AI Krish",
    short_name: "AI Krish",
    description: "AI Krish personal assistant",
    start_url: "/",
    display: "standalone",
    background_color: "#f8fafc",
    theme_color: "#2563eb",
    icons: [
      { src: "/pwa-192", sizes: "192x192", type: "image/png" },
      { src: "/pwa-512", sizes: "512x512", type: "image/png" },
    ],
  };
}
