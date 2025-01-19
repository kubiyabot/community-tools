'use client';

import { useSearchParams } from 'next/navigation';
import { Button } from '@/app/components/button';
import { useRouter } from 'next/navigation';
import { AlertCircle, ArrowLeft, Home } from 'lucide-react';

export default function AuthErrorPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const error = searchParams?.get('error');
  const errorDescription = searchParams?.get('error_description');

  const getErrorMessage = () => {
    switch (error) {
      case 'unauthorized':
        return 'You are not authorized to access this application.';
      case 'invalid_connection':
        return 'The selected authentication method is not available.';
      case 'login_required':
        return 'Please log in to continue.';
      default:
        return errorDescription || 'An error occurred during authentication.';
    }
  };

  return (
    <div className="min-h-screen bg-[#0F172A] flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 bg-[#1E293B] p-8 rounded-lg shadow-xl border border-[#2D3B4E]">
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          
          <h1 className="text-2xl font-bold text-white">Authentication Error</h1>
          
          <p className="text-[#94A3B8] text-sm">
            {getErrorMessage()}
          </p>
        </div>

        <div className="space-y-4">
          <Button
            onClick={() => router.push('/api/auth/auth0/login')}
            className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white transition-colors"
          >
            Try Again
          </Button>

          <div className="flex gap-4">
            <Button
              onClick={() => router.back()}
              variant="outline"
              className="flex-1 border-[#2D3B4E] text-[#94A3B8] hover:bg-[#2D3B4E] hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>

            <Button
              onClick={() => router.push('/')}
              variant="outline"
              className="flex-1 border-[#2D3B4E] text-[#94A3B8] hover:bg-[#2D3B4E] hover:text-white"
            >
              <Home className="w-4 h-4 mr-2" />
              Home
            </Button>
          </div>
        </div>

        <div className="text-center">
          <p className="text-xs text-[#64748B]">
            If this issue persists, please contact support at{' '}
            <a 
              href="mailto:support@kubiya.ai"
              className="text-[#7C3AED] hover:text-[#6D28D9] transition-colors"
            >
              support@kubiya.ai
            </a>
          </p>
        </div>
      </div>
    </div>
  );
} 