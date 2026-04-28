import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import Home from '../app/page'
import { useAuth } from '@/lib/auth-context'

jest.mock('@/lib/auth-context', () => ({
  useAuth: jest.fn(),
}))

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

describe('Home navigation entry points (web)', () => {
  const logoutMock = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows login and signup links when unauthenticated', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      logout: logoutMock,
    })

    render(<Home />)

    const loginLink = screen.getByText('Log In').closest('a')
    const signupLink = screen.getByText('Sign Up').closest('a')

    expect(loginLink).toHaveAttribute('href', '/auth/login')
    expect(signupLink).toHaveAttribute('href', '/auth/signup')
    expect(screen.queryByText('Go to Dashboard')).not.toBeInTheDocument()
    expect(screen.queryByText('Logout')).not.toBeInTheDocument()
  })

  it('shows dashboard and logout actions when authenticated', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@example.com' },
      logout: logoutMock,
    })

    render(<Home />)

    const dashboardLink = screen.getByText('Go to Dashboard').closest('a')
    expect(dashboardLink).toHaveAttribute('href', '/dashboard')
    expect(screen.getByText('Logout')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('calls logout from authenticated home state', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@example.com' },
      logout: logoutMock,
    })

    render(<Home />)

    fireEvent.click(screen.getByText('Logout'))

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1)
    })
  })
})
