import type { Metadata } from "next";
import { GeistSans } from 'geist/font';
import { Providers } from "./components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kubiya Chat",
  description: "Chat with your Kubiya teammates",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <body className={`${GeistSans.className} h-full bg-[#0A0F1E] text-white antialiased`} suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
