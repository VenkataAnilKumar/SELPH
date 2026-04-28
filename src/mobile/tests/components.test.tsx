import * as SecureStore from 'expo-secure-store'
import { mobileAuthStorage } from '../lib/auth-storage'

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
