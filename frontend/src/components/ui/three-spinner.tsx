'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ThreeSpinnerProps {
  size?: number;
  color?: string;
  className?: string;
}

export function ThreeSpinner({ 
  size = 64,
  color = 'currentColor',
  className = ''
}: ThreeSpinnerProps) {
  return (
    <div 
      className={cn("inline-flex items-center justify-center", className)}
      style={{ 
        width: size, 
        height: size,
      }} 
    >
      <div className="relative">
        {/* Outer ring */}
        <div 
          className="absolute border-2 border-current rounded-full animate-spin opacity-20"
          style={{
            width: size * 0.9,
            height: size * 0.9,
            borderTopColor: 'transparent',
            borderRightColor: color,
            animationDuration: '3s',
            animationDirection: 'reverse'
          }}
        />
        
        {/* Middle ring */}
        <div 
          className="absolute border-2 border-current rounded-full animate-spin opacity-40"
          style={{
            width: size * 0.6,
            height: size * 0.6,
            left: size * 0.15,
            top: size * 0.15,
            borderTopColor: 'transparent',
            borderLeftColor: color,
            animationDuration: '2s'
          }}
        />
        
        {/* Inner ring */}
        <div 
          className="absolute border-2 border-current rounded-full animate-spin opacity-60"
          style={{
            width: size * 0.3,
            height: size * 0.3,
            left: size * 0.3,
            top: size * 0.3,
            borderTopColor: 'transparent',
            borderRightColor: color,
            animationDuration: '1.5s',
            animationDirection: 'reverse'
          }}
        />
        
        {/* Center dot */}
        <div 
          className="absolute bg-current rounded-full animate-pulse opacity-80"
          style={{
            width: size * 0.1,
            height: size * 0.1,
            left: size * 0.4,
            top: size * 0.4,
            animationDuration: '2s'
          }}
        />
      </div>
    </div>
  );
} 