import * as SecureStore from 'expo-secure-store'
import React from 'react'
import { fireEvent, render, waitFor } from '@testing-library/react-native'
import { mobileAuthStorage } from '../lib/auth-storage'
import { MobileAuthProvider, useMobileAuth } from '../lib/auth-context'
import { Text, Pressable, View } from 'react-native'
import { apiClient } from '@selph/shared'

const mockPost = jest.fn()

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

const MobileAuthHarness = () => {
  const auth = useMobileAuth()

  return (
    <View>
      <Text testID='loading'>{String(auth.loading)}</Text>
      <Text testID='is-auth'>{String(auth.isAuthenticated)}</Text>
      <Text testID='error'>{auth.error ?? ''}</Text>
      <Pressable onPress={() => auth.login('test@example.com', 'password').catch(() => undefined)}>
        <Text>login</Text>
      </Pressable>
      <Pressable onPress={() => auth.logout().catch(() => undefined)}>
        <Text>logout</Text>
      </Pressable>
      <Pressable onPress={auth.clearError}>
        <Text>clear-error</Text>
      </Pressable>
    </View>
  )
}

describe('mobileAuthStorage', () => {
  const user = { id: 'u1', email: 'test@example.com' }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('stores tokens and user in SecureStore', async () => {
    await mobileAuthStorage.setTokens('access-1', 'refresh-1', user)

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('selph_access_token', 'access-1')
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('selph_refresh_token', 'refresh-1')
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('selph_user', JSON.stringify(user))
  })

  it('reads access and refresh tokens', async () => {
    ;(SecureStore.getItemAsync as jest.Mock)
      .mockResolvedValueOnce('access-1')
      .mockResolvedValueOnce('refresh-1')

    await expect(mobileAuthStorage.getAccessToken()).resolves.toBe('access-1')
    await expect(mobileAuthStorage.getRefreshToken()).resolves.toBe('refresh-1')
  })

  it('reads and parses user payload', async () => {
    ;(SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce(JSON.stringify(user))

    await expect(mobileAuthStorage.getUser()).resolves.toEqual(user)
  })

  it('returns false when token is missing', async () => {
    ;(SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce(null)

    await expect(mobileAuthStorage.isAuthenticated()).resolves.toBe(false)
  })

  it('clears tokens and user from SecureStore', async () => {
    await mobileAuthStorage.clearTokens()

    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('selph_access_token')
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('selph_refresh_token')
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('selph_user')
  })
})

describe('MobileAuthProvider', () => {
  const user = {
    id: 'u1',
    email: 'test@example.com',
    created_at: '2026-01-01T00:00:00Z',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    delete (apiClient.defaults.headers.common as Record<string, string>).Authorization
  })

  it('hydrates authenticated state from secure storage', async () => {
    jest.spyOn(mobileAuthStorage, 'getUser').mockResolvedValue(user)
    jest.spyOn(mobileAuthStorage, 'getAccessToken').mockResolvedValue('access-1')

    const { getByTestId } = render(
      <MobileAuthProvider>
        <MobileAuthHarness />
      </MobileAuthProvider>
    )

    await waitFor(() => {
      expect(getByTestId('loading').props.children).toBe('false')
    })
    expect(getByTestId('is-auth').props.children).toBe('true')
    expect((apiClient.defaults.headers.common as Record<string, string>).Authorization).toBe(
      'Bearer access-1'
    )
  })

  it('logs in using nested token response shape', async () => {
    jest.spyOn(mobileAuthStorage, 'getUser').mockResolvedValue(null)
    const setTokensSpy = jest.spyOn(mobileAuthStorage, 'setTokens').mockResolvedValue()
    mockPost.mockResolvedValueOnce({
      data: {
        user,
        tokens: {
          access_token: 'access-1',
          refresh_token: 'refresh-1',
        },
      },
    })

    const { getByText } = render(
      <MobileAuthProvider>
        <MobileAuthHarness />
      </MobileAuthProvider>
    )

    fireEvent.press(getByText('login'))

    await waitFor(() => {
      expect(setTokensSpy).toHaveBeenCalledWith('access-1', 'refresh-1', user)
    })
    expect((apiClient.defaults.headers.common as Record<string, string>).Authorization).toBe(
      'Bearer access-1'
    )
  })

  it('sets and clears login error', async () => {
    jest.spyOn(mobileAuthStorage, 'getUser').mockResolvedValue(null)
    mockPost.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Invalid credentials',
        },
      },
    })

    const { getByText, getByTestId } = render(
      <MobileAuthProvider>
        <MobileAuthHarness />
      </MobileAuthProvider>
    )

    fireEvent.press(getByText('login'))

    await waitFor(() => {
      expect(getByTestId('error').props.children).toBe('Invalid credentials')
    })

    fireEvent.press(getByText('clear-error'))
    expect(getByTestId('error').props.children).toBe('')
  })

  it('logs out and clears local auth data even if logout endpoint fails', async () => {
    jest.spyOn(mobileAuthStorage, 'getUser').mockResolvedValue(user)
    const clearTokensSpy = jest.spyOn(mobileAuthStorage, 'clearTokens').mockResolvedValue()
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => undefined)
    mockPost.mockRejectedValueOnce(new Error('network down'))

    const { getByText, getByTestId } = render(
      <MobileAuthProvider>
        <MobileAuthHarness />
      </MobileAuthProvider>
    )

    await waitFor(() => {
      expect(getByTestId('is-auth').props.children).toBe('true')
    })

    fireEvent.press(getByText('logout'))

    await waitFor(() => {
      expect(clearTokensSpy).toHaveBeenCalledTimes(1)
    })
    expect(getByTestId('is-auth').props.children).toBe('false')
    consoleErrorSpy.mockRestore()
  })
})
