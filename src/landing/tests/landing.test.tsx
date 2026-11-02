import React from 'react'
import { render, screen, within } from '@testing-library/react'
import Home from '../app/page'
import { SECTION_IDS } from '../components/sections'
import { FAQ, FEATURES, NAV_LINKS, SIGNUP_URL, TRUST } from '../components/content'

describe('Landing page', () => {
  it('has a single h1 and the core promise', () => {
    render(<Home />)
    const h1 = screen.getAllByRole('heading', { level: 1 })
    expect(h1).toHaveLength(1)
    expect(h1[0]).toHaveTextContent(/Sent only when you say so/)
  })

  it('every in-page anchor points at a real section', () => {
    const { container } = render(<Home />)
    const targets = Array.from(container.querySelectorAll('a[href^="#"]')).map((a) => a.getAttribute('href')!.slice(1))
    for (const id of targets) {
      expect(container.querySelector(`#${CSS.escape(id)}`)).not.toBeNull()
    }
    for (const id of SECTION_IDS) expect(container.querySelector(`#${id}`)).not.toBeNull()
    for (const link of NAV_LINKS) expect(link.href.startsWith('#')).toBe(true)
  })

  it('primary calls to action go to the signup page', () => {
    render(<Home />)
    const ctas = screen.getAllByRole('link', { name: /create your twin|get started/i })
    expect(ctas.length).toBeGreaterThanOrEqual(3)
    ctas.forEach((a) => expect(a).toHaveAttribute('href', SIGNUP_URL))
  })

  it('renders every feature, trust rule and FAQ entry', () => {
    render(<Home />)
    FEATURES.forEach((f) => expect(screen.getByRole('heading', { name: f.title })).toBeInTheDocument())
    TRUST.forEach((t) => expect(screen.getByRole('heading', { name: t.title })).toBeInTheDocument())
    FAQ.forEach((item) => expect(screen.getByText(item.q)).toBeInTheDocument())
  })

  it('uses landmarks and a skip link for accessibility', () => {
    render(<Home />)
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /skip to content/i })).toHaveAttribute('href', '#main')
  })

  it('does not make claims the product cannot back up', () => {
    const { container } = render(<Home />)
    const text = container.textContent || ''
    for (const banned of [/\$\d/, /per month/i, /free trial/i, /GDPR/i, /CCPA/i, /C2PA/i, /SOC ?2/i, /Twitter|WhatsApp|Slack|Discord/i, /auto-?send(s)? (for|messages)/i]) {
      expect(text).not.toMatch(banned)
    }
    expect(within(container).getAllByText(/Instagram DMs and Gmail/).length).toBeGreaterThanOrEqual(1)
  })

  it('every section heading is associated with its section', () => {
    const { container } = render(<Home />)
    container.querySelectorAll('section[aria-labelledby]').forEach((s) => {
      const id = s.getAttribute('aria-labelledby')!
      expect(container.querySelector(`#${id}`)).not.toBeNull()
    })
  })
})
