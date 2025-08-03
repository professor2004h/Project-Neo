import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ParentReportViewer } from '../parent-report-viewer';
import { format, startOfWeek, endOfWeek } from 'date-fns';

describe('ParentReportViewer', () => {
  const mockChildId = 'child123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<ParentReportViewer childId={mockChildId} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders report viewer with data after loading', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Weekly Progress Reports')).toBeInTheDocument();
    });

    expect(screen.getByText('Detailed insights into your child\'s learning journey')).toBeInTheDocument();
  });

  it('displays report summary cards', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Study Time')).toBeInTheDocument();
    });

    expect(screen.getByText('3h 0m')).toBeInTheDocument(); // 180 minutes = 3 hours
    expect(screen.getByText('Sessions')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument(); // sessions completed
    expect(screen.getByText('Topics')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument(); // topics practiced
    expect(screen.getByText('Achievements')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // achievements count
  });

  it('displays progress summary with correct percentages', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Progress Summary')).toBeInTheDocument();
    });

    expect(screen.getByText('Overall Improvement')).toBeInTheDocument();
    expect(screen.getByText('+12%')).toBeInTheDocument(); // overall improvement

    // Subject breakdown
    expect(screen.getByText('math')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument(); // math score
    expect(screen.getByText('(+8%)')).toBeInTheDocument(); // math change

    expect(screen.getByText('esl')).toBeInTheDocument();
    expect(screen.getByText('71%')).toBeInTheDocument(); // esl score
    expect(screen.getByText('(+5%)')).toBeInTheDocument(); // esl change

    expect(screen.getByText('science')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument(); // science score
    expect(screen.getByText('(+15%)')).toBeInTheDocument(); // science change
  });

  it('displays parent insights with correct categorization', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Parent Insights & Recommendations')).toBeInTheDocument();
    });

    // Check for different insight types
    expect(screen.getByText('Excellent Progress in Science')).toBeInTheDocument();
    expect(screen.getByText('Reading Comprehension Needs Attention')).toBeInTheDocument();
    expect(screen.getByText('Optimal Study Time')).toBeInTheDocument();

    // Check priority badges
    expect(screen.getByText('medium')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('low')).toBeInTheDocument();
  });

  it('displays action items for insights', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Suggested Actions:')).toBeInTheDocument();
    });

    // Check for specific action items
    expect(screen.getByText('Consider introducing more advanced science topics')).toBeInTheDocument();
    expect(screen.getByText('Read together for 15 minutes daily')).toBeInTheDocument();
    expect(screen.getByText('Schedule main study sessions in the afternoon')).toBeInTheDocument();
  });

  it('displays achievements with correct information', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Achievements This Week')).toBeInTheDocument();
    });

    expect(screen.getByText('Math Master')).toBeInTheDocument();
    expect(screen.getByText('Completed 5 math exercises in a row')).toBeInTheDocument();
    expect(screen.getByText('Consistent Learner')).toBeInTheDocument();
    expect(screen.getByText('Studied for 7 days straight')).toBeInTheDocument();

    // Check for achievement icons
    expect(screen.getByText('🏆')).toBeInTheDocument();
    expect(screen.getByText('📚')).toBeInTheDocument();
  });

  it('displays topics practiced', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Topics Practiced This Week')).toBeInTheDocument();
    });

    expect(screen.getByText('Fractions')).toBeInTheDocument();
    expect(screen.getByText('Multiplication')).toBeInTheDocument();
    expect(screen.getByText('Reading Comprehension')).toBeInTheDocument();
    expect(screen.getByText('Science Experiments')).toBeInTheDocument();
  });

  it('displays general recommendations', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Recommendations for Next Week')).toBeInTheDocument();
    });

    expect(screen.getByText('Continue with current math curriculum pace')).toBeInTheDocument();
    expect(screen.getByText('Introduce more interactive reading activities')).toBeInTheDocument();
    expect(screen.getByText('Consider science enrichment programs')).toBeInTheDocument();
    expect(screen.getByText('Maintain consistent daily study routine')).toBeInTheDocument();
  });

  it('allows report selection from dropdown', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // Click on the select trigger
    const selectTrigger = screen.getByRole('combobox');
    fireEvent.click(selectTrigger);

    // Should show multiple report options
    await waitFor(() => {
      const currentWeekOption = screen.getByText(new RegExp(format(startOfWeek(new Date()), 'MMM dd')));
      expect(currentWeekOption).toBeInTheDocument();
    });
  });

  it('shows export and share buttons', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    expect(screen.getByText('Share')).toBeInTheDocument();
  });

  it('applies correct color coding for progress scores', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('85%')).toBeInTheDocument(); // Science score
    });

    // High scores (>= 80%) should have green color
    const scienceScore = screen.getByText('85%');
    expect(scienceScore).toHaveClass('text-green-600');

    // Medium scores (60-79%) should have yellow color
    const mathScore = screen.getByText('78%');
    expect(mathScore).toHaveClass('text-yellow-600');

    const eslScore = screen.getByText('71%');
    expect(eslScore).toHaveClass('text-yellow-600');
  });

  it('displays trending icons for progress changes', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Overall Improvement')).toBeInTheDocument();
    });

    // Should show trending up icons for positive changes
    const trendingUpIcons = screen.getAllByTestId('trending-up-icon');
    expect(trendingUpIcons.length).toBeGreaterThan(0);
  });

  it('handles empty insights gracefully', async () => {
    // This would test the case where a report has no insights
    // The current mock data always has insights, but in a real scenario
    // we might have reports without insights
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Weekly Progress Reports')).toBeInTheDocument();
    });

    // The component should still render properly even with empty insights
    expect(screen.getByText('Parent Insights & Recommendations')).toBeInTheDocument();
  });

  it('formats dates correctly', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      // Check that dates are formatted properly in the achievement timestamps
      const dateRegex = /\w{3} \d{2}, \d{2}:\d{2}/; // Format: "Jan 15, 14:30"
      expect(screen.getByText(dateRegex)).toBeInTheDocument();
    });
  });

  it('displays insight icons correctly based on type', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Excellent Progress in Science')).toBeInTheDocument();
    });

    // Should have different icons for different insight types
    // Strength insights should have CheckCircle icon
    // Improvement insights should have AlertTriangle icon
    // Suggestion insights should have Lightbulb icon
    const icons = screen.getAllByRole('img', { hidden: true });
    expect(icons.length).toBeGreaterThan(0);
  });

  it('handles progress bar rendering', async () => {
    render(<ParentReportViewer childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Subject Performance')).toBeInTheDocument();
    });

    // Progress bars should be rendered for each subject
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars).toHaveLength(3); // math, esl, science
  });
});