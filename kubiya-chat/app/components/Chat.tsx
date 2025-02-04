"use client";

import React, { useState, useCallback, useMemo, lazy, Suspense } from 'react';
import { ChatMessages } from './assistant-ui/ChatMessages';
import { useTeammateContext } from '../MyRuntimeProvider';
import { toast } from './ui/use-toast';

// Lazy load modals
const TaskSchedulingModal = lazy(() => import('./TaskSchedulingModal').then(mod => ({ default: mod.TaskSchedulingModal })));

interface Teammate {
  uuid: string;
  name?: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
}

interface ScheduledTaskData {
  task_type: string;
  scheduled_time: string;
  channel_id: string;
  parameters: {
    message_text: string;
    selected_agent: string;
    selected_agent_name: string;
    cron_string: string;
    context: Record<string, any>;
  };
}

interface ScheduleTaskPayload {
  schedule_time: string;
  channel_id: string;
  task_description: string;
  selected_agent: string;
  cron_string: string;
}

interface ScheduleTaskResult {
  task_id: string;
  task_uuid: string;
}

export function Chat() {
  const [showTaskModal, setShowTaskModal] = useState(false);
  const { selectedTeammate } = useTeammateContext();
  const [messages, setMessages] = useState<any[]>([]);

  // Memoize message creation function
  const createScheduledTaskMessage = useCallback((taskData: ScheduledTaskData) => {
    const scheduledTime = new Date(taskData.scheduled_time);
    const isRecurring = taskData.parameters.cron_string;
    
    let scheduleInfo = `Scheduled for ${scheduledTime.toLocaleString()}`;
    if (isRecurring) {
      scheduleInfo += ` (Recurring)`;
    }

    return {
      id: `scheduled-task-${Date.now()}`,
      role: 'system',
      content: [{
        type: 'text',
        text: `✅ Task Scheduled Successfully\n\n🎯 Task: ${taskData.parameters.message_text}\n⏰ ${scheduleInfo}\n📍 Channel: ${taskData.channel_id}\n🤖 Teammate: ${taskData.parameters.selected_agent_name}`
      }],
      metadata: {
        custom: {
          isSystemMessage: true,
          type: 'scheduled-task'
        }
      },
      createdAt: new Date()
    };
  }, []);

  const addMessage = useCallback((message: any) => {
    setMessages(prev => [...prev, message]);
  }, []);

  // Memoize schedule task handler
  const handleScheduleTask = useCallback(async (data: ScheduleTaskPayload): Promise<ScheduleTaskResult> => {
    try {
      const taskData = {
        task_type: 'chat_activity',
        scheduled_time: data.schedule_time,
        channel_id: data.channel_id,
        parameters: {
          message_text: data.task_description,
          selected_agent: data.selected_agent,
          selected_agent_name: selectedTeammateObj?.name || data.selected_agent,
          cron_string: data.cron_string || '',
          context: {}
        }
      };

      const response = await fetch('/api/scheduled_tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(taskData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to schedule task' }));
        throw new Error(errorData.error || 'Failed to schedule task');
      }

      const result = await response.json();
      
      const confirmationMessage = createScheduledTaskMessage({
        ...taskData,
        parameters: {
          ...taskData.parameters,
          selected_agent_name: selectedTeammateObj?.name || data.selected_agent
        }
      });
      addMessage(confirmationMessage);

      return {
        task_id: result.task_id,
        task_uuid: result.task_uuid
      };
    } catch (error) {
      console.error('Failed to schedule task:', error);
      throw error;
    }
  }, [selectedTeammate, createScheduledTaskMessage, addMessage]);

  // Memoize teammate object
  const selectedTeammateObj = useMemo(() => typeof selectedTeammate === 'string' ? {
    uuid: selectedTeammate,
  } as Teammate : selectedTeammate, [selectedTeammate]);

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[#0F1117] to-[#1A1F2E] relative">
      {/* Background Pattern */}
      <div 
        className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]"
        style={{ backgroundSize: '30px 30px' }}
      />

      {/* Chat Container */}
      <div className="relative flex flex-col h-full">
        {/* Main Chat Area */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full relative flex flex-col">
            <ChatMessages
              messages={messages}
              isCollectingSystemMessages={false}
              teammate={selectedTeammateObj}
              onScheduleTask={() => setShowTaskModal(true)}
            />
          </div>
        </div>

        {/* Modals */}
        {showTaskModal && (
          <Suspense fallback={null}>
            <TaskSchedulingModal
              isOpen={showTaskModal}
              onClose={() => setShowTaskModal(false)}
              teammate={selectedTeammateObj}
              onSchedule={handleScheduleTask}
            />
          </Suspense>
        )}
      </div>
    </div>
  );
} 