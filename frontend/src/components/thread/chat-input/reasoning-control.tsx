'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Brain, Zap, Target, Rocket, Crown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { isLocalMode } from '@/lib/config';

export interface ReasoningSettings {
  enabled: boolean;
  effort: 'none' | 'medium' | 'high';
}

interface ReasoningControlProps {
  value: ReasoningSettings;
  onChange: (settings: ReasoningSettings) => void;
  disabled?: boolean;
  modelName?: string;
  subscriptionStatus?: string;
}

const REASONING_LEVELS = [
  {
    value: 'none',
    label: 'Chill',
    description: 'Standard speed, no enhanced reasoning',
    icon: Zap,
    color: 'text-white',
    bgColor: 'bg-gray-50 dark:bg-gray-900/20',
    isReasoning: false,
  },
  {
    value: 'medium',
    label: 'Boost',
    description: 'Enhanced reasoning for complex problems (+credits)',
    icon: Brain,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    isReasoning: true,
  },
  {
    value: 'high',
    label: 'Turbo',
    description: 'Maximum reasoning power (+more credits)',
    icon: Rocket,
    color: 'text-purple-500',
    bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    isReasoning: true,
  },
] as const;

// localStorage key for persisting reasoning settings
const REASONING_SETTINGS_KEY = 'reasoning-settings';

// Helper function to save settings to localStorage
const saveReasoningSettings = (settings: ReasoningSettings) => {
  try {
    localStorage.setItem(REASONING_SETTINGS_KEY, JSON.stringify(settings));
  } catch (error) {
    console.warn('Failed to save reasoning settings to localStorage:', error);
  }
};

// Helper function to load settings from localStorage
const loadReasoningSettings = (): ReasoningSettings | null => {
  try {
    const stored = localStorage.getItem(REASONING_SETTINGS_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.warn('Failed to load reasoning settings from localStorage:', error);
  }
  return null;
};

export const ReasoningControl: React.FC<ReasoningControlProps> = ({
  value,
  onChange,
  disabled = false,
  modelName = '',
  subscriptionStatus = '',
}) => {
  // Check if the model supports reasoning (Claude models)
  const supportsReasoning = modelName.toLowerCase().includes('claude');
  
  // Check if user is on free plan (same check as existing limitation logic)
  const isFreePlan = subscriptionStatus === 'no_subscription' && !isLocalMode();
  
  // Disable reasoning control for free plan users
  const isReasoningDisabled = disabled || isFreePlan;

  // Save settings whenever they change
  useEffect(() => {
    if (!isFreePlan) {
      saveReasoningSettings(value);
    }
  }, [value, isFreePlan]);

  const handleDotClick = (level: typeof REASONING_LEVELS[number], index: number) => {
    if (isFreePlan) return; // Prevent changes on free plan
    
    onChange({ 
      enabled: level.isReasoning,
      effort: level.value as 'none' | 'medium' | 'high'
    });
  };

  const handleToggle = () => {
    if (isFreePlan) return; // Prevent changes on free plan
    
    // Cycle through: none -> medium -> high -> none
    const currentIndex = REASONING_LEVELS.findIndex(level => level.value === value.effort);
    const nextIndex = (currentIndex + 1) % REASONING_LEVELS.length;
    const nextLevel = REASONING_LEVELS[nextIndex];
    
    onChange({ 
      enabled: nextLevel.isReasoning,
      effort: nextLevel.value as 'none' | 'medium' | 'high'
    });
  };

  if (!supportsReasoning) {
    return null;
  }

  const currentLevel = REASONING_LEVELS.find(level => level.value === value.effort) || REASONING_LEVELS[0];
  const currentLevelIndex = REASONING_LEVELS.findIndex(level => level.value === value.effort);
  const IconToShow = isFreePlan ? Crown : currentLevel.icon;

  return (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggle}
              disabled={isReasoningDisabled}
              className={cn(
                "h-8 w-8 p-0 rounded-full transition-all duration-200",
                !isFreePlan ? currentLevel.bgColor : "hover:bg-muted",
                isReasoningDisabled && "opacity-50 cursor-not-allowed",
                isFreePlan && "opacity-60" // Special styling for free plan
              )}
            >
              <IconToShow 
                className={cn(
                  "h-4 w-4 transition-colors",
                  !isFreePlan ? currentLevel.color : "text-muted-foreground",
                  isFreePlan && "text-amber-500" // Crown icon in amber for free plan
                )} 
              />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">
            <div className="flex flex-col gap-1">
              {isFreePlan ? (
                <>
                  <p className="font-medium">Big Brain Mode</p>
                  <p className="text-muted-foreground">
                    Upgrade to unlock enhanced reasoning capabilities
                  </p>
                </>
              ) : (
                <>
                  <p className="font-medium">{currentLevel.label}</p>
                  <p className="text-muted-foreground">{currentLevel.description}</p>
                </>
              )}
            </div>
          </TooltipContent>
        </Tooltip>

        {!isFreePlan && (
          <div className="flex items-center gap-3 animate-in slide-in-from-left-2 duration-300">
            {/* Unified Reasoning Component */}
            <div className="relative flex items-end gap-6 py-2 px-3 rounded-lg transition-all duration-500 ease-out">
              {/* Liquid Flow Background */}
              <div 
                className="absolute inset-0 rounded-lg transition-all duration-700 ease-out opacity-20"
                style={{
                  background: currentLevelIndex === 0 
                    ? 'linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)'
                    : currentLevelIndex === 1 
                    ? 'linear-gradient(90deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.05) 100%)'
                    : 'linear-gradient(90deg, rgba(168,85,247,0.1) 0%, rgba(168,85,247,0.05) 100%)',
                  transform: `scaleX(${(currentLevelIndex + 1) / 3})`,
                  transformOrigin: 'left',
                }}
              />
              
              {/* Flowing Connection Line */}
              <div 
                className="absolute top-3 left-0 h-0.5 transition-all duration-700 ease-out"
                style={{
                  width: `${20 + (currentLevelIndex * 24)}px`,
                  background: currentLevelIndex === 0 
                    ? 'linear-gradient(90deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.2) 100%)'
                    : currentLevelIndex === 1 
                    ? 'linear-gradient(90deg, rgba(59,130,246,0.8) 0%, rgba(59,130,246,0.3) 100%)'
                    : 'linear-gradient(90deg, rgba(168,85,247,0.8) 0%, rgba(168,85,247,0.3) 100%)',
                  boxShadow: currentLevelIndex === 0 
                    ? '0 0 8px rgba(255,255,255,0.3)'
                    : currentLevelIndex === 1 
                    ? '0 0 8px rgba(59,130,246,0.4)'
                    : '0 0 8px rgba(168,85,247,0.4)',
                }}
              />

              {REASONING_LEVELS.map((level, index) => {
                const isActive = index <= currentLevelIndex;
                const isHighlighted = index === currentLevelIndex;
                
                // Dynamic colors based on current level
                const dotColor = isActive
                  ? currentLevelIndex === 0 ? 'bg-white' 
                    : currentLevelIndex === 1 ? 'bg-blue-500' 
                    : 'bg-purple-500'
                  : 'bg-gray-300 dark:bg-gray-600';
                
                const textColor = isActive
                  ? currentLevelIndex === 0 ? 'text-white' 
                    : currentLevelIndex === 1 ? 'text-blue-500' 
                    : 'text-purple-500'
                  : 'text-gray-400 dark:text-gray-500';
                
                const glowColor = isActive
                  ? currentLevelIndex === 0 ? 'drop-shadow-[0_0_4px_rgba(255,255,255,0.6)]' 
                    : currentLevelIndex === 1 ? 'drop-shadow-[0_0_4px_rgba(59,130,246,0.6)]' 
                    : 'drop-shadow-[0_0_4px_rgba(168,85,247,0.6)]'
                  : '';

                return (
                  <Tooltip key={level.value}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleDotClick(level, index)}
                        disabled={isReasoningDisabled}
                        className={cn(
                          "relative flex flex-col items-center gap-1 transition-all duration-500 ease-out group",
                          "hover:scale-105 active:scale-95",
                          isReasoningDisabled && "opacity-50 cursor-not-allowed"
                        )}
                        aria-label={`Set reasoning to ${level.label}`}
                      >
                        {/* Dot with liquid effect */}
                        <div className="relative">
                          <div
                            className={cn(
                              "w-2.5 h-2.5 rounded-full transition-all duration-500 ease-out",
                              dotColor,
                              glowColor,
                              isHighlighted && "scale-125 animate-pulse",
                              isActive && "shadow-lg",
                              "group-hover:scale-110"
                            )}
                          />
                          {/* Liquid ripple effect */}
                          {isHighlighted && (
                            <div 
                              className="absolute inset-0 rounded-full animate-ping opacity-30"
                              style={{
                                background: currentLevelIndex === 0 ? 'rgba(255,255,255,0.6)' 
                                  : currentLevelIndex === 1 ? 'rgba(59,130,246,0.6)' 
                                  : 'rgba(168,85,247,0.6)',
                              }}
                            />
                          )}
                        </div>
                        
                        {/* Text label */}
                        <span className={cn(
                          "text-xs font-medium transition-all duration-500 ease-out whitespace-nowrap",
                          textColor,
                          isActive && "font-semibold",
                          isHighlighted && "text-shadow-sm"
                        )}>
                          {level.label}
                        </span>
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">
                      <div className="flex flex-col gap-1">
                        <p className="font-medium">{level.label}</p>
                        <p className="text-muted-foreground text-[10px]">{level.description}</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}; 