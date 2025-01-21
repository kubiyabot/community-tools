import { useState } from "react";
import { Button } from "@/app/components/button";
import { 
  LockIcon, 
  ChevronRightIcon,
  ExternalLinkIcon,
  GithubIcon,
  BookOpenIcon,
  HelpCircleIcon,
  ArrowRightIcon
} from "lucide-react";
import Image from "next/image";
import { cn } from "@/lib/utils";

const HELPFUL_LINKS = [
  {
    name: 'Documentation',
    href: 'https://docs.kubiya.ai',
    icon: BookOpenIcon,
  },
  {
    name: 'GitHub',
    href: 'https://github.com/kubiya-ai',
    icon: GithubIcon,
  },
  {
    name: 'Support',
    href: 'https://support.kubiya.ai',
    icon: HelpCircleIcon,
  }
] as const;

export function ApiKeySetup() {
  const [isLoading, setIsLoading] = useState(false);
  const [isHoveringHelp, setIsHoveringHelp] = useState(false);

  const handleLogin = () => {
    console.log('Login button clicked');
    setIsLoading(true);
    const loginUrl = new URL('/api/auth/auth0/login', window.location.origin);
    loginUrl.searchParams.set('returnTo', '/chat');
    window.location.assign(loginUrl.toString());
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0A0F1E] to-[#1E293B]">
      {/* Top Navigation */}
      <nav className="fixed top-0 left-0 right-0 flex justify-between items-center px-6 py-4 bg-[#0A0F1E]/80 backdrop-blur-lg border-b border-white/5">
        <div className="flex items-center gap-2 group cursor-pointer">
          <div className="relative">
            <Image
              src="/favicon-32x32.png"
              alt="Kubiya"
              width={24}
              height={24}
              className="rounded-lg transition-transform group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-[#7C3AED] rounded-lg opacity-0 group-hover:opacity-20 transition-opacity" />
          </div>
          <span className="text-white font-medium group-hover:text-[#7C3AED] transition-colors">Kubiya</span>
        </div>
        <a
          href="https://kubiya.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center px-4 py-2 text-sm text-[#94A3B8] hover:text-white transition-all rounded-lg hover:bg-white/5 group"
        >
          <ExternalLinkIcon className="h-4 w-4 mr-2 group-hover:rotate-12 transition-transform" />
          Visit Website
          <ArrowRightIcon className="h-4 w-4 ml-1 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
        </a>
      </nav>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-sm w-full">
          {/* Sign In Card */}
          <div 
            onClick={() => console.log('Card clicked')} 
            className="text-center space-y-6 bg-gradient-to-br from-[#1E293B] to-[#0F172A] rounded-2xl p-8 border border-white/5 shadow-xl relative group pointer-events-auto"
          >
            {/* Animated Border Effect */}
            <div className="absolute -inset-[1px] bg-gradient-to-r from-[#7C3AED]/0 via-[#7C3AED]/20 to-[#7C3AED]/0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
            
            {/* Logo */}
            <div className="flex justify-center mb-2">
              <div className="relative group/logo cursor-pointer">
                <Image
                  src="/favicon-32x32.png"
                  alt="Kubiya"
                  width={40}
                  height={40}
                  className="rounded-xl shadow-2xl ring-1 ring-white/10 transition-transform group-hover/logo:scale-110"
                />
                <div className="absolute inset-0 bg-[#7C3AED] rounded-xl opacity-0 group-hover/logo:opacity-20 transition-opacity" />
              </div>
            </div>
            
            {/* Title */}
            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-white">
                Welcome Back
              </h1>
              <p className="text-sm text-[#94A3B8]">
                Sign in securely with your organization's credentials
              </p>
            </div>

            {/* Sign In Button */}
            <button
              type="button"
              onClick={handleLogin}
              disabled={isLoading}
              className={cn(
                "w-full h-12 text-base font-medium transition-all duration-300",
                "bg-[#7C3AED] hover:bg-[#6D28D9] text-white",
                "rounded-xl shadow-lg hover:shadow-[#7C3AED]/25 hover:scale-[1.02]",
                "flex items-center justify-center gap-3 group/btn",
                "disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100",
                "pointer-events-auto relative z-50"
              )}
            >
              {isLoading ? (
                <>
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <LockIcon className="h-5 w-5 group-hover/btn:scale-110 transition-transform" />
                  <span>Continue with SSO</span>
                  <ChevronRightIcon className="h-5 w-5 group-hover/btn:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            {/* Security Badge */}
            <div 
              className="flex items-center justify-center gap-2 pt-4 border-t border-white/5 group/badge cursor-help"
              onMouseEnter={() => setIsHoveringHelp(true)}
              onMouseLeave={() => setIsHoveringHelp(false)}
            >
              <div className={cn(
                "w-4 h-4 rounded-full bg-[#7C3AED]/10 flex items-center justify-center transition-transform",
                isHoveringHelp && "scale-110"
              )}>
                <LockIcon className="h-2.5 w-2.5 text-[#7C3AED]" />
              </div>
              <p className="text-xs text-[#94A3B8] group-hover/badge:text-white transition-colors">
                Enterprise-grade security with Auth0
              </p>
            </div>
          </div>

          {/* Footer with Helpful Links */}
          <footer className="mt-8 space-y-4">
            <div className="flex justify-center items-center gap-6">
              {HELPFUL_LINKS.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-center gap-2 text-[#94A3B8] hover:text-white transition-all"
                  title={link.name}
                >
                  <link.icon className="h-4 w-4 transition-transform group-hover:scale-110" />
                  <span className="text-sm">{link.name}</span>
                </a>
              ))}
            </div>
            <p className="text-xs text-[#64748B] text-center hover:text-[#94A3B8] transition-colors cursor-default">
              © {new Date().getFullYear()} Kubiya, Inc. All rights reserved.
            </p>
          </footer>
        </div>
      </div>
    </div>
  );
} 