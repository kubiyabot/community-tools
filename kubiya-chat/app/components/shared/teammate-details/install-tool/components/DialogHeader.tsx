import * as React from 'react';
import { X, PackageOpen } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import {
  DialogHeader as BaseDialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/app/components/ui/dialog";
import { styles } from '../styles';

interface DialogHeaderProps {
  onClose: () => void;
}

export function DialogHeader({ onClose }: DialogHeaderProps) {
  return (
    <BaseDialogHeader className={styles.dialog.header}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
            <PackageOpen className="h-6 w-6 text-purple-400" />
          </div>
          <div>
            <DialogTitle className={styles.text.primary + " text-xl font-semibold"}>
              Install Tools
            </DialogTitle>
            <DialogDescription className={styles.text.secondary + " mt-1"}>
              Add tools to your teammate from a Git repository or choose from our community tools.
            </DialogDescription>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className={styles.buttons.ghost}
          onClick={onClose}
        >
          <X className="h-5 w-5" />
        </Button>
      </div>
    </BaseDialogHeader>
  );
} 