/**
 * Mobile signup screen
 */

import React, { useState } from 'react'
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Alert,
} from 'react-native'
import { useMobileAuth } from '@/lib/auth-context'

export default function SignupScreen() {
  const { signup, error, clearError, loading } = useMobileAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [validationErrors, setValidationErrors] = useState<{
    email?: string
    password?: string
    confirmPassword?: string
  }>({})

  const validateEmail = (emailStr: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(emailStr)
  }

  const validatePassword = (pwd: string) => {
    if (!pwd) return 'Password is required'
    if (pwd.length < 8)
      return 'Password must be at least 8 characters long'
    if (!/[A-Z]/.test(pwd))
      return 'Password must contain at least one uppercase letter'
    if (!/[a-z]/.test(pwd))
      return 'Password must contain at least one lowercase letter'
    if (!/[0-9]/.test(pwd))
      return 'Password must contain at least one number'
    return null
  }

  const handleSignup = async () => {
    clearError()
    setValidationErrors({})

    // Validation
    const newErrors: typeof validationErrors = {}

    if (!email) newErrors.email = 'Email is required'
    else if (!validateEmail(email)) newErrors.email = 'Please enter a valid email'

    const passwordError = validatePassword(password)
    if (passwordError) newErrors.password = passwordError

    if (!confirmPassword)
      newErrors.confirmPassword = 'Please confirm your password'
    else if (password !== confirmPassword)
      newErrors.confirmPassword = 'Passwords do not match'

    if (Object.keys(newErrors).length > 0) {
      setValidationErrors(newErrors)
      return
    }

    try {
      await signup(email, password)
    } catch (err: any) {
      Alert.alert('Signup Failed', error || 'Please try again')
    }
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>SELPH</Text>
          <Text style={styles.subtitle}>Your Digital Twin AI</Text>
        </View>

        {/* Error Message */}
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Form */}
        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={[
                styles.input,
                validationErrors.email ? styles.inputError : {},
              ]}
              placeholder="you@example.com"
              value={email}
              onChangeText={setEmail}
              editable={!loading}
              keyboardType="email-address"
              autoCapitalize="none"
            />
            {validationErrors.email && (
              <Text style={styles.fieldError}>{validationErrors.email}</Text>
            )}
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={[
                styles.input,
                validationErrors.password ? styles.inputError : {},
              ]}
              placeholder="Min 8 chars, uppercase, lowercase, number"
              value={password}
              onChangeText={setPassword}
              editable={!loading}
              secureTextEntry
            />
            {validationErrors.password && (
              <Text style={styles.fieldError}>{validationErrors.password}</Text>
            )}
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Confirm Password</Text>
            <TextInput
              style={[
                styles.input,
                validationErrors.confirmPassword ? styles.inputError : {},
              ]}
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              editable={!loading}
              secureTextEntry
            />
            {validationErrors.confirmPassword && (
              <Text style={styles.fieldError}>{validationErrors.confirmPassword}</Text>
            )}
          </View>

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleSignup}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Create Account</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Password Requirements */}
        <View style={styles.requirementsBox}>
          <Text style={styles.requirementsTitle}>Password requirements:</Text>
          <Text style={styles.requirementItem}>• At least 8 characters</Text>
          <Text style={styles.requirementItem}>• At least one uppercase letter (A-Z)</Text>
          <Text style={styles.requirementItem}>• At least one lowercase letter (a-z)</Text>
          <Text style={styles.requirementItem}>• At least one number (0-9)</Text>
        </View>

        {/* Footer */}
        <Text style={styles.footerText}>
          By creating an account, you agree to our Terms of Service and Privacy Policy
        </Text>
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    padding: 20,
    justifyContent: 'center',
    minHeight: '100%',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
    marginTop: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
  },
  errorBox: {
    backgroundColor: '#fee2e2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginBottom: 24,
  },
  errorText: {
    color: '#991b1b',
    fontSize: 14,
  },
  form: {
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  inputError: {
    borderColor: '#ef4444',
  },
  fieldError: {
    fontSize: 12,
    color: '#dc2626',
    marginTop: 4,
  },
  button: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: {
    backgroundColor: '#9ca3af',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  requirementsBox: {
    backgroundColor: '#eff6ff',
    borderWidth: 1,
    borderColor: '#bfdbfe',
    borderRadius: 8,
    padding: 12,
    marginBottom: 24,
  },
  requirementsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 8,
  },
  requirementItem: {
    fontSize: 12,
    color: '#1e3a8a',
    marginBottom: 4,
  },
  footerText: {
    textAlign: 'center',
    fontSize: 11,
    color: '#6b7280',
    marginTop: 16,
  },
})
