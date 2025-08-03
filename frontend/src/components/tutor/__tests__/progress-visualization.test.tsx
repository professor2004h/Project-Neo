/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProgressVisualization } from '../progress-visualization';
import { ProgressData } from '../types';

// Mock the ProgressChart component
jest.mock('../progress-chart', () => ({
  ProgressChart: ({ data, timeframe }: any) => (
    <div data-testid="progress-chart">
      Chart for {data.subject} - {timeframe}
    </div>
  )
}));

describe('ProgressVisualization', () => {
  const mockProgressData: ProgressData = {
    user_id: 'user123',
    subject: 'math',
    topics: [
      {
        topic_id: 'fractions_basic',
        topic_name: 'Basic Fractions',
        cambridge_code: 'M3N1.1',
        skill_level: 0.85,
        confidence_score: 0.8,
        last_practiced: new Date('2024-01-01'),
        mastery_indicators: {
          understanding: 0.9,
          application: 0.8,
          retention: 0.85
        },
        improvement_areas: ['Word problems']
      },
      {
        topic_id: 'multiplication',
        topic_name: 'Multiplication Tables',
        cambridge_code: 'M3N2.3',
        skill_level: 0.65,
        confidence_score: 0.7,
        last_practiced: new Date('2024-01-02'),
        mastery_indicators: {
          understanding: 0.7,
          application: 0.6,
          retention: 0.65
        },
        improvement_areas: ['Speed', 'Accuracy']
      },
      {
        topic_id: 'addition',
        topic_name: 'Addition',
        cambridge_code: 'M3N1.2',
        skill_level: 0.45,
        confidence_score: 0.5,
        last_practiced: new Date('2024-01-03'),
        mastery_indicators: {
          understanding: 0.5,
          application: 0.4,
          retention: 0.45
        },
        improvement_areas: ['Carrying', 'Large numbers']
      }
    ],
    overall_score: 0.65,
    last_updated: new Date('2024-01-03')
  };

  const defaultProps = {
    data: mockProgressData,
    timeframe: 'week' as const,
    showDetails: false
  };

  it('renders overall progress correctly', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByText('Overall Progress - MATH')).toBeInTheDocument();
    expect(screen.getAllByText('65%')).toHaveLength(2); // Overall score and one topic
    expect(screen.getByText('week')).toBeInTheDocument();
  });

  it('displays topics mastered count', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    // Should show 1 topic mastered (skill_level >= 0.8)
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('out of 3 topics')).toBeInTheDocument();
  });

  it('shows last practice date', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByText('Jan 03')).toBeInTheDocument();
  });

  it('renders progress chart', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByTestId('progress-chart')).toBeInTheDocument();
    expect(screen.getByText('Chart for math - week')).toBeInTheDocument();
  });

  it('displays all topics in breakdown', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByText('Basic Fractions')).toBeInTheDocument();
    expect(screen.getByText('Multiplication Tables')).toBeInTheDocument();
    expect(screen.getByText('Addition')).toBeInTheDocument();
  });

  it('shows Cambridge codes for topics', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByText('M3N1.1')).toBeInTheDocument();
    expect(screen.getByText('M3N2.3')).toBeInTheDocument();
    expect(screen.getByText('M3N1.2')).toBeInTheDocument();
  });

  it('displays skill levels as percentages', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByText('85%')).toBeInTheDocument(); // Basic Fractions
    expect(screen.getAllByText('65%')).toHaveLength(2); // Overall and Multiplication
    expect(screen.getByText('45%')).toBeInTheDocument(); // Addition
  });

  it('shows detailed breakdown when showDetails is true', () => {
    render(<ProgressVisualization {...defaultProps} showDetails={true} />);
    
    expect(screen.getAllByText('Mastery Indicators')).toHaveLength(3); // One for each topic
    expect(screen.getAllByText('Areas for Improvement')).toHaveLength(3); // One for each topic
    expect(screen.getAllByText('Understanding')).toHaveLength(3);
    expect(screen.getAllByText('Application')).toHaveLength(3);
    expect(screen.getAllByText('Retention')).toHaveLength(3);
  });

  it('displays improvement areas when showDetails is true', () => {
    render(<ProgressVisualization {...defaultProps} showDetails={true} />);
    
    expect(screen.getByText('Word problems')).toBeInTheDocument();
    expect(screen.getByText('Speed')).toBeInTheDocument();
    expect(screen.getByText('Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Carrying')).toBeInTheDocument();
    expect(screen.getByText('Large numbers')).toBeInTheDocument();
  });

  it('shows congratulations for topics with no improvement areas', () => {
    const dataWithPerfectTopic: ProgressData = {
      ...mockProgressData,
      topics: [
        {
          ...mockProgressData.topics[0],
          improvement_areas: []
        }
      ]
    };

    render(<ProgressVisualization {...defaultProps} data={dataWithPerfectTopic} showDetails={true} />);
    
    expect(screen.getByText('No areas for improvement - Great job!')).toBeInTheDocument();
  });

  it('handles different timeframes', () => {
    const { rerender } = render(<ProgressVisualization {...defaultProps} timeframe="month" />);
    
    expect(screen.getByText('month')).toBeInTheDocument();
    
    rerender(<ProgressVisualization {...defaultProps} timeframe="term" />);
    
    expect(screen.getByText('term')).toBeInTheDocument();
  });

  it('applies correct color coding for scores', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    // High score (85%) should have green color class
    const highScoreElement = screen.getByText('85%');
    expect(highScoreElement).toHaveClass('text-green-600');
    
    // Medium score (65%) should have yellow color class
    const mediumScoreElements = screen.getAllByText('65%');
    mediumScoreElements.forEach(element => {
      expect(element).toHaveClass('text-yellow-600');
    });
    
    // Low score (45%) should have red color class
    const lowScoreElement = screen.getByText('45%');
    expect(lowScoreElement).toHaveClass('text-red-600');
  });

  it('displays confidence scores correctly', () => {
    render(<ProgressVisualization {...defaultProps} />);
    
    expect(screen.getByText('Confidence: 80%')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 70%')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 50%')).toBeInTheDocument();
  });

  it('shows mastery indicators percentages when details are shown', () => {
    render(<ProgressVisualization {...defaultProps} showDetails={true} />);
    
    // Check for mastery indicator percentages
    expect(screen.getByText('90%')).toBeInTheDocument(); // Understanding for fractions
    expect(screen.getByText('80%')).toBeInTheDocument(); // Application for fractions
    expect(screen.getByText('70%')).toBeInTheDocument(); // Understanding for multiplication
    expect(screen.getByText('60%')).toBeInTheDocument(); // Application for multiplication
    expect(screen.getByText('50%')).toBeInTheDocument(); // Understanding for addition
    expect(screen.getByText('40%')).toBeInTheDocument(); // Application for addition
  });
});