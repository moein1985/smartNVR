import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactCompiler: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://frigate-intelligence:8000/api/:path*",
      },
      {
        source: "/frigate-api/:path*",
        destination: "http://frigate:5000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
