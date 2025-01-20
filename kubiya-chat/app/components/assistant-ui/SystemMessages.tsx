import React from 'react';

interface SystemMessagesProps {
  messages: string[];
}

export const SystemMessages: React.FC<SystemMessagesProps> = ({ messages }) => {
  return (
    <div className="system-messages-container">
      {messages.map((message, index) => (
        <div key={index} className="system-message">
          {message}
        </div>
      ))}
    </div>
  );
}; 