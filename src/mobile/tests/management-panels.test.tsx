import { fireEvent, render, waitFor } from '@testing-library/react-native'
import { SimulateMessage } from '../components/simulate-message'
import { BriefingsPanel } from '../components/briefings-panel'
import { VipTiersPanel } from '../components/vip-tiers-panel'
import { apiClient } from '@selph/shared'

jest.mock('@selph/shared', () => ({
  apiClient: { get: jest.fn(), post: jest.fn(), put: jest.fn(), delete: jest.fn() },
}))

const api = apiClient as unknown as Record<'get' | 'post' | 'put' | 'delete', jest.Mock>

beforeEach(() => Object.values(api).forEach((m) => m.mockReset()))

describe('SimulateMessage (mobile)', () => {
  it('posts to /messages/ingest and refreshes the dashboard', async () => {
    api.post.mockResolvedValue({ data: { draft_id: 'd1', status: 'draft_ready' } })
    const onIngested = jest.fn()
    const { getByTestId, findByText } = render(<SimulateMessage onIngested={onIngested} />)

    fireEvent.press(getByTestId('sim-channel-gmail'))
    fireEvent.changeText(getByTestId('sim-sender-name'), 'Priya Rao')
    fireEvent.changeText(getByTestId('sim-content'), 'How do you stay focused?')
    fireEvent.press(getByTestId('sim-submit'))

    expect(await findByText(/Draft created/)).toBeTruthy()
    expect(api.post).toHaveBeenCalledWith('/messages/ingest', {
      channel: 'gmail',
      sender_name: 'Priya Rao',
      sender_id: 'priya_rao',
      content: 'How do you stay focused?',
    })
    expect(onIngested).toHaveBeenCalled()
  })

  it('does not submit an empty message', () => {
    const { getByTestId } = render(<SimulateMessage onIngested={jest.fn()} />)
    fireEvent.press(getByTestId('sim-submit'))
    expect(api.post).not.toHaveBeenCalled()
  })

  it('explains VIP routing and surfaces API errors', async () => {
    api.post.mockResolvedValueOnce({ data: { draft_id: null, routing_action: 'direct_notify' } })
    const { getByTestId, findByText } = render(<SimulateMessage onIngested={jest.fn()} />)
    fireEvent.changeText(getByTestId('sim-content'), 'term sheet')
    fireEvent.press(getByTestId('sim-submit'))
    expect(await findByText(/VIP sender/)).toBeTruthy()

    api.post.mockRejectedValueOnce({ response: { data: { detail: 'boom' } } })
    fireEvent.changeText(getByTestId('sim-content'), 'again')
    fireEvent.press(getByTestId('sim-submit'))
    expect(await findByText('boom')).toBeTruthy()
  })
})

describe('BriefingsPanel (mobile)', () => {
  const briefing = (o = {}) => ({
    id: 'b1', briefing_type: 'availability', topic: 'conference week', content: 'Slower replies',
    priority: 8, is_active: true, use_count: 1, max_uses: null, expires_at: null, cleared_at: null, ...o,
  })

  it('lists active briefings only and shows the empty state', async () => {
    api.get.mockResolvedValueOnce({
      data: { items: [briefing(), briefing({ id: 'b2', topic: 'old', cleared_at: '2026-01-01' })] },
    })
    const first = render(<BriefingsPanel />)
    expect(await first.findByText(/conference week · availability/)).toBeTruthy()
    expect(first.queryByText(/old ·/)).toBeNull()

    api.get.mockResolvedValueOnce({ data: { items: [] } })
    const second = render(<BriefingsPanel />)
    expect(await second.findByText(/No active briefings/)).toBeTruthy()
  })

  it('creates a briefing with an expiry and reloads', async () => {
    api.get.mockResolvedValue({ data: { items: [] } })
    api.post.mockResolvedValue({ data: {} })
    const { getByTestId, findByText } = render(<BriefingsPanel />)
    await findByText(/No active briefings/)

    fireEvent.press(getByTestId('briefing-type-instruction'))
    fireEvent.changeText(getByTestId('briefing-topic'), 'launch')
    fireEvent.changeText(getByTestId('briefing-content'), 'Mention my course')
    fireEvent.changeText(getByTestId('briefing-expires'), '24')
    fireEvent.press(getByTestId('briefing-submit'))

    await waitFor(() => expect(api.post).toHaveBeenCalled())
    const [url, body] = api.post.mock.calls[0]
    expect(url).toBe('/identity/briefings')
    expect(body).toMatchObject({ briefing_type: 'instruction', topic: 'launch', content: 'Mention my course' })
    expect(new Date(body.expires_at).getTime() - Date.now()).toBeGreaterThan(23 * 3600_000)
    await waitFor(() => expect(api.get.mock.calls.length).toBeGreaterThan(1))
  })

  it('clears a briefing', async () => {
    api.get.mockResolvedValue({ data: { items: [briefing()] } })
    api.post.mockResolvedValue({ data: {} })
    const { findByTestId } = render(<BriefingsPanel />)
    fireEvent.press(await findByTestId('briefing-clear-b1'))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/identity/briefings/b1/clear'))
  })
})

describe('VipTiersPanel (mobile)', () => {
  const tier = (o = {}) => ({ id: 't1', sender_id: 'james@cofounder.com', platform: 'gmail', tier: 0, tier_label: 'Co-founder', ...o })

  it('lists senders with a readable tier', async () => {
    api.get.mockResolvedValue({ data: { items: [tier()] } })
    const { findByText } = render(<VipTiersPanel />)
    expect(await findByText('Co-founder · VIP: bypass twin')).toBeTruthy()
    expect(await findByText('james@cofounder.com · gmail')).toBeTruthy()
  })

  it('saves a sender tier via PUT', async () => {
    api.get.mockResolvedValue({ data: { items: [] } })
    api.put.mockResolvedValue({ data: {} })
    const { getByTestId, findByText } = render(<VipTiersPanel />)
    await findByText(/No special senders yet/)

    fireEvent.changeText(getByTestId('vip-sender-id'), '  partner@vc.com ')
    fireEvent.press(getByTestId('vip-platform-gmail'))
    fireEvent.press(getByTestId('vip-tier-1'))
    fireEvent.changeText(getByTestId('vip-label'), 'Investor')
    fireEvent.press(getByTestId('vip-submit'))

    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith('/identity/sender-tiers', {
        sender_id: 'partner@vc.com', platform: 'gmail', tier: 1, tier_label: 'Investor',
      })
    )
  })

  it('removes a sender with an URL-encoded path', async () => {
    api.get.mockResolvedValue({ data: { items: [tier()] } })
    api.delete.mockResolvedValue({})
    const { findByTestId } = render(<VipTiersPanel />)
    fireEvent.press(await findByTestId('vip-remove-t1'))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/identity/sender-tiers/gmail/james%40cofounder.com'))
  })
})
