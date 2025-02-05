import './globals.css';
import { GeistSans } from 'geist/font/sans';
import { Metadata } from 'next';
import { Toaster } from "sonner";
import { SpeedInsights } from '@vercel/speed-insights/next';
import { Analytics } from '@vercel/analytics/react';
import type { ReactNode } from 'react';
import { Providers } from './providers/Providers';

export const metadata: Metadata = {
  title: 'Kubiya Chat',
  description: 'Chat with your Kubiya teammates',
  icons: {
    icon: [
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' }
    ],
    shortcut: '/favicon-32x32.png',
    apple: '/favicon-32x32.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}): JSX.Element {
  return (
    <html lang="en" className="h-full">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@4.5.0/index.css"
        />
      </head>
      <body className={`${GeistSans.className} h-full bg-[#0A0F1E] text-white antialiased`}>
        <Providers>
          {children}
          <Toaster />
          <SpeedInsights />
          <Analytics />
        </Providers>
      </body>
    </html>
  );
}
