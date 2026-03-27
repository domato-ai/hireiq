import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.microsoftonline.com",
      },
      {
        protocol: "https",
        hostname: "graph.microsoft.com",
      },
    ],
  },
  // Standalone output for containerized deployments
  // output: "standalone",
};

export default nextConfig;
