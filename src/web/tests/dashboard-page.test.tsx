import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import DashboardPage from '../app/dashboard/page'
import { useAuth } from '@/lib/auth-context'
import { apiClient } from '@selph/shared'

jest.mock('@/lib/auth-context', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/components/protected-route', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

jest.mock('@selph/shared', () => ({
  apiClient: {
    get: jest.fn(),
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

  const primeDashboardFetches = () => {
    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(twinResponse)
      .mockResolvedValueOnce(statsResponse)
      .mockResolvedValueOnce(pendingDraftsResponse)
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
    })

    expect(screen.getByText('Career Coaching')).toBeInTheDocument()
    expect(screen.getByText('Professional')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('Logged in as')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('Approval Loop')).toBeInTheDocument()
    expect(screen.getAllByText('Pending Drafts')).toHaveLength(2)
    expect(screen.getByText('Here is a thoughtful response for your audience.')).toBeInTheDocument()
    expect(screen.getByText('Model Signals')).toBeInTheDocument()
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
})
