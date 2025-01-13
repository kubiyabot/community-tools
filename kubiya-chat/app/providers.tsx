'use client';

import { type ReactNode } from 'react';
import { ConfigProvider } from "@/lib/config-context";

type Props = {
  children: ReactNode;
};

export function Providers({ children }: Props) {
  return (
    <ConfigProvider>
      {children}
    </ConfigProvider>
  );
} 