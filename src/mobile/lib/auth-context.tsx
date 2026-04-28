/**
 * Mobile app authentication context
 * Manages user state, login, signup, logout
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiClient } from '@selph/shared'
import { mobileAuthStorage } from './auth-storage'

interface User {
  id: string
  email: string
  created_at: string
}

interface MobileAuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  signup: (email: string, password: string, name: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  error: string | null
  clearError: () => void
}

const MobileAuthContext = createContext<MobileAuthContextType | undefined>(
  undefined
)

export const MobileAuthProvider = ({
  children,
}: {
  children: React.ReactNode
}) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize user from secure storage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedUser = await mobileAuthStorage.getUser()
        if (storedUser) {
          setUser(storedUser)
          // Set token in API client
          const token = await mobileAuthStorage.getAccessToken()
          if (token) {
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
          }
        }
      } catch (err) {
        console.error('Failed to initialize auth:', err)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const signup = async (email: string, password: string, name: string) => {
    try {
      setError(null)
      setLoading(true)

      const response = await apiClient.post('/auth/signup', {
        email,
        password,
        name,
      })

      const { user: newUser } = response.data
      const tokens = response.data.tokens ?? response.data
      const { access_token, refresh_token } = tokens

      // Store tokens securely
      await mobileAuthStorage.setTokens(access_token, refresh_token, newUser)
      setUser(newUser)

      // Update API client with token
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        'Signup failed. Please try again.'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      setError(null)
      setLoading(true)

      const response = await apiClient.post('/auth/login', {
        email,
        password,
      })

      const { user: loggedUser } = response.data
      const tokens = response.data.tokens ?? response.data
      const { access_token, refresh_token } = tokens

      // Store tokens securely
      await mobileAuthStorage.setTokens(access_token, refresh_token, loggedUser)
      setUser(loggedUser)

      // Update API client with token
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        'Login failed. Please try again.'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      setLoading(true)

      // Call logout endpoint
      try {
        await apiClient.post('/auth/logout')
      } catch (err) {
        console.error('Logout API call failed:', err)
      }

      // Clear secure storage
      await mobileAuthStorage.clearTokens()
      setUser(null)
      delete apiClient.defaults.headers.common['Authorization']
    } catch (err: any) {
      setError('Logout failed. Please try again.')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const clearError = () => setError(null)

  const value: MobileAuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    signup,
    login,
    logout,
    error,
    clearError,
  }

  return (
    <MobileAuthContext.Provider value={value}>
      {children}
    </MobileAuthContext.Provider>
  )
}

/**
 * Hook to use mobile authentication context
 */
export const useMobileAuth = () => {
  const context = useContext(MobileAuthContext)
  if (context === undefined) {
    throw new Error(
      'useMobileAuth must be used within a MobileAuthProvider'
    )
  }
  return context
}
