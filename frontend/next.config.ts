import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // External packages for server components
  serverExternalPackages: [],
  
  // Experimental features
  experimental: {},
  
  // ESLint configuration for build
  eslint: {
    ignoreDuringBuilds: false,
  },
  
  // Image optimization
  images: {
    domains: [],
    unoptimized: true, // For better performance in Cloud Run
  },
};

export default nextConfig;
