"use client";

import { ReactNode } from "react";
import MyRuntimeProvider from "../MyRuntimeProvider";
import { ConfigProvider } from "@/lib/config-context";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider>
      <MyRuntimeProvider>{children}</MyRuntimeProvider>
    </ConfigProvider>
  );
} 