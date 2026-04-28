import React from 'react'
import { Alert, AppState } from 'react-native'
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
    post: jest.fn(),
    put: jest.fn(),
    approveDraft: jest.fn(),
  },
}))

describe('Dashboard screen (mobile)', () => {
  const logoutMock = jest.fn()

  const twinResponse = {
    data: {
      id: 'twin-1',
      user_id: 'u-1',
      domain: 'Career Coaching',
      tone: 'Professional',
      status: 'active',
    },
  }

  const statsResponse = {
    data: {
      total_messages: 8,
      pending_drafts: 1,
      processed_drafts: 3,
      total_estimated_tokens: 420,
      total_estimated_cost_usd: 0.0024,
      fallback_rate: 0.25,
      approval_rate: 0.75,
      generation_source_breakdown: {
        llm: 3,
        deterministic: 1,
      },
      model_breakdown: {
        'claude-sonnet-4-6': 3,
      },
      fallback_reason_breakdown: {
        llm_disabled: 1,
      },
    },
  }

  const pendingDraftsResponse = {
    data: [
      {
        id: 'draft-1',
        content: 'Here is a thoughtful response for your audience.',
        status: 'pending_approval',
        confidence_score: 0.91,
        confidence_label: 'High',
        confidence_reasoning: 'Strong match with known tone and domain.',
        generation_source: 'llm',
        llm_model: 'claude-sonnet-4-6',
        fallback_reason: null,
        estimated_total_tokens: 160,
        estimated_cost_usd: 0.00096,
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
  }

  const identityResponse = {
    data: {
      vocabulary_description: 'focused, clear, supportive',
      communication_style: 'friendly',
      topics_known: ['productivity'],
      topics_avoided: ['politics'],
      profile_complete: true,
    },
  }

  const channelsResponse = {
    data: [
      { channel: 'instagram', connected: false, scope: null, updated_at: '2026-01-01T00:00:00Z' },
      { channel: 'gmail', connected: false, scope: null, updated_at: '2026-01-01T00:00:00Z' },
    ],
  }

  const primeDashboardFetches = () => {
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(twinResponse)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce(pendingDraftsResponse)
      .mockResolvedValueOnce(identityResponse)
      .mockResolvedValueOnce(channelsResponse)
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@example.com' },
      logout: logoutMock,
    })
  })

  it('renders twin profile after successful fetch', async () => {
    primeDashboardFetches()

    const { getByText, getAllByText, queryByText } = render(<DashboardScreen />)

    expect(getByText('Loading profile...')).toBeTruthy()

    await waitFor(() => {
      expect(getByText('Twin Profile')).toBeTruthy()
    })

    expect(getByText('Career Coaching')).toBeTruthy()
    expect(getByText('Professional')).toBeTruthy()
    expect(getByText('active')).toBeTruthy()
    expect(getByText('Approval Loop')).toBeTruthy()
    expect(getAllByText('Pending Drafts')).toHaveLength(2)
    expect(getByText('Here is a thoughtful response for your audience.')).toBeTruthy()
    expect(getByText('Model Signals')).toBeTruthy()
    expect(queryByText('Loading profile...')).toBeNull()
  })

  it('shows API error when dashboard fetch fails', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Dashboard unavailable',
        },
      },
    })

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Dashboard unavailable')).toBeTruthy()
    })
  })

  it('opens logout confirmation alert', async () => {
    primeDashboardFetches()

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
    primeDashboardFetches()

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
    primeDashboardFetches()

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

  it('approves a draft and refreshes the queue', async () => {
    primeDashboardFetches()
    ;(apiClient.approveDraft as jest.Mock).mockResolvedValueOnce({ data: {} })
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce(channelsResponse)

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Approve')).toBeTruthy()
    })

    fireEvent.press(getByText('Approve'))

    await waitFor(() => {
      expect(apiClient.approveDraft).toHaveBeenCalledWith('draft-1', 'approve', undefined)
    })

    await waitFor(() => {
      expect(getByText('Draft approved successfully.')).toBeTruthy()
    })
  })

  it('refreshes dashboard when app returns to foreground', async () => {
    let appStateHandler: ((state: string) => void) | undefined
    const removeMock = jest.fn()
    jest.spyOn(AppState, 'addEventListener').mockImplementation(
      (_event: string, handler: (state: string) => void) => {
        appStateHandler = handler
        return { remove: removeMock } as any
      }
    )

    primeDashboardFetches()
    // prime data returned by the foreground refresh
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce(channelsResponse)

    const { getByText } = render(<DashboardScreen />)

    await waitFor(() => {
      expect(getByText('Twin Profile')).toBeTruthy()
    })

    // simulate app coming to foreground
    appStateHandler?.('active')

    await waitFor(() => {
      // initial: 5 calls; foreground refresh: 3 calls = 8 total
      expect((apiClient.get as jest.Mock).mock.calls.length).toBe(8)
    })

    jest.restoreAllMocks()
  })
})
