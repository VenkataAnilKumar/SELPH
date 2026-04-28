/**
 * Mobile login screen
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

export default function LoginScreen() {
  const { login, error, clearError, loading } = useMobileAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [validationErrors, setValidationErrors] = useState<{
    email?: string
    password?: string
  }>({})

  const validateEmail = (emailStr: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(emailStr)
  }

  const handleLogin = async () => {
    clearError()
    setValidationErrors({})

    // Validation
    const newErrors: typeof validationErrors = {}
    if (!email) newErrors.email = 'Email is required'
    else if (!validateEmail(email)) newErrors.email = 'Please enter a valid email'
    if (!password) newErrors.password = 'Password is required'

    if (Object.keys(newErrors).length > 0) {
      setValidationErrors(newErrors)
      return
    }

    try {
      await login(email, password)
    } catch (err: any) {
      Alert.alert('Login Failed', error || 'Please try again')
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
              placeholder="Enter your password"
              value={password}
              onChangeText={setPassword}
              editable={!loading}
              secureTextEntry
            />
            {validationErrors.password && (
              <Text style={styles.fieldError}>{validationErrors.password}</Text>
            )}
          </View>

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Sign In</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Footer */}
        <Text style={styles.footerText}>
          Don't have an account? Sign up in the signup screen.
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
    marginBottom: 32,
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
  footerText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#6b7280',
    marginTop: 16,
  },
})
