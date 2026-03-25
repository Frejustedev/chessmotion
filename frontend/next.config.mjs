/** @type {import('next').NextConfig} */

// When NEXT_PUBLIC_API_URL is set (production), the frontend calls the backend
// directly — no rewrites needed. In local dev (no env var) we use rewrites to
// proxy /api/* to localhost:8000 so CORS is avoided.
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const isStatic = process.env.NEXT_PUBLIC_API_URL !== undefined;

const nextConfig = {
  reactStrictMode: true,
  // Static export for Render Static Site hosting
  ...(isStatic ? { output: "export", trailingSlash: true } : {}),
  // Dev-only proxy rewrites (ignored during static export)
  ...(!isStatic
    ? {
        async rewrites() {
          return [
            { source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` },
            { source: "/output/:path*", destination: `${BACKEND_URL}/output/:path*` },
          ];
        },
      }
    : {}),
};

export default nextConfig;
