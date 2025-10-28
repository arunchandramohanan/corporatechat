// API Configuration from environment variables
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3009',
  ENDPOINTS: {
    CHAT: import.meta.env.VITE_API_CHAT_ENDPOINT || '/chat',
    DOCUMENTS: '/documents'
  }
};
