import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow access via Cloudflare Tunnel (trycloudflare.com) during dev.
  // Each restart generates a new subdomain, so use a wildcard.
  allowedDevOrigins: ["*.trycloudflare.com", "localhost:3000", "localhost"],
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    ];
  },
};

export default nextConfig;
