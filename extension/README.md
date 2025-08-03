# Cambridge AI Tutor Chrome Extension

A Chrome extension that provides AI-powered educational support for Cambridge primary curriculum students. The extension integrates with educational websites to offer context-aware help, explanations, and tutoring assistance.

## Features

### Core Functionality
- **Context-Aware Help**: Automatically detects educational content on web pages
- **AI Tutoring**: Provides explanations and answers questions about curriculum topics
- **Educational Site Integration**: Works seamlessly with Cambridge, BBC Bitesize, Khan Academy, and other educational platforms
- **Multi-Platform Sync**: Synchronizes with the main Cambridge AI Tutor web application

### User Interface
- **Floating Help Button**: Always-accessible help button on educational pages
- **Interactive Widget**: Chat-like interface for asking questions and getting explanations
- **Popup Interface**: Quick access to settings and account management
- **Context Menu**: Right-click options for explaining selected text

### Educational Features
- **Curriculum Alignment**: All content aligned with Cambridge primary standards
- **Age-Appropriate Responses**: Explanations tailored to the child's grade level
- **Subject Support**: Mathematics, English as Second Language (ESL), and Science
- **Progress Tracking**: Monitors learning activities and provides insights

## Installation

### Development Installation
1. Clone the repository and navigate to the extension directory
2. Install dependencies: `npm install`
3. Run tests: `npm test`
4. Open Chrome and go to `chrome://extensions/`
5. Enable "Developer mode"
6. Click "Load unpacked" and select the extension directory

### Production Installation
1. Download the extension from the Chrome Web Store (when available)
2. Click "Add to Chrome" to install
3. Sign in with your Cambridge AI Tutor account
4. Grant necessary permissions for educational site access

## Usage

### Getting Started
1. Install the extension and sign in to your account
2. Navigate to any educational website (Cambridge, BBC Bitesize, Khan Academy, etc.)
3. Look for the green help button in the bottom-right corner
4. Click the button to open the AI tutor widget

### Asking Questions
1. Type your question in the chat interface
2. The AI tutor will provide age-appropriate explanations
3. Ask follow-up questions for deeper understanding
4. All interactions are saved to your learning progress

### Context-Aware Help
1. Select any text on an educational page
2. Right-click and choose "Explain with AI Tutor"
3. Get instant explanations tailored to the content
4. The extension automatically detects the subject and grade level

### Settings and Preferences
1. Click the extension icon in the Chrome toolbar
2. Access settings through the popup interface
3. Configure auto-help, contextual hints, and voice features
4. View recent learning activity and progress

## Technical Architecture

### Components
- **Background Script**: Handles authentication, API communication, and context menus
- **Content Script**: Injects help interface and analyzes page content
- **Popup Interface**: Provides quick access to settings and account management
- **Manifest**: Defines permissions and extension configuration

### API Integration
- Connects to the Cambridge AI Tutor backend API
- Supports real-time synchronization with web and mobile apps
- Handles authentication and session management
- Tracks learning activities for progress reporting

### Security and Privacy
- Follows Chrome extension security best practices
- Encrypts all communication with backend services
- Complies with COPPA and GDPR privacy regulations
- Minimal data collection focused on educational improvement

## Development

### Prerequisites
- Node.js 16+ and npm
- Chrome browser for testing
- Access to Cambridge AI Tutor backend API

### Setup
```bash
# Install dependencies
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Build for production
npm run build

# Package for distribution
npm run package
```

### Testing
The extension includes comprehensive test suites:
- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test communication between components
- **End-to-End Tests**: Test complete user workflows

### File Structure
```
extension/
├── manifest.json          # Extension configuration
├── background.js          # Background script
├── content.js            # Content script for page integration
├── content.css           # Styles for injected content
├── popup.html            # Popup interface HTML
├── popup.js              # Popup interface logic
├── popup.css             # Popup interface styles
├── icons/                # Extension icons
├── tests/                # Test files
│   ├── setup.js          # Test configuration
│   ├── background.test.js # Background script tests
│   ├── content.test.js   # Content script tests
│   ├── popup.test.js     # Popup interface tests
│   └── integration.test.js # Integration tests
├── package.json          # Dependencies and scripts
└── README.md            # This file
```

## Permissions

The extension requires the following permissions:
- **activeTab**: Access to the currently active tab for content analysis
- **storage**: Store user preferences and authentication tokens
- **scripting**: Inject content scripts into educational websites
- **tabs**: Manage tab interactions and navigation

### Host Permissions
- Cambridge educational sites (`*.cambridge.org`)
- BBC Bitesize (`*.bbc.co.uk/bitesize`)
- Khan Academy (`*.khanacademy.org`)
- Math is Fun (`*.mathsisfun.com`)
- Education.com (`*.education.com`)
- Local development (`http://localhost:*`)

## Contributing

### Code Style
- Follow ESLint configuration in package.json
- Use modern JavaScript (ES2021+)
- Write comprehensive tests for new features
- Document all public functions and classes

### Pull Request Process
1. Fork the repository and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass and code meets coverage requirements
4. Update documentation as needed
5. Submit pull request with clear description

### Bug Reports
1. Use the GitHub issue tracker
2. Include steps to reproduce the issue
3. Provide browser version and extension version
4. Include relevant console errors or logs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the FAQ in the main Cambridge AI Tutor documentation
- Submit issues through the GitHub issue tracker
- Contact support through the main application

## Changelog

### Version 1.0.0
- Initial release with core functionality
- Educational site integration
- AI tutoring capabilities
- Context-aware help system
- Progress tracking integration