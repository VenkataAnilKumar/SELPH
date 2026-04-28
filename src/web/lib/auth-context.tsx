"use client";

/**
 * Authentication context and provider
 * Manages user state, login, signup, logout
 */

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@selph/shared";
import { authStorage } from "./auth-storage";

interface User {
  id: string;
  email: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  signup: (email: string, password: string, name: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize user from storage
  useEffect(() => {
    const storedUser = authStorage.getUser();
    if (storedUser) {
      setUser(storedUser);
    }
    setLoading(false);
  }, []);

  const signup = async (email: string, password: string, name: string) => {
    try {
      setError(null);
      setLoading(true);

      const response = await apiClient.post("/auth/signup", {
        email,
        password,
        name,
      });

      const { user: newUser, tokens } = response.data;
      const { access_token, refresh_token } = tokens;

      // Store tokens and user
      authStorage.setTokens(access_token, refresh_token, newUser);
      setUser(newUser);

      // Update API client with token
      apiClient.defaults.headers.common[
        "Authorization"
      ] = `Bearer ${access_token}`;

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Signup failed. Please try again.";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setError(null);
      setLoading(true);

      const response = await apiClient.post("/auth/login", {
        email,
        password,
      });

      const { user: loggedUser, tokens } = response.data;
      const { access_token, refresh_token } = tokens;

      // Store tokens and user
      authStorage.setTokens(access_token, refresh_token, loggedUser);
      setUser(loggedUser);

      // Update API client with token
      apiClient.defaults.headers.common[
        "Authorization"
      ] = `Bearer ${access_token}`;

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Login failed. Please try again.";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);

      // Call logout endpoint to invalidate token
      try {
        await apiClient.post("/auth/logout");
      } catch (err) {
        // Even if endpoint fails, clear local data
        console.error("Logout API call failed:", err);
      }

      // Clear local auth data
      authStorage.clearTokens();
      setUser(null);
      delete apiClient.defaults.headers.common["Authorization"];

      // Redirect to home
      router.push("/");
    } catch (err: any) {
      setError("Logout failed. Please try again.");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    signup,
    login,
    logout,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};

/**
 * Hook to use authentication context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
