/**
 * Mobile app authentication storage using SecureStore
 * Stores sensitive tokens securely on device
 */

import * as SecureStore from 'expo-secure-store'

const TOKEN_KEY = 'selph_access_token'
const REFRESH_TOKEN_KEY = 'selph_refresh_token'
const USER_KEY = 'selph_user'

export const mobileAuthStorage = {
  /**
   * Store tokens and user data securely
   */
  setTokens: async (accessToken: string, refreshToken: string, user: any) => {
    try {
      await SecureStore.setItemAsync(TOKEN_KEY, accessToken)
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken)
      await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user))
    } catch (err) {
      console.error('Failed to store tokens:', err)
    }
  },

  /**
   * Get access token
   */
  getAccessToken: async (): Promise<string | null> => {
    try {
      return await SecureStore.getItemAsync(TOKEN_KEY)
    } catch (err) {
      console.error('Failed to get access token:', err)
      return null
    }
  },

  /**
   * Get refresh token
   */
  getRefreshToken: async (): Promise<string | null> => {
    try {
      return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY)
    } catch (err) {
      console.error('Failed to get refresh token:', err)
      return null
    }
  },

  /**
   * Get stored user data
   */
  getUser: async () => {
    try {
      const user = await SecureStore.getItemAsync(USER_KEY)
      return user ? JSON.parse(user) : null
    } catch (err) {
      console.error('Failed to get user:', err)
      return null
    }
  },

  /**
   * Clear all auth data
   */
  clearTokens: async () => {
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY)
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY)
      await SecureStore.deleteItemAsync(USER_KEY)
    } catch (err) {
      console.error('Failed to clear tokens:', err)
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: async (): Promise<boolean> => {
    try {
      const token = await SecureStore.getItemAsync(TOKEN_KEY)
      return !!token
    } catch (err) {
      console.error('Failed to check authentication:', err)
      return false
    }
  },
}
