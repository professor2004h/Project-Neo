'use client';

import React from 'react';
import { ProgressData } from './types';
import { cn } from '@/lib/utils';

interface ProgressChartProps {
  data: ProgressData;
  timeframe: 'week' | 'month' | 'term';
}

export function ProgressChart({ data, timeframe }: ProgressChartProps) {
  // Generate mock data points for the chart
  const generateChartData = () => {
    const points = timeframe === 'week' ? 7 : timeframe === 'month' ? 30 : 90;
    const chartData = [];
    
    for (let i = 0; i < points; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (points - 1 - i));
      
      // Generate realistic progress data with some variation
      const baseScore = data.overall_score;
      const variation = (Math.random() - 0.5) * 0.2; // ±10% variation
      const score = Math.max(0, Math.min(1, baseScore + variation));
      
      chartData.push({
        date,
        score,
        topics: data.topics.map(topic => ({
          ...topic,
          skill_level: Math.max(0, Math.min(1, topic.skill_level + variation))
        }))
      });
    }
    
    return chartData;
  };

  const chartData = generateChartData();
  const maxScore = Math.max(...chartData.map(d => d.score));
  const minScore = Math.min(...chartData.map(d => d.score));

  const getDateLabel = (date: Date, index: number) => {
    if (timeframe === 'week') {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else if (timeframe === 'month') {
      return index % 5 === 0 ? date.getDate().toString() : '';
    } else {
      return index % 15 === 0 ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'stroke-green-500 fill-green-500';
    if (score >= 0.6) return 'stroke-yellow-500 fill-yellow-500';
    return 'stroke-red-500 fill-red-500';
  };

  return (
    <div className="w-full h-64 relative">
      {/* Chart Container */}
      <div className="absolute inset-0 flex flex-col">
        {/* Y-axis labels */}
        <div className="flex-1 flex flex-col justify-between text-xs text-muted-foreground py-2">
          <span>100%</span>
          <span>75%</span>
          <span>50%</span>
          <span>25%</span>
          <span>0%</span>
        </div>
      </div>

      {/* SVG Chart */}
      <svg className="w-full h-full pl-8 pr-4" viewBox="0 0 400 200">
        {/* Grid lines */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Horizontal grid lines */}
        {[0, 25, 50, 75, 100].map((percent) => (
          <line
            key={percent}
            x1="0"
            y1={200 - (percent * 2)}
            x2="400"
            y2={200 - (percent * 2)}
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.2"
          />
        ))}

        {/* Progress line */}
        <path
          d={chartData.map((point, index) => {
            const x = (index / (chartData.length - 1)) * 380 + 10;
            const y = 200 - (point.score * 180) - 10;
            return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
          }).join(' ')}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="2"
          className="drop-shadow-sm"
        />

        {/* Progress area fill */}
        <path
          d={[
            ...chartData.map((point, index) => {
              const x = (index / (chartData.length - 1)) * 380 + 10;
              const y = 200 - (point.score * 180) - 10;
              return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
            }),
            `L ${(chartData.length - 1) / (chartData.length - 1) * 380 + 10} 190`,
            'L 10 190',
            'Z'
          ].join(' ')}
          fill="hsl(var(--primary))"
          opacity="0.1"
        />

        {/* Data points */}
        {chartData.map((point, index) => {
          const x = (index / (chartData.length - 1)) * 380 + 10;
          const y = 200 - (point.score * 180) - 10;
          
          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r="3"
                fill="hsl(var(--primary))"
                stroke="hsl(var(--background))"
                strokeWidth="2"
                className="drop-shadow-sm"
              />
              
              {/* Tooltip on hover */}
              <circle
                cx={x}
                cy={y}
                r="8"
                fill="transparent"
                className="cursor-pointer hover:fill-primary/10"
              >
                <title>
                  {getDateLabel(point.date, index)}: {Math.round(point.score * 100)}%
                </title>
              </circle>
            </g>
          );
        })}
      </svg>

      {/* X-axis labels */}
      <div className="flex justify-between text-xs text-muted-foreground px-8 pt-2">
        {chartData.map((point, index) => (
          <span key={index} className={cn(
            "text-center",
            index % Math.ceil(chartData.length / 6) !== 0 && "opacity-0"
          )}>
            {getDateLabel(point.date, index)}
          </span>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-primary"></div>
          <span>Overall Progress</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span>80%+ Mastery</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <span>60-79% Progress</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span>Below 60%</span>
        </div>
      </div>
    </div>
  );
}