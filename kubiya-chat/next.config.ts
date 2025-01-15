import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.prod.website-files.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'kubiya-public-20221113173935726800000003.s3.us-east-1.amazonaws.com',
        pathname: '/**',
      }
    ],
  },
};

export default nextConfig;
