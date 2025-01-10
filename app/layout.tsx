import React from 'react'
import { RuntimeProvider } from './components/RuntimeProvider'
import { SSEHandler } from './components/SSEHandler'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Kubiya Chat',
  description: 'Kubiya Chat Interface',
  viewport: 'width=device-width, initial-scale=1',
  robots: 'noindex,nofollow'
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body suppressHydrationWarning>
        <RuntimeProvider>
          <SSEHandler />
          {children}
        </RuntimeProvider>
      </body>
    </html>
  )
} 