/**
 * usePushNotifications
 *
 * Requests Expo push-notification permission, obtains the Expo push token,
 * and registers it with the SELPH backend so the server can send draft-ready
 * notifications.
 *
 * Call this hook inside the authenticated root layout (after the user is
 * known to be logged in).  Registration is idempotent — re-sending the same
 * token is a no-op on the server.
 */

import { useEffect } from 'react'
import * as Notifications from 'expo-notifications'
import { Platform } from 'react-native'
import { apiClient } from '@selph/shared'

export function usePushNotifications(isAuthenticated: boolean): void {
  useEffect(() => {
    if (!isAuthenticated) return

    let cancelled = false

    const register = async () => {
      try {
        // Ask for permission
        const { status: existingStatus } =
          await Notifications.getPermissionsAsync()

        let finalStatus = existingStatus
        if (existingStatus !== 'granted') {
          const { status } = await Notifications.requestPermissionsAsync()
          finalStatus = status
        }

        if (finalStatus !== 'granted') {
          return
        }

        // Android requires a notification channel
        if (Platform.OS === 'android') {
          await Notifications.setNotificationChannelAsync('default', {
            name: 'Default',
            importance: Notifications.AndroidImportance.MAX,
          })
        }

        const { data: expoPushToken } = await Notifications.getExpoPushTokenAsync()

        if (!cancelled) {
          await apiClient.registerPushToken(expoPushToken)
        }
      } catch (err) {
        // Never crash the app over a failed push-token registration
        console.warn('[usePushNotifications] registration failed:', err)
      }
    }

    register()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated])
}
