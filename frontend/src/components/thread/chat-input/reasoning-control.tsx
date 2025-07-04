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
    label: 'Brain',
    description: 'Standard speed, no enhanced reasoning',
    icon: Zap,
    color: 'text-gray-500',
    bgColor: 'bg-gray-50 dark:bg-gray-900/20',
    isReasoning: false,
  },
  {
    value: 'medium',
    label: 'Big Brain',
    description: 'Enhanced reasoning for complex problems (+credits)',
    icon: Brain,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    isReasoning: true,
  },
  {
    value: 'high',
    label: 'Galaxy Brain',
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
          <div className="flex items-center gap-2 animate-in slide-in-from-left-2 duration-300">
            {/* Dot Tower */}
            <div className="flex flex-col items-center gap-0.5 py-1">
              {REASONING_LEVELS.map((level, index) => {
                const isActive = index <= currentLevelIndex;
                const isSelected = index === currentLevelIndex;
                return (
                  <Tooltip key={level.value}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleDotClick(level, index)}
                        disabled={isReasoningDisabled}
                        className={cn(
                          "w-2 h-2 rounded-full transition-all duration-200 hover:scale-125",
                          isActive 
                            ? "bg-white shadow-sm ring-1 ring-gray-200 dark:ring-gray-700 dark:bg-gray-100" 
                            : "bg-gray-300 dark:bg-gray-600",
                          isSelected && "ring-2 ring-blue-500 dark:ring-blue-400",
                          isReasoningDisabled && "opacity-50 cursor-not-allowed",
                          "hover:bg-white dark:hover:bg-gray-100"
                        )}
                        aria-label={`Set reasoning to ${level.label}`}
                      />
                    </TooltipTrigger>
                    <TooltipContent side="right" className="text-xs">
                      <p className="font-medium">{level.label}</p>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
            <span className={cn(
              "text-xs font-medium whitespace-nowrap",
              currentLevel.color,
              isReasoningDisabled && "opacity-50"
            )}>
              {currentLevel.label}
            </span>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}; 