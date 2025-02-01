"use client";

import { useAssistantToolUI } from "@assistant-ui/react";
import { useUser } from '@auth0/nextjs-auth0/client';
import { LoginButton } from './LoginButton';
import { GenericToolUI } from './assistant-ui/ToolUI';
import { Chat } from './assistant-ui/Chat';
import { useTeammateContext } from '../MyRuntimeProvider';
import { useConfig } from '../../lib/config-context';
import { TeammateSelector } from './TeammateSelector';
import { UserProfileButton } from './UserProfileButton';

export default function MyAssistant() {
  const { user } = useUser();
  const { selectedTeammate, teammates, setSelectedTeammate } = useTeammateContext();
  const { clearApiKey } = useConfig();

  // Register the generic tool UI handler for all tools
  useAssistantToolUI({
    toolName: "*",
    render: (props) => (
      <GenericToolUI 
        {...props}
        key={`${props.args.id || ''}_${Date.now()}`} // Ensure unique key for each render
      />
    )
  });

  // Register specific tool handlers for better type safety
  useAssistantToolUI({
    toolName: "tool_init",
    render: GenericToolUI
  });

  useAssistantToolUI({
    toolName: "tool_output",
    render: GenericToolUI
  });

  return (
    <div className="flex h-screen bg-[#0A0F1E] overflow-hidden">
      {/* Sidebar */}
      <div className="w-72 flex-shrink-0 flex flex-col bg-[#1E293B] border-r border-[#2D3B4E] shadow-xl">
        {/* Logo Header */}
        <div className="flex-shrink-0 p-3 border-b border-[#2D3B4E] bg-[#1A1F2E]">
          <div className="flex items-center gap-2.5">
            <img
              src="https://media.licdn.com/dms/image/v2/D560BAQG9BrF3G3A3Aw/company-logo_200_200/company-logo_200_200/0/1726534282425/kubiya_logo?e=2147483647&v=beta&t=2BT_nUHPJVNqbU2JjeU5XEWF6y2kn78xr-WZQcYVq5s"
              alt="Kubiya Logo"
              className="w-8 h-8 rounded-md"
            />
            <h1 className="text-white font-semibold text-sm tracking-wide">Kubiya Chat</h1>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Teammate Selector */}
          <TeammateSelector
            onSelect={setSelectedTeammate}
            selectedId={selectedTeammate}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="h-14 border-b border-[#2D3B4E] bg-[#1A1F2E] flex items-center justify-between px-4 flex-shrink-0 shadow-md">
          <div className="flex items-center space-x-3">
            <h2 className="text-white font-medium text-sm">
              {teammates.find(t => t.uuid === selectedTeammate)?.name || 'Select a Teammate'}
            </h2>
          </div>
          <div className="flex items-center space-x-3">
            <UserProfileButton 
              onLogout={() => {
                clearApiKey();
                window.location.href = '/api/auth/logout';
              }}
            />
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 min-h-0 relative">
          <Chat />

          {/* Footer Logo */}
          <div className="absolute bottom-3 left-3 opacity-20 transition-opacity duration-200 hover:opacity-40">
            <img
              src="https://media.licdn.com/dms/image/v2/D560BAQG9BrF3G3A3Aw/company-logo_200_200/company-logo_200_200/0/1726534282425/kubiya_logo?e=2147483647&v=beta&t=2BT_nUHPJVNqbU2JjeU5XEWF6y2kn78xr-WZQcYVq5s"
              alt="Kubiya Logo"
              className="w-10 h-10"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
