import React from 'react'
import { Alert } from 'react-native'
import { fireEvent, render, waitFor } from '@testing-library/react-native'
import DashboardScreen from '../app/(dashboard)/index'
import { useMobileAuth } from '@/lib/auth-context'
import { apiClient } from '@selph/shared'

jest.mock('@/lib/auth-context', () => ({
  useMobileAuth: jest.fn(),
}))

jest.mock('@selph/shared', () => ({
  apiClient: {
    get: jest.fn(),
  },
}))

describe('Dashboard screen (mobile)', () => {
  const logoutMock = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@example.com' },
      logout: logoutMock,
    })
  })

  it('renders twin profile after successful fetch', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: {
        id: 'twin-1',
        user_id: 'u-1',
        domain: 'Career Coaching',
        tone: 'Professional',
        status: 'active',
      },
    })

    const { getByText, queryByText } = render(<DashboardScreen />)

    expect(getByText('Loading profile...')).toBeTruthy()

    await waitFor(() => {
      expect(getByText('Twin Profile')).toBeTruthy()
    })

    expect(getByText('Career Coaching')).toBeTruthy()
    expect(getByText('Professional')).toBeTruthy()
    expect(getByText('active')).toBeTruthy()
    expect(getByText('Quick Actions')).toBeTruthy()
    expect(queryByText('Loading profile...')).toBeNull()
  })

  it('shows API error when twin fetch fails', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Twin profile unavailable',
        },
      },
    })

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Twin profile unavailable')).toBeTruthy()
    })
  })

  it('opens logout confirmation alert', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: {
        id: 'twin-1',
        user_id: 'u-1',
        domain: 'Career Coaching',
        tone: 'Professional',
        status: 'active',
      },
    })

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Logout')).toBeTruthy()
    })

    fireEvent.press(getByText('Logout'))

    expect(Alert.alert).toHaveBeenCalledWith(
      'Logout',
      'Are you sure you want to log out?',
      expect.any(Array)
    )
  })

  it('runs logout action when confirmation button is pressed', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: {
        id: 'twin-1',
        user_id: 'u-1',
        domain: 'Career Coaching',
        tone: 'Professional',
        status: 'active',
      },
    })

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Logout')).toBeTruthy()
    })

    fireEvent.press(getByText('Logout'))

    const alertCalls = (Alert.alert as jest.Mock).mock.calls
    const firstCall = alertCalls[0]
    const actionButtons = firstCall[2] as Array<{
      text: string
      onPress?: () => Promise<void> | void
    }>
    const logoutAction = actionButtons.find((button) => button.text === 'Logout')

    await logoutAction?.onPress?.()

    expect(logoutMock).toHaveBeenCalledTimes(1)
  })

  it('shows error alert when confirmed logout fails', async () => {
    logoutMock.mockRejectedValueOnce(new Error('network error'))
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: {
        id: 'twin-1',
        user_id: 'u-1',
        domain: 'Career Coaching',
        tone: 'Professional',
        status: 'active',
      },
    })

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Logout')).toBeTruthy()
    })

    fireEvent.press(getByText('Logout'))

    const actionButtons = (Alert.alert as jest.Mock).mock.calls[0][2] as Array<{
      text: string
      onPress?: () => Promise<void> | void
    }>
    const logoutAction = actionButtons.find((button) => button.text === 'Logout')

    await logoutAction?.onPress?.()

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenLastCalledWith('Error', 'Failed to logout')
    })
  })
})
