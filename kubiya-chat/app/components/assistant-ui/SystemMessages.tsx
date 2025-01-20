import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, X } from 'lucide-react';

interface SystemMessagesProps {
  messages: string[];
}

export const SystemMessages = ({ messages }: SystemMessagesProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const [dismissedCount, setDismissedCount] = useState(0);

  useEffect(() => {
    if (messages.length > dismissedCount) {
      setHasNewMessages(true);
      setIsExpanded(true); // Auto-expand when new messages arrive
    }
  }, [messages.length, dismissedCount]);

  const handleDismiss = () => {
    setDismissedCount(messages.length);
    setHasNewMessages(false);
  };

  // Don't render if no messages
  if (!messages || messages.length === 0) {
    return null;
  }

  // Format message to remove prefixes and clean up
  const formatMessage = (message: string) => {
    return message
      .replace(/^(WARNING:|ERROR:)\s*/i, '')
      .replace(/^data:\s*/i, '')
      .trim();
  };

  const messageCount = messages.length - dismissedCount;

  return (
    <div className="bg-[#1E293B] border border-[#334155] rounded-lg shadow-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-[#2D3B4E] transition-colors"
      >
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-medium text-white">
            System Messages
            {messageCount > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-amber-500 text-black text-xs rounded-full">
                {messageCount}
              </span>
            )}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-[#94A3B8]" />
        ) : (
          <ChevronDown className="h-4 w-4 text-[#94A3B8]" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-[#334155]">
          <div className="max-h-[calc(100vh-200px)] overflow-y-auto p-3 space-y-2">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`flex items-start space-x-2 p-2 rounded ${
                  index >= dismissedCount ? 'bg-[#2D3B4E]' : ''
                }`}
              >
                <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <span className="flex-1 text-sm text-[#E2E8F0] whitespace-pre-wrap">
                  {formatMessage(message)}
                </span>
              </div>
            ))}
          </div>
          {hasNewMessages && (
            <div className="border-t border-[#334155] p-2 flex justify-end bg-[#2D3B4E]">
              <button
                onClick={handleDismiss}
                className="flex items-center space-x-1 px-2 py-1 text-xs text-[#94A3B8] hover:text-white hover:bg-[#1E293B] rounded transition-colors"
              >
                <X className="h-3 w-3" />
                <span>Dismiss all</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}; 