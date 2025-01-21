import './globals.css';
import { GeistSans } from 'geist/font/sans';
import { Metadata } from 'next';
import { ErrorBoundary } from '@/app/components/ErrorBoundary';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import { ConfigProvider } from '@/lib/config-context';
import ClientProvider from './components/ClientProvider';
import { SessionHandler } from './components/SessionHandler';

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
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${GeistSans.className} h-full bg-[#0A0F1E] text-white antialiased`}>
        <ErrorBoundary>
          <UserProvider>
            <ConfigProvider>
              <ClientProvider>
                <SessionHandler />
                {children}
              </ClientProvider>
            </ConfigProvider>
          </UserProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
