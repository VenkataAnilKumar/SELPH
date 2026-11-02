/**
 * Landing page copy. Every claim here maps to behavior that exists in the product;
 * keep it that way (no invented pricing, compliance badges, or integrations).
 */

export const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'
export const SIGNUP_URL = `${APP_URL}/auth/signup`
export const LOGIN_URL = `${APP_URL}/auth/login`

export const NAV_LINKS = [
  { href: '#how-it-works', label: 'How it works' },
  { href: '#features', label: 'Features' },
  { href: '#trust', label: 'Trust & safety' },
  { href: '#faq', label: 'FAQ' },
]

export const STEPS = [
  {
    title: 'Teach it who you are',
    body: 'Answer six questions about your role, tone and reply length, and list topics you never discuss. Add expertise as you go.',
  },
  {
    title: 'Messages arrive, drafts appear',
    body: 'When a DM or email comes in, your twin drafts a reply in your style and shows how confident it is.',
  },
  {
    title: 'You decide',
    body: 'Approve, edit, reject or skip. Nothing is sent until you do. Every decision teaches your twin.',
  },
]

export const FEATURES = [
  {
    id: 'briefing',
    title: 'Twin Briefing',
    body: 'Tell your twin something once, like "I\'m at a conference this week, keep it short." Every draft reflects it until it expires or you clear it.',
  },
  {
    id: 'vip',
    title: 'VIP senders',
    body: 'Your co-founder never gets a templated reply: their messages skip the twin and notify you directly. Investors can be set to "always review first".',
  },
  {
    id: 'batch',
    title: 'Batch approval',
    body: 'Fifty people asked the same question? Approve one template and each recipient gets a personalized copy.',
  },
  {
    id: 'learning',
    title: 'Gets better with every decision',
    body: 'Approvals and edits feed a confidence score that shows how well your twin knows you, based on what you actually accept.',
  },
  {
    id: 'verify',
    title: 'Verifiable replies',
    body: 'Approved replies are signed, so a recipient can check that a message really came from your twin and was approved by you.',
  },
  {
    id: 'voice',
    title: 'Voice and avatar, with consent',
    body: 'Optionally turn approved replies into voice or avatar clips. Both stay off until you explicitly consent.',
  },
]

export const MODES = [
  {
    name: 'Transparent',
    tagline: 'Best for creators and public figures',
    body: 'Replies are labeled as coming from your digital twin. Honesty that builds credibility.',
  },
  {
    name: 'Private',
    tagline: 'Best for consultants and executives',
    body: 'Replies read as you, because you approved every one of them.',
  },
]

export const TRUST = [
  { title: 'You approve every draft', body: 'There is no auto-send path. A reply goes out only after your decision.' },
  { title: 'One-tap pause', body: 'Stop all drafting instantly. A paused twin does not generate anything.' },
  { title: 'Sensitive messages go to you', body: 'Self-harm, medical, legal and financial requests are flagged for you instead of answered with a template.' },
  { title: 'Hostile text is not trusted', body: 'Messages that try to override your twin ("ignore your instructions") are flagged and never obeyed.' },
  { title: 'No invented facts', body: 'Drafts never make up prices, dates, links or promises. Questions get an honest "let me get back to you".' },
  { title: 'Full audit trail', body: 'Every approval, edit and rejection is logged. Connected account tokens are encrypted at rest.' },
]

export const FAQ = [
  {
    q: 'Does SELPH send messages on its own?',
    a: 'No. Every reply waits for your approval. You can approve, edit, reject or skip, and you can pause the twin at any time.',
  },
  {
    q: 'Which channels does it support?',
    a: 'Instagram DMs and Gmail. You connect your own accounts, and Instagram requires a Business account. More channels are planned but not available yet.',
  },
  {
    q: 'Do I need an AI provider key?',
    a: 'No. SELPH includes a built-in drafter that works with no key: it recognizes questions, thanks, meeting requests and business inquiries and matches your tone. For richer drafts, add a model key of your choice, or run a local model.',
  },
  {
    q: 'What happens to messages from people I never want automated?',
    a: 'Mark them as VIP. Their messages bypass the twin entirely and notify you directly.',
  },
  {
    q: 'Can I try it without connecting anything?',
    a: 'Yes. The dashboard has a "Simulate incoming message" panel, so you can watch your twin draft and approve a reply without any channel.',
  },
]
