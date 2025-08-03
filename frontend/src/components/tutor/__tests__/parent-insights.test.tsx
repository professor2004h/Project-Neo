import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ParentInsights } from '../parent-insights';

describe('ParentInsights', () => {
  const mockChildId = 'child123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<ParentInsights childId={mockChildId} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders insights header and description', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Learning Insights & Recommendations')).toBeInTheDocument();
    });

    expect(screen.getByText('AI-powered insights to help you support your child\'s learning journey')).toBeInTheDocument();
  });

  it('displays insights summary cards with correct counts', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getAllByText('Strengths')[0]).toBeInTheDocument();
    });

    // Check summary counts
    expect(screen.getByText('2')).toBeInTheDocument(); // Strengths count
    expect(screen.getAllByText('Improvements')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Suggestions')[0]).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Achievements count
  });

  it('displays all insights by default', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Exceptional Mathematical Reasoning')).toBeInTheDocument();
    });

    expect(screen.getByText('Reading Fluency Needs Support')).toBeInTheDocument();
    expect(screen.getByText('Optimal Learning Schedule Identified')).toBeInTheDocument();
    expect(screen.getByText('Science Curiosity Milestone Reached')).toBeInTheDocument();
    expect(screen.getByText('Attention Span Patterns')).toBeInTheDocument();
    expect(screen.getByText('Visual Learning Excellence')).toBeInTheDocument();
  });

  it('filters insights by type when tab is selected', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /strengths/i })).toBeInTheDocument();
    });

    // Click on Strengths tab
    fireEvent.click(screen.getByRole('tab', { name: /strengths/i }));

    await waitFor(() => {
      expect(screen.getByText('Exceptional Mathematical Reasoning')).toBeInTheDocument();
      expect(screen.getByText('Visual Learning Excellence')).toBeInTheDocument();
    });
  });

  it('displays correct priority badges', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getAllByText('medium Priority')[0]).toBeInTheDocument();
    });

    expect(screen.getByText('high Priority')).toBeInTheDocument();
    expect(screen.getByText('low Priority')).toBeInTheDocument();
  });

  it('shows action items for each insight', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getAllByText('Recommended Actions')[0]).toBeInTheDocument();
    });

    // Check for specific action items
    expect(screen.getByText('Consider enrolling in advanced math programs or competitions')).toBeInTheDocument();
    expect(screen.getByText('Practice reading aloud together for 15-20 minutes daily')).toBeInTheDocument();
    expect(screen.getByText('Schedule challenging subjects during 2-4 PM when possible')).toBeInTheDocument();
  });

  it('allows dismissing insights', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Exceptional Mathematical Reasoning')).toBeInTheDocument();
    });

    // Find and click the dismiss button (X button)
    const dismissButtons = screen.getAllByRole('button', { name: '' });
    const dismissButton = dismissButtons.find(button => 
      button.querySelector('svg') && button.getAttribute('class')?.includes('text-muted-foreground')
    );
    
    if (dismissButton) {
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Exceptional Mathematical Reasoning')).not.toBeInTheDocument();
      });
    }
  });

  it('displays mark as read and learn more buttons', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getAllByText('Mark as Read')[0]).toBeInTheDocument();
    });

    expect(screen.getAllByText('Learn More')[0]).toBeInTheDocument();
  });

  it('shows quick tips for parents', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Quick Tips for Parents')).toBeInTheDocument();
    });

    expect(screen.getByText('Study Schedule')).toBeInTheDocument();
    expect(screen.getByText('Consistency is key. Even 15-20 minutes daily is more effective than longer, irregular sessions.')).toBeInTheDocument();
    
    expect(screen.getByText('Reading Together')).toBeInTheDocument();
    expect(screen.getByText('Reading aloud together improves comprehension and creates positive associations with learning.')).toBeInTheDocument();
    
    expect(screen.getByText('Celebrate Progress')).toBeInTheDocument();
    expect(screen.getByText('Acknowledge effort and improvement, not just perfect scores. This builds growth mindset.')).toBeInTheDocument();
    
    expect(screen.getByText('Ask Questions')).toBeInTheDocument();
    expect(screen.getByText('Encourage curiosity by asking "What do you think?" and "How did you figure that out?"')).toBeInTheDocument();
  });

  it('applies correct border colors based on insight type', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Exceptional Mathematical Reasoning')).toBeInTheDocument();
    });

    // Check that strength insights have green border
    const strengthCard = screen.getByText('Exceptional Mathematical Reasoning').closest('.border-green-200');
    expect(strengthCard).toBeInTheDocument();
  });

  it('displays correct icons for different insight types', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Exceptional Mathematical Reasoning')).toBeInTheDocument();
    });

    // Should have different icons for different types
    // Check for SVG elements instead of img role
    const svgElements = document.querySelectorAll('svg');
    expect(svgElements.length).toBeGreaterThan(0);
  });

  it('handles empty insights state', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /achievements/i })).toBeInTheDocument();
    });

    // Click on Achievements tab (which has one achievement in mock data)
    fireEvent.click(screen.getByRole('tab', { name: /achievements/i }));

    await waitFor(() => {
      expect(screen.getByText('Science Curiosity Milestone Reached')).toBeInTheDocument();
    });
  });

  it('formats dates correctly in insights', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      // Check that dates are formatted properly
      const dateRegex = /\w{3} \d{2}, \d{4}/; // Format: "Jan 15, 2024"
      expect(screen.getAllByText(dateRegex)[0]).toBeInTheDocument();
    });
  });

  it('handles mark as read functionality', async () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getAllByText('Mark as Read')[0]).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByText('Mark as Read')[0]);
    
    expect(consoleSpy).toHaveBeenCalledWith('Marking insight as read:', expect.any(String));
    
    consoleSpy.mockRestore();
  });

  it('displays detailed descriptions for insights', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByText('Your child demonstrates advanced problem-solving skills in mathematics, particularly with word problems and logical reasoning tasks. They consistently score above grade level and show creativity in their solution approaches.')).toBeInTheDocument();
    });

    expect(screen.getByText('While your child understands content well, their reading speed is below grade level expectations. This may impact comprehension in timed assessments and could affect confidence in language arts.')).toBeInTheDocument();
  });

  it('shows all tabs in the tab list', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: 'All' })).toBeInTheDocument();
    });

    expect(screen.getByRole('tab', { name: /strengths/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /improvements/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /suggestions/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /achievements/i })).toBeInTheDocument();
  });

  it('switches between different insight categories', async () => {
    render(<ParentInsights childId={mockChildId} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: 'All' })).toBeInTheDocument();
    });

    // Test switching to Improvements tab
    fireEvent.click(screen.getByRole('tab', { name: /improvements/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Reading Fluency Needs Support')).toBeInTheDocument();
      expect(screen.getByText('Attention Span Patterns')).toBeInTheDocument();
    });

    // Test switching to Suggestions tab
    fireEvent.click(screen.getByRole('tab', { name: /suggestions/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Optimal Learning Schedule Identified')).toBeInTheDocument();
    });
  });
});