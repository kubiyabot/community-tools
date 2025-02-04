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
    if (isServer) {
      config.externals.push({
        'child_process': 'commonjs child_process',
        'fs': 'commonjs fs',
        'path': 'commonjs path',
        'os': 'commonjs os'
      });
    }
    return config;
  }
}

module.exports = nextConfig 