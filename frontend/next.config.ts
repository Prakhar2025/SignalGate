import type { NextConfig } from "next";

const BACKEND = process.env.SIGNALGATE_API ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/metrics", destination: `${BACKEND}/api/metrics` },
      { source: "/api/digest", destination: `${BACKEND}/api/digest` },
      { source: "/api/runs", destination: `${BACKEND}/api/runs` },
      { source: "/investigate", destination: `${BACKEND}/investigate` },
      { source: "/healthz", destination: `${BACKEND}/healthz` },
      { source: "/examples/:path*", destination: `${BACKEND}/examples/:path*` },
      { source: "/runs/:path*", destination: `${BACKEND}/runs/:path*` },
    ];
  },
};

export default nextConfig;
