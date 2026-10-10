import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Loading cryptographic intelligence...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-4">
      <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      <p className="text-sm text-gray-400 font-medium tracking-wide">{message}</p>
    </div>
  );
};
