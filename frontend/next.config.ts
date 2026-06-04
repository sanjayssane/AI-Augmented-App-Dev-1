import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  // Uncomment for local API proxy during Phase 5 integration:
  // async rewrites() {
  //   return [
  //     {
  //       source: "/api/v1/:path*",
  //       destination: `${process.env.API_PROXY_URL ?? "http://localhost:8000"}/api/v1/:path*`,
  //     },
  //   ];
  // },
};

export default nextConfig;
