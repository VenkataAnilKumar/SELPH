/**
 * Shared API client for web and mobile
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import { ApiResponse } from '../types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
  }

  // Auth endpoints
  async signup(email: string, password: string, name: string) {
    return this.client.post('/auth/signup', { email, password, name })
  }

  async login(email: string, password: string) {
    return this.client.post('/auth/login', { email, password })
  }

  async refresh() {
    return this.client.post('/auth/refresh')
  }

  // Twin endpoints
  async getTwin() {
    return this.client.get('/twin/me')
  }

  async pauseTwin() {
    return this.client.post('/twin/pause')
  }

  async resumeTwin() {
    return this.client.post('/twin/resume')
  }

  async getTwinStats() {
    return this.client.get('/twin/stats')
  }

  // Drafts endpoints
  async getPendingDrafts() {
    return this.client.get('/drafts/pending')
  }

  async getDraft(draftId: string) {
    return this.client.get(`/drafts/${draftId}`)
  }

  async approveDraft(draftId: string, action: string, editedContent?: string) {
    return this.client.post(`/drafts/${draftId}/approve`, {
      action,
      edited_content: editedContent,
    })
  }

  // Channels endpoints
  async connectInstagram(credentialValue?: string, scope?: string) {
    return this.client.post('/channels/instagram/connect', {
      credential_value: credentialValue,
      scope,
    })
  }

  async connectGmail(credentialValue?: string, scope?: string) {
    return this.client.post('/channels/gmail/connect', {
      credential_value: credentialValue,
      scope,
    })
  }

  async getConnectedChannels() {
    return this.client.get('/channels/connected')
  }

  async disconnectChannel(channel: string) {
    return this.client.post(`/channels/${channel}/disconnect`)
  }

  // Phase 10: Proactive Twin
  async getProactiveSuggestions(statusFilter?: string, limit = 50) {
    return this.client.get('/proactive/suggestions', {
      params: {
        status_filter: statusFilter,
        limit,
      },
    })
  }

  async actOnProactiveSuggestion(
    suggestionId: string,
    action: 'approve' | 'dismiss' | 'never' | 'snooze',
    editedMessage?: string,
    snoozeDays = 30
  ) {
    return this.client.post(`/proactive/suggestions/${suggestionId}/act`, {
      action,
      edited_message: editedMessage,
      snooze_days: snoozeDays,
    })
  }

  async getProactivePreferences() {
    return this.client.get('/proactive/preferences')
  }

  async updateProactivePreferences(payload: {
    enabled?: boolean
    enabled_types?: string[]
    cold_threshold_days?: number
    open_thread_hours?: number
    max_suggestions_per_day?: number
  }) {
    return this.client.patch('/proactive/preferences', payload)
  }

  async runProactiveScan() {
    return this.client.post('/proactive/scan')
  }

  // Phase 10: Crisis / Surge
  async getSurgeStatus() {
    return this.client.get('/twin/surge-status')
  }

  async activateCrisis(mode: 'crisis_alert' | 'crisis_mode' | 'manual_pause' = 'crisis_mode') {
    return this.client.post('/twin/crisis/activate', {
      mode,
      trigger_type: 'manual',
    })
  }

  async resolveCrisis() {
    return this.client.post('/twin/crisis/resolve', {
      resolution_type: 'manual_resume',
    })
  }

  // Phase 10: Multi-Identity
  async listIdentityProfiles() {
    return this.client.get('/identity/profiles')
  }

  async createIdentityProfile(payload: {
    profile_name: string
    profile_type: string
    vocabulary_description?: string
    communication_style?: string
  }) {
    return this.client.post('/identity/profiles', payload)
  }

  // Phase 10: Style Evolution
  async refreshStyleCheckpoint(profileId?: string) {
    return this.client.post('/twin/style/refresh', null, {
      params: profileId ? { profile_id: profileId } : undefined,
    })
  }

  async listStyleCheckpoints() {
    return this.client.get('/twin/style/checkpoints')
  }

  // Phase 10: Verification
  async getMyCertificate() {
    return this.client.get('/twin/certificate')
  }

  async revokeMyCertificate(reason?: string) {
    return this.client.post('/twin/certificate/revoke', { reason })
  }

  async verifyTwinMessage(twinId: string, messageHash: string, signature?: string) {
    return this.client.get(`/verify/${twinId}/${messageHash}`, {
      params: signature ? { signature } : undefined,
    })
  }

  // Phase 10: Privacy
  async getPrivacySettings() {
    return this.client.get('/privacy/settings')
  }

  async updatePrivacySettings(payload: {
    processing_mode?: 'cloud' | 'hybrid' | 'on_device'
    cloud_sync_scope?: 'full' | 'metadata_only' | 'none'
    voice_clone_enabled?: boolean
    avatar_enabled?: boolean
  }) {
    return this.client.patch('/privacy/settings', payload)
  }

  async updatePrivacyCapability(onDeviceCapable: boolean) {
    return this.client.post('/privacy/capability-check', {
      on_device_capable: onDeviceCapable,
    })
  }

  // Phase 10: Twin-to-Twin protocol
  async createT2TSession(initiatingTwin: string, receivingTwin: string, sessionType: 'scheduling' | 'availability' | 'introduction') {
    return this.client.post(`/t2t/sessions?initiating_twin=${encodeURIComponent(initiatingTwin)}`, {
      receiving_twin: receivingTwin,
      session_type: sessionType,
    })
  }

  async listT2TSessions(twinId: string) {
    return this.client.get('/t2t/sessions', { params: { twin_id: twinId } })
  }

  // Health check
  async health() {
    return this.client.get('/health')
  }

  // Push token registration
  async registerPushToken(token: string) {
    return this.client.post('/auth/push-token', { token })
  }

  // Generic HTTP methods (for direct use in pages/contexts)
  async get(url: string, config?: any) {
    return this.client.get(url, config)
  }

  async post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config)
  }

  async put(url: string, data?: any, config?: any) {
    return this.client.put(url, data, config)
  }

  async delete(url: string, config?: any) {
    return this.client.delete(url, config)
  }

  get defaults() {
    return this.client.defaults
  }
}

export const apiClient = new ApiClient()
