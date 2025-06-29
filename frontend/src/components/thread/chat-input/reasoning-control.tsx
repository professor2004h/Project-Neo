'use client';

import React, { useState, useEffect } from 'react';
import { Slider } from '@/components/ui/slider';
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
    label: 'Quick Think',
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

export const ReasoningControl: React.FC<ReasoningControlProps> = ({
  value,
  onChange,
  disabled = false,
  modelName = '',
  subscriptionStatus = '',
}) => {
  const [sliderValue, setSliderValue] = useState([0]);

  // Check if the model supports reasoning (Claude models)
  const supportsReasoning = modelName.toLowerCase().includes('claude');
  
  // Check if user is on free plan (same check as existing limitation logic)
  const isFreePlan = subscriptionStatus === 'no_subscription' && !isLocalMode();
  
  // Disable reasoning control for free plan users
  const isReasoningDisabled = disabled || isFreePlan;

  useEffect(() => {
    const levelIndex = REASONING_LEVELS.findIndex(level => level.value === value.effort);
    setSliderValue([levelIndex]);
  }, [value]);

  const handleSliderChange = (newValue: number[]) => {
    if (isFreePlan) return; // Prevent changes on free plan
    
    const level = newValue[0];
    setSliderValue(newValue);
    
    const selectedLevel = REASONING_LEVELS[level];
    onChange({ 
      enabled: selectedLevel.isReasoning,
      effort: selectedLevel.value as 'none' | 'medium' | 'high'
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
    setSliderValue([nextIndex]);
  };

  if (!supportsReasoning) {
    return null;
  }

  const currentLevel = REASONING_LEVELS.find(level => level.value === value.effort) || REASONING_LEVELS[0];
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
            <div className="flex items-center gap-1 min-w-0">
              <Slider
                value={sliderValue}
                onValueChange={handleSliderChange}
                max={2}
                min={0}
                step={1}
                disabled={isReasoningDisabled}
                className="w-16 flex-shrink-0"
              />
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