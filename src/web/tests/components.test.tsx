import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { authStorage } from '../lib/auth-storage'
import { AuthProvider, useAuth } from '../lib/auth-context'
import { apiClient } from '@selph/shared'

const mockPush = jest.fn()
const mockPost = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

jest.mock(
  '@selph/shared',
  () => ({
    apiClient: {
      post: (...args: unknown[]) => mockPost(...args),
      defaults: {
        headers: {
          common: {},
        },
      },
    },
  }),
  { virtual: true }
)

const AuthHarness = () => {
  const auth = useAuth()

  return (
    <div>
      <span data-testid='loading'>{String(auth.loading)}</span>
      <span data-testid='is-auth'>{String(auth.isAuthenticated)}</span>
      <span data-testid='error'>{auth.error ?? ''}</span>
      <button onClick={() => auth.login('test@example.com', 'password').catch(() => undefined)}>
        login
      </button>
      <button onClick={() => auth.logout().catch(() => undefined)}>
        logout
      </button>
      <button onClick={auth.clearError}>clear-error</button>
    </div>
  )
}

describe('authStorage (web)', () => {
  const user = { id: 'u1', email: 'test@example.com' }

  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  it('stores and retrieves tokens and user', () => {
    authStorage.setTokens('access-1', 'refresh-1', user)

    expect(authStorage.getAccessToken()).toBe('access-1')
    expect(authStorage.getRefreshToken()).toBe('refresh-1')
    expect(authStorage.getUser()).toEqual(user)
    expect(authStorage.isAuthenticated()).toBe(true)
  })

  it('clears tokens and user', () => {
    authStorage.setTokens('access-1', 'refresh-1', user)
    authStorage.clearTokens()

    expect(authStorage.getAccessToken()).toBeNull()
    expect(authStorage.getRefreshToken()).toBeNull()
    expect(authStorage.getUser()).toBeNull()
    expect(authStorage.isAuthenticated()).toBe(false)
  })

  it('returns null for malformed stored user payload', () => {
    localStorage.setItem('selph_user', '{bad json')

    expect(authStorage.getUser()).toBeNull()
  })
})

describe('AuthProvider (web)', () => {
  const user = {
    id: 'u1',
    email: 'test@example.com',
    created_at: '2026-01-01T00:00:00Z',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
    delete (apiClient.defaults.headers.common as Record<string, string>).Authorization
  })

  it('hydrates authenticated state from storage', async () => {
    jest.spyOn(authStorage, 'getUser').mockReturnValue(user)

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    expect(screen.getByTestId('is-auth')).toHaveTextContent('true')
  })

  it('logs in and navigates to dashboard', async () => {
    jest.spyOn(authStorage, 'getUser').mockReturnValue(null)
    const setTokensSpy = jest.spyOn(authStorage, 'setTokens')
    mockPost.mockResolvedValueOnce({
      data: {
        user,
        tokens: {
          access_token: 'access-1',
          refresh_token: 'refresh-1',
        },
      },
    })

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    fireEvent.click(screen.getByText('login'))

    await waitFor(() => {
      expect(setTokensSpy).toHaveBeenCalledWith('access-1', 'refresh-1', user)
    })
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
    expect((apiClient.defaults.headers.common as Record<string, string>).Authorization).toBe(
      'Bearer access-1'
    )
  })

  it('sets and clears login error state', async () => {
    jest.spyOn(authStorage, 'getUser').mockReturnValue(null)
    mockPost.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Invalid credentials',
        },
      },
    })

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    fireEvent.click(screen.getByText('login'))

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials')
    })

    fireEvent.click(screen.getByText('clear-error'))
    expect(screen.getByTestId('error')).toHaveTextContent('')
  })

  it('logs out and clears local auth state even if API logout fails', async () => {
    jest.spyOn(authStorage, 'getUser').mockReturnValue(user)
    const clearTokensSpy = jest.spyOn(authStorage, 'clearTokens')
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => undefined)
    mockPost.mockRejectedValueOnce(new Error('network down'))

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('is-auth')).toHaveTextContent('true')
    })

    fireEvent.click(screen.getByText('logout'))

    await waitFor(() => {
      expect(clearTokensSpy).toHaveBeenCalledTimes(1)
    })
    expect(mockPush).toHaveBeenCalledWith('/')
    expect(screen.getByTestId('is-auth')).toHaveTextContent('false')
    consoleErrorSpy.mockRestore()
  })
})
