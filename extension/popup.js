/**
 * Cambridge AI Tutor Chrome Extension - Popup Script
 * Handles popup interface interactions and communication with background script
 */

class TutorPopup {
  constructor() {
    this.currentUser = null;
    this.currentTab = null;
    this.pageAnalysis = null;
    
    this.init();
  }

  async init() {
    // Get current tab information
    await this.getCurrentTab();
    
    // Check authentication status
    await this.checkAuthStatus();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Analyze current page
    await this.analyzeCurrentPage();
    
    // Load user settings
    await this.loadSettings();
  }

  async getCurrentTab() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      this.currentTab = tab;
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
    // Authentication
    document.getElementById('login-btn').addEventListener('click', this.handleLogin.bind(this));
    document.getElementById('register-link').addEventListener('click', this.handleRegister.bind(this));
    document.getElementById('forgot-link').addEventListener('click', this.handleForgotPassword.bind(this));
    document.getElementById('logout-btn').addEventListener('click', this.handleLogout.bind(this));
    
    // Quick actions
    document.getElementById('help-page-btn').addEventListener('click', this.handlePageHelp.bind(this));
    document.getElementById('explain-selection-btn').addEventListener('click', this.handleExplainSelection.bind(this));
    document.getElementById('practice-btn').addEventListener('click', this.handlePractice.bind(this));
    
    // Settings
    document.getElementById('auto-help').addEventListener('change', this.handleSettingChange.bind(this));
    document.getElementById('contextual-hints').addEventListener('change', this.handleSettingChange.bind(this));
    document.getElementById('voice-enabled').addEventListener('change', this.handleSettingChange.bind(this));
    
    // Error handling
    document.getElementById('retry-btn').addEventListener('click', this.handleRetry.bind(this));
    
    // Enter key for login
    document.getElementById('password').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.handleLogin();
      }
    });
  }

  async handleLogin() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
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
        await this.analyzeCurrentPage();
      } else {
        this.showAuthSection();
        this.showError(response.error || 'Login failed');
      }
    } catch (error) {
      this.showAuthSection();
      this.showError('Login failed. Please try again.');
      console.error('Login error:', error);
    }
  }

  handleRegister() {
    // Open registration page in new tab
    chrome.tabs.create({
      url: 'http://localhost:3000/auth?mode=register'
    });
    window.close();
  }

  handleForgotPassword() {
    // Open forgot password page in new tab
    chrome.tabs.create({
      url: 'http://localhost:3000/auth?mode=forgot'
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
      // Send message to content script to show page help
      await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'showPageHelp',
        analysis: this.pageAnalysis
      });
      
      // Track activity
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

  async handleExplainSelection() {
    if (!this.currentTab) {
      this.showError('No active tab found');
      return;
    }
    
    try {
      // Get selected text from content script
      const response = await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'getSelectedText'
      });
      
      if (response && response.selectedText) {
        // Request explanation from background script
        const explanation = await chrome.runtime.sendMessage({
          action: 'askQuestion',
          question: `Please explain: ${response.selectedText}`,
          context: {
            pageUrl: this.currentTab.url,
            pageTitle: this.currentTab.title,
            selectedText: response.selectedText
          }
        });
        
        // Show explanation in content script
        await chrome.tabs.sendMessage(this.currentTab.id, {
          action: 'showExplanation',
          explanation: explanation.answer,
          selectedText: response.selectedText
        });
        
        window.close();
      } else {
        this.showError('No text selected. Please select text on the page first.');
      }
    } catch (error) {
      console.error('Explain selection error:', error);
      this.showError('Failed to explain selection');
    }
  }

  async handlePractice() {
    if (!this.pageAnalysis || !this.pageAnalysis.educational) {
      // Open general practice page
      chrome.tabs.create({
        url: 'http://localhost:3000/practice'
      });
    } else {
      // Open practice page for current subject
      const subject = this.pageAnalysis.subject || 'general';
      chrome.tabs.create({
        url: `http://localhost:3000/practice?subject=${subject}&level=${this.pageAnalysis.level || 'auto'}`
      });
    }
    
    window.close();
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

  handleRetry() {
    this.init();
  }

  async analyzeCurrentPage() {
    if (!this.currentTab || !this.currentUser) {
      return;
    }
    
    try {
      // Get page content from content script
      const contentResponse = await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'getPageContent'
      });
      
      if (contentResponse && contentResponse.content) {
        // Analyze content with background script
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
        document.getElementById('auto-help').checked = settings.autoHelp || false;
        document.getElementById('contextual-hints').checked = settings.contextualHints || false;
        document.getElementById('voice-enabled').checked = settings.voiceEnabled || false;
      }
    } catch (error) {
      console.error('Settings load error:', error);
    }
  }

  updateUserInfo() {
    if (!this.currentUser) return;
    
    const userInitial = document.getElementById('user-initial');
    const userName = document.getElementById('user-name');
    const userRole = document.getElementById('user-role');
    
    userInitial.textContent = this.currentUser.name ? this.currentUser.name.charAt(0).toUpperCase() : 'U';
    userName.textContent = this.currentUser.name || 'User';
    userRole.textContent = this.currentUser.role || 'Parent';
  }

  updatePageStatus(hasAnalysis = true) {
    const statusIndicator = document.getElementById('educational-status');
    const pageDescription = document.getElementById('page-description');
    const explainBtn = document.getElementById('explain-selection-btn');
    
    if (!hasAnalysis || !this.pageAnalysis) {
      statusIndicator.className = 'status-indicator non-educational';
      statusIndicator.textContent = '●';
      pageDescription.textContent = 'No educational content detected';
      explainBtn.disabled = true;
      return;
    }
    
    if (this.pageAnalysis.educational) {
      statusIndicator.className = 'status-indicator educational';
      statusIndicator.textContent = '●';
      
      const subject = this.pageAnalysis.subject || 'Educational content';
      const level = this.pageAnalysis.level ? ` (${this.pageAnalysis.level})` : '';
      pageDescription.textContent = `${subject} detected${level}`;
      
      explainBtn.disabled = false;
    } else {
      statusIndicator.className = 'status-indicator non-educational';
      statusIndicator.textContent = '●';
      pageDescription.textContent = 'General webpage';
      explainBtn.disabled = true;
    }
  }

  showAuthSection() {
    this.hideAllSections();
    document.getElementById('auth-section').style.display = 'block';
  }

  showMainSection() {
    this.hideAllSections();
    document.getElementById('main-section').style.display = 'block';
  }

  showLoadingSection() {
    this.hideAllSections();
    document.getElementById('loading-section').style.display = 'block';
  }

  showErrorSection(message) {
    this.hideAllSections();
    document.getElementById('error-section').style.display = 'block';
    document.getElementById('error-text').textContent = message;
  }

  hideAllSections() {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
      section.style.display = 'none';
    });
  }

  showError(message) {
    // Create or update error message in current section
    let errorDiv = document.querySelector('.error-message-inline');
    
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'error-message-inline';
      errorDiv.style.cssText = `
        background: #ffebee;
        color: #c62828;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 8px 0;
        font-size: 12px;
        border-left: 3px solid #f44336;
      `;
      
      const authForm = document.querySelector('.auth-form');
      if (authForm) {
        authForm.appendChild(errorDiv);
      }
    }
    
    errorDiv.textContent = message;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (errorDiv && errorDiv.parentNode) {
        errorDiv.parentNode.removeChild(errorDiv);
      }
    }, 5000);
  }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new TutorPopup();
});