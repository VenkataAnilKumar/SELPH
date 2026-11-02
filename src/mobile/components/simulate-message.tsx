/**
 * Simulate an incoming message so the full message -> draft -> approve loop
 * can be tried without connecting Instagram or Gmail. Nothing is sent externally.
 */

import { useState } from 'react'
import { View, Text, TextInput, TouchableOpacity } from 'react-native'
import { apiClient } from '@selph/shared'
import { Chips, ui } from './ui'

const CHANNELS = [
  { value: 'instagram_dm', label: 'Instagram' },
  { value: 'gmail', label: 'Gmail' },
  { value: 'manual', label: 'Manual' },
]

export function SimulateMessage({ onIngested }: { onIngested: () => void | Promise<void> }) {
  const [channel, setChannel] = useState('instagram_dm')
  const [senderName, setSenderName] = useState('')
  const [senderId, setSenderId] = useState('')
  const [content, setContent] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = content.trim().length > 0 && !busy

  const submit = async () => {
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const name = senderName.trim() || 'Test Sender'
      const response = await apiClient.post('/messages/ingest', {
        channel,
        sender_name: name,
        sender_id: senderId.trim() || name.toLowerCase().replace(/\s+/g, '_'),
        content: content.trim(),
      })
      const data = response.data
      // Refresh the dashboard first so the message never points at a list that does not show the draft yet.
      setContent('')
      await onIngested()
      if (data.draft_id) setResult('Draft created. Review it under Pending Drafts.')
      else if (data.routing_action === 'direct_notify') setResult('VIP sender: routed straight to you, no draft created.')
      else if (data.routing_action === 'skipped_manual_pause') setResult('Twin is paused: no draft created.')
      else setResult(`Message received (${data.routing_action || data.status}).`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send test message')
    } finally {
      setBusy(false)
    }
  }

  return (
    <View style={ui.card} testID="simulate-message">
      <Text style={ui.title}>Simulate Incoming Message</Text>
      <Text style={ui.subtitle}>Try your twin without connecting a channel. Nothing is sent externally.</Text>
      <Chips options={CHANNELS} value={channel} onChange={setChannel} testIDPrefix="sim-channel" />
      <TextInput
        style={ui.input}
        placeholder="Sender name (e.g. Priya)"
        value={senderName}
        onChangeText={setSenderName}
        testID="sim-sender-name"
      />
      <TextInput
        style={ui.input}
        placeholder="Sender ID (use a VIP's ID to test bypass)"
        value={senderId}
        onChangeText={setSenderId}
        autoCapitalize="none"
        testID="sim-sender-id"
      />
      <TextInput
        style={[ui.input, ui.multiline]}
        placeholder="Write the message your twin should reply to…"
        value={content}
        onChangeText={setContent}
        multiline
        maxLength={10000}
        testID="sim-content"
      />
      <TouchableOpacity
        style={[ui.button, !canSubmit && ui.buttonDisabled]}
        disabled={!canSubmit}
        onPress={submit}
        testID="sim-submit"
      >
        <Text style={ui.buttonText}>{busy ? 'Generating…' : 'Send to my twin'}</Text>
      </TouchableOpacity>
      {result && <Text style={ui.ok}>{result}</Text>}
      {error && <Text style={ui.error}>{error}</Text>}
    </View>
  )
}
