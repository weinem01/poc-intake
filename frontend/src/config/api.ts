// API configuration that works for both local and deployed environments
export const getApiUrl = () => {
  // Check if we're running in the browser
  if (typeof window !== 'undefined') {
    // In production, the frontend and backend are on different domains
    if (window.location.hostname.includes('run.app')) {
      // Replace frontend URL with backend URL
      return window.location.origin.replace('poc-intake-frontend', 'poc-intake-backend');
    }
  }
  
  // Use environment variable if set (for build-time configuration)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Default to localhost for local development
  return 'http://localhost:8000';
};

export const API_URL = getApiUrl();