import { moderationReasons } from '../lib/moderation-labels'

describe('moderationReasons', () => {
  it('returns nothing when there are no flags', () => {
    expect(moderationReasons(undefined)).toEqual([])
    expect(moderationReasons(null)).toEqual([])
    expect(moderationReasons([])).toEqual([])
  })

  it('maps known categories to plain language and collapses duplicates', () => {
    const reasons = moderationReasons([
      { category: 'prompt_injection' },
      { category: 'prompt_injection' },
      { category: 'hard_block_medical' },
    ])
    expect(reasons).toHaveLength(2)
    expect(reasons[0]).toMatch(/override your twin/i)
    expect(reasons[1]).toMatch(/medical/i)
  })

  it('never shows a blank reason for unknown or missing categories', () => {
    expect(moderationReasons([{ category: 'something_new' }, {}, { category: null }])).toEqual([
      'Flagged by safety checks',
    ])
  })
})
