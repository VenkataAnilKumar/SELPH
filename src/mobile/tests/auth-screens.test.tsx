import React from 'react'
import { Alert } from 'react-native'
import { fireEvent, render, waitFor } from '@testing-library/react-native'
import LoginScreen from '../app/(auth)/login'
import SignupScreen from '../app/(auth)/signup'
import { useMobileAuth } from '@/lib/auth-context'

jest.mock('@/lib/auth-context', () => ({
  useMobileAuth: jest.fn(),
}))

describe('Auth screens validation (mobile)', () => {
  const loginMock = jest.fn()
  const signupMock = jest.fn()
  const clearErrorMock = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      login: loginMock,
      signup: signupMock,
      clearError: clearErrorMock,
      error: null,
      loading: false,
    })
  })

  it('shows required field errors on login', () => {
    const { getByText } = render(<LoginScreen />)

    fireEvent.press(getByText('Sign In'))

    expect(getByText('Email is required')).toBeTruthy()
    expect(getByText('Password is required')).toBeTruthy()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('shows invalid email error on login', () => {
    const { getByPlaceholderText, getByText } = render(<LoginScreen />)

    fireEvent.changeText(getByPlaceholderText('you@example.com'), 'invalid-email')
    fireEvent.changeText(getByPlaceholderText('Enter your password'), 'Password1')
    fireEvent.press(getByText('Sign In'))

    expect(getByText('Please enter a valid email')).toBeTruthy()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('submits valid login credentials', () => {
    const { getByPlaceholderText, getByText } = render(<LoginScreen />)

    fireEvent.changeText(getByPlaceholderText('you@example.com'), 'test@example.com')
    fireEvent.changeText(getByPlaceholderText('Enter your password'), 'Password1')
    fireEvent.press(getByText('Sign In'))

    expect(loginMock).toHaveBeenCalledWith('test@example.com', 'Password1')
  })

  it('shows signup validation errors for weak password and mismatch', () => {
    const { getByPlaceholderText, getByText } = render(<SignupScreen />)

    fireEvent.changeText(getByPlaceholderText('Your full name'), 'Test User')
    fireEvent.changeText(getByPlaceholderText('you@example.com'), 'test@example.com')
    fireEvent.changeText(
      getByPlaceholderText('Min 8 chars, uppercase, lowercase, number'),
      'password1'
    )
    fireEvent.changeText(getByPlaceholderText('Re-enter your password'), 'password2')
    fireEvent.press(getByText('Create Account'))

    expect(getByText('Password must contain at least one uppercase letter')).toBeTruthy()
    expect(getByText('Passwords do not match')).toBeTruthy()
    expect(signupMock).not.toHaveBeenCalled()
  })

  it('submits valid signup payload', () => {
    const { getByPlaceholderText, getByText } = render(<SignupScreen />)

    fireEvent.changeText(getByPlaceholderText('Your full name'), 'Test User')
    fireEvent.changeText(getByPlaceholderText('you@example.com'), 'test@example.com')
    fireEvent.changeText(
      getByPlaceholderText('Min 8 chars, uppercase, lowercase, number'),
      'Password1'
    )
    fireEvent.changeText(getByPlaceholderText('Re-enter your password'), 'Password1')
    fireEvent.press(getByText('Create Account'))

    expect(signupMock).toHaveBeenCalledWith('test@example.com', 'Password1', 'Test User')
  })

  it('shows alert when login rejects', async () => {
    loginMock.mockRejectedValueOnce(new Error('invalid'))
    const alertSpy = jest.spyOn(Alert, 'alert')

    const { getByPlaceholderText, getByText } = render(<LoginScreen />)

    fireEvent.changeText(getByPlaceholderText('you@example.com'), 'test@example.com')
    fireEvent.changeText(getByPlaceholderText('Enter your password'), 'Password1')
    fireEvent.press(getByText('Sign In'))

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Login Failed', 'Please try again')
    })
  })
})
