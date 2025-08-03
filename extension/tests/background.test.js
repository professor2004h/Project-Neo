/**
 * Unit tests for Chrome Extension Background Script
 */

// Mock Chrome APIs
global.chrome = {
  runtime: {
    onInstalled: { addListener: jest.fn() },
    onMessage: { addListener: jest.fn() },
    getURL: jest.fn((path) => `chrome-extension://test/${path}`)
  },
  tabs: {
    onActivated: { addListener: jest.fn() },
    onUpdated: { addListener: jest.fn() },
    get: jest.fn(),
    create: jest.fn(),
    query: jest.fn(),
    sendMessage: jest.fn()
  },
  contextMenus: {
    create: jest.fn(),
    onClicked: { addListener: jest.fn() }
  },
  scripting: {
    executeScript: jest.fn()
  },
  storage: {
    sync: {
      get: jest.fn(),
      set: jest.fn(),
      remove: jest.fn()
    }
  }
};

// Mock fetch
global.fetch = jest.fn();

describe('ExtensionBackground', () => {
  let ExtensionBackground;
  let backgroundInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset fetch mock
    fetch.mockClear();
    
    // Import the background script class
    // Note: In actual implementation, you'd need to structure the background.js
    // to export the class for testing
    ExtensionBackground = class {
      constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.isAuthenticated = false;
        this.userProfile = null;
        this.init();
      }

      init() {
        chrome.runtime.onInstalled.addListener(this.handleInstalled.bind(this));
        chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
        chrome.tabs.onActivated.addListener(this.handleTabActivated.bind(this));
        chrome.tabs.onUpdated.addListener(this.handleTabUpdated.bind(this));
        this.setupContextMenu();
        this.checkAuthStatus();
      }

      handleInstalled(details) {
        console.log('Extension installed:', details.reason);
        chrome.storage.sync.set({
          settings: {
            autoHelp: true,
            contextualHints: true,
            voiceEnabled: false,
            difficultyLevel: 'auto'
          }
        });
      }

      async handleMessage(request, sender, sendResponse) {
        switch (request.action) {
          case 'getAuthStatus':
            sendResponse({ authenticated: this.isAuthenticated, profile: this.userProfile });
            break;
          case 'authenticate':
            const authResult = await this.authenticate(request.credentials);
            sendResponse(authResult);
            break;
          case 'askQuestion':
            const answer = await this.askTutorQuestion(request.question, request.context);
            sendResponse(answer);
            break;
          default:
            sendResponse({ error: 'Unknown action' });
        }
        return true;
      }

      setupContextMenu() {
        chrome.contextMenus.create({
          id: 'explainSelection',
          title: 'Explain with AI Tutor',
          contexts: ['selection']
        });
      }

      isEducationalSite(url) {
        const educationalDomains = [
          'cambridge.org',
          'bbc.co.uk/bitesize',
          'khanacademy.org'
        ];
        return educationalDomains.some(domain => url.includes(domain));
      }

      async authenticate(credentials) {
        try {
          const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials)
          });

          if (response.ok) {
            const data = await response.json();
            this.isAuthenticated = true;
            this.userProfile = data.profile;
            return { success: true, profile: data.profile };
          } else {
            return { success: false, error: 'Authentication failed' };
          }
        } catch (error) {
          return { success: false, error: error.message };
        }
      }

      async askTutorQuestion(question, context = {}) {
        if (!this.isAuthenticated) {
          throw new Error('User not authenticated');
        }

        const response = await fetch(`${this.apiBaseUrl}/tutor/ask`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          },
          body: JSON.stringify({ question, context })
        });

        if (response.ok) {
          return await response.json();
        } else {
          throw new Error('Failed to get tutor response');
        }
      }

      async checkAuthStatus() {
        const result = await chrome.storage.sync.get(['authToken', 'userProfile']);
        if (result.authToken) {
          this.isAuthenticated = true;
          this.userProfile = result.userProfile;
        }
      }
    };

    backgroundInstance = new ExtensionBackground();
  });

  describe('Initialization', () => {
    test('should set up event listeners on initialization', () => {
      expect(chrome.runtime.onInstalled.addListener).toHaveBeenCalled();
      expect(chrome.runtime.onMessage.addListener).toHaveBeenCalled();
      expect(chrome.tabs.onActivated.addListener).toHaveBeenCalled();
      expect(chrome.tabs.onUpdated.addListener).toHaveBeenCalled();
    });

    test('should create context menu items', () => {
      expect(chrome.contextMenus.create).toHaveBeenCalledWith({
        id: 'explainSelection',
        title: 'Explain with AI Tutor',
        contexts: ['selection']
      });
    });

    test('should check authentication status on init', () => {
      expect(chrome.storage.sync.get).toHaveBeenCalledWith(['authToken', 'userProfile']);
    });
  });

  describe('Installation Handler', () => {
    test('should set default settings on installation', () => {
      backgroundInstance.handleInstalled({ reason: 'install' });

      expect(chrome.storage.sync.set).toHaveBeenCalledWith({
        settings: {
          autoHelp: true,
          contextualHints: true,
          voiceEnabled: false,
          difficultyLevel: 'auto'
        }
      });
    });
  });

  describe('Message Handler', () => {
    test('should handle getAuthStatus message', async () => {
      const mockSendResponse = jest.fn();
      backgroundInstance.isAuthenticated = true;
      backgroundInstance.userProfile = { name: 'Test User' };

      await backgroundInstance.handleMessage(
        { action: 'getAuthStatus' },
        {},
        mockSendResponse
      );

      expect(mockSendResponse).toHaveBeenCalledWith({
        authenticated: true,
        profile: { name: 'Test User' }
      });
    });

    test('should handle unknown action', async () => {
      const mockSendResponse = jest.fn();

      await backgroundInstance.handleMessage(
        { action: 'unknownAction' },
        {},
        mockSendResponse
      );

      expect(mockSendResponse).toHaveBeenCalledWith({
        error: 'Unknown action'
      });
    });
  });

  describe('Educational Site Detection', () => {
    test('should identify educational sites correctly', () => {
      expect(backgroundInstance.isEducationalSite('https://www.cambridge.org/test')).toBe(true);
      expect(backgroundInstance.isEducationalSite('https://www.bbc.co.uk/bitesize/test')).toBe(true);
      expect(backgroundInstance.isEducationalSite('https://www.khanacademy.org/test')).toBe(true);
      expect(backgroundInstance.isEducationalSite('https://www.google.com')).toBe(false);
    });
  });

  describe('Authentication', () => {
    test('should authenticate successfully with valid credentials', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          token: 'test-token',
          profile: { name: 'Test User', role: 'parent' }
        })
      };
      fetch.mockResolvedValue(mockResponse);

      const result = await backgroundInstance.authenticate({
        email: 'test@example.com',
        password: 'password'
      });

      expect(result).toEqual({
        success: true,
        profile: { name: 'Test User', role: 'parent' }
      });
      expect(backgroundInstance.isAuthenticated).toBe(true);
    });

    test('should handle authentication failure', async () => {
      const mockResponse = { ok: false };
      fetch.mockResolvedValue(mockResponse);

      const result = await backgroundInstance.authenticate({
        email: 'test@example.com',
        password: 'wrong-password'
      });

      expect(result).toEqual({
        success: false,
        error: 'Authentication failed'
      });
      expect(backgroundInstance.isAuthenticated).toBe(false);
    });

    test('should handle network errors during authentication', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      const result = await backgroundInstance.authenticate({
        email: 'test@example.com',
        password: 'password'
      });

      expect(result).toEqual({
        success: false,
        error: 'Network error'
      });
    });
  });

  describe('Tutor Questions', () => {
    beforeEach(() => {
      backgroundInstance.isAuthenticated = true;
    });

    test('should ask tutor question when authenticated', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          answer: 'This is the explanation',
          confidence: 0.9
        })
      };
      fetch.mockResolvedValue(mockResponse);

      const result = await backgroundInstance.askTutorQuestion(
        'What is 2+2?',
        { subject: 'math' }
      );

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/tutor/ask',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          },
          body: JSON.stringify({
            question: 'What is 2+2?',
            context: { subject: 'math' }
          })
        })
      );

      expect(result).toEqual({
        answer: 'This is the explanation',
        confidence: 0.9
      });
    });

    test('should throw error when not authenticated', async () => {
      backgroundInstance.isAuthenticated = false;

      await expect(
        backgroundInstance.askTutorQuestion('What is 2+2?')
      ).rejects.toThrow('User not authenticated');
    });

    test('should handle API errors', async () => {
      const mockResponse = { ok: false };
      fetch.mockResolvedValue(mockResponse);

      await expect(
        backgroundInstance.askTutorQuestion('What is 2+2?')
      ).rejects.toThrow('Failed to get tutor response');
    });
  });

  describe('Auth Status Check', () => {
    test('should set authenticated status when token exists', async () => {
      chrome.storage.sync.get.mockResolvedValue({
        authToken: 'test-token',
        userProfile: { name: 'Test User' }
      });

      await backgroundInstance.checkAuthStatus();

      expect(backgroundInstance.isAuthenticated).toBe(true);
      expect(backgroundInstance.userProfile).toEqual({ name: 'Test User' });
    });

    test('should remain unauthenticated when no token exists', async () => {
      chrome.storage.sync.get.mockResolvedValue({});

      await backgroundInstance.checkAuthStatus();

      expect(backgroundInstance.isAuthenticated).toBe(false);
      expect(backgroundInstance.userProfile).toBeNull();
    });
  });
});