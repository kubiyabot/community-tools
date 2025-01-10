'use client'

import React from 'react';

interface ToolExecutionUIProps {
  toolName: string
  args: any
  status?: any
  result?: any
}

export const ToolUI = ({ children }: { children?: React.ReactNode }) => {
  return (
    <div className="tool-ui-container">
      {children}
    </div>
  );
};

export const SystemMessageUI = ({ message }: { message: string }) => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center space-x-3">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-medium text-blue-900">System Message</h3>
          <p className="mt-1 text-sm text-blue-700">{message}</p>
        </div>
      </div>
    </div>
  );
};

export const ToolExecutionUI: React.FC<ToolExecutionUIProps> = ({ toolName, args, status, result }) => {
  return (
    <div className="bg-gray-100 p-4 rounded-lg">
      <div className="font-bold mb-2">Tool Execution: {toolName}</div>
      <div className="mb-4">
        <div className="font-semibold">Arguments:</div>
        <pre className="bg-white p-2 rounded">{JSON.stringify(args, null, 2)}</pre>
      </div>
      {status && (
        <div className="mb-4">
          <div className="font-semibold">Status:</div>
          <pre className="bg-white p-2 rounded">{JSON.stringify(status, null, 2)}</pre>
        </div>
      )}
      {result && (
        <div>
          <div className="font-semibold">Result:</div>
          <pre className="bg-white p-2 rounded">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};