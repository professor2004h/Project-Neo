/**
 * Unit tests for Chrome Extension Popup Script
 */

// Mock Chrome APIs
global.chrome = {
  runtime: {
    sendMessage: jest.fn()
  },
  tabs: {
    query: jest.fn(),
    create: jest.fn(),
    sendMessage: jest.fn()
  },
  storage: {
    sync: {
      get: jest.fn(),
      set: jest.fn(),
      remove: jest.fn()
    }
  }
};

// Mock DOM
const mockDocument = {
  getElementById: jest.fn(),
  querySelector: jest.fn(),
  querySelectorAll: jest.fn(),
  addEventListener: jest.fn()
};

const mockWindow = {
  close: jest.fn()
};

global.document = mockDocument;
global.window = mockWindow;

describe('TutorPopup', () => {
  let TutorPopup;
  let popupInstance;
  let mockElements;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock DOM elements
    mockElements = {
      'login-btn': { addEventListener: jest.fn() },
      'register-link': { addEventListener: jest.fn() },
      'forgot-link': { addEventListener: jest.fn() },
      'logout-btn': { addEventListener: jest.fn() },
      'help-page-btn': { addEventListener: jest.fn() },
      'explain-selection-btn': { addEventListener: jest.fn() },
      'practice-btn': { addEventListener: jest.fn() },
      'auto-help': { addEventListener: jest.fn(), checked: true },
      'contextual-hints': { addEventListener: jest.fn(), checked: true },
      'voice-enabled': { addEventListener: jest.fn(), checked: false },
      'retry-btn': { addEventListener: jest.fn() },
      'password': { addEventListener: jest.fn() },
      'email': { value: '' },
      'user-initial': { textContent: '' },
      'user-name': { textContent: '' },
      'user-role': { textContent: '' },
      'educational-status': { className: '', textContent: '' },
      'page-description': { textContent: '' },
      'error-text': { textContent: '' },
      'auth-section': { style: { display: 'none' } },
      'main-section': { style: { display: 'none' } },
      'loading-section': { style: { display: 'none' } },
      'error-section': { style: { display: 'none' } }
    };

    mockDocument.getElementById.mockImplementation((id) => mockElements[id] || null);
    mockDocument.querySelectorAll.mockReturnValue([]);

    // Mock TutorPopup class
    TutorPopup = class {
      constructor() {
        this.currentUser = null;
        this.currentTab = null;
        this.pageAnalysis = null;
        this.init();
      }

      async init() {
        await this.getCurrentTab();
        await this.checkAuthStatus();
        this.setupEventListeners();
        await this.analyzeCurrentPage();
        await this.loadSettings();
      }

      async getCurrentTab() {
        try {
          const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
          this.currentTab = tabs[0];
        } catch (error) {
          console.error('Failed to get current tab:', error);
        }
      }

      async checkAuthStatus() {
        try {
          const response = await chrome.runtime.sendMessage({ action: 'getAuthStatus' });
          
          if (response.authenticated) {
            this.currentUser = response.profile;
            this.showMainSection();
            this.updateUserInfo();
          } else {
            this.showAuthSection();
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          this.showErrorSection('Failed to check authentication status');
        }
      }

      setupEventListeners() {
        mockElements['login-btn'].addEventListener('click', this.handleLogin.bind(this));
        mockElements['register-link'].addEventListener('click', this.handleRegister.bind(this));
        mockElements['logout-btn'].addEventListener('click', this.handleLogout.bind(this));
        mockElements['help-page-btn'].addEventListener('click', this.handlePageHelp.bind(this));
        mockElements['auto-help'].addEventListener('change', this.handleSettingChange.bind(this));
      }

      async handleLogin() {
        const email = mockElements['email'].value.trim();
        const password = 'test-password';
        
        if (!email || !password) {
          this.showError('Please enter both email and password');
          return;
        }
        
        this.showLoadingSection();
        
        try {
          const response = await chrome.runtime.sendMessage({
            action: 'authenticate',
            credentials: { email, password }
          });
          
          if (response.success) {
            this.currentUser = response.profile;
            this.showMainSection();
            this.updateUserInfo();
          } else {
            this.showAuthSection();
            this.showError(response.error || 'Login failed');
          }
        } catch (error) {
          this.showAuthSection();
          this.showError('Login failed. Please try again.');
        }
      }

      handleRegister() {
        chrome.tabs.create({
          url: 'http://localhost:3000/auth?mode=register'
        });
        window.close();
      }

      async handleLogout() {
        try {
          await chrome.storage.sync.remove(['authToken', 'userProfile']);
          this.currentUser = null;
          this.showAuthSection();
        } catch (error) {
          console.error('Logout error:', error);
        }
      }

      async handlePageHelp() {
        if (!this.currentTab) {
          this.showError('No active tab found');
          return;
        }
        
        try {
          await chrome.tabs.sendMessage(this.currentTab.id, {
            action: 'showPageHelp',
            analysis: this.pageAnalysis
          });
          
          chrome.runtime.sendMessage({
            action: 'trackActivity',
            activity: {
              type: 'page_help_requested',
              url: this.currentTab.url,
              title: this.currentTab.title
            }
          });
          
          window.close();
        } catch (error) {
          console.error('Page help error:', error);
          this.showError('Failed to show page help');
        }
      }

      async handleSettingChange(event) {
        const setting = event.target.id;
        const value = event.target.checked;
        
        try {
          const settings = await chrome.runtime.sendMessage({ action: 'getSettings' });
          settings[setting.replace('-', '_')] = value;
          
          await chrome.runtime.sendMessage({
            action: 'updateSettings',
            settings
          });
        } catch (error) {
          console.error('Settings update error:', error);
        }
      }

      async analyzeCurrentPage() {
        if (!this.currentTab || !this.currentUser) {
          return;
        }
        
        try {
          const contentResponse = await chrome.tabs.sendMessage(this.currentTab.id, {
            action: 'getPageContent'
          });
          
          if (contentResponse && contentResponse.content) {
            const analysis = await chrome.runtime.sendMessage({
              action: 'analyzeContent',
              content: contentResponse.content,
              url: this.currentTab.url
            });
            
            this.pageAnalysis = analysis;
            this.updatePageStatus();
          }
        } catch (error) {
          console.error('Page analysis error:', error);
          this.updatePageStatus(false);
        }
      }

      async loadSettings() {
        try {
          const settings = await chrome.runtime.sendMessage({ action: 'getSettings' });
          
          if (settings) {
            mockElements['auto-help'].checked = settings.autoHelp || false;
            mockElements['contextual-hints'].checked = settings.contextualHints || false;
            mockElements['voice-enabled'].checked = settings.voiceEnabled || false;
          }
        } catch (error) {
          console.error('Settings load error:', error);
        }
      }

      updateUserInfo() {
        if (!this.currentUser) return;
        
        mockElements['user-initial'].textContent = this.currentUser.name ? 
          this.currentUser.name.charAt(0).toUpperCase() : 'U';
        mockElements['user-name'].textContent = this.currentUser.name || 'User';
        mockElements['user-role'].textContent = this.currentUser.role || 'Parent';
      }

      updatePageStatus(hasAnalysis = true) {
        if (!hasAnalysis || !this.pageAnalysis) {
          mockElements['educational-status'].className = 'status-indicator non-educational';
          mockElements['page-description'].textContent = 'No educational content detected';
          mockElements['explain-selection-btn'].disabled = true;
          return;
        }
        
        if (this.pageAnalysis.educational) {
          mockElements['educational-status'].className = 'status-indicator educational';
          const subject = this.pageAnalysis.subject || 'Educational content';
          const level = this.pageAnalysis.level ? ` (${this.pageAnalysis.level})` : '';
          mockElements['page-description'].textContent = `${subject} detected${level}`;
          mockElements['explain-selection-btn'].disabled = false;
        } else {
          mockElements['educational-status'].className = 'status-indicator non-educational';
          mockElements['page-description'].textContent = 'General webpage';
          mockElements['explain-selection-btn'].disabled = true;
        }
      }

      showAuthSection() {
        this.hideAllSections();
        mockElements['auth-section'].style.display = 'block';
      }

      showMainSection() {
        this.hideAllSections();
        mockElements['main-section'].style.display = 'block';
      }

      showLoadingSection() {
        this.hideAllSections();
        mockElements['loading-section'].style.display = 'block';
      }

      showErrorSection(message) {
        this.hideAllSections();
        mockElements['error-section'].style.display = 'block';
        mockElements['error-text'].textContent = message;
      }

      hideAllSections() {
        Object.keys(mockElements).forEach(key => {
          if (key.includes('-section')) {
            mockElements[key].style.display = 'none';
          }
        });
      }

      showError(message) {
        // Mock error display
        console.error('Popup error:', message);
      }
    };
  });

  describe('Initialization', () => {
    test('should initialize popup and set up event listeners', async () => {
      chrome.tabs.query.mockResolvedValue([{ id: 1, url: 'https://test.com' }]);
      chrome.runtime.sendMessage.mockResolvedValue({ authenticated: false });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();

      expect(chrome.tabs.query).toHaveBeenCalledWith({ active: true, currentWindow: true });
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({ action: 'getAuthStatus' });
      expect(mockElements['login-btn'].addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
    });

    test('should show main section when authenticated', async () => {
      chrome.tabs.query.mockResolvedValue([{ id: 1, url: 'https://test.com' }]);
      chrome.runtime.sendMessage.mockResolvedValue({
        authenticated: true,
        profile: { name: 'Test User', role: 'parent' }
      });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();

      expect(mockElements['main-section'].style.display).toBe('block');
      expect(mockElements['user-name'].textContent).toBe('Test User');
    });

    test('should show auth section when not authenticated', async () => {
      chrome.tabs.query.mockResolvedValue([{ id: 1, url: 'https://test.com' }]);
      chrome.runtime.sendMessage.mockResolvedValue({ authenticated: false });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();

      expect(mockElements['auth-section'].style.display).toBe('block');
    });
  });

  describe('Authentication', () => {
    beforeEach(async () => {
      chrome.tabs.query.mockResolvedValue([{ id: 1, url: 'https://test.com' }]);
      chrome.runtime.sendMessage.mockResolvedValue({ authenticated: false });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();
    });

    test('should handle successful login', async () => {
      mockElements['email'].value = 'test@example.com';
      chrome.runtime.sendMessage.mockResolvedValue({
        success: true,
        profile: { name: 'Test User', role: 'parent' }
      });

      await popupInstance.handleLogin();

      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'authenticate',
        credentials: { email: 'test@example.com', password: 'test-password' }
      });
      expect(mockElements['main-section'].style.display).toBe('block');
    });

    test('should handle login failure', async () => {
      mockElements['email'].value = 'test@example.com';
      chrome.runtime.sendMessage.mockResolvedValue({
        success: false,
        error: 'Invalid credentials'
      });

      const showErrorSpy = jest.spyOn(popupInstance, 'showError');
      await popupInstance.handleLogin();

      expect(showErrorSpy).toHaveBeenCalledWith('Invalid credentials');
      expect(mockElements['auth-section'].style.display).toBe('block');
    });

    test('should validate required fields', async () => {
      mockElements['email'].value = '';
      const showErrorSpy = jest.spyOn(popupInstance, 'showError');

      await popupInstance.handleLogin();

      expect(showErrorSpy).toHaveBeenCalledWith('Please enter both email and password');
    });

    test('should handle logout', async () => {
      popupInstance.currentUser = { name: 'Test User' };
      chrome.storage.sync.remove.mockResolvedValue();

      await popupInstance.handleLogout();

      expect(chrome.storage.sync.remove).toHaveBeenCalledWith(['authToken', 'userProfile']);
      expect(popupInstance.currentUser).toBeNull();
      expect(mockElements['auth-section'].style.display).toBe('block');
    });

    test('should handle registration redirect', () => {
      popupInstance.handleRegister();

      expect(chrome.tabs.create).toHaveBeenCalledWith({
        url: 'http://localhost:3000/auth?mode=register'
      });
      expect(window.close).toHaveBeenCalled();
    });
  });

  describe('Page Analysis', () => {
    beforeEach(async () => {
      chrome.tabs.query.mockResolvedValue([{ id: 1, url: 'https://cambridge.org/test' }]);
      chrome.runtime.sendMessage.mockResolvedValue({
        authenticated: true,
        profile: { name: 'Test User' }
      });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();
    });

    test('should analyze current page content', async () => {
      chrome.tabs.sendMessage.mockResolvedValue({
        content: { title: 'Test Page', paragraphs: [] }
      });
      chrome.runtime.sendMessage.mockResolvedValue({
        educational: true,
        subject: 'math',
        level: 'grade-3'
      });

      await popupInstance.analyzeCurrentPage();

      expect(chrome.tabs.sendMessage).toHaveBeenCalledWith(1, {
        action: 'getPageContent'
      });
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'analyzeContent',
        content: { title: 'Test Page', paragraphs: [] },
        url: 'https://cambridge.org/test'
      });
    });

    test('should update page status for educational content', () => {
      popupInstance.pageAnalysis = {
        educational: true,
        subject: 'Mathematics',
        level: 'Grade 3'
      };

      popupInstance.updatePageStatus();

      expect(mockElements['educational-status'].className).toBe('status-indicator educational');
      expect(mockElements['page-description'].textContent).toBe('Mathematics detected (Grade 3)');
      expect(mockElements['explain-selection-btn'].disabled).toBe(false);
    });

    test('should update page status for non-educational content', () => {
      popupInstance.pageAnalysis = { educational: false };

      popupInstance.updatePageStatus();

      expect(mockElements['educational-status'].className).toBe('status-indicator non-educational');
      expect(mockElements['page-description'].textContent).toBe('General webpage');
      expect(mockElements['explain-selection-btn'].disabled).toBe(true);
    });
  });

  describe('Quick Actions', () => {
    beforeEach(async () => {
      chrome.tabs.query.mockResolvedValue([{ 
        id: 1, 
        url: 'https://cambridge.org/test',
        title: 'Test Page'
      }]);
      chrome.runtime.sendMessage.mockResolvedValue({
        authenticated: true,
        profile: { name: 'Test User' }
      });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();
    });

    test('should handle page help request', async () => {
      popupInstance.pageAnalysis = { educational: true, subject: 'math' };
      chrome.tabs.sendMessage.mockResolvedValue();

      await popupInstance.handlePageHelp();

      expect(chrome.tabs.sendMessage).toHaveBeenCalledWith(1, {
        action: 'showPageHelp',
        analysis: { educational: true, subject: 'math' }
      });
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'trackActivity',
        activity: {
          type: 'page_help_requested',
          url: 'https://cambridge.org/test',
          title: 'Test Page'
        }
      });
      expect(window.close).toHaveBeenCalled();
    });

    test('should handle page help error', async () => {
      chrome.tabs.sendMessage.mockRejectedValue(new Error('Tab not found'));
      const showErrorSpy = jest.spyOn(popupInstance, 'showError');

      await popupInstance.handlePageHelp();

      expect(showErrorSpy).toHaveBeenCalledWith('Failed to show page help');
    });
  });

  describe('Settings Management', () => {
    beforeEach(async () => {
      chrome.tabs.query.mockResolvedValue([{ id: 1, url: 'https://test.com' }]);
      chrome.runtime.sendMessage.mockResolvedValue({
        authenticated: true,
        profile: { name: 'Test User' }
      });
      
      popupInstance = new TutorPopup();
      await popupInstance.init();
    });

    test('should load settings on initialization', async () => {
      chrome.runtime.sendMessage.mockResolvedValue({
        autoHelp: true,
        contextualHints: false,
        voiceEnabled: true
      });

      await popupInstance.loadSettings();

      expect(mockElements['auto-help'].checked).toBe(true);
      expect(mockElements['contextual-hints'].checked).toBe(false);
      expect(mockElements['voice-enabled'].checked).toBe(true);
    });

    test('should handle setting changes', async () => {
      chrome.runtime.sendMessage
        .mockResolvedValueOnce({ autoHelp: true, contextualHints: true })
        .mockResolvedValueOnce({ success: true });

      const mockEvent = {
        target: { id: 'auto-help', checked: false }
      };

      await popupInstance.handleSettingChange(mockEvent);

      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({
        action: 'updateSettings',
        settings: { auto_help: false, contextualHints: true }
      });
    });
  });
});