import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { ProtectedRoute } from '../components/protected-route'
import { useAuth } from '@/lib/auth-context'

const pushMock = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

jest.mock('@/lib/auth-context', () => ({
  useAuth: jest.fn(),
}))

describe('ProtectedRoute (web)', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows loading state while auth is initializing', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      loading: true,
    })

    render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })

  it('redirects unauthenticated users to login', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      loading: false,
    })

    const { container } = render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    )

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/auth/login')
    })

    expect(container).toBeEmptyDOMElement()
  })

  it('renders children for authenticated users', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      loading: false,
    })

    render(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Protected content')).toBeInTheDocument()
    expect(pushMock).not.toHaveBeenCalled()
  })
})
