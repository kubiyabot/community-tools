"use client";

import { ReactNode } from "react";
import MyRuntimeProvider from "../MyRuntimeProvider";

export function Providers({ children }: { children: ReactNode }) {
  return <MyRuntimeProvider>{children}</MyRuntimeProvider>;
} 