import React from 'react';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Button } from '../ui/button';
import { Search, Trello, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

// Checkbox component
interface CheckboxProps {
  id: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
}

function Checkbox({ id, checked, onCheckedChange, className }: CheckboxProps) {
  return (
    <div
      role="checkbox"
      aria-checked={checked}
      id={id}
      className={cn(
        "h-4 w-4 rounded border border-[#2D3B4E] transition-colors cursor-pointer",
        checked ? "bg-blue-500 border-blue-500" : "bg-[#1E293B]",
        className
      )}
      onClick={() => onCheckedChange(!checked)}
    >
      {checked && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-3 w-3 text-white"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      )}
    </div>
  );
}

interface JiraBoard {
  id: string;
  name: string;
  key: string;
}

interface JiraTicket {
  id: string;
  key: string;
  summary: string;
  status: string;
  priority: string;
}

interface JiraTransition {
  id: string;
  name: string;
  to: {
    name: string;
    statusCategory: {
      colorName: string;
    };
  };
}

interface JiraFlowProps {
  selectedBoard: string;
  onBoardSelect: (boardId: string) => void;
  selectedTicket: string;
  onTicketSelect: (ticketId: string) => void;
  additionalContext: string;
  onContextChange: (context: string) => void;
  shouldComment: boolean;
  onCommentChange: (shouldComment: boolean) => void;
  shouldTransition: boolean;
  onTransitionChange: (shouldTransition: boolean) => void;
  selectedTransition: string;
  onTransitionSelect: (transitionId: string) => void;
  ticketsPage: number;
  onPageChange: (page: number) => void;
  ticketSearch: string;
  onSearchChange: (search: string) => void;
  boards: JiraBoard[];
  tickets: JiraTicket[];
  transitions: JiraTransition[];
  isLoadingBoards?: boolean;
  isLoadingTickets?: boolean;
  isLoadingTransitions?: boolean;
  totalPages?: number;
}

export function JiraFlow({
  selectedBoard,
  onBoardSelect,
  selectedTicket,
  onTicketSelect,
  additionalContext,
  onContextChange,
  shouldComment,
  onCommentChange,
  shouldTransition,
  onTransitionChange,
  selectedTransition,
  onTransitionSelect,
  ticketsPage,
  onPageChange,
  ticketSearch,
  onSearchChange,
  boards,
  tickets,
  transitions,
  isLoadingBoards,
  isLoadingTickets,
  isLoadingTransitions,
  totalPages = 1
}: JiraFlowProps) {
  return (
    <div className="space-y-6">
      {/* Board Selection */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Trello className="h-5 w-5 text-blue-400" />
          <h3 className="text-base font-medium text-slate-200">Select Board</h3>
        </div>
        <Select value={selectedBoard} onValueChange={onBoardSelect}>
          <SelectTrigger className="bg-[#1E293B] border-[#2D3B4E] h-12">
            <SelectValue placeholder="Choose a board" />
          </SelectTrigger>
          <SelectContent>
            {boards.map((board) => (
              <SelectItem key={board.id} value={board.id}>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-200">{board.name}</span>
                  <span className="text-xs text-slate-400">({board.key})</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Ticket Selection */}
      {selectedBoard && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-medium text-slate-200">Select Ticket</h3>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search tickets..."
                value={ticketSearch}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-9 bg-[#1E293B] border-[#2D3B4E] h-9"
              />
            </div>
          </div>

          <div className="space-y-2">
            {tickets.map((ticket) => (
              <div
                key={ticket.id}
                onClick={() => onTicketSelect(ticket.id)}
                className={cn(
                  "p-4 rounded-lg border cursor-pointer transition-all",
                  "hover:bg-blue-500/5 hover:border-blue-500/30",
                  selectedTicket === ticket.id
                    ? "bg-blue-500/10 border-blue-500/30"
                    : "bg-[#1E293B] border-[#2D3B4E]"
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-200">{ticket.key}</span>
                      <span className="text-xs text-slate-400">{ticket.status}</span>
                    </div>
                    <p className="text-sm text-slate-300">{ticket.summary}</p>
                  </div>
                  <span className={cn(
                    "text-xs px-2 py-1 rounded-full",
                    ticket.priority === 'High' && "bg-red-500/10 text-red-400",
                    ticket.priority === 'Medium' && "bg-yellow-500/10 text-yellow-400",
                    ticket.priority === 'Low' && "bg-green-500/10 text-green-400"
                  )}>
                    {ticket.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">
              Page {ticketsPage} of {totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(ticketsPage - 1)}
                disabled={ticketsPage === 1}
                className="bg-[#1E293B] border-[#2D3B4E]"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(ticketsPage + 1)}
                disabled={ticketsPage === totalPages}
                className="bg-[#1E293B] border-[#2D3B4E]"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Additional Context */}
      {selectedTicket && (
        <div className="space-y-4">
          <h3 className="text-base font-medium text-slate-200">Additional Context</h3>
          <textarea
            placeholder="Add any additional context or instructions..."
            value={additionalContext}
            onChange={(e) => onContextChange(e.target.value)}
            className={cn(
              "w-full h-32 bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-3",
              "text-sm text-slate-200 resize-none",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/30"
            )}
          />
        </div>
      )}

      {/* Actions */}
      {selectedTicket && (
        <div className="space-y-4">
          <h3 className="text-base font-medium text-slate-200">Actions</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Checkbox
                id="comment"
                checked={shouldComment}
                onCheckedChange={(checked) => onCommentChange(checked as boolean)}
              />
              <label htmlFor="comment" className="text-sm text-slate-200 cursor-pointer">
                Add comment with task results
              </label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="transition"
                checked={shouldTransition}
                onCheckedChange={(checked) => onTransitionChange(checked as boolean)}
              />
              <label htmlFor="transition" className="text-sm text-slate-200 cursor-pointer">
                Transition ticket after completion
              </label>
            </div>
          </div>

          {shouldTransition && (
            <div className="space-y-2">
              <Select value={selectedTransition} onValueChange={onTransitionSelect}>
                <SelectTrigger className="bg-[#1E293B] border-[#2D3B4E] h-10">
                  <SelectValue placeholder="Select transition" />
                </SelectTrigger>
                <SelectContent>
                  {transitions.map((transition) => (
                    <SelectItem key={transition.id} value={transition.id}>
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "w-2 h-2 rounded-full",
                          transition.to.statusCategory.colorName === 'blue-gray' && "bg-slate-400",
                          transition.to.statusCategory.colorName === 'yellow' && "bg-yellow-400",
                          transition.to.statusCategory.colorName === 'green' && "bg-green-400"
                        )} />
                        <span className="text-sm text-slate-200">{transition.name}</span>
                        <span className="text-xs text-slate-400">→ {transition.to.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 