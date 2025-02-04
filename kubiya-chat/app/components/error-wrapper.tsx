'use client';

import { ErrorBoundary } from './ErrorBoundary';
import React from 'react';

export default function ErrorWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  return React.createElement(ErrorBoundary, { children });
} 