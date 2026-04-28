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
  async connectInstagram() {
    window.location.href = `${API_URL}/v1/channels/instagram/connect`
  }

  async connectGmail() {
    window.location.href = `${API_URL}/v1/channels/gmail/connect`
  }

  async getConnectedChannels() {
    return this.client.get('/channels/connected')
  }

  async disconnectChannel(channel: string) {
    return this.client.post(`/channels/${channel}/disconnect`)
  }

  // Health check
  async health() {
    return this.client.get('/health')
  }
}

export const api = new ApiClient()
