/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@auth0/nextjs-auth0'],
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000', '10.100.102.7:3000']
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
  headers: async () => {
    return [
      {
        source: '/api/auth/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,DELETE,PATCH,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ]
  }
}

module.exports = nextConfig 