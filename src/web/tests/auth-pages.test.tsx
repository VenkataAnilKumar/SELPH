import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import LoginPage from '../app/auth/login/page'
import SignupPage from '../app/auth/signup/page'
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

describe('Auth pages validation (web)', () => {
  const loginMock = jest.fn()
  const signupMock = jest.fn()
  const clearErrorMock = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useAuth as jest.Mock).mockReturnValue({
      login: loginMock,
      signup: signupMock,
      clearError: clearErrorMock,
      error: null,
    })
  })

  it('shows required field errors on login submit', () => {
    render(<LoginPage />)

    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(screen.getByText('Email is required')).toBeInTheDocument()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('shows invalid email error on login', () => {
    render(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'invalid-email' },
    })
    fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
      target: { value: 'Password1' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(screen.getByText('Please enter a valid email')).toBeInTheDocument()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('submits valid login credentials', () => {
    render(<LoginPage />)

    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
      target: { value: 'Password1' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(loginMock).toHaveBeenCalledWith('test@example.com', 'Password1')
  })

  it('shows signup validation errors for weak password and mismatch', () => {
    render(<SignupPage />)

    fireEvent.change(screen.getByPlaceholderText('Your full name'), {
      target: { value: 'Test User' },
    })
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(
      screen.getByPlaceholderText('Min 8 chars, uppercase, lowercase, number'),
      {
      target: { value: 'password1' },
      }
    )
    fireEvent.change(screen.getByPlaceholderText('Re-enter your password'), {
      target: { value: 'password2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create Account' }))

    expect(
      screen.getByText('Password must contain at least one uppercase letter')
    ).toBeInTheDocument()
    expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    expect(signupMock).not.toHaveBeenCalled()
  })

  it('submits valid signup payload and trims name', () => {
    render(<SignupPage />)

    fireEvent.change(screen.getByPlaceholderText('Your full name'), {
      target: { value: '  Test User  ' },
    })
    fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(
      screen.getByPlaceholderText('Min 8 chars, uppercase, lowercase, number'),
      {
      target: { value: 'Password1' },
      }
    )
    fireEvent.change(screen.getByPlaceholderText('Re-enter your password'), {
      target: { value: 'Password1' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create Account' }))

    expect(signupMock).toHaveBeenCalledWith('test@example.com', 'Password1', 'Test User')
  })
})
