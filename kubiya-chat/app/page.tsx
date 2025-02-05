"use client";

import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { ArrowRight, Bot, Shield, Zap } from 'lucide-react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useEffect } from 'react';

const features = [
  {
    icon: Bot,
    title: 'AI-Powered Assistant',
    description: 'Interact with your intelligent Kubiya teammate for seamless workflow automation.'
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Bank-grade security with SSO integration and role-based access control.'
  },
  {
    icon: Zap,
    title: 'Instant Automation',
    description: 'Automate your workflows and tasks with natural language commands.'
  }
];

export default function LandingPage() {
  const router = useRouter();
  const { user, isLoading } = useUser();

  useEffect(() => {
    if (user && !isLoading) {
      router.push('/chat');
    }
  }, [user, isLoading, router]);

  const handleGetStarted = () => {
    const loginUrl = new URL('/api/auth/login', window.location.origin);
    loginUrl.searchParams.set('returnTo', '/chat');
    window.location.href = loginUrl.toString();
  };

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
        <div className="text-center space-y-8 max-w-3xl mx-auto">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <div className="relative group cursor-pointer">
              <Image
                src="/favicon-32x32.png"
                alt="Kubiya"
                width={64}
                height={64}
                className="rounded-xl shadow-2xl ring-1 ring-white/10 transition-transform group-hover:scale-110"
              />
              <div className="absolute inset-0 bg-[#7C3AED] rounded-xl opacity-0 group-hover:opacity-20 transition-opacity" />
            </div>
          </div>

          {/* Hero Text */}
          <h1 className="text-4xl sm:text-6xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Your AI-Powered Teammate
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Automate your workflows and interact with your systems using natural language.
            Let Kubiya be your intelligent assistant.
          </p>

          {/* CTA Button */}
          <div className="flex justify-center gap-4">
            <button
              onClick={handleGetStarted}
              className="group relative px-6 py-3 text-lg font-medium rounded-xl bg-[#7C3AED] text-white hover:bg-[#6D28D9] transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#7C3AED] shadow-lg hover:shadow-[#7C3AED]/25"
            >
              <span className="flex items-center">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 max-w-7xl mx-auto px-4">
          {features.map((feature, index) => (
            <div
              key={index}
              className="relative group rounded-xl bg-white/5 p-6 hover:bg-white/10 transition-all duration-200 hover:scale-105"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-[#7C3AED]/10 to-transparent opacity-0 group-hover:opacity-100 rounded-xl transition-opacity" />
              <div className="relative">
                <feature.icon className="h-8 w-8 text-[#7C3AED] mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 border-t border-white/10">
        <div className="text-center text-sm text-gray-400">
          © {new Date().getFullYear()} Kubiya, Inc. All rights reserved.
        </div>
      </footer>
    </main>
  );
}
