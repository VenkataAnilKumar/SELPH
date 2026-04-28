import { renderHook, act } from '@testing-library/react-native'
import { Platform } from 'react-native'
import { usePushNotifications } from '../lib/use-push-notifications'
import { apiClient } from '@selph/shared'

jest.mock('@selph/shared', () => ({
  apiClient: {
    registerPushToken: jest.fn(),
  },
}))

jest.mock('expo-notifications', () => ({
  getPermissionsAsync: jest.fn(),
  requestPermissionsAsync: jest.fn(),
  getExpoPushTokenAsync: jest.fn(),
  setNotificationChannelAsync: jest.fn(),
  AndroidImportance: { MAX: 5 },
}))

import * as Notifications from 'expo-notifications'

describe('usePushNotifications', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(Platform as any).OS = 'ios'
  })

  it('registers push token with backend when permission is granted', async () => {
    ;(Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'granted',
    })
    ;(Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({
      data: 'ExponentPushToken[mock-token]',
    })
    ;(apiClient.registerPushToken as jest.Mock).mockResolvedValue({ data: { registered: true } })

    const { rerender } = renderHook(
      ({ isAuthenticated }: { isAuthenticated: boolean }) =>
        usePushNotifications(isAuthenticated),
      { initialProps: { isAuthenticated: true } }
    )

    // Allow async effects to settle
    await act(async () => {
      await Promise.resolve()
    })

    expect(apiClient.registerPushToken).toHaveBeenCalledWith(
      'ExponentPushToken[mock-token]'
    )
  })

  it('requests permission when not already granted', async () => {
    ;(Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'undetermined',
    })
    ;(Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'granted',
    })
    ;(Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({
      data: 'ExponentPushToken[mock-token]',
    })
    ;(apiClient.registerPushToken as jest.Mock).mockResolvedValue({ data: { registered: true } })

    renderHook(() => usePushNotifications(true))

    await act(async () => {
      await Promise.resolve()
    })

    expect(Notifications.requestPermissionsAsync).toHaveBeenCalled()
    expect(apiClient.registerPushToken).toHaveBeenCalledWith(
      'ExponentPushToken[mock-token]'
    )
  })

  it('does not register when permission is denied', async () => {
    ;(Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'denied',
    })
    ;(Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'denied',
    })

    renderHook(() => usePushNotifications(true))

    await act(async () => {
      await Promise.resolve()
    })

    expect(apiClient.registerPushToken).not.toHaveBeenCalled()
  })

  it('does nothing when user is not authenticated', async () => {
    renderHook(() => usePushNotifications(false))

    await act(async () => {
      await Promise.resolve()
    })

    expect(Notifications.getPermissionsAsync).not.toHaveBeenCalled()
    expect(apiClient.registerPushToken).not.toHaveBeenCalled()
  })

  it('silently swallows errors during registration', async () => {
    ;(Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'granted',
    })
    ;(Notifications.getExpoPushTokenAsync as jest.Mock).mockRejectedValue(
      new Error('device not registered')
    )

    // Should not throw
    expect(() => {
      renderHook(() => usePushNotifications(true))
    }).not.toThrow()

    await act(async () => {
      await Promise.resolve()
    })

    expect(apiClient.registerPushToken).not.toHaveBeenCalled()
  })
})
