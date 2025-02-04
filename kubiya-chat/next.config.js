/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@auth0/nextjs-auth0'],
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000', 'chat.kubiya.ai']
    }
  },
  typescript: {
    // This is temporary until Auth0 fixes their types for Next.js 14
    ignoreBuildErrors: true,
  },
  eslint: {
    // This is temporary until Auth0 fixes their types for Next.js 14
    ignoreDuringBuilds: true,
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Don't attempt to import node modules on the client side
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        child_process: false,
        os: false,
      };
    }
    return config;
  }
}

module.exports = nextConfig 