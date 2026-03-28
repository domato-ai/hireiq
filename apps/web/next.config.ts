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
  output: "export",
};

export default nextConfig;
