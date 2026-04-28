/**
 * Shared TypeScript types for SELPH
 */

// User & Auth
export interface User {
  id: string
  email: string
  name: string
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// Twin
export interface Twin {
  id: string
  user_id: string
  domain: string
  tone: string
  vocab: string[]
  avg_response_length: number
  topics_known: string[]
  topics_avoided: string[]
  status: 'active' | 'paused'
  created_at: string
}

// Message
export interface Message {
  id: string
  user_id: string
  channel: 'instagram_dm' | 'gmail' | 'twitter_dm' | 'whatsapp' | 'slack'
  sender_id: string
  sender_name: string
  content: string
  received_at: string
  status: 'received' | 'processed' | 'draft_ready'
}

// Draft
export interface Draft {
  id: string
  message_id: string
  user_id: string
  content: string
  confidence_score: number
  confidence_label: 'High' | 'Medium' | 'Low'
  moderation_passed: boolean
  status: 'pending_approval' | 'approved' | 'edited' | 'rejected' | 'sent'
  edited_content?: string
  created_at: string
}

// API Response
export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}
