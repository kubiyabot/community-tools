import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Calendar } from '../ui/calendar';
import { format, addHours, addDays } from 'date-fns';
import { CalendarClock, Clock, CalendarDays, CalendarRange } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScheduleOption {
  label: string;
  icon: React.ComponentType;
  value: Date;
  description: string;
}

const scheduleOptions: ScheduleOption[] = [
  { 
    label: "In 1 hour", 
    icon: Clock, 
    value: addHours(new Date(), 1),
    description: format(addHours(new Date(), 1), 'h:mm a')
  },
  { 
    label: "Tomorrow 9 AM", 
    icon: CalendarDays, 
    value: (() => {
      const tomorrow = addDays(new Date(), 1);
      tomorrow.setHours(9, 0, 0, 0);
      return tomorrow;
    })(),
    description: "Tomorrow at 9:00 AM"
  },
  { 
    label: "Next Monday 10 AM", 
    icon: CalendarRange, 
    value: (() => {
      const today = new Date();
      const nextMonday = addDays(today, (8 - today.getDay()) % 7 || 7);
      nextMonday.setHours(10, 0, 0, 0);
      return nextMonday;
    })(),
    description: format((() => {
      const today = new Date();
      const nextMonday = addDays(today, (8 - today.getDay()) % 7 || 7);
      nextMonday.setHours(10, 0, 0, 0);
      return nextMonday;
    })(), 'MMM d, h:mm a')
  }
];

interface ScheduleSectionProps {
  date: Date;
  onDateChange: (date: Date) => void;
  scheduleType: 'quick' | 'custom';
  onScheduleTypeChange: (type: 'quick' | 'custom') => void;
  repeatOption: string;
  onRepeatOptionChange: (option: string) => void;
  customTime: string;
  onCustomTimeChange: (time: string) => void;
}

export function ScheduleSection({
  date,
  onDateChange,
  scheduleType,
  onScheduleTypeChange,
  repeatOption,
  onRepeatOptionChange,
  customTime,
  onCustomTimeChange
}: ScheduleSectionProps) {
  const handleDateSelect = (newDate: Date | undefined) => {
    if (newDate) {
      onDateChange(newDate);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-purple-400" />
          <h3 className="text-base font-medium text-slate-200">When should it run?</h3>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onScheduleTypeChange('quick')}
            className={cn(
              "bg-[#1E293B] border-[#2D3B4E] hover:bg-purple-500/10",
              scheduleType === 'quick' && "bg-purple-500/10 border-purple-500/30"
            )}
          >
            Quick Options
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onScheduleTypeChange('custom')}
            className={cn(
              "bg-[#1E293B] border-[#2D3B4E] hover:bg-purple-500/10",
              scheduleType === 'custom' && "bg-purple-500/10 border-purple-500/30"
            )}
          >
            Custom Schedule
          </Button>
        </div>
      </div>

      {scheduleType === 'quick' ? (
        <div className="grid grid-cols-3 gap-3">
          {scheduleOptions.map((option) => (
            <Button
              key={option.label}
              variant="outline"
              className={cn(
                "flex items-center gap-3 px-4 py-3 h-auto",
                "bg-[#1E293B] hover:bg-purple-500/10",
                "border-[#2D3B4E] hover:border-purple-500/30",
                date.getTime() === option.value.getTime() && "bg-purple-500/10 border-purple-500/30"
              )}
              onClick={() => onDateChange(option.value)}
            >
              <div className="flex flex-col items-start gap-3">
                <div className="text-sm font-medium text-slate-200">{option.label}</div>
                <span className="text-xs text-slate-400">{option.description}</span>
              </div>
            </Button>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-[1fr,auto] gap-4">
          <Calendar
            mode="single"
            selected={date}
            onSelect={handleDateSelect}
            className="rounded-lg border border-[#2D3B4E] bg-[#1E293B] p-3"
          />
          <div className="space-y-4">
            {/* Time picker */}
            <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
              <h4 className="text-sm font-medium text-slate-200 mb-3">Time</h4>
              <Input
                type="time"
                value={customTime}
                onChange={(e) => {
                  onCustomTimeChange(e.target.value);
                  const [hours, minutes] = e.target.value.split(':');
                  const newDate = new Date(date);
                  newDate.setHours(parseInt(hours), parseInt(minutes));
                  onDateChange(newDate);
                }}
                className="bg-[#1E293B] border-[#2D3B4E] h-10"
              />
            </div>

            {/* Repeat options */}
            <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
              <h4 className="text-sm font-medium text-slate-200 mb-3">Repeat</h4>
              <Select value={repeatOption} onValueChange={onRepeatOptionChange}>
                <SelectTrigger className="bg-[#1E293B] border-[#2D3B4E] h-10">
                  <SelectValue placeholder="Choose frequency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="never">Never</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Selected schedule summary */}
            <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
              <h4 className="text-sm font-medium text-slate-200 mb-2">Selected Schedule:</h4>
              <p className="text-sm text-slate-400">
                {format(date, 'MMMM d')} at {format(date, 'h:mm a')}
              </p>
              {repeatOption !== 'never' && (
                <p className="text-sm text-purple-400 mt-1">Repeats {repeatOption}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 