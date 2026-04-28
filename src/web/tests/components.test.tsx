import { authStorage } from '../lib/auth-storage'

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

    expect(() => authStorage.getUser()).toThrow()
  })
})
