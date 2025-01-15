/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@auth0/nextjs-auth0'],
  experimental: {
    serverActions: true,
  },
  typescript: {
    // This is temporary until Auth0 fixes their types for Next.js 14
    ignoreBuildErrors: true,
  },
  eslint: {
    // This is temporary until Auth0 fixes their types for Next.js 14
    ignoreDuringBuilds: true,
  },
}

module.exports = nextConfig 