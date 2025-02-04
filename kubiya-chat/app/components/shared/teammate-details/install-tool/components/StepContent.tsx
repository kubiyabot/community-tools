import * as React from 'react';
import { useInstallToolContext } from '../context';
import { CustomSourceTab } from './CustomSourceTab';
import { SelectStep, type SelectStepProps } from './SelectStep';
import { PreviewStep } from './PreviewStep';
import { ConfigureStep } from './ConfigureStep';
import type { FormState } from '../types';

export function StepContent() {
  const { 
    currentStep,
    methods,
    selectedTool,
    formState,
    handleToolSelect,
    failedIcons,
    handleIconError,
    expandedTools,
    setExpandedTools,
    handleRefresh,
    handleCommunityToolSelect,
    isLoading,
    isInstallationComplete
  } = useInstallToolContext();

  const renderStep = () => {
    switch (currentStep) {
      case 'source':
        return <CustomSourceTab methods={methods} />;
      case 'select':
        const selectProps: SelectStepProps = {
          formState: formState as FormState,
          onToolSelect: handleCommunityToolSelect,
          onRefresh: handleRefresh,
          failedIcons,
          onIconError: handleIconError,
          expandedTools,
          setExpandedTools
        };
        return <SelectStep {...selectProps} />;
      case 'preview':
        return <PreviewStep selectedTool={selectedTool} isLoading={isLoading} />;
      case 'configure':
        return <ConfigureStep isInstallationComplete={isInstallationComplete} />;
      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      {renderStep()}
    </div>
  );
} 