'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface SupportModalProps {
  isOpen: boolean;
  onCloseAction: () => void;
}

export function SupportModal({ isOpen, onCloseAction }: SupportModalProps) {
  const [currentStep, setCurrentStep] = useState<'select' | 'preview' | 'configure'>('select');
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setCurrentStep('select');
      setSelectedOption(null);
    }
  }, [isOpen]);

  const supportOptions = [
    {
      title: 'Documentation',
      description: 'Browse our comprehensive documentation',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ),
      link: 'https://docs.kubiya.ai',
      color: 'bg-gray-50 dark:bg-gray-800',
      hoverColor: 'hover:bg-gray-100 dark:hover:bg-gray-700'
    },
    {
      title: 'Community Tools',
      description: 'Explore our community tools repository',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ),
      link: 'https://github.com/kubiyabot/community-tools/tree/main/terraform_module_tools',
      color: 'bg-gray-50 dark:bg-gray-800',
      hoverColor: 'hover:bg-gray-100 dark:hover:bg-gray-700'
    }
  ];

  const handleOptionClick = (option: string) => {
    setSelectedOption(option);
    setCurrentStep('preview');
  };

  const handleNext = () => {
    if (currentStep === 'preview') {
      setCurrentStep('configure');
    }
  };

  const handleBack = () => {
    if (currentStep === 'configure') {
      setCurrentStep('preview');
    } else if (currentStep === 'preview') {
      setCurrentStep('select');
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'select':
        return (
          <div className="p-6 space-y-4">
            {supportOptions.map((option, index) => (
              <motion.button
                key={option.title}
                onClick={() => handleOptionClick(option.title)}
                className={`w-full flex items-center space-x-4 p-4 rounded-lg ${option.color} ${option.hoverColor} transition-all duration-200 group cursor-pointer border border-gray-200 dark:border-gray-700`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex-shrink-0 p-2 rounded-full bg-primary/10 text-primary">
                  {option.icon}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {option.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {option.description}
                  </p>
                </div>
                <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-400" viewBox="0 0 20 20" fill="none" stroke="currentColor">
                  <path d="M5 10h10m0 0l-4-4m4 4l-4 4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </motion.button>
            ))}
          </div>
        );
      case 'preview':
        const selectedOptionData = supportOptions.find(opt => opt.title === selectedOption);
        return (
          <div className="p-6 space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {selectedOption}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                You will be redirected to {selectedOptionData?.link}
              </p>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={handleBack}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              >
                Back
              </button>
              <a
                href={selectedOptionData?.link}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
                onClick={onCloseAction}
              >
                Continue
              </a>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCloseAction}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100]"
          />
          
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed left-1/2 top-[30%] -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-[101] px-4"
          >
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-800">
              {/* Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <svg className="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Need Help?</h2>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Choose your preferred support option</p>
                    </div>
                  </div>
                  <button
                    onClick={onCloseAction}
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor">
                      <path d="M6 6l8 8m0-8l-8 8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>

              {renderStepContent()}
            </div>
          </motion.div>
        </>
      )}
    </>
  );
} 