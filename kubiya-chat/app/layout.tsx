import type { Metadata } from "next";
import { GeistSans } from 'geist/font';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import { ConfigProvider } from "@/lib/config-context";
import MyRuntimeProvider from "@/app/MyRuntimeProvider";
import "./globals.css";
import { ErrorBoundary } from '@/components/ErrorBoundary';

export const metadata: Metadata = {
  title: "Kubiya Chat",
  description: "Chat with your Kubiya teammates",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${GeistSans.className} h-full bg-[#0A0F1E] text-white antialiased`}>
        <ErrorBoundary>
          <UserProvider>
            <ConfigProvider>
              <MyRuntimeProvider>
                {children}
              </MyRuntimeProvider>
            </ConfigProvider>
          </UserProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
