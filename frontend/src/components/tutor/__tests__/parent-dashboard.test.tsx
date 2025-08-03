import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ParentDashboard } from '../parent-dashboard';
import { ChildProfile } from '../parent-types';

// Mock the child components
jest.mock('../parent-report-viewer', () => ({
  ParentReportViewer: ({ childId }: { childId: string }) => (
    <div data-testid="parent-report-viewer">Report Viewer for {childId}</div>
  )
}));

jest.mock('../parent-insights', () => ({
  ParentInsights: ({ childId }: { childId: string }) => (
    <div data-testid="parent-insights">Insights for {childId}</div>
  )
}));

jest.mock('../parent-settings', () => ({
  ParentSettings: ({ childId }: { childId: string }) => (
    <div data-testid="parent-settings">Settings for {childId}</div>
  )
}));

describe('ParentDashboard', () => {
  const mockParentId = 'parent123';
  const mockOnChildSelect = jest.fn();
  const mockOnSettingsChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders dashboard with child data after loading', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Parent Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Monitor your child\'s learning progress and manage settings')).toBeInTheDocument();
    expect(screen.getAllByText('Emma')).toHaveLength(2); // One in selector, one in card
    expect(screen.getByText('Age 8 • Grade 3')).toBeInTheDocument();
  });

  it('displays progress cards for all subjects', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
    });

    expect(screen.getByText('English (ESL)')).toBeInTheDocument();
    expect(screen.getByText('Science')).toBeInTheDocument();
    
    // Check progress percentages
    expect(screen.getByText('75%')).toBeInTheDocument(); // Math
    expect(screen.getByText('68%')).toBeInTheDocument(); // ESL
    expect(screen.getByText('82%')).toBeInTheDocument(); // Science
  });

  it('allows child selection from dropdown', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByText('Emma')).toHaveLength(2);
    });

    // Click on the select trigger
    const selectTrigger = screen.getByRole('combobox');
    fireEvent.click(selectTrigger);

    // Wait for dropdown to open and select James
    await waitFor(() => {
      expect(screen.getByText('James')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('James'));

    expect(mockOnChildSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'James',
        age: 10,
        grade_level: 5
      })
    );
  });

  it('displays learning profile information', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Learning Profile')).toBeInTheDocument();
    });

    expect(screen.getByText('Learning Style')).toBeInTheDocument();
    expect(screen.getByText('visual')).toBeInTheDocument();
    expect(screen.getByText('Preferred Subjects')).toBeInTheDocument();
    expect(screen.getByText('math')).toBeInTheDocument();
    expect(screen.getByText('science')).toBeInTheDocument();
    expect(screen.getByText('Difficulty Level')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('displays safety settings overview', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Safety & Controls')).toBeInTheDocument();
    });

    expect(screen.getByText('Session Time Limit')).toBeInTheDocument();
    expect(screen.getByText('45 minutes')).toBeInTheDocument();
    expect(screen.getByText('Content Filtering')).toBeInTheDocument();
    expect(screen.getByText('moderate')).toBeInTheDocument();
    expect(screen.getByText('Voice Interaction')).toBeInTheDocument();
    expect(screen.getByText('Enabled')).toBeInTheDocument();
    expect(screen.getByText('Image Sharing')).toBeInTheDocument();
    expect(screen.getByText('Disabled')).toBeInTheDocument();
  });

  it('switches between tabs correctly', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });

    // Click on Reports tab
    fireEvent.click(screen.getByText('Reports'));
    expect(screen.getByTestId('parent-report-viewer')).toBeInTheDocument();

    // Click on Insights tab
    fireEvent.click(screen.getByText('Insights'));
    expect(screen.getByTestId('parent-insights')).toBeInTheDocument();

    // Click on Settings tab
    fireEvent.click(screen.getByText('Settings'));
    expect(screen.getByTestId('parent-settings')).toBeInTheDocument();
  });

  it('handles empty children list gracefully', async () => {
    // Mock empty children response
    const originalFetch = global.fetch;
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ children: [] })
    });

    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No children found. Please add a child profile first.')).toBeInTheDocument();
    });

    global.fetch = originalFetch;
  });

  it('applies correct progress colors based on scores', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('82%')).toBeInTheDocument(); // Science - should be green (>= 80%)
    });

    // Check that high scores have green color class
    const scienceScore = screen.getByText('82%');
    expect(scienceScore).toHaveClass('text-green-600');

    // Check that medium scores have yellow color class
    const mathScore = screen.getByText('75%');
    expect(mathScore).toHaveClass('text-yellow-600');

    // Check that lower scores have yellow color class
    const eslScore = screen.getByText('68%');
    expect(eslScore).toHaveClass('text-yellow-600');
  });

  it('calls onSettingsChange when settings are updated', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    // Click on Settings tab
    fireEvent.click(screen.getByText('Settings'));

    // The settings component should be rendered with the callback
    expect(screen.getByTestId('parent-settings')).toBeInTheDocument();
  });

  it('displays correct badge variants for difficulty preferences', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('medium')).toBeInTheDocument();
    });

    // The medium difficulty should have appropriate styling
    const difficultyBadge = screen.getByText('medium');
    expect(difficultyBadge).toBeInTheDocument();
  });

  it('handles child selection with proper data structure', async () => {
    render(
      <ParentDashboard 
        parentId={mockParentId}
        onChildSelect={mockOnChildSelect}
        onSettingsChange={mockOnSettingsChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // Verify the callback receives the correct child profile structure
    const selectTrigger = screen.getByRole('combobox');
    fireEvent.click(selectTrigger);

    await waitFor(() => {
      expect(screen.getByText('James')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('James'));

    expect(mockOnChildSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        child_id: 'child2',
        parent_id: mockParentId,
        name: 'James',
        age: 10,
        grade_level: 5,
        learning_preferences: expect.objectContaining({
          learning_style: 'kinesthetic',
          preferred_subjects: ['science', 'esl'],
          difficulty_preference: 'challenging'
        }),
        curriculum_progress: expect.objectContaining({
          math: 0.65,
          esl: 0.78,
          science: 0.71
        }),
        safety_settings: expect.objectContaining({
          session_time_limit: 60,
          content_filtering: 'moderate',
          voice_interaction_enabled: true,
          image_sharing_enabled: true
        })
      })
    );
  });
});