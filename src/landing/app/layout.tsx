import type { Metadata } from 'next'
import './globals.css'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

export const metadata: Metadata = {
  title: 'SELPH — Your Digital Twin, Always Approved by You',
  description:
    'SELPH drafts replies in your voice across Instagram DMs and Gmail. You approve every message before it is sent.',
  metadataBase: new URL(APP_URL),
  openGraph: {
    title: 'SELPH — Your Digital Twin',
    description: 'Replies in your voice. Nothing sends without your tap.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body">{children}</body>
    </html>
  )
}
