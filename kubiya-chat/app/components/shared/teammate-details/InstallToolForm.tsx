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
import type { InstallToolFormProps } from './install-tool/types';

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
    handleRefresh
  } = useInstallTool({ onInstall, teammate });

  const contextValue = React.useMemo(() => ({
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
    handleRefresh
  }), [
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
    handleRefresh
  ]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[800px] flex flex-col p-0 bg-slate-900 border border-slate-800">
        {formState.installation.isLoading ? (
          <div className="p-6 flex-1 flex flex-col items-center justify-center">
            <InstallationProgress />
          </div>
        ) : (
          <InstallToolProvider value={contextValue}>
            <FormProvider {...methods}>
              <DialogHeader onClose={onClose} />
              
              <div className="flex-1 flex flex-col min-h-0">
                <StepIndicator steps={STEPS} currentStep={currentStep} />
                
                <ScrollArea className="flex-1">
                  <div className="p-6">
                    <StepContent />
                  </div>
                </ScrollArea>

                <DialogFooter 
                  currentStep={currentStep}
                  onClose={onClose}
                  formState={formState}
                  methods={methods}
                  onBack={goToPreviousStep}
                  onNext={goToNextStep}
                  onSubmit={handleSubmit}
                  canProceed={canProceed}
                />
              </div>
            </FormProvider>
          </InstallToolProvider>
        )}
      </DialogContent>
    </Dialog>
  );
} 