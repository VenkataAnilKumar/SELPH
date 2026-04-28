import React from 'react'
import { render, waitFor } from '@testing-library/react-native'
import RootLayout from '../app/_layout'
import { useMobileAuth } from '@/lib/auth-context'

const mockReplace = jest.fn()
let mockSegments: string[] = []

jest.mock('expo-router', () => ({
  Slot: () => null,
  useRouter: () => ({
    replace: mockReplace,
  }),
  useSegments: () => mockSegments,
}))

jest.mock('@/lib/auth-context', () => ({
  useMobileAuth: jest.fn(),
  MobileAuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('Root layout navigation (mobile)', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockSegments = []
  })

  it('redirects unauthenticated users outside auth group to login', async () => {
    mockSegments = ['(dashboard)']
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      loading: false,
    })

    render(<RootLayout />)

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/(auth)/login')
    })
  })

  it('redirects authenticated users from auth group to dashboard', async () => {
    mockSegments = ['(auth)']
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      loading: false,
    })

    render(<RootLayout />)

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/(dashboard)/')
    })
  })

  it('does not redirect while loading', async () => {
    mockSegments = ['(dashboard)']
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      loading: true,
    })

    render(<RootLayout />)

    await waitFor(() => {
      expect(mockReplace).not.toHaveBeenCalled()
    })
  })

  it('does not redirect unauthenticated users already in auth group', async () => {
    mockSegments = ['(auth)']
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      loading: false,
    })

    render(<RootLayout />)

    await waitFor(() => {
      expect(mockReplace).not.toHaveBeenCalled()
    })
  })

  it('does not redirect authenticated users already outside auth group', async () => {
    mockSegments = ['(dashboard)']
    ;(useMobileAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      loading: false,
    })

    render(<RootLayout />)

    await waitFor(() => {
      expect(mockReplace).not.toHaveBeenCalled()
    })
  })
})
