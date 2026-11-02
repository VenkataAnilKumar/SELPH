import React from 'react'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import DashboardPage from '../app/dashboard/page'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@selph/shared'

jest.mock('@/lib/auth-context', () => ({
  useAuth: jest.fn(),
}))

// The panels fetch on mount and have their own tests; stub them so they do not consume the
// ordered apiClient.get mock responses this suite feeds to the dashboard itself.
jest.mock('@/components/briefings-panel', () => ({
  BriefingsPanel: () => <div data-testid="briefings-panel-stub" />,
}))
jest.mock('@/components/vip-tiers-panel', () => ({
  VipTiersPanel: () => <div data-testid="vip-tiers-panel-stub" />,
}))

jest.mock('@/components/protected-route', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

jest.mock('@selph/shared', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    approveDraft: jest.fn(),
  },
}))

describe('Dashboard page (web)', () => {
  const logoutMock = jest.fn()

  const twinResponse = {
    data: {
      id: 'twin-1',
      user_id: 'u-1',
      domain: 'Career Coaching',
      tone: 'Professional',
      status: 'active',
      created_at: '2026-01-01T00:00:00Z',
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
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@example.com' },
      logout: logoutMock,
    })
  })

  it('renders twin profile after successful fetch', async () => {
    primeDashboardFetches()

    render(<DashboardPage />)

    expect(screen.getByText('Loading twin profile...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Twin Profile')).toBeInTheDocument()
      expect(screen.getByTestId('briefings-panel-stub')).toBeInTheDocument()
      expect(screen.getByTestId('vip-tiers-panel-stub')).toBeInTheDocument()
      expect(screen.getByText('Simulate Incoming Message')).toBeInTheDocument()
    })

    expect(screen.getByText('Career Coaching')).toBeInTheDocument()
    expect(screen.getByText('Professional')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('Logged in as')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('Approval Loop')).toBeInTheDocument()
    expect(screen.getAllByText('Pending Drafts')).toHaveLength(2)
    expect(screen.getByText('Approval Rate')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText('Here is a thoughtful response for your audience.')).toBeInTheDocument()
    expect(screen.getByText('Model Signals')).toBeInTheDocument()
  })

  it('explains why a flagged draft needs attention and marks clean drafts as normal', async () => {
    const flagged = {
      ...pendingDraftsResponse.data[0],
      id: 'draft-flagged',
      confidence_label: 'Low',
      moderation_passed: false,
      moderation_flags: [
        { pattern: 'ignore all previous instructions', risk: 0.9, category: 'prompt_injection' },
        { pattern: 'reveal your system prompt', risk: 0.9, category: 'prompt_injection' },
        { pattern: 'diagnose', risk: 0.9, category: 'sensitive_incoming' },
      ],
    }
    const clean = { ...pendingDraftsResponse.data[0], id: 'draft-clean', moderation_passed: true, moderation_flags: [] }
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(twinResponse)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce({ data: [flagged, clean] })
      .mockResolvedValueOnce(identityResponse)
      .mockResolvedValueOnce(channelsResponse)

    render(<DashboardPage />)

    const banners = await screen.findAllByTestId('draft-flagged')
    expect(banners).toHaveLength(1) // only the flagged draft, not the clean one
    expect(banners[0]).toHaveTextContent(/will not be sent automatically/i)
    expect(banners[0]).toHaveTextContent(/override your twin's instructions/i)
    expect(banners[0]).toHaveTextContent(/Sensitive request/i)
    expect(banners[0].querySelectorAll('li')).toHaveLength(2) // duplicate reasons collapsed
  })

  it('makes no API calls for a signed-out visitor', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({ user: null, logout: logoutMock })
    render(<DashboardPage />)
    await new Promise((resolve) => setTimeout(resolve, 50))
    expect(apiClient.get).not.toHaveBeenCalled()
  })

  it('shows API error when twin fetch fails', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Dashboard unavailable',
        },
      },
    })

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Dashboard unavailable')).toBeInTheDocument()
    })
  })

  it('calls logout when logout button is clicked', async () => {
    primeDashboardFetches()

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Logout')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Logout'))
    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1)
    })
  })

  it('approves a draft and refreshes dashboard data', async () => {
    primeDashboardFetches()
    ;(apiClient.approveDraft as jest.Mock).mockResolvedValueOnce({ data: {} })
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce(channelsResponse)

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Approve')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Approve'))

    await waitFor(() => {
      expect(apiClient.approveDraft).toHaveBeenCalledWith('draft-1', 'approve', undefined)
    })

    await waitFor(() => {
      expect(screen.getByText('Draft approved successfully.')).toBeInTheDocument()
    })
  })

  it('polls dashboard data every 30 seconds', async () => {
    jest.useFakeTimers()
    primeDashboardFetches()
    // prime the data returned by the automatic refresh
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce(channelsResponse)

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Twin Profile')).toBeInTheDocument()
    })

    act(() => {
      jest.advanceTimersByTime(30_000)
    })

    await waitFor(() => {
      // initial fetch: 5 calls (twin/stats/drafts/identity/channels); poll refresh: 3 calls
      expect((apiClient.get as jest.Mock).mock.calls.length).toBe(8)
    })

    jest.useRealTimers()
  })
})
