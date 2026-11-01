/**
 * VIP / relationship tiers: decide who your twin may answer.
 *   0 = bypass the twin (you are notified directly), 1 = twin drafts, you always review.
 */

import { useCallback, useEffect, useState } from 'react'
import { View, Text, TextInput, TouchableOpacity } from 'react-native'
import { apiClient } from '@selph/shared'
import { Chips, ui } from './ui'

interface SenderTier {
  id: string
  sender_id: string
  platform: string
  tier: number
  tier_label?: string | null
}

const TIERS = [
  { value: 0, label: 'VIP: bypass twin' },
  { value: 1, label: 'Review first' },
  { value: 2, label: 'Standard' },
  { value: 3, label: 'Low priority' },
]

const PLATFORMS = [
  { value: 'instagram_dm', label: 'Instagram' },
  { value: 'gmail', label: 'Gmail' },
]

export function VipTiersPanel() {
  const [items, setItems] = useState<SenderTier[]>([])
  const [loading, setLoading] = useState(true)
  const [senderId, setSenderId] = useState('')
  const [platform, setPlatform] = useState('instagram_dm')
  const [tier, setTier] = useState(0)
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const response = await apiClient.get('/identity/sender-tiers')
      setItems(response.data.items || [])
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load sender tiers')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const canSubmit = senderId.trim().length > 0 && !busy

  const submit = async () => {
    if (!canSubmit) return
    setBusy(true)
    setError(null)
    try {
      await apiClient.put('/identity/sender-tiers', {
        sender_id: senderId.trim(),
        platform,
        tier,
        ...(label.trim() ? { tier_label: label.trim() } : {}),
      })
      setSenderId('')
      setLabel('')
      await load()
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to save sender tier')
    } finally {
      setBusy(false)
    }
  }

  const remove = async (item: SenderTier) => {
    setError(null)
    try {
      await apiClient.delete(
        `/identity/sender-tiers/${encodeURIComponent(item.platform)}/${encodeURIComponent(item.sender_id)}`
      )
      await load()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove sender tier')
    }
  }

  const tierLabel = (value: number) => TIERS.find((t) => t.value === value)?.label ?? `Tier ${value}`

  return (
    <View style={ui.card} testID="vip-tiers-panel">
      <Text style={ui.title}>VIP Senders</Text>
      <Text style={ui.subtitle}>Your closest relationships never get a templated reply.</Text>
      <TextInput
        style={ui.input}
        placeholder="Sender ID (e.g. james@cofounder.com)"
        value={senderId}
        onChangeText={setSenderId}
        autoCapitalize="none"
        testID="vip-sender-id"
      />
      <Chips options={PLATFORMS} value={platform} onChange={setPlatform} testIDPrefix="vip-platform" />
      <Chips options={TIERS} value={tier} onChange={setTier} testIDPrefix="vip-tier" />
      <TextInput style={ui.input} placeholder="Label (optional)" value={label} onChangeText={setLabel} testID="vip-label" />
      <TouchableOpacity
        style={[ui.button, !canSubmit && ui.buttonDisabled]}
        disabled={!canSubmit}
        onPress={submit}
        testID="vip-submit"
      >
        <Text style={ui.buttonText}>{busy ? 'Saving…' : 'Save sender'}</Text>
      </TouchableOpacity>
      {error && <Text style={ui.error}>{error}</Text>}

      {loading ? (
        <Text style={ui.empty}>Loading…</Text>
      ) : items.length === 0 ? (
        <Text style={ui.empty}>No special senders yet. Everyone gets the standard flow.</Text>
      ) : (
        items.map((item) => (
          <View key={item.id} style={ui.row}>
            <Text style={ui.rowTitle}>
              {item.tier_label || item.sender_id} · {tierLabel(item.tier)}
            </Text>
            <Text style={ui.rowMeta}>
              {item.sender_id} · {item.platform}
            </Text>
            <TouchableOpacity
              style={[ui.ghostButton, { marginTop: 8 }]}
              onPress={() => remove(item)}
              testID={`vip-remove-${item.id}`}
            >
              <Text style={ui.ghostButtonText}>Remove</Text>
            </TouchableOpacity>
          </View>
        ))
      )}
    </View>
  )
}
