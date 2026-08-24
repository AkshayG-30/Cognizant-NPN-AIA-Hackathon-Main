import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CarePath · Navigation Intelligence',
  description: 'Healthcare care-management decision support prototype for navigation opportunities.',
  generator: 'v0.app',
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#f4f8fa',
  userScalable: true,
}

import { Chatbot } from '@/components/Chatbot'

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="light bg-background">
      <body className="antialiased">
        {children}
        <Chatbot />
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
