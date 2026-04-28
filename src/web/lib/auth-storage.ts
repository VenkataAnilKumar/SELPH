/**
 * Authentication utilities for web app
 * Token storage, retrieval, and validation
 */

const TOKEN_KEY = "selph_access_token";
const REFRESH_TOKEN_KEY = "selph_refresh_token";
const USER_KEY = "selph_user";

export const authStorage = {
  /**
   * Store tokens and user data
   */
  setTokens: (accessToken: string, refreshToken: string, user: any) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(TOKEN_KEY, accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
  },

  /**
   * Get access token
   */
  getAccessToken: (): string | null => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  },

  /**
   * Get refresh token
   */
  getRefreshToken: (): string | null => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(REFRESH_TOKEN_KEY);
    }
    return null;
  },

  /**
   * Get stored user data
   */
  getUser: () => {
    if (typeof window !== "undefined") {
      const user = localStorage.getItem(USER_KEY);
      return user ? JSON.parse(user) : null;
    }
    return null;
  },

  /**
   * Clear all auth data
   */
  clearTokens: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    if (typeof window !== "undefined") {
      return !!localStorage.getItem(TOKEN_KEY);
    }
    return false;
  },
};
