/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@auth0/nextjs-auth0'],
  experimental: {
    esmExternals: 'loose',
    serverActions: {
      bodySizeLimit: '2mb'
    }
  }
}

module.exports = nextConfig 