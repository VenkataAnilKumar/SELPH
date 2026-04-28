/**
 * Mobile app root layout with authentication provider
 */

import React, { useEffect, useState } from 'react'
import { Slot, useRouter, useSegments } from 'expo-router'
import { MobileAuthProvider, useMobileAuth } from '@/lib/auth-context'

/**
 * Layout wrapper that handles navigation based on auth state
 */
function RootLayoutNav() {
  const router = useRouter()
  const segments = useSegments()
  const { isAuthenticated, loading } = useMobileAuth()
  const [isNavigationReady, setIsNavigationReady] = useState(false)

  useEffect(() => {
    if (!isNavigationReady) return

    // Redirect based on auth state
    const inAuthGroup = segments[0] === '(auth)'

    if (loading) {
      return
    }

    if (!isAuthenticated && !inAuthGroup) {
      // Not authenticated and not in auth group → redirect to login
      router.replace('/(auth)/login')
    } else if (isAuthenticated && inAuthGroup) {
      // Authenticated and in auth group → redirect to dashboard
      router.replace('/(dashboard)/')
    }
  }, [isAuthenticated, loading, segments, isNavigationReady])

  // Set navigation ready after first render
  useEffect(() => {
    setIsNavigationReady(true)
  }, [])

  return <Slot />
}

/**
 * Root layout component
 */
export default function RootLayout() {
  return (
    <MobileAuthProvider>
      <RootLayoutNav />
    </MobileAuthProvider>
  )
}
