"use client";

import * as React from 'react';
import { Dialog, DialogContent } from "../../ui/dialog";
import { FormProvider } from 'react-hook-form';
import { useInstallTool } from './install-tool/hooks/useInstallTool';
import { ScrollArea } from "../../ui/scroll-area";
import { STEPS } from './install-tool/constants';
import { InstallToolProvider } from './install-tool/context';
import {
  DialogHeader,
  DialogFooter,
  StepContent,
  StepIndicator,
  InstallationProgress
} from './install-tool/components';
import type { InstallToolFormProps, UseInstallToolReturn } from './install-tool/types';

export function InstallToolForm({ isOpen, onClose, onInstall, teammate }: InstallToolFormProps) {
  const {
    formState,
    methods,
    currentStep,
    activeCategory,
    setActiveCategory,
    selectedTool,
    handleToolSelect,
    failedIcons,
    handleIconError,
    expandedTools,
    setExpandedTools,
    handleSubmit,
    goToNextStep,
    goToPreviousStep,
    canProceed,
    handleCommunityToolSelect,
    handleRefresh,
    renderStepContent,
    selectedTools,
    setSelectedTools,
    teammate: teammateState,
    setState,
    steps,
    setSteps,
    isLoading
  } = useInstallTool({ onInstall, teammate });

  // Prevent dialog from closing during installation
  const handleClose = () => {
    if (!formState.installation.isLoading) {
      onClose();
    }
  };

  // Show installation view when installing or when there are steps
  const showInstallationView = formState.installation.isLoading || 
    (formState.installation.data?.steps && formState.installation.data.steps.length > 0);

  const value: UseInstallToolReturn = {
    formState,
    methods,
    currentStep,
    activeCategory,
    setActiveCategory,
    selectedTool,
    handleToolSelect,
    failedIcons,
    handleIconError,
    expandedTools,
    setExpandedTools,
    handleCommunityToolSelect,
    handleRefresh,
    handleSubmit,
    goToNextStep,
    goToPreviousStep,
    selectedTools,
    setSelectedTools,
    canProceed,
    renderStepContent,
    teammate: teammateState,
    setState,
    steps: formState.installation.data?.steps || [],
    setSteps: (steps) => setState(prev => ({ ...prev, installation: { ...prev.installation, data: { ...prev.installation.data, steps } } })),
    isLoading: formState.installation.isLoading
  };

  // Reset installation state when dialog is closed
  React.useEffect(() => {
    if (!isOpen) {
      setState(prev => ({
        ...prev,
        installation: {
          isLoading: false,
          error: null,
          data: null
        }
      }));
    }
  }, [isOpen, setState]);

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl h-[800px] flex flex-col p-0 bg-slate-900 border border-slate-800">
        {showInstallationView ? (
          <div className="flex-1 flex flex-col">
            <DialogHeader onClose={handleClose} />
            <div className="flex-1 p-6 overflow-auto">
              <InstallationProgress 
                steps={formState.installation.data?.steps || []} 
              />
            </div>
          </div>
        ) : (
          <InstallToolProvider
            teammate={teammate}
            initialState={formState}
            value={{
              formState,
              methods,
              currentStep,
              activeCategory,
              setActiveCategory,
              selectedTool,
              handleToolSelect,
              failedIcons,
              handleIconError,
              expandedTools,
              setExpandedTools,
              handleCommunityToolSelect,
              handleRefresh,
              handleSubmit,
              goToNextStep,
              goToPreviousStep,
              selectedTools,
              setSelectedTools,
              canProceed,
              renderStepContent,
              teammate: teammateState,
              setState,
              steps: formState.installation.data?.steps || [],
              setSteps: (steps) => setState(prev => ({ ...prev, installation: { ...prev.installation, data: { ...prev.installation.data, steps } } })),
              isLoading: formState.installation.isLoading
            }}
          >
            <FormProvider {...methods}>
              <DialogHeader onClose={handleClose} />
              
              <div className="flex-1 flex flex-col min-h-0">
                <StepIndicator steps={STEPS} currentStep={currentStep} />
                
                <ScrollArea className="flex-1">
                  <div className="p-6">
                    <StepContent />
                  </div>
                </ScrollArea>

                <DialogFooter 
                  currentStep={currentStep}
                  onClose={handleClose}
                  formState={formState}
                  methods={methods}
                  onBack={goToPreviousStep}
                  onNext={goToNextStep}
                  onSubmit={handleSubmit}
                  canProceed={canProceed && !formState.installation.isLoading}
                />
              </div>
            </FormProvider>
          </InstallToolProvider>
        )}
      </DialogContent>
    </Dialog>
  );
} 