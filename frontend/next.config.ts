import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Optimize for production
  swcMinify: true,
  
  // Experimental features
  experimental: {
    // Enable server components optimization
    serverComponentsExternalPackages: [],
  },
  
  // Image optimization
  images: {
    domains: [],
    unoptimized: true, // For better performance in Cloud Run
  },
};

export default nextConfig;
