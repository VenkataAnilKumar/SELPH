/**
 * Twin Briefings: tell your twin something once and every draft reflects it.
 */

import { useCallback, useEffect, useState } from 'react'
import { View, Text, TextInput, TouchableOpacity } from 'react-native'
import { apiClient } from '@selph/shared'
import { Chips, ui } from './ui'

interface Briefing {
  id: string
  briefing_type: string
  topic: string
  content: string
  priority: number
  is_active: boolean
  expires_at?: string | null
  max_uses?: number | null
  use_count: number
  cleared_at?: string | null
}

const TYPES = [
  { value: 'availability', label: 'Availability' },
  { value: 'instruction', label: 'Instruction' },
  { value: 'fact', label: 'Fact' },
  { value: 'opinion', label: 'Opinion' },
  { value: 'boundary', label: 'Boundary' },
]

export function BriefingsPanel() {
  const [items, setItems] = useState<Briefing[]>([])
  const [loading, setLoading] = useState(true)
  const [type, setType] = useState('availability')
  const [topic, setTopic] = useState('')
  const [content, setContent] = useState('')
  const [expiresInHours, setExpiresInHours] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const response = await apiClient.get('/identity/briefings')
      setItems(response.data.items || [])
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load briefings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const canSubmit = topic.trim().length > 0 && content.trim().length > 0 && !busy

  const submit = async () => {
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      const hours = Number(expiresInHours)
      await apiClient.post('/identity/briefings', {
        briefing_type: type,
        topic: topic.trim(),
        content: content.trim(),
        priority: 5,
        ...(hours > 0 ? { expires_at: new Date(Date.now() + hours * 3600_000).toISOString() } : {}),
      })
      setTopic('')
      setContent('')
      setExpiresInHours('')
      await load()
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to save briefing')
    } finally {
      setBusy(false)
    }
  }

  const clear = async (id: string) => {
    setError(null)
    try {
      await apiClient.post(`/identity/briefings/${id}/clear`)
      await load()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear briefing')
    }
  }

  const active = items.filter((b) => b.is_active && !b.cleared_at)

  return (
    <View style={ui.card} testID="briefings-panel">
      <Text style={ui.title}>Twin Briefings</Text>
      <Text style={ui.subtitle}>Tell your twin something once; every draft reflects it until it expires.</Text>
      <Chips options={TYPES} value={type} onChange={setType} testIDPrefix="briefing-type" />
      <TextInput style={ui.input} placeholder="Topic (e.g. conference week)" value={topic} onChangeText={setTopic} testID="briefing-topic" />
      <TextInput
        style={[ui.input, ui.multiline]}
        placeholder="What should your twin know?"
        value={content}
        onChangeText={setContent}
        multiline
        testID="briefing-content"
      />
      <TextInput
        style={ui.input}
        placeholder="Expires in hours (optional)"
        value={expiresInHours}
        onChangeText={setExpiresInHours}
        keyboardType="numeric"
        testID="briefing-expires"
      />
      <TouchableOpacity
        style={[ui.button, !canSubmit && ui.buttonDisabled]}
        disabled={!canSubmit}
        onPress={submit}
        testID="briefing-submit"
      >
        <Text style={ui.buttonText}>{busy ? 'Saving…' : 'Add briefing'}</Text>
      </TouchableOpacity>
      {error && <Text style={ui.error}>{error}</Text>}

      {loading ? (
        <Text style={ui.empty}>Loading…</Text>
      ) : active.length === 0 ? (
        <Text style={ui.empty}>No active briefings. Your twin is using only your profile.</Text>
      ) : (
        active.map((b) => (
          <View key={b.id} style={ui.row}>
            <Text style={ui.rowTitle}>
              {b.topic} · {b.briefing_type} · P{b.priority}
            </Text>
            <Text style={ui.rowBody}>{b.content}</Text>
            <Text style={ui.rowMeta}>
              Used {b.use_count}
              {b.max_uses ? ` / ${b.max_uses}` : ''} times
              {b.expires_at ? ` · expires ${new Date(b.expires_at).toLocaleString()}` : ''}
            </Text>
            <TouchableOpacity
              style={[ui.ghostButton, { marginTop: 8 }]}
              onPress={() => clear(b.id)}
              testID={`briefing-clear-${b.id}`}
            >
              <Text style={ui.ghostButtonText}>Clear</Text>
            </TouchableOpacity>
          </View>
        ))
      )}
    </View>
  )
}
