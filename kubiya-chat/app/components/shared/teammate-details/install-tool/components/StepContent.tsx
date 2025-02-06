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
      case 'configure':
        return <CustomSourceTab methods={methods} />;
      case 'install':
        return (
          <PreviewStep 
            selectedTool={selectedTool || {
              name: methods.getValues('name'),
              description: 'Custom source',
              tools: formState.preview.data?.tools || [],
              type: 'custom'
            }} 
            isLoading={isLoading} 
          />
        );
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