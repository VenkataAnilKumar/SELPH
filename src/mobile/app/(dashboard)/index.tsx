/**
 * Mobile dashboard screen
 */

import React, { useEffect, useState } from 'react'
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native'
import { useMobileAuth } from '@/lib/auth-context'
import { apiClient } from '@selph/shared'

interface Twin {
  id: string
  user_id: string
  domain: string
  tone: string
  status: string
}

export default function DashboardScreen() {
  const { user, logout } = useMobileAuth()
  const [twin, setTwin] = useState<Twin | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTwin = async () => {
      try {
        const response = await apiClient.get('/v1/twin/me')
        setTwin(response.data)
      } catch (err: any) {
        setError(
          err.response?.data?.detail || 'Failed to load twin profile'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchTwin()
  }, [])

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to log out?',
      [
        {
          text: 'Cancel',
          onPress: () => {},
          style: 'cancel',
        },
        {
          text: 'Logout',
          onPress: async () => {
            try {
              await logout()
            } catch (err) {
              Alert.alert('Error', 'Failed to logout')
            }
          },
          style: 'destructive',
        },
      ]
    )
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </View>
    )
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>SELPH Dashboard</Text>
          <Text style={styles.headerSubtitle}>{user?.email}</Text>
        </View>
        <TouchableOpacity
          style={styles.logoutButton}
          onPress={handleLogout}
        >
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Error */}
      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Twin Profile Card */}
      {twin && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Twin Profile</Text>
          
          <View style={styles.profileItem}>
            <Text style={styles.profileLabel}>Domain</Text>
            <Text style={styles.profileValue}>{twin.domain}</Text>
          </View>

          <View style={styles.profileItem}>
            <Text style={styles.profileLabel}>Tone</Text>
            <Text style={styles.profileValue}>{twin.tone}</Text>
          </View>

          <View style={styles.profileItem}>
            <Text style={styles.profileLabel}>Status</Text>
            <View style={styles.statusBadge}>
              <View
                style={[
                  styles.statusDot,
                  {
                    backgroundColor:
                      twin.status === 'active' ? '#22c55e' : '#eab308',
                  },
                ]}
              />
              <Text style={styles.statusText}>{twin.status}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Quick Actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Quick Actions</Text>
        
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>View Messages</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>Approve Drafts</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>Update Twin Profile</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>View Settings</Text>
        </TouchableOpacity>
      </View>

      {/* Getting Started */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Getting Started</Text>
        
        <View style={styles.stepItem}>
          <View style={styles.stepNumber}>
            <Text style={styles.stepNumberText}>1</Text>
          </View>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Connect Channels</Text>
            <Text style={styles.stepDescription}>
              Link your Instagram, Gmail, or other channels to start receiving messages.
            </Text>
          </View>
        </View>

        <View style={styles.stepItem}>
          <View style={styles.stepNumber}>
            <Text style={styles.stepNumberText}>2</Text>
          </View>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Customize Your Twin</Text>
            <Text style={styles.stepDescription}>
              Set your twin's domain, tone, vocabulary, and communication style.
            </Text>
          </View>
        </View>

        <View style={styles.stepItem}>
          <View style={styles.stepNumber}>
            <Text style={styles.stepNumberText}>3</Text>
          </View>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Review & Approve</Text>
            <Text style={styles.stepDescription}>
              Your twin will generate responses, and you'll review and approve before they're sent.
            </Text>
          </View>
        </View>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    color: '#6b7280',
    fontSize: 14,
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  logoutButton: {
    backgroundColor: '#ef4444',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  errorBox: {
    backgroundColor: '#fee2e2',
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444',
    padding: 12,
    margin: 16,
    borderRadius: 6,
  },
  errorText: {
    color: '#991b1b',
    fontSize: 13,
  },
  card: {
    backgroundColor: '#fff',
    margin: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  profileItem: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  profileLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  profileValue: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
    textTransform: 'capitalize',
  },
  actionButton: {
    backgroundColor: '#f3f4f6',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginBottom: 8,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  stepItem: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  stepDescription: {
    fontSize: 12,
    color: '#6b7280',
    lineHeight: 18,
  },
})
