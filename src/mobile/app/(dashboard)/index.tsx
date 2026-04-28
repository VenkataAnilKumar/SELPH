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
  TextInput,
  AppState,
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

interface TwinStats {
  total_messages: number
  pending_drafts: number
  processed_drafts: number
  total_estimated_tokens: number
  total_estimated_cost_usd: number
  fallback_rate: number
  approval_rate: number
  generation_source_breakdown: Record<string, number>
  model_breakdown: Record<string, number>
  fallback_reason_breakdown: Record<string, number>
}

interface Draft {
  id: string
  content: string
  status: string
  confidence_score: number
  confidence_label: string
  confidence_reasoning?: string | null
  generation_source?: string | null
  llm_model?: string | null
  fallback_reason?: string | null
  estimated_total_tokens?: number | null
  estimated_cost_usd?: number | null
  created_at: string
}

interface IdentityProfile {
  vocabulary_description?: string | null
  communication_style?: string | null
  topics_known: string[]
  topics_avoided: string[]
  profile_complete: boolean
}

interface ConnectedChannel {
  channel: string
  connected: boolean
  scope?: string | null
  updated_at: string
}

export default function DashboardScreen() {
  const { user, logout } = useMobileAuth()
  const [twin, setTwin] = useState<Twin | null>(null)
  const [stats, setStats] = useState<TwinStats | null>(null)
  const [pendingDrafts, setPendingDrafts] = useState<Draft[]>([])
  const [identityProfile, setIdentityProfile] = useState<IdentityProfile | null>(null)
  const [channels, setChannels] = useState<ConnectedChannel[]>([])
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [activeDraftId, setActiveDraftId] = useState<string | null>(null)
  const [editDraftId, setEditDraftId] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState('')
  const [settingsDomain, setSettingsDomain] = useState('')
  const [settingsTone, setSettingsTone] = useState('')
  const [onboardingRole, setOnboardingRole] = useState('')
  const [onboardingStyle, setOnboardingStyle] = useState('friendly')
  const [onboardingAvoidedTopics, setOnboardingAvoidedTopics] = useState('')
  const [onboardingLength, setOnboardingLength] = useState('medium')
  const [onboardingAudienceTone, setOnboardingAudienceTone] = useState('')
  const [onboardingThreeWords, setOnboardingThreeWords] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [twinResponse, statsResponse, draftsResponse, identityResponse, channelsResponse] = await Promise.all([
          apiClient.get('/twin/me'),
          apiClient.get('/twin/stats'),
          apiClient.get('/drafts/pending'),
          apiClient.get('/identity/profile'),
          apiClient.get('/channels/connected'),
        ])
        setTwin(twinResponse.data)
        setSettingsDomain(twinResponse.data.domain || '')
        setSettingsTone(twinResponse.data.tone || '')
        setStats(statsResponse.data)
        setPendingDrafts(draftsResponse.data)
        setIdentityProfile(identityResponse.data)
        setChannels(channelsResponse.data)
        setError(null)
      } catch (err: any) {
        setError(
          err.response?.data?.detail || 'Failed to load dashboard'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  const refreshDashboard = async () => {
    const [statsResponse, draftsResponse, channelsResponse] = await Promise.all([
      apiClient.get('/twin/stats'),
      apiClient.get('/drafts/pending'),
      apiClient.get('/channels/connected'),
    ])
    setStats(statsResponse.data)
    setPendingDrafts(draftsResponse.data)
    setChannels(channelsResponse.data)
  }

  // Auto-refresh: foreground resume + 30-second interval
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      if (nextState === 'active') {
        refreshDashboard()
      }
    })

    const intervalId = setInterval(() => {
      refreshDashboard()
    }, 30_000)

    return () => {
      subscription.remove()
      clearInterval(intervalId)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleDraftAction = async (
    draftId: string,
    action: 'approve' | 'reject' | 'edit' | 'skip',
    editedValue?: string
  ) => {
    setActionMessage(null)
    setActionError(null)
    setActiveDraftId(draftId)

    try {
      await apiClient.approveDraft(draftId, action, editedValue)
      await refreshDashboard()
      setActionMessage(
        action === 'edit'
          ? 'Draft updated and approved.'
          : `Draft ${action}d successfully.`
      )
      if (action === 'edit') {
        setEditDraftId(null)
        setEditedContent('')
      }
    } catch (err: any) {
      setActionError(
        err.response?.data?.detail || `Failed to ${action} draft`
      )
    } finally {
      setActiveDraftId(null)
    }
  }

  const handleCompleteOnboarding = async () => {
    try {
      setActionError(null)
      const avoided = onboardingAvoidedTopics
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean)
      const threeWords = onboardingThreeWords
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean)

      await apiClient.post('/identity/onboard', {
        role: onboardingRole,
        communication_style: onboardingStyle,
        topics_avoided: avoided,
        response_length: onboardingLength,
        audience_tone: onboardingAudienceTone,
        three_words: threeWords,
      })

      const [identityResponse, twinResponse] = await Promise.all([
        apiClient.get('/identity/profile'),
        apiClient.get('/twin/me'),
      ])

      setIdentityProfile(identityResponse.data)
      setTwin(twinResponse.data)
      setSettingsDomain(twinResponse.data.domain || '')
      setSettingsTone(twinResponse.data.tone || '')
      setActionMessage('Onboarding saved. Your twin is now configured.')
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to complete onboarding')
    }
  }

  const connectChannel = async (channel: 'instagram' | 'gmail') => {
    try {
      setActionError(null)
      const endpoint = channel === 'instagram' ? '/channels/instagram/connect' : '/channels/gmail/connect'
      await apiClient.post(endpoint, {})
      await refreshDashboard()
      setActionMessage(`${channel} connected successfully.`)
    } catch (err: any) {
      setActionError(err.response?.data?.detail || `Failed to connect ${channel}`)
    }
  }

  const disconnectChannel = async (channel: string) => {
    try {
      setActionError(null)
      await apiClient.post(`/channels/${channel}/disconnect`)
      await refreshDashboard()
      setActionMessage(`${channel} disconnected.`)
    } catch (err: any) {
      setActionError(err.response?.data?.detail || `Failed to disconnect ${channel}`)
    }
  }

  const toggleTwinStatus = async () => {
    if (!twin) return
    try {
      setActionError(null)
      const response = twin.status === 'active'
        ? await apiClient.post('/twin/pause')
        : await apiClient.post('/twin/resume')
      setTwin(response.data)
      setActionMessage(
        response.data.status === 'active'
          ? 'Twin resumed and processing is active.'
          : 'Twin paused successfully.'
      )
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to update twin status')
    }
  }

  const updateTwinSettings = async () => {
    try {
      setActionError(null)
      const response = await apiClient.put('/twin/me', {
        domain: settingsDomain,
        tone: settingsTone,
      })
      setTwin(response.data)
      setActionMessage('Twin settings updated.')
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to update twin settings')
    }
  }

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

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {actionMessage && (
        <View style={styles.successBox}>
          <Text style={styles.successText}>{actionMessage}</Text>
        </View>
      )}

      {actionError && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{actionError}</Text>
        </View>
      )}

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

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Approval Loop</Text>
        {stats ? (
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.profileLabel}>Pending Drafts</Text>
              <Text style={styles.statValue}>{stats.pending_drafts}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.profileLabel}>Processed Drafts</Text>
              <Text style={styles.statValue}>{stats.processed_drafts}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.profileLabel}>Messages Seen</Text>
              <Text style={styles.statValue}>{stats.total_messages}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.profileLabel}>Fallback Rate</Text>
              <Text style={styles.statValue}>
                {(stats.fallback_rate * 100).toFixed(0)}%
              </Text>
            </View>
            <View style={[styles.statCard, styles.approvalRateCard]}>
              <Text style={[styles.profileLabel, styles.approvalRateLabel]}>Approval Rate</Text>
              <Text style={[styles.statValue, styles.approvalRateValue]}>
                {(stats.approval_rate * 100).toFixed(0)}%
              </Text>
            </View>
          </View>
        ) : (
          <Text style={styles.emptyText}>No stats available yet.</Text>
        )}
      </View>

      {identityProfile && !identityProfile.profile_complete && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Identity Onboarding</Text>
          <Text style={styles.sectionSubtitle}>
            Configure your twin before enabling live channels.
          </Text>
          <TextInput
            style={styles.settingsInput}
            placeholder="Role or domain"
            value={onboardingRole}
            onChangeText={setOnboardingRole}
          />
          <TextInput
            style={styles.settingsInput}
            placeholder="Communication style (formal/casual/friendly/direct/humorous)"
            value={onboardingStyle}
            onChangeText={setOnboardingStyle}
          />
          <TextInput
            style={styles.settingsInput}
            placeholder="Topics to avoid (comma separated)"
            value={onboardingAvoidedTopics}
            onChangeText={setOnboardingAvoidedTopics}
          />
          <TextInput
            style={styles.settingsInput}
            placeholder="Response length (short/medium/detailed)"
            value={onboardingLength}
            onChangeText={setOnboardingLength}
          />
          <TextInput
            style={styles.settingsInput}
            placeholder="Audience tone"
            value={onboardingAudienceTone}
            onChangeText={setOnboardingAudienceTone}
          />
          <TextInput
            style={styles.settingsInput}
            placeholder="Three words (comma separated)"
            value={onboardingThreeWords}
            onChangeText={setOnboardingThreeWords}
          />
          <TouchableOpacity style={styles.primaryButton} onPress={handleCompleteOnboarding}>
            <Text style={styles.primaryButtonText}>Save Onboarding</Text>
          </TouchableOpacity>
        </View>
      )}

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Channel Connections</Text>
        <Text style={styles.sectionSubtitle}>
          Connect Instagram and Gmail so inbound messages flow into SELPH.
        </Text>
        {['instagram', 'gmail'].map((channel) => {
          const current = channels.find((item) => item.channel === channel)
          const connected = !!current?.connected

          return (
            <View key={channel} style={styles.channelRow}>
              <View>
                <Text style={styles.profileValue}>{channel}</Text>
                <Text style={styles.profileLabel}>{connected ? 'Connected' : 'Not connected'}</Text>
              </View>
              {connected ? (
                <TouchableOpacity
                  style={styles.rejectButton}
                  onPress={() => disconnectChannel(channel)}
                >
                  <Text style={styles.rejectButtonText}>Disconnect</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={() => connectChannel(channel as 'instagram' | 'gmail')}
                >
                  <Text style={styles.primaryButtonText}>Connect</Text>
                </TouchableOpacity>
              )}
            </View>
          )
        })}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Settings</Text>
        <Text style={styles.sectionSubtitle}>
          Pause/resume the twin and tune tone/domain.
        </Text>
        <TextInput
          style={styles.settingsInput}
          placeholder="Domain"
          value={settingsDomain}
          onChangeText={setSettingsDomain}
        />
        <TextInput
          style={styles.settingsInput}
          placeholder="Tone"
          value={settingsTone}
          onChangeText={setSettingsTone}
        />
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.primaryButton} onPress={updateTwinSettings}>
            <Text style={styles.primaryButtonText}>Update Tone/Domain</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={twin?.status === 'active' ? styles.pauseButton : styles.resumeButton}
            onPress={toggleTwinStatus}
          >
            <Text style={styles.primaryButtonText}>
              {twin?.status === 'active' ? 'Pause Twin' : 'Resume Twin'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Pending Drafts</Text>
        <Text style={styles.sectionSubtitle}>
          Review generated replies before SELPH sends anything.
        </Text>

        {pendingDrafts.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No drafts are waiting for approval.</Text>
          </View>
        ) : (
          pendingDrafts.map((draft) => {
            const isEditing = editDraftId === draft.id
            const isSubmitting = activeDraftId === draft.id

            return (
              <View key={draft.id} style={styles.draftCard}>
                <View style={styles.badgeRow}>
                  <Text style={styles.confidenceBadge}>
                    {draft.confidence_label} confidence
                  </Text>
                  <Text style={styles.sourceBadge}>
                    {draft.generation_source || 'unknown source'}
                  </Text>
                </View>

                <Text style={styles.draftContent}>{draft.content}</Text>
                <Text style={styles.metaText}>
                  Confidence score: {draft.confidence_score.toFixed(2)}
                </Text>
                <Text style={styles.metaText}>
                  Estimated tokens: {draft.estimated_total_tokens ?? 0}
                </Text>
                <Text style={styles.metaText}>
                  Estimated cost: ${Number(draft.estimated_cost_usd ?? 0).toFixed(4)}
                </Text>
                <Text style={styles.metaText}>
                  Model: {draft.llm_model || 'No model recorded'}
                </Text>
                <Text style={styles.metaText}>
                  Fallback reason: {draft.fallback_reason || 'None'}
                </Text>
                {draft.confidence_reasoning ? (
                  <Text style={styles.reasoningText}>{draft.confidence_reasoning}</Text>
                ) : null}

                {isEditing ? (
                  <View style={styles.editBox}>
                    <Text style={styles.editLabel}>Edited response</Text>
                    <TextInput
                      value={editedContent}
                      onChangeText={setEditedContent}
                      multiline
                      style={styles.editInput}
                    />
                    <View style={styles.actionRow}>
                      <TouchableOpacity
                        style={styles.primaryButton}
                        onPress={() => handleDraftAction(draft.id, 'edit', editedContent)}
                        disabled={isSubmitting || editedContent.trim().length === 0}
                      >
                        <Text style={styles.primaryButtonText}>Save Edit</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.secondaryButton}
                        onPress={() => {
                          setEditDraftId(null)
                          setEditedContent('')
                        }}
                      >
                        <Text style={styles.secondaryButtonText}>Cancel</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ) : null}

                <View style={styles.actionRow}>
                  <TouchableOpacity
                    style={styles.approveButton}
                    onPress={() => handleDraftAction(draft.id, 'approve')}
                    disabled={isSubmitting}
                  >
                    <Text style={styles.approveButtonText}>Approve</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.editButton}
                    onPress={() => {
                      setEditDraftId(draft.id)
                      setEditedContent(draft.content)
                    }}
                    disabled={isSubmitting}
                  >
                    <Text style={styles.editButtonText}>Edit</Text>
                  </TouchableOpacity>
                </View>
                <View style={styles.actionRow}>
                  <TouchableOpacity
                    style={styles.rejectButton}
                    onPress={() => handleDraftAction(draft.id, 'reject')}
                    disabled={isSubmitting}
                  >
                    <Text style={styles.rejectButtonText}>Reject</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.secondaryButton}
                    onPress={() => handleDraftAction(draft.id, 'skip')}
                    disabled={isSubmitting}
                  >
                    <Text style={styles.secondaryButtonText}>Skip</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )
          })
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Model Signals</Text>
        {stats ? (
          <>
            <Text style={styles.signalTitle}>Generation Sources</Text>
            {Object.entries(stats.generation_source_breakdown).map(([source, count]) => (
              <View key={source} style={styles.signalRow}>
                <Text style={styles.signalLabel}>{source}</Text>
                <Text style={styles.signalValue}>{count}</Text>
              </View>
            ))}

            <Text style={styles.signalTitle}>Models</Text>
            {Object.entries(stats.model_breakdown).map(([model, count]) => (
              <View key={model} style={styles.signalRow}>
                <Text style={styles.signalLabel}>{model}</Text>
                <Text style={styles.signalValue}>{count}</Text>
              </View>
            ))}

            <Text style={styles.signalTitle}>Fallback Reasons</Text>
            {Object.keys(stats.fallback_reason_breakdown).length === 0 ? (
              <Text style={styles.emptyText}>No fallbacks recorded.</Text>
            ) : (
              Object.entries(stats.fallback_reason_breakdown).map(([reason, count]) => (
                <View key={reason} style={styles.signalRow}>
                  <Text style={styles.signalLabel}>{reason}</Text>
                  <Text style={styles.signalValue}>{count}</Text>
                </View>
              ))
            )}

            <View style={styles.spendCard}>
              <Text style={styles.profileLabel}>Estimated spend</Text>
              <Text style={styles.spendValue}>
                ${stats.total_estimated_cost_usd.toFixed(4)}
              </Text>
              <Text style={styles.metaText}>
                {stats.total_estimated_tokens} tokens processed so far
              </Text>
            </View>
          </>
        ) : (
          <Text style={styles.emptyText}>Stats will appear after draft activity.</Text>
        )}
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
  successBox: {
    backgroundColor: '#dcfce7',
    borderLeftWidth: 4,
    borderLeftColor: '#16a34a',
    padding: 12,
    margin: 16,
    borderRadius: 6,
  },
  successText: {
    color: '#166534',
    fontSize: 13,
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
  sectionSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: -8,
    marginBottom: 16,
    lineHeight: 18,
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
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -4,
  },
  statCard: {
    width: '50%',
    padding: 4,
  },
  approvalRateCard: {
    width: '100%',
    backgroundColor: '#f0fdf4',
    borderRadius: 8,
    padding: 12,
    marginTop: 4,
  },
  approvalRateLabel: {
    color: '#15803d',
    fontWeight: '600',
  },
  approvalRateValue: {
    color: '#14532d',
  },
  statValue: {
    marginTop: 8,
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  emptyState: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#d1d5db',
    padding: 16,
  },
  emptyText: {
    fontSize: 13,
    color: '#6b7280',
  },
  draftCard: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 10,
    padding: 14,
    marginBottom: 14,
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  confidenceBadge: {
    backgroundColor: '#dbeafe',
    color: '#1d4ed8',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    overflow: 'hidden',
  },
  sourceBadge: {
    backgroundColor: '#f3f4f6',
    color: '#374151',
    fontSize: 11,
    fontWeight: '600',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    overflow: 'hidden',
  },
  draftContent: {
    fontSize: 15,
    lineHeight: 22,
    color: '#111827',
    marginBottom: 12,
  },
  metaText: {
    fontSize: 12,
    color: '#4b5563',
    marginBottom: 4,
  },
  reasoningText: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
    lineHeight: 18,
  },
  editBox: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    marginBottom: 12,
  },
  editLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  editInput: {
    minHeight: 100,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    backgroundColor: '#fff',
    padding: 12,
    textAlignVertical: 'top',
    color: '#111827',
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  approveButton: {
    flex: 1,
    backgroundColor: '#16a34a',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  approveButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  editButton: {
    flex: 1,
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  editButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  rejectButton: {
    flex: 1,
    backgroundColor: '#e11d48',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  rejectButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#e5e7eb',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#111827',
    fontSize: 13,
    fontWeight: '700',
  },
  primaryButton: {
    flex: 1,
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  settingsInput: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    backgroundColor: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#111827',
    marginBottom: 10,
  },
  channelRow: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  pauseButton: {
    flex: 1,
    backgroundColor: '#d97706',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  resumeButton: {
    flex: 1,
    backgroundColor: '#059669',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  signalTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111827',
    marginTop: 12,
    marginBottom: 8,
  },
  signalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  signalLabel: {
    flex: 1,
    fontSize: 12,
    color: '#4b5563',
    paddingRight: 12,
  },
  signalValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#111827',
  },
  spendCard: {
    marginTop: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
  },
  spendValue: {
    marginTop: 8,
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
})
