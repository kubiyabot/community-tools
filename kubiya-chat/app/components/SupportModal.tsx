'use client';

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';

interface SupportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SupportModal({ isOpen, onClose }: SupportModalProps) {
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

  if (!isOpen) return null;

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
      color: 'bg-[#1a2234] text-blue-400',
      hoverColor: 'hover:bg-[#232b3e]'
    },
    {
      title: 'Community Slack',
      description: 'Join our community on Slack',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
        </svg>
      ),
      link: 'https://join.slack.com/t/kubiya-community/shared_invite/zt-1wn5h5y84-NHwwHZFPVg3WCTlRFGHHGQ',
      color: 'bg-[#1a2234] text-[#36C5F0]',
      hoverColor: 'hover:bg-[#232b3e]'
    },
    {
      title: 'Email Support',
      description: 'Get help via email',
      icon: (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ),
      link: 'mailto:support@kubiya.ai',
      color: 'bg-[#1a2234] text-green-400',
      hoverColor: 'hover:bg-[#232b3e]'
    }
  ];

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100]"
      />
      
      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ type: "spring", duration: 0.5 }}
        className="fixed left-1/2 top-[30%] -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-[101] px-4"
      >
        <div className="bg-[#1a2234] rounded-lg shadow-2xl border border-[#2d3545] overflow-hidden">
          {/* Header */}
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-[#7C3AED]/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-[#7C3AED]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-medium text-white">How can we help?</h2>
                <p className="text-sm text-[#94A3B8]">Choose your preferred support option</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-[#232b3e] text-[#94A3B8] hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor">
                <path d="M6 6l8 8m0-8l-8 8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-2">
            {supportOptions.map((option, index) => (
              <motion.a
                key={option.title}
                href={option.link}
                target={option.link.startsWith('http') ? '_blank' : undefined}
                rel={option.link.startsWith('http') ? 'noopener noreferrer' : undefined}
                className={`flex items-center space-x-3 p-3 rounded-lg ${option.color} ${option.hoverColor} transition-all duration-200 group cursor-pointer`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="flex-shrink-0">
                  {option.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium truncate text-current">
                    {option.title}
                  </h3>
                  <p className="text-sm truncate opacity-80">
                    {option.description}
                  </p>
                </div>
              </motion.a>
            ))}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-[#2d3545]">
            <p className="text-sm text-[#94A3B8] text-center">
              Need immediate assistance?{' '}
              <a 
                href="mailto:support@kubiya.ai" 
                className="text-[#7C3AED] hover:text-[#9061FF] transition-colors inline-flex items-center"
              >
                Contact us directly
                <svg className="w-4 h-4 ml-1 transform -rotate-45" viewBox="0 0 20 20" fill="none" stroke="currentColor">
                  <path d="M5 10h10m0 0l-4-4m4 4l-4 4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </a>
            </p>
          </div>
        </div>
      </motion.div>
    </>
  );
} 