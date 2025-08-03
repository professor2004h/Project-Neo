import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ParentSettings } from '../parent-settings';
import { ParentalControl } from '../parent-types';

describe('ParentSettings', () => {
  const mockChildId = 'child123';
  const mockOnSettingsUpdate = jest.fn();
  const mockCurrentSettings: ParentalControl[] = [
    {
      control_id: 'session_time_limit',
      child_id: mockChildId,
      setting_name: 'Session Time Limit',
      setting_value: 45,
      description: 'Maximum time per study session in minutes',
      category: 'time',
      updated_at: new Date()
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders settings header and description', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={mockCurrentSettings}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    expect(screen.getByText('Parental Controls & Settings')).toBeInTheDocument();
    expect(screen.getByText('Manage your child\'s learning environment and privacy settings')).toBeInTheDocument();
  });

  it('displays all settings tabs', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={mockCurrentSettings}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    expect(screen.getByText('Safety')).toBeInTheDocument();
    expect(screen.getByText('Time & Schedule')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
    expect(screen.getByText('Privacy')).toBeInTheDocument();
  });

  it('initializes with default settings when none provided', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Should show default values
    expect(screen.getByText('Voice Interaction')).toBeInTheDocument();
    expect(screen.getByText('Image Sharing')).toBeInTheDocument();
    expect(screen.getByText('Content Filtering Level')).toBeInTheDocument();
  });

  it('displays safety controls correctly', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Safety tab should be active by default
    expect(screen.getByText('Child Safety Controls')).toBeInTheDocument();
    expect(screen.getByText('Allow your child to speak with the AI tutor using voice commands')).toBeInTheDocument();
    expect(screen.getByText('Allow your child to share drawings and images with the tutor')).toBeInTheDocument();
    expect(screen.getByText('Control the level of content filtering for educational materials')).toBeInTheDocument();
  });

  it('allows toggling voice interaction setting', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Find the voice interaction switch
    const voiceSwitch = screen.getByRole('switch', { name: /voice interaction/i });
    expect(voiceSwitch).toBeChecked(); // Default is true

    // Toggle it off
    fireEvent.click(voiceSwitch);
    expect(voiceSwitch).not.toBeChecked();

    // Should show save changes button
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });
  });

  it('allows toggling image sharing setting', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Find the image sharing switch
    const imageSwitch = screen.getByRole('switch', { name: /image sharing/i });
    expect(imageSwitch).not.toBeChecked(); // Default is false

    // Toggle it on
    fireEvent.click(imageSwitch);
    expect(imageSwitch).toBeChecked();

    // Should show save changes button
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });
  });

  it('displays content filtering options', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on content filtering select
    const filteringSelect = screen.getByRole('combobox');
    fireEvent.click(filteringSelect);

    expect(screen.getByText('Strict')).toBeInTheDocument();
    expect(screen.getByText('Maximum filtering, very conservative')).toBeInTheDocument();
    expect(screen.getByText('Moderate')).toBeInTheDocument();
    expect(screen.getByText('Balanced filtering, recommended')).toBeInTheDocument();
    expect(screen.getByText('Relaxed')).toBeInTheDocument();
    expect(screen.getByText('Minimal filtering, more freedom')).toBeInTheDocument();
  });

  it('displays time and schedule settings', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    expect(screen.getByText('Session Time Limits')).toBeInTheDocument();
    expect(screen.getByText('Maximum Session Duration')).toBeInTheDocument();
    expect(screen.getByText('45 minutes')).toBeInTheDocument(); // Default value
    expect(screen.getByText('Study Schedule')).toBeInTheDocument();
  });

  it('allows adjusting session time limit with slider', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    // Find the slider
    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();

    // Change the slider value
    fireEvent.change(slider, { target: { value: '60' } });

    // Should show save changes button
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });
  });

  it('allows adding study schedules', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    // Click Add Schedule button
    fireEvent.click(screen.getByText('Add Schedule'));

    // Should show a new schedule form
    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    expect(screen.getByText('Day of Week')).toBeInTheDocument();
    expect(screen.getByText('Start Time')).toBeInTheDocument();
    expect(screen.getByText('Duration (minutes)')).toBeInTheDocument();
    expect(screen.getByText('Subjects')).toBeInTheDocument();
  });

  it('allows removing study schedules', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    // Add a schedule first
    fireEvent.click(screen.getByText('Add Schedule'));

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    // Find and click the remove button
    const removeButton = screen.getByRole('button', { name: '' });
    fireEvent.click(removeButton);

    // Schedule should be removed
    await waitFor(() => {
      expect(screen.queryByText('Monday')).not.toBeInTheDocument();
    });
  });

  it('displays content preferences', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Content tab
    fireEvent.click(screen.getByText('Content'));

    expect(screen.getByText('Content Preferences')).toBeInTheDocument();
    expect(screen.getByText('Difficulty Level Preference')).toBeInTheDocument();
    expect(screen.getByText('Set the preferred difficulty level for learning content')).toBeInTheDocument();
    expect(screen.getByText('Learning Style Adaptation')).toBeInTheDocument();
    expect(screen.getByText('How should the AI adapt to your child\'s learning style?')).toBeInTheDocument();
  });

  it('displays privacy settings', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Privacy tab
    fireEvent.click(screen.getByText('Privacy'));

    expect(screen.getByText('Data Privacy & Security')).toBeInTheDocument();
    expect(screen.getByText('Learning Analytics')).toBeInTheDocument();
    expect(screen.getByText('Collect learning data to provide progress insights and personalized recommendations')).toBeInTheDocument();
    expect(screen.getByText('Educational Research Participation')).toBeInTheDocument();
    expect(screen.getByText('Share anonymized data with educational research partners to improve learning outcomes')).toBeInTheDocument();
  });

  it('displays data management options', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Privacy tab
    fireEvent.click(screen.getByText('Privacy'));

    expect(screen.getByText('Data Management')).toBeInTheDocument();
    expect(screen.getByText('Export Data')).toBeInTheDocument();
    expect(screen.getByText('Delete Account')).toBeInTheDocument();
  });

  it('displays privacy protection notice', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Privacy tab
    fireEvent.click(screen.getByText('Privacy'));

    expect(screen.getByText('Privacy Protection')).toBeInTheDocument();
    expect(screen.getByText('We comply with COPPA and GDPR regulations to protect your child\'s privacy. All data is encrypted and stored securely. You can request data deletion at any time.')).toBeInTheDocument();
    expect(screen.getByText('Read our Privacy Policy')).toBeInTheDocument();
  });

  it('saves settings when save button is clicked', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Make a change to trigger save button
    const voiceSwitch = screen.getByRole('switch', { name: /voice interaction/i });
    fireEvent.click(voiceSwitch);

    // Click save button
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Save Changes'));

    // Should show saving state
    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });

    // Should call the callback
    await waitFor(() => {
      expect(mockOnSettingsUpdate).toHaveBeenCalled();
    });
  });

  it('allows selecting subjects for study schedules', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    // Add a schedule
    fireEvent.click(screen.getByText('Add Schedule'));

    await waitFor(() => {
      expect(screen.getByText('math')).toBeInTheDocument();
    });

    // Should show subject badges
    expect(screen.getByText('esl')).toBeInTheDocument();
    expect(screen.getByText('science')).toBeInTheDocument();

    // Click on a subject to toggle it
    fireEvent.click(screen.getByText('esl'));

    // Should show save changes button
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });
  });

  it('handles empty schedule state', () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    // Should show empty state message
    expect(screen.getByText('No study schedules set up yet.')).toBeInTheDocument();
  });

  it('displays day names correctly in schedule', async () => {
    render(
      <ParentSettings 
        childId={mockChildId}
        currentSettings={[]}
        onSettingsUpdate={mockOnSettingsUpdate}
      />
    );

    // Click on Time & Schedule tab
    fireEvent.click(screen.getByText('Time & Schedule'));

    // Add a schedule
    fireEvent.click(screen.getByText('Add Schedule'));

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    // Click on day selector
    const daySelect = screen.getByRole('combobox');
    fireEvent.click(daySelect);

    // Should show all days of the week
    expect(screen.getByText('Sunday')).toBeInTheDocument();
    expect(screen.getByText('Tuesday')).toBeInTheDocument();
    expect(screen.getByText('Wednesday')).toBeInTheDocument();
    expect(screen.getByText('Thursday')).toBeInTheDocument();
    expect(screen.getByText('Friday')).toBeInTheDocument();
    expect(screen.getByText('Saturday')).toBeInTheDocument();
  });
});