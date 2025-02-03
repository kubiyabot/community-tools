import * as React from 'react';
import {
  Dialog,
  DialogContent,
} from '@/app/components/ui/dialog';
import { DialogHeader } from './components/DialogHeader';
// ... other imports

interface InstallToolDialogProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export function InstallToolDialog({ 
  isOpen, 
  onClose,
  children 
}: InstallToolDialogProps) {
  // Add handler to clear state when dialog closes
  const handleClose = () => {
    // Clear any stored state here
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl h-[800px] flex flex-col p-0 bg-slate-900 border border-slate-800">
        <DialogHeader onClose={handleClose} />
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </DialogContent>
    </Dialog>
  );
} 