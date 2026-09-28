/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      { source: '/api/m1/:path*', destination: 'http://127.0.0.1:8000/:path*' },
      { source: '/api/m2/:path*', destination: 'http://127.0.0.1:8002/:path*' },
      { source: '/api/m3/:path*', destination: 'http://127.0.0.1:8001/:path*' },
    ]
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(self), geolocation=(self), speaker=(self)' },
        ],
      },
      {
        // Allow service worker to cache from root scope
        source: '/sw.js',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=0, must-revalidate' },
          { key: 'Service-Worker-Allowed', value: '/' },
        ],
      },
    ]
  },
}

export default nextConfig
