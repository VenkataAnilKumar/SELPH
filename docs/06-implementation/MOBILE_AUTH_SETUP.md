# Mobile Authentication Setup

## Overview

The mobile app authentication system is built with React Native, Expo Router, and secure token storage. All authentication tokens are stored securely using `expo-secure-store` instead of localStorage (which is insecure on mobile).

## Architecture

### Components

1. **auth-storage.ts** - Secure token storage
   - Uses Expo's `SecureStore` for encrypted token persistence
   - Async methods: `setTokens`, `getAccessToken`, `getRefreshToken`, `getUser`, `clearTokens`, `isAuthenticated`
   - All storage operations are async-safe

2. **auth-context.tsx** - React Context for auth state
   - Provides `useMobileAuth` hook for components
   - Methods: `signup`, `login`, `logout`
   - State: `user`, `loading`, `isAuthenticated`, `error`
   - Automatically initializes user from secure storage on app startup

3. **app/_layout.tsx** - Root layout with navigation control
   - Wraps app with `MobileAuthProvider`
   - `RootLayoutNav` component handles auth-based routing
   - Redirects unauthenticated users to `/(auth)/login`
   - Redirects authenticated users to `/(dashboard)/`

4. **app/(auth)/_layout.tsx** - Auth group layout
   - Manages login and signup screens
   - Hidden header navigation

5. **app/(dashboard)/_layout.tsx** - Dashboard group layout
   - Main app content after authentication

### Screens

1. **Login Screen** (`app/(auth)/login.tsx`)
   - Email and password inputs
   - Form validation with error display
   - Uses `useMobileAuth` context

2. **Signup Screen** (`app/(auth)/signup.tsx`)
   - Email, password, confirm password inputs
   - Password strength requirements display
   - Client-side validation

3. **Dashboard Screen** (`app/(dashboard)/index.tsx`)
   - Shows logged-in user's email
   - Displays twin profile
   - Quick action buttons
   - Getting started guide
   - Logout button with confirmation

## Authentication Flow

### Signup Flow
```
User enters email/password
    ↓
Client validates input
    ↓
POST /auth/signup to backend
    ↓
Backend creates user + auto-creates twin
    ↓
Backend returns access_token + refresh_token + user
    ↓
Client stores tokens in SecureStore
    ↓
Client sets Authorization header
    ↓
Redirect to dashboard
```

### Login Flow
```
User enters email/password
    ↓
Client validates input
    ↓
POST /auth/login to backend
    ↓
Backend validates credentials (bcrypt)
    ↓
Backend returns access_token + refresh_token + user
    ↓
Client stores tokens in SecureStore
    ↓
Client sets Authorization header
    ↓
Redirect to dashboard
```

### App Startup Flow
```
App starts
    ↓
RootLayout renders with MobileAuthProvider
    ↓
MobileAuthProvider calls initAuth() on mount
    ↓
initAuth() reads tokens from SecureStore
    ↓
If tokens exist: setUser, set auth header, allow navigation
    ↓
If no tokens: redirect to login
```

### Logout Flow
```
User clicks logout
    ↓
Confirmation alert
    ↓
POST /auth/logout to backend
    ↓
Client clears SecureStore tokens
    ↓
Client removes Authorization header
    ↓
Redirect to login
```

## Token Management

### Access Token
- **Duration**: 24 hours
- **Storage**: Encrypted SecureStore
- **Usage**: Sent in `Authorization: Bearer <token>` header
- **Validation**: Backend verifies signature and expiration

### Refresh Token
- **Duration**: 7 days
- **Storage**: Encrypted SecureStore
- **Usage**: Sent to `/auth/refresh` endpoint to get new access token
- **Future**: Implement automatic refresh on 401 response

## Security Features

1. **Secure Storage**: Tokens encrypted by OS (iOS Keychain, Android Keystore)
2. **No localStorage**: Completely avoids insecure storage
3. **HTTP-only like**: SecureStore simulates HTTP-only cookies (tokens not accessible to JavaScript)
4. **HTTPS Required**: All API calls to backend must use HTTPS
5. **CORS Protected**: Backend validates origin
6. **Password Hashing**: Backend uses bcrypt (never sent plaintext)

## Usage

### In Components

```typescript
import { useMobileAuth } from '@/lib/auth-context'

export default function MyComponent() {
  const { user, isAuthenticated, login, logout, error } = useMobileAuth()

  if (!isAuthenticated) {
    return <Text>Please log in</Text>
  }

  return (
    <View>
      <Text>Welcome {user?.email}</Text>
      <TouchableOpacity onPress={logout}>
        <Text>Logout</Text>
      </TouchableOpacity>
    </View>
  )
}
```

### Protected Routes

The root layout automatically protects routes:
- Unauthenticated users → redirected to `/(auth)/login`
- Authenticated users on login page → redirected to `/(dashboard)/`

## Dependencies Added

```json
"expo-secure-store": "~13.0.0"
```

## Validation Rules

### Email
- Must match regex: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
- Required field

### Password
- Minimum 8 characters
- Must contain at least one uppercase letter (A-Z)
- Must contain at least one lowercase letter (a-z)
- Must contain at least one number (0-9)

### Password Confirmation
- Must match password field exactly

## Error Handling

All error messages from backend are displayed to user:
- Invalid credentials
- Email already exists
- Network errors
- Validation errors

Errors are also logged to console for debugging.

## Next Steps

1. **Token Refresh**: Implement automatic token refresh on 401 responses
2. **Biometric Auth**: Add Face ID / Fingerprint authentication
3. **Session Management**: Add session timeout and background handling
4. **Deep Linking**: Implement deep links for password reset, email verification
5. **Offline Support**: Cache user data and sync when online
6. **Multi-factor Authentication**: Add MFA support

## Testing

To test authentication:

1. **Signup Flow**:
   - Open app
   - Navigate to signup
   - Enter valid email and strong password
   - Should redirect to dashboard

2. **Login Flow**:
   - After signup, logout
   - Go back to login
   - Enter same credentials
   - Should redirect to dashboard

3. **Persistence**:
   - Login successfully
   - Kill app
   - Reopen app
   - Should still be logged in (tokens persisted)

4. **Session Expiration**:
   - Login successfully
   - Wait 24 hours (or modify token in SecureStore)
   - Try to access protected endpoint
   - Should get 401 and redirect to login

## Files Created

- `src/mobile/lib/auth-storage.ts` - Secure storage
- `src/mobile/lib/auth-context.tsx` - Auth context provider
- `src/mobile/app/_layout.tsx` - Root layout with auth routing
- `src/mobile/app/(auth)/_layout.tsx` - Auth group layout
- `src/mobile/app/(auth)/login.tsx` - Login screen
- `src/mobile/app/(auth)/signup.tsx` - Signup screen
- `src/mobile/app/(dashboard)/_layout.tsx` - Dashboard group layout
- `src/mobile/app/(dashboard)/index.tsx` - Dashboard screen

## Troubleshooting

### Issue: App stuck on loading
- Check that Expo Router is properly installed
- Verify `app/_layout.tsx` is in correct location
- Check console for errors in RootLayoutNav

### Issue: Tokens not persisting
- Verify SecureStore is installed: `expo install expo-secure-store`
- Check iOS/Android build includes SecureStore plugin
- Review console errors when storing/retrieving tokens

### Issue: Cannot authenticate
- Verify backend is running and accessible
- Check API client base URL in shared package
- Verify Authorization header format in network requests

### Issue: Cannot logout
- Verify backend logout endpoint exists
- Check that clearTokens completes successfully
- Confirm Authorization header is removed after logout
