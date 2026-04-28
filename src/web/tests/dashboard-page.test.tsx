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
  },
}))

describe('Dashboard page (web)', () => {
  const logoutMock = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useAuth as jest.Mock).mockReturnValue({
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
        created_at: '2026-01-01T00:00:00Z',
      },
    })

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
    expect(screen.getByText('Quick Actions')).toBeInTheDocument()
  })

  it('shows API error when twin fetch fails', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Twin profile unavailable',
        },
      },
    })

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Twin profile unavailable')).toBeInTheDocument()
    })
  })

  it('calls logout when logout button is clicked', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: {
        id: 'twin-1',
        user_id: 'u-1',
        domain: 'Career Coaching',
        tone: 'Professional',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
      },
    })

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText('Logout')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Logout'))
    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1)
    })
  })
})
