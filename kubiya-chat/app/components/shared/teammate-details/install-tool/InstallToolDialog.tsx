import * as React from 'react';
import {
  Dialog,
  DialogContent,
} from '@/app/components/ui/dialog';
import { DialogHeader } from './components/DialogHeader';
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { TeammateDetails } from '@/app/types/teammate';
import type { InstallationStep } from './types';
import { sourceFormSchema } from './schema';
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/app/components/ui/form';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Alert, AlertDescription } from '@/app/components/ui/alert';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import type { FormValues } from './schema';

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
  const handleClose = () => {
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent 
        className="max-w-6xl h-[800px] flex flex-col p-0 bg-slate-900 border border-slate-800"
      >
        <DialogHeader onClose={handleClose} />
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (
    values: FormValues,
    updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void
  ) => Promise<void>;
  teammate: TeammateDetails;
  initialValues?: Partial<FormValues>;
}

export function InstallToolForm({ 
  isOpen, 
  onClose, 
  onInstall, 
  teammate,
  initialValues 
}: InstallToolFormProps) {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [installationSteps, setInstallationSteps] = React.useState<InstallationStep[]>([
    {
      id: 'validate',
      status: 'pending',
      description: 'Validating configuration'
    },
    {
      id: 'prepare',
      status: 'pending',
      description: 'Preparing installation'
    },
    {
      id: 'install',
      status: 'pending',
      description: 'Installing tools'
    },
    {
      id: 'configure',
      status: 'pending',
      description: 'Configuring tools'
    }
  ]);

  const updateStepStatus = React.useCallback((
    stepId: string, 
    status: 'pending' | 'loading' | 'success' | 'error',
    error?: string
  ) => {
    setInstallationSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, status, error } : step
    ));
  }, []);

  const form = useForm<FormValues>({
    resolver: zodResolver(sourceFormSchema),
    defaultValues: initialValues || {
      name: "",
      url: "",
      runner: "automatic",
      dynamic_config: {} as Record<string, unknown>
    },
    mode: "onChange",
  });

  const handleSubmit = async (values: FormValues) => {
    try {
      // Validate required fields before submission
      if (!values.url.trim()) {
        setError("URL is required");
        form.setError("url", { message: "URL is required" });
        return;
      }

      if (!values.name.trim()) {
        setError("Name is required");
        form.setError("name", { message: "Name is required" });
        return;
      }

      setIsSubmitting(true);
      setError(null);
      
      try {
        await onInstall(values, updateStepStatus);
        onClose();
      } catch (installError: any) {
        // Handle installation error
        const errorMessage = installError?.message || 'Installation failed';
        const currentStep = installationSteps.find(step => step.status === 'loading');
        if (currentStep) {
          updateStepStatus(currentStep.id, 'error', errorMessage);
        }
        throw installError;
      }
    } catch (err: any) {
      // Handle API error response
      const apiError = err?.message || 'Failed to install tool';
      setError(apiError);
      
      // Set field-specific errors if they exist in the API response
      if (apiError.includes('url')) {
        form.setError("url", { message: apiError });
      } else if (apiError.includes('name')) {
        form.setError("name", { message: apiError });
      } else {
        form.setError("root", { message: apiError });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reset error when form changes
  React.useEffect(() => {
    const subscription = form.watch(() => {
      if (error) {
        setError(null);
      }
    });
    return () => subscription.unsubscribe();
  }, [form, error]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader onClose={onClose} />
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="Tool source name" 
                      {...field} 
                      onChange={(e) => {
                        field.onChange(e);
                        form.clearErrors("name");
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="Tool source URL" 
                      {...field} 
                      onChange={(e) => {
                        field.onChange(e);
                        form.clearErrors("url");
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button 
              type="submit" 
              disabled={isSubmitting || !form.formState.isValid}
              className="w-full"
            >
              {isSubmitting ? 'Installing from URL...' : 'Install Tools from URL'}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
} 